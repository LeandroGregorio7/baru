# -*- coding: utf-8 -*-
"""
Report Generator Module
Generate validation reports in various formats without external dependencies
"""

import os
import csv
from datetime import datetime
import pandas as pd
import numpy as np

class ReportGenerator:
    """Generate validation reports using HTML/CSS for better compatibility"""

    def __init__(self):
        """Initialize report generator"""
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate(self, file_path, results, format_type='html', 
                 include_confusion=True, include_charts=False):
        """
        Generate report in specified format
        
        Args:
            file_path: Output file path
            results: Validation results dictionary
            format_type: 'html' or 'csv' (PDF removed due to reportlab dependency)
            include_confusion: Include confusion matrix
            include_charts: Include charts (not implemented yet)
        """
        format_type = format_type.lower()
        
        # If user selected PDF, we force HTML since we want to avoid reportlab
        # Most modern browsers/OSs can print HTML to PDF easily
        if format_type == 'pdf' or format_type == 'html':
            # Ensure extension is .html if we are generating HTML
            if format_type == 'pdf' and not file_path.lower().endswith('.html'):
                file_path = os.path.splitext(file_path)[0] + ".html"
            self._generate_html(file_path, results, include_confusion)
        elif format_type == 'csv':
            self._generate_csv(file_path, results)
        else:
            # Default to HTML if unknown
            self._generate_html(file_path, results, include_confusion)

    def _generate_html(self, file_path, results, include_confusion):
        """Generate a high-quality HTML report that looks professional and can be printed to PDF"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Baru Validator - Relatório de Validação</title>
            <style>
                :root {{
                    --primary-color: #1f4788;
                    --secondary-color: #2c3e50;
                    --accent-color: #3498db;
                    --bg-color: #f4f7f6;
                    --text-color: #333;
                    --border-color: #ddd;
                }}
                
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    line-height: 1.6; 
                    color: var(--text-color); 
                    background-color: var(--bg-color);
                    margin: 0;
                    padding: 40px 20px;
                }}
                
                .container {{ 
                    max-width: 1000px; 
                    margin: 0 auto; 
                    background-color: white; 
                    padding: 40px; 
                    border-radius: 8px; 
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                
                header {{
                    text-align: center;
                    border-bottom: 3px solid var(--primary-color);
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                }}
                
                h1 {{ color: var(--primary-color); margin: 0; font-size: 28px; }}
                h2 {{ 
                    color: var(--primary-color); 
                    border-left: 5px solid var(--primary-color);
                    padding-left: 15px;
                    margin-top: 40px;
                    font-size: 22px;
                }}
                
                .meta {{ color: #7f8c8d; font-size: 0.9em; margin-top: 10px; }}
                
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }}
                
                .metric-card {{
                    background: #fff;
                    border: 1px solid var(--border-color);
                    border-radius: 6px;
                    padding: 20px;
                    text-align: center;
                    transition: transform 0.2s;
                }}
                
                .metric-card:hover {{ transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,0,0,0.05); }}
                
                .metric-title {{ font-size: 0.9em; color: #7f8c8d; text-transform: uppercase; margin-bottom: 10px; }}
                .metric-value {{ font-size: 1.8em; font-weight: bold; color: var(--primary-color); }}
                .metric-desc {{ font-size: 0.85em; color: #95a5a6; margin-top: 5px; }}
                
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 20px 0; 
                    font-size: 0.95em;
                }}
                
                th {{ 
                    background-color: var(--primary-color); 
                    color: white; 
                    padding: 12px 15px; 
                    text-align: left; 
                }}
                
                td {{ 
                    padding: 10px 15px; 
                    border-bottom: 1px solid var(--border-color); 
                }}
                
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                tr:hover {{ background-color: #f1f1f1; }}
                
                .confusion-matrix-container {{ overflow-x: auto; }}
                .confusion-matrix th, .confusion-matrix td {{ text-align: center; }}
                .confusion-matrix th:first-child {{ text-align: left; }}
                
                .diagonal {{ background-color: rgba(31, 71, 136, 0.1) !important; font-weight: bold; }}
                
                footer {{
                    margin-top: 50px;
                    text-align: center;
                    font-size: 0.8em;
                    color: #bdc3c7;
                    border-top: 1px solid #eee;
                    padding-top: 20px;
                }}
                
                @media print {{
                    body {{ background-color: white; padding: 0; }}
                    .container {{ box-shadow: none; border: none; width: 100%; max-width: none; }}
                    .metric-card {{ break-inside: avoid; }}
                    h2 {{ break-after: avoid; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>Baru Validator - Relatório de Validação</h1>
                    <div class="meta">Gerado em: {self.timestamp}</div>
                </header>

                <h2>Resumo das Métricas</h2>
                <div class="metrics-grid">
        """

        # Overall Accuracy
        if 'overall_accuracy' in results:
            oa = results['overall_accuracy']
            html_content += f"""
                    <div class="metric-card">
                        <div class="metric-title">Acurácia Global</div>
                        <div class="metric-value">{oa*100:.2f}%</div>
                        <div class="metric-desc">Proporção total de acertos</div>
                    </div>
            """

        # Cohen's Kappa
        if 'kappa' in results:
            kappa = results['kappa']
            interpretation = self._interpret_kappa(kappa)
            html_content += f"""
                    <div class="metric-card">
                        <div class="metric-title">Índice Kappa</div>
                        <div class="metric-value">{kappa:.4f}</div>
                        <div class="metric-desc">{interpretation}</div>
                    </div>
            """

        # QADI Index
        if 'qadi' in results:
            qadi = results['qadi']
            html_content += f"""
                    <div class="metric-card">
                        <div class="metric-title">Índice QADI</div>
                        <div class="metric-value">{qadi:.4f}</div>
                        <div class="metric-desc">Quanto menor, melhor</div>
                    </div>
            """

        # MCC
        if 'mcc' in results:
            mcc = results['mcc']
            html_content += f"""
                    <div class="metric-card">
                        <div class="metric-title">MCC</div>
                        <div class="metric-value">{mcc:.4f}</div>
                        <div class="metric-desc">Coef. de Corr. de Matthews</div>
                    </div>
            """

        html_content += "</div>"

        # Detailed Stats Table
        html_content += """
                <h2>Estatísticas por Classe</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Classe</th>
                            <th>F1-Score</th>
                            <th>Acurácia do Produtor (Recall)</th>
                            <th>Acurácia do Usuário (Precision)</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Get all classes from any of the dictionaries
        all_classes = set()
        for key in ['f1_scores', 'producer_accuracy', 'user_accuracy']:
            if key in results:
                all_classes.update(results[key].keys())
        
        for cls in sorted(all_classes):
            f1 = f"{results['f1_scores'].get(cls, 0):.4f}" if 'f1_scores' in results else "-"
            pa = f"{results['producer_accuracy'].get(cls, 0):.4f}" if 'producer_accuracy' in results else "-"
            ua = f"{results['user_accuracy'].get(cls, 0):.4f}" if 'user_accuracy' in results else "-"
            
            html_content += f"""
                        <tr>
                            <td><strong>{cls}</strong></td>
                            <td>{f1}</td>
                            <td>{pa}</td>
                            <td>{ua}</td>
                        </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
        """

        # Confusion Matrix
        if include_confusion and 'confusion_matrix' in results:
            cm_df = results['confusion_matrix']
            html_content += """
                <h2>Matriz de Confusão</h2>
                <div class="confusion-matrix-container">
                    <table class="confusion-matrix">
                        <thead>
                            <tr>
                                <th>Referência \\ Classificado</th>
            """
            for col in cm_df.columns:
                html_content += f"<th>{col}</th>"
            html_content += "</tr></thead><tbody>"
            
            for idx in cm_df.index:
                html_content += f"<tr><td><strong>{idx}</strong></td>"
                for col in cm_df.columns:
                    val = int(cm_df.loc[idx, col])
                    is_diagonal = " class='diagonal'" if idx == col else ""
                    html_content += f"<td{is_diagonal}>{val}</td>"
                html_content += "</tr>"
            
            html_content += "</tbody></table></div>"

        html_content += """
                <footer>
                    Plugin Baru Validator para QGIS - Desenvolvido para Validação de Modelos de ML
                </footer>
            </div>
        </body>
        </html>
        """

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _generate_csv(self, file_path, results):
        """Generate CSV report"""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            writer.writerow(['Baru Validator - Relatório de Validação'])
            writer.writerow(['Gerado em', self.timestamp])
            writer.writerow([])

            # Overall Accuracy
            if 'overall_accuracy' in results:
                writer.writerow(['Acurácia Global', results['overall_accuracy']])

            # Cohen's Kappa
            if 'kappa' in results:
                writer.writerow(['Índice Kappa', results['kappa']])

            # QADI
            if 'qadi' in results:
                writer.writerow(['Índice QADI', results['qadi']])

            # MCC
            if 'mcc' in results:
                writer.writerow(['Coeficiente de Correlação de Matthews', results['mcc']])

            writer.writerow([])
            writer.writerow(['Estatísticas por Classe'])
            writer.writerow(['Classe', 'F1-Score', 'Acurácia do Produtor', 'Acurácia do Usuário'])
            
            all_classes = set()
            for key in ['f1_scores', 'producer_accuracy', 'user_accuracy']:
                if key in results:
                    all_classes.update(results[key].keys())
            
            for cls in sorted(all_classes):
                f1 = results['f1_scores'].get(cls, "") if 'f1_scores' in results else ""
                pa = results['producer_accuracy'].get(cls, "") if 'producer_accuracy' in results else ""
                ua = results['user_accuracy'].get(cls, "") if 'user_accuracy' in results else ""
                writer.writerow([cls, f1, pa, ua])

    def export_csv(self, file_path, results):
        """Export results to CSV"""
        self._generate_csv(file_path, results)

    @staticmethod
    def _interpret_kappa(kappa):
        """Interpret Kappa value"""
        if kappa < 0:
            return "Concordância Pobre"
        elif kappa < 0.2:
            return "Concordância Leve"
        elif kappa < 0.4:
            return "Concordância Razoável"
        elif kappa < 0.6:
            return "Concordância Moderada"
        elif kappa < 0.8:
            return "Concordância Substancial"
        else:
            return "Concordância Quase Perfeita"
