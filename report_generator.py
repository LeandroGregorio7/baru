# -*- coding: utf-8 -*-
"""
Report Generator Module - V12 (Final Decision Version)
Includes Model Ranking, Automated Conclusion, and Interactive Class Filtering.
"""

import os
import re
import json
from datetime import datetime
import pandas as pd
import numpy as np

class ReportGenerator:
    """Generate professional validation reports using HTML/CSS/JS"""

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _safe_float(self, val):
        """Conversor Absoluto: Impede qualquer erro de conversão de texto para número"""
        try:
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                val = re.sub(r'<[^>]+>', '', val).strip()
                val = re.sub(r'[^\d.,-]', '', val)
                val = val.replace(',', '.')
                if not val: return 0.0
            return float(val)
        except Exception:
            return 0.0

    def generate(self, file_path, results):
        if not file_path.lower().endswith(('.html', '.htm')):
            file_path = str(file_path) + ".html"
        self._generate_html(file_path, results)

    def _generate_html(self, file_path, results):
        """Builds the Individual Report with JSON metadata"""
        metrics_dict = {
            "oa": self._safe_float(results.get('overall_accuracy', 0)),
            "kappa": self._safe_float(results.get('kappa', 0)),
            "qadi": self._safe_float(results.get('qadi', 0)),
            "mcc": self._safe_float(results.get('mcc', 0)),
            "classes": {}
        }
        for cls in results.get('f1_scores', {}).keys():
            metrics_dict["classes"][str(cls)] = {
                "f1": self._safe_float(results['f1_scores'].get(cls, 0)),
                "pa": self._safe_float(results['producer_accuracy'].get(cls, 0)),
                "ua": self._safe_float(results['user_accuracy'].get(cls, 0))
            }
        json_data = json.dumps(metrics_dict)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"<html><body><script id='metrics-data' type='application/json'>{json_data}</script>Relatório Individual Gerado</body></html>")

    # =====================================================================
    # MÓDULO CONSOLIDADOR (Dashboard Master V12)
    # =====================================================================
    def generate_master_dashboard(self, file_path, models_data):
        if not file_path.lower().endswith(('.html', '.htm')):
            file_path = str(file_path) + ".html"
            
        parsed_models = []
        all_classes = set()
        
        for model in models_data:
            data = self._parse_accuracy_html(model['acc_path'])
            data['name'] = model['name']
            if 'classes' in data:
                for cls_id in data['classes'].keys():
                    all_classes.add(cls_id)
            shap_html, top_band = self._parse_shap_html(model['shap_path'])
            data['shap_html'] = shap_html
            data['top_band'] = top_band
            parsed_models.append(data)
            
        html = self._build_master_html(parsed_models, sorted(list(all_classes)))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)

    def _parse_accuracy_html(self, path):
        res = {'oa': '0.0000', 'kappa': '0.0000', 'qadi': '0.0000', 'mcc': '0.0000', 'classes': {}, 'cm_html': ''}
        if not path or not os.path.exists(path): return res
        try:
            with open(path, 'r', encoding='utf-8') as f: html = f.read()
        except:
            try:
                with open(path, 'r', encoding='latin-1') as f: html = f.read()
            except: return res
            
        json_match = re.search(r'<script id="metrics-data" type="application/json">(.*?)</script>', html, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                res['oa'] = f"{self._safe_float(data.get('oa', 0)):.4f}"
                res['kappa'] = f"{self._safe_float(data.get('kappa', 0)):.4f}"
                res['qadi'] = f"{self._safe_float(data.get('qadi', 0)):.4f}"
                res['mcc'] = f"{self._safe_float(data.get('mcc', 0)):.4f}"
                for cls_id, m in data.get('classes', {}).items():
                    res['classes'][str(cls_id)] = {'f1': f"{self._safe_float(m.get('f1', 0)):.4f}", 'pa': f"{self._safe_float(m.get('pa', 0)):.4f}", 'ua': f"{self._safe_float(m.get('ua', 0)):.4f}"}
                cm_match = re.search(r'<table class="confusion-matrix.*?>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
                if cm_match: res['cm_html'] = f'<table class="confusion-matrix">{cm_match.group(1)}</table>'
                return res
            except: pass

        cards = re.findall(r'<div class="metric-card".*?>(.*?)</div>\s*</div>', html, re.DOTALL | re.IGNORECASE)
        for card in cards:
            title_m = re.search(r'class="metric-title">(.*?)</div>', card, re.IGNORECASE)
            value_m = re.search(r'class="metric-value">(.*?)</div>', card, re.IGNORECASE)
            if title_m and value_m:
                title, val = title_m.group(1).upper(), value_m.group(1)
                if 'KAPPA' in title: res['kappa'] = f"{self._safe_float(val):.4f}"
                elif 'QADI' in title: res['qadi'] = f"{self._safe_float(val):.4f}"
                elif 'MCC' in title: res['mcc'] = f"{self._safe_float(val):.4f}"
                elif 'OVERALL' in title or 'OA' in title: res['oa'] = f"{self._safe_float(val):.4f}"

        tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
        for table in tables:
            if any(x in table.upper() for x in ['OVERALL ACCURACY', 'OA', 'KAPPA']):
                tds = re.findall(r'<td[^>]*>(.*?)</td>', table, re.DOTALL | re.IGNORECASE)
                nums = [self._safe_float(t) for t in tds]
                if len(nums) >= 4: res['oa'], res['kappa'], res['qadi'], res['mcc'] = [f"{n:.4f}" for n in nums[:4]]
            elif any(x in table.upper() for x in ['F1-SCORE', 'RECALL', 'PRODUTOR']):
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.IGNORECASE)
                for r in rows:
                    tds = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL | re.IGNORECASE)
                    if len(tds) >= 4:
                        cls_id = re.sub(r'<[^>]+>', '', tds[0]).strip()
                        if cls_id.isdigit() or cls_id.lower() != 'classe':
                            res['classes'][cls_id] = {'f1': f"{self._safe_float(tds[1]):.4f}", 'pa': f"{self._safe_float(tds[2]):.4f}", 'ua': f"{self._safe_float(tds[3]):.4f}"}
            elif 'diagonal' in table.lower() or 'referência' in table.lower():
                res['cm_html'] = f'<table class="confusion-matrix">{table}</table>'

        if res['oa'] == '0.0000' and res['cm_html']:
            try:
                nums = [int(n) for n in re.findall(r'<td[^>]*>(\d+)</td>', res['cm_html'])]
                diagonal = re.findall(r"class=['\"]diagonal['\"][^>]*>(\d+)</td>", res['cm_html'])
                if diagonal and nums:
                    correct, total = sum([int(d) for d in diagonal]), sum(nums)
                    if total > 0: res['oa'] = f"{(correct/total):.4f}"
            except: pass
        return res

    def _parse_shap_html(self, path):
        if not path or not os.path.exists(path): return "<p>Sem dados SHAP registados.</p>", "N/A"
        try:
            with open(path, 'r', encoding='utf-8') as f: html = f.read()
            rows = re.findall(r'<tr>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
            shap_rows = [f"<tr>{r}</tr>" for r in rows if 'bar-fill' in r]
            top_band = "Nenhuma"
            if shap_rows:
                band_m = re.search(r'<b>(.*?)</b>', shap_rows[0])
                if band_m: top_band = band_m.group(1)
            table_html = "<table class='shap-table'><thead><tr><th>Banda</th><th>Peso (%)</th><th>Impacto</th></tr></thead><tbody>" + "".join(shap_rows[:10]) + "</tbody></table>"
            return table_html, top_band
        except: return "<p>Erro ao ler SHAP.</p>", "N/A"

    def _build_master_html(self, models, all_classes):
        models_json, classes_json = json.dumps(models), json.dumps(all_classes)
        html_parts = []
        html_parts.append("<!DOCTYPE html><html lang='pt-br'><head><meta charset='UTF-8'><title>Dashboard Master V12 - Baru Validator</title>")
        html_parts.append("<script src='https://cdn.jsdelivr.net/npm/chart.js'></script><script src='https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js'></script>")
        html_parts.append("<style>:root { --primary: #1f4788; --baru: #a4161a; --bg: #f4f7f6; --text: #333; --gold: #f1c40f; --silver: #bdc3c7; --bronze: #cd7f32; }")
        html_parts.append("body { font-family: 'Segoe UI', sans-serif; background: var(--bg); margin: 0; color: var(--text); }")
        html_parts.append(".top-bar { background: #111; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; position: sticky; top:0; z-index: 1000; box-shadow: 0 2px 10px rgba(0,0,0,0.3); }")
        html_parts.append(".filter-box { background: #222; padding: 10px 20px; border-radius: 5px; display: flex; align-items: center; gap: 15px; }")
        html_parts.append("select { padding: 8px; border-radius: 4px; border: none; font-weight: bold; background: var(--primary); color: white; cursor: pointer; }")
        html_parts.append(".container { max-width: 1200px; margin: 30px auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }")
        html_parts.append("h1, h2 { color: var(--primary); } table { width: 100%; border-collapse: collapse; margin: 20px 0; border-radius: 8px; overflow: hidden; }")
        html_parts.append("th { background: var(--primary); color: white; padding: 15px; } td { padding: 12px; text-align: center; border-bottom: 1px solid #eee; }")
        html_parts.append(".highlight { background: #fff8f8; font-weight: bold; color: var(--baru); } .diagonal { background: #d4edda; font-weight: bold; }")
        html_parts.append(".grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; } .card { border: 1px solid #eee; padding: 20px; border-radius: 10px; background: #fafafa; }")
        html_parts.append(".ranking-badge { padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 0.8em; color: white; text-transform: uppercase; }")
        html_parts.append(".rank-1 { background: var(--gold); } .rank-2 { background: var(--silver); } .rank-3 { background: var(--bronze); }")
        html_parts.append(".conclusion-box { background: #e8f4fd; padding: 30px; border-radius: 10px; border-left: 8px solid var(--primary); margin: 40px 0; line-height: 1.6; font-size: 1.1em; }")
        html_parts.append(".shap-table { font-size: 12px; } .bar-bg { background: #eee; height: 12px; border-radius: 6px; width: 100px; } .bar-fill { background: var(--primary); height: 100%; border-radius: 6px; }")
        html_parts.append(".btn-export { background: #27ae60; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }</style></head><body>")
        
        html_parts.append("<div class='top-bar'><div style='font-size: 1.4em; font-weight: bold;'>Baru Validator <span style='color:#3498db'>Master V12</span></div>")
        html_parts.append("<div class='filter-box'><span>Analisar Classe:</span><select id='classFilter' onchange='updateDashboard()'>")
        for cls in all_classes:
            label = f"Baru ({cls})" if str(cls) == "1" else f"Classe {cls}"
            html_parts.append(f"<option value='{cls}' {'selected' if str(cls)=='1' else ''}>{label}</option>")
        html_parts.append("</select></div><button class='btn-export' onclick='exportPDF()'>Exportar PDF</button></div>")
        
        html_parts.append("<div id='report-content' class='container'><header style='text-align:center; margin-bottom:40px;'><h1>Relatório Consolidado e Ranking de Modelos</h1><p style='color:#666'>Gerado em " + self.timestamp + "</p></header>")
        
        html_parts.append("<h2>1. Conclusão Analítica Automática</h2><div class='conclusion-box' id='conclusionBox'>Processando conclusão...</div>")
        
        html_parts.append("<h2>2. Ranking Geral de Performance</h2><div id='rankingSection'></div>")
        
        html_parts.append("<h2>3. Comparativo Estatístico Global</h2><table id='globalTable'><thead><tr><th>Modelo</th><th>OA</th><th>Kappa</th><th>QADI</th><th>MCC</th></tr></thead><tbody id='globalBody'></tbody></table>")
        
        html_parts.append("<h2 id='classTitle'>4. Desempenho por Classe</h2><table id='classTable'><thead><tr><th>Modelo</th><th>F1-Score</th><th>Recall</th><th>Precision</th></tr></thead><tbody id='classBody'></tbody></table>")
        
        html_parts.append("<div style='margin: 40px 0;'><canvas id='metricsChart' height='100'></canvas></div>")
        
        html_parts.append("<h2>5. Detalhes Espaciais e Espectrais (SHAP)</h2><div class='grid-2' id='detailsGrid'></div></div>")
        
        html_parts.append(f"<script>const models = {models_json}; let chart = null;")
        html_parts.append("""
        function updateDashboard() {
            const cls = document.getElementById('classFilter').value;
            const isBaru = (cls === '1');
            document.getElementById('classTitle').innerText = `4. Desempenho Específico (Classe: ${isBaru ? 'Baru' : cls})`;
            
            // 1. Sort Models by Global (OA) and Class (F1)
            const sortedGlobal = [...models].sort((a, b) => parseFloat(b.oa) - parseFloat(a.oa));
            const sortedClass = [...models].sort((a, b) => {
                const f1A = parseFloat((a.classes[cls] || {f1:0}).f1);
                const f1B = parseFloat((b.classes[cls] || {f1:0}).f1);
                return f1B - f1A;
            });
            
            // 2. Build Global Table
            document.getElementById('globalBody').innerHTML = sortedGlobal.map(m => `<tr><td style='text-align:left; font-weight:bold;'>${m.name}</td><td>${m.oa}</td><td>${m.kappa}</td><td>${m.qadi}</td><td>${m.mcc}</td></tr>`).join('');
            
            // 3. Build Class Table
            document.getElementById('classBody').innerHTML = sortedClass.map(m => {
                const mc = m.classes[cls] || {f1:'0.0000', pa:'0.0000', ua:'0.0000'};
                return `<tr><td style='text-align:left; font-weight:bold;'>${m.name}</td><td class='highlight'>${mc.f1}</td><td>${mc.pa}</td><td>${mc.ua}</td></tr>`;
            }).join('');
            
            // 4. Build Ranking Section
            const bestGlobal = sortedGlobal[0];
            const bestClass = sortedClass[0];
            document.getElementById('rankingSection').innerHTML = `
                <div class='grid-2'>
                    <div class='card' style='border-top: 5px solid var(--primary);'>
                        <h4 style='margin-top:0;'>Vencedor Global (OA)</h4>
                        <div style='font-size:1.5em; font-weight:bold;'>${bestGlobal.name} <span class='ranking-badge rank-1'>1º Lugar</span></div>
                        <p style='color:#666;'>Maior acurácia no mapeamento de toda a área.</p>
                    </div>
                    <div class='card' style='border-top: 5px solid var(--baru);'>
                        <h4 style='margin-top:0;'>Vencedor de Classe (${isBaru ? 'Baru' : cls})</h4>
                        <div style='font-size:1.5em; font-weight:bold;'>${bestClass.name} <span class='ranking-badge rank-1'>1º Lugar</span></div>
                        <p style='color:#666;'>Melhor equilíbrio entre falsos positivos e negativos para este alvo.</p>
                    </div>
                </div>
            `;
            
            // 5. Build Conclusion
            const topModel = bestClass;
            const mcTop = topModel.classes[cls] || {f1:'0.0000'};
            const bands = topModel.top_band || 'N/A';
            const conclusion = `
                A análise comparativa aponta o modelo <strong>${topModel.name}</strong> como a escolha técnica superior para a detecção de <strong>${isBaru ? 'Baru' : 'Classe '+cls}</strong>, atingindo um F1-Score de <strong>${mcTop.f1}</strong>. 
                Este modelo demonstrou o menor grau de confusão espacial (falsos alarmes) e a maior robustez estatística. 
                A variável espectral de maior importância foi a banda <strong>${bands}</strong>, que atuou como o principal discriminador para separar este alvo dos demais. 
                Recomenda-se o uso do <strong>${topModel.name}</strong> para a extração dos shapes finais e replicação cartográfica.
            `;
            document.getElementById('conclusionBox').innerHTML = conclusion;
            
            // 6. Charts and Details
            const labels = models.map(m => m.name);
            const oaData = models.map(m => parseFloat(m.oa));
            const f1Data = models.map(m => parseFloat((m.classes[cls] || {f1:0}).f1));
            
            if(chart) chart.destroy();
            chart = new Chart(document.getElementById('metricsChart').getContext('2d'), {
                type: 'bar',
                data: { labels, datasets: [{label:'Global (OA)', data:oaData, backgroundColor:'#1f4788'}, {label:isBaru?'F1 (Baru)':`F1 (Cl ${cls})`, data:f1Data, backgroundColor:'#a4161a'}] },
                options: { scales: { y: { min: 0, max: 1 } } }
            });
            
            document.getElementById('detailsGrid').innerHTML = models.map(m => `
                <div class='card'>
                    <h3 style='text-align:center;'>${m.name}</h3>
                    <div style='font-size:0.9em;'><strong>Matriz de Confusão:</strong></div>${m.cm_html}
                    <div style='margin-top:15px; font-size:0.9em;'><strong>Importância (SHAP):</strong></div>${m.shap_html}
                </div>
            `).join('');
        }
        function exportPDF() { html2pdf().from(document.getElementById('report-content')).set({margin:10, filename:'Dashboard_Master_V12.pdf', jsPDF:{format:'a4', orientation:'portrait'}}).save(); }
        window.onload = updateDashboard;
        </script></body></html>""")
        return "".join(html_parts)

