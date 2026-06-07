# -*- coding: utf-8 -*-
"""
Baru Validator - QGIS Plugin for ML Model Validation
Main plugin class with validation metrics, UI and Master Dashboard
"""

import os
import re
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import (
    QAction, QFileDialog, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox, QCheckBox, QTabWidget, QWidget, 
    QTextEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QAbstractItemView, QInputDialog, QApplication
)

from qgis.core import (
    QgsRasterLayer, QgsVectorLayer, QgsProject, QgsFeature, QgsGeometry,
    QgsField, QgsMessageLog, Qgis, QgsMapLayer, QgsWkbTypes, QgsApplication,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsMapLayerProxyModel,
    QgsSpatialIndex, QgsDistanceArea
)
from qgis.gui import QgsMapLayerComboBox
from osgeo import gdal

from .validation_metrics import ValidationMetrics
from .confusion_matrix import ConfusionMatrix
from .report_generator import ReportGenerator
from .spatial_conformity import SpatialConformity

class BaruValidator:
    """QGIS Plugin for ML Model Validation in Baru Detection"""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = u'&Baru Validator'
        self.dialog = None
        self.report_generator = ReportGenerator()
        self.results = {}

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icons', 'baru_icon.png')
        if not os.path.exists(icon_path):
            icon_path = os.path.join(self.plugin_dir, 'icon.png')
            
        action = QAction(QIcon(icon_path), u'Baru Validator', self.iface.mainWindow())
        action.triggered.connect(self.run)
        
        self.iface.addPluginToMenu(self.menu, action)
        self.iface.addToolBarIcon(action)
        self.actions.append(action)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        if not self.dialog:
            self.dialog = QDialog(self.iface.mainWindow())
            self.dialog.setWindowTitle("Baru Validator - ML Validation Suite")
            self.dialog.resize(950, 750)
            
            main_layout = QVBoxLayout()
            self.tabs = QTabWidget()
            
            self.tab_individual = QWidget()
            self.setup_individual_tab()
            self.tabs.addTab(self.tab_individual, "Validação Individual")
            
            self.tab_dashboard = QWidget()
            self.setup_dashboard_tab()
            self.tabs.addTab(self.tab_dashboard, "Dashboard Consolidado (Master)")
            
            self.tab_conformity = QWidget()
            self.setup_conformity_tab()
            self.tabs.addTab(self.tab_conformity, "Avaliação Híbrida (Geo-Score)")
            
            main_layout.addWidget(self.tabs)
            self.dialog.setLayout(main_layout)

        self.dialog.show()
        
    def setup_individual_tab(self):
        layout = QVBoxLayout()
        group_inputs = QGroupBox("Input Data")
        vbox_inputs = QVBoxLayout()
        
        hbox_class = QHBoxLayout()
        hbox_class.addWidget(QLabel("Classified Layer (Raster/Vector):"))
        self.combo_classified = QgsMapLayerComboBox()
        self.combo_classified.setFilters(QgsMapLayerProxyModel.RasterLayer | QgsMapLayerProxyModel.VectorLayer)
        hbox_class.addWidget(self.combo_classified)
        
        hbox_class_field = QHBoxLayout()
        hbox_class_field.addWidget(QLabel("Class Field (if Vector):"))
        self.combo_class_field = QComboBox()
        hbox_class_field.addWidget(self.combo_class_field)
        
        hbox_val = QHBoxLayout()
        hbox_val.addWidget(QLabel("Validation Layer (Vector):"))
        self.combo_validation = QgsMapLayerComboBox()
        self.combo_validation.setFilters(QgsMapLayerProxyModel.VectorLayer)
        hbox_val.addWidget(self.combo_validation)
        
        hbox_val_field = QHBoxLayout()
        hbox_val_field.addWidget(QLabel("Validation Class Field:"))
        self.combo_val_field = QComboBox()
        hbox_val_field.addWidget(self.combo_val_field)
        
        vbox_inputs.addLayout(hbox_class)
        vbox_inputs.addLayout(hbox_class_field)
        vbox_inputs.addLayout(hbox_val)
        vbox_inputs.addLayout(hbox_val_field)
        group_inputs.setLayout(vbox_inputs)
        
        group_reports = QGroupBox("Reporting Options")
        vbox_reports = QVBoxLayout()
        self.cb_confusion = QCheckBox("Include Confusion Matrix")
        self.cb_confusion.setChecked(True)
        self.cb_charts = QCheckBox("Include Visual Charts")
        self.cb_charts.setChecked(True)
        vbox_reports.addWidget(self.cb_confusion)
        vbox_reports.addWidget(self.cb_charts)
        group_reports.setLayout(vbox_reports)
        
        hbox_buttons = QHBoxLayout()
        btn_validate = QPushButton("Run Validation")
        btn_validate.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold; padding: 8px;")
        btn_validate.clicked.connect(self.run_validation)
        
        btn_report = QPushButton("Generate Report (HTML/PDF)")
        btn_report.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        btn_report.clicked.connect(self.generate_report)
        
        hbox_buttons.addWidget(btn_validate)
        hbox_buttons.addWidget(btn_report)
        
        self.text_results = QTextEdit()
        self.text_results.setReadOnly(True)
        
        layout.addWidget(group_inputs)
        layout.addWidget(group_reports)
        layout.addWidget(self.text_results)
        layout.addLayout(hbox_buttons)
        self.tab_individual.setLayout(layout)
        
        self.combo_classified.layerChanged.connect(self.update_classified_fields)
        self.combo_validation.layerChanged.connect(self.update_validation_fields)
        self.update_classified_fields(self.combo_classified.currentLayer())
        self.update_validation_fields(self.combo_validation.currentLayer())

    def setup_dashboard_tab(self):
        layout = QVBoxLayout()
        lbl_info = QLabel("<b>Módulo Consolidado:</b> Adicione os relatórios HTML de acurácia e SHAP para comparar todos os modelos.")
        layout.addWidget(lbl_info)
        
        self.table_models = QTableWidget(0, 3)
        self.table_models.setHorizontalHeaderLabels(["Nome do Modelo", "Relatório Acurácia", "Relatório SHAP"])
        self.table_models.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_models.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table_models)
        
        hbox_table_btns = QHBoxLayout()
        btn_add_model = QPushButton("+ Adicionar Modelo")
        btn_add_model.clicked.connect(self.add_model_row)
        btn_remove_model = QPushButton("- Remover Modelo")
        btn_remove_model.clicked.connect(self.remove_model_row)
        hbox_table_btns.addWidget(btn_add_model)
        hbox_table_btns.addWidget(btn_remove_model)
        layout.addLayout(hbox_table_btns)
        
        btn_generate_master = QPushButton("Gerar Dashboard Master (HTML)")
        btn_generate_master.setStyleSheet("background-color: #1f4788; color: white; font-weight: bold; padding: 10px;")
        btn_generate_master.clicked.connect(self.generate_master_dashboard)
        layout.addWidget(btn_generate_master)
        
        self.tab_dashboard.setLayout(layout)

    def add_model_row(self):
        model_name, ok = QInputDialog.getText(self.dialog, "Novo Modelo", "Nome do Modelo (ex: Random Forest):")
        if ok and model_name:
            acc_path, _ = QFileDialog.getOpenFileName(self.dialog, f"Acurácia HTML para {model_name}", "", "HTML Files (*.html)")
            shap_path, _ = QFileDialog.getOpenFileName(self.dialog, f"SHAP HTML para {model_name} (Opcional)", "", "HTML Files (*.html)")
            
            row = self.table_models.rowCount()
            self.table_models.insertRow(row)
            self.table_models.setItem(row, 0, QTableWidgetItem(model_name))
            self.table_models.setItem(row, 1, QTableWidgetItem(acc_path if acc_path else ""))
            self.table_models.setItem(row, 2, QTableWidgetItem(shap_path if shap_path else ""))

    def remove_model_row(self):
        current_row = self.table_models.currentRow()
        if current_row >= 0:
            self.table_models.removeRow(current_row)

    def generate_master_dashboard(self):
        if self.table_models.rowCount() == 0:
            QMessageBox.warning(self.dialog, "Erro", "Adicione pelo menos um modelo.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self.dialog, "Salvar Dashboard Master", "Dashboard_Master.html", "HTML Files (*.html)")
        if not file_path:
            return
            
        models_data = []
        for row in range(self.table_models.rowCount()):
            m_name = self.table_models.item(row, 0).text()
            m_acc = self.table_models.item(row, 1).text()
            m_shap = self.table_models.item(row, 2).text()
            models_data.append({"name": m_name, "acc_path": m_acc, "shap_path": m_shap})
            
        try:
            self.report_generator.generate_master_dashboard(file_path, models_data)
            QMessageBox.information(self.dialog, "Sucesso", "Dashboard Master gerado com sucesso!")
        except Exception as e:
            QgsMessageLog.logMessage(traceback.format_exc(), 'Baru Validator', Qgis.Critical)
            QMessageBox.critical(self.dialog, "Erro", f"Erro ao gerar Dashboard Master:\n{str(e)}")

    def setup_conformity_tab(self):
        layout = QVBoxLayout()
        lbl_info = QLabel("<b>Módulo Híbrido:</b> Cruze a nota estatística (F1-Score Específico) com a coerência espacial (Geo-Score).")
        layout.addWidget(lbl_info)
        
        group_roi = QGroupBox("Parâmetros da Área")
        vbox_roi = QVBoxLayout()
        
        hbox_roi = QHBoxLayout()
        hbox_roi.addWidget(QLabel("Limites da Área (ROI - Vetor):"))
        self.combo_roi = QgsMapLayerComboBox()
        self.combo_roi.setFilters(QgsMapLayerProxyModel.VectorLayer)
        hbox_roi.addWidget(self.combo_roi)
        vbox_roi.addLayout(hbox_roi)
        
        hbox_params = QHBoxLayout()
        hbox_params.addWidget(QLabel("Tamanho médio da Copa (m²):"))
        self.input_patch_size = QTextEdit("150")
        self.input_patch_size.setMaximumHeight(30)
        hbox_params.addWidget(self.input_patch_size)
        
        hbox_params.addWidget(QLabel("ID da Classe Alvo:"))
        self.input_target_id = QTextEdit("1")
        self.input_target_id.setMaximumHeight(30)
        hbox_params.addWidget(self.input_target_id)
        vbox_roi.addLayout(hbox_params)
        
        hbox_params2 = QHBoxLayout()
        hbox_params2.addWidget(QLabel("Nome do Campo (Se for Vetor):"))
        self.input_class_field = QTextEdit("classe")
        self.input_class_field.setMaximumHeight(30)
        hbox_params2.addWidget(self.input_class_field)
        vbox_roi.addLayout(hbox_params2)
        
        group_roi.setLayout(vbox_roi)
        layout.addWidget(group_roi)
        
        group_models = QGroupBox("Modelos para Cruzamento Híbrido")
        vbox_models = QVBoxLayout()
        
        self.table_vectors = QTableWidget(0, 3)
        self.table_vectors.setHorizontalHeaderLabels(["Nome do Modelo", "Camada (Raster/Vetor)", "Relatório HTML (Estatística)"])
        self.table_vectors.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_vectors.setSelectionBehavior(QAbstractItemView.SelectRows)
        vbox_models.addWidget(self.table_vectors)
        
        hbox_vec_btns = QHBoxLayout()
        btn_add_vec = QPushButton("+ Adicionar Modelo Híbrido")
        btn_add_vec.clicked.connect(self.add_hybrid_row)
        btn_rem_vec = QPushButton("- Remover Modelo")
        btn_rem_vec.clicked.connect(self.remove_hybrid_row)
        hbox_vec_btns.addWidget(btn_add_vec)
        hbox_vec_btns.addWidget(btn_rem_vec)
        vbox_models.addLayout(hbox_vec_btns)
        
        group_models.setLayout(vbox_models)
        layout.addWidget(group_models)
        
        btn_run_conformity = QPushButton("Gerar Relatório Híbrido (HTML)")
        btn_run_conformity.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; padding: 12px; font-size: 14px;")
        btn_run_conformity.clicked.connect(self.run_conformity)
        layout.addWidget(btn_run_conformity)
        
        self.tab_conformity.setLayout(layout)

    def add_hybrid_row(self):
        model_name, ok = QInputDialog.getText(self.dialog, "Novo Modelo Híbrido", "Nome do Modelo:")
        if ok and model_name:
            layer_path, _ = QFileDialog.getOpenFileName(self.dialog, f"1. Selecione a Camada Classificada ({model_name})", "", "Raster & Vector Files (*.shp *.gpkg *.tif *.tiff)")
            if layer_path:
                html_path, _ = QFileDialog.getOpenFileName(self.dialog, f"2. Selecione o Relatório HTML de Acurácia ({model_name})", "", "HTML Files (*.html *.htm)")
                if html_path:
                    row = self.table_vectors.rowCount()
                    self.table_vectors.insertRow(row)
                    self.table_vectors.setItem(row, 0, QTableWidgetItem(model_name))
                    self.table_vectors.setItem(row, 1, QTableWidgetItem(layer_path))
                    self.table_vectors.setItem(row, 2, QTableWidgetItem(html_path))

    def remove_hybrid_row(self):
        current_row = self.table_vectors.currentRow()
        if current_row >= 0:
            self.table_vectors.removeRow(current_row)

    def extract_metrics_from_html(self, html_path, target_class_id):
        metrics = {'kappa': 0.0, 'oa': 0.0, 'f1': 0.0, 'recall': 0.0, 'precision': 0.0}
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()

            m_kappa = re.search(r'"kappa"\s*:\s*"([\d\.]+)"', content, re.IGNORECASE)
            if not m_kappa: m_kappa = re.search(r'Kappa[^\d]*([\d]+[\.,][\d]+)', content, re.IGNORECASE)
            if m_kappa: metrics['kappa'] = float(m_kappa.group(1).replace(',', '.'))

            m_oa = re.search(r'"oa"\s*:\s*"([\d\.]+)"', content, re.IGNORECASE)
            if not m_oa: m_oa = re.search(r'Overall Accuracy[^\d]*([\d]+[\.,][\d]+)', content, re.IGNORECASE)
            if m_oa: metrics['oa'] = float(m_oa.group(1).replace(',', '.'))

            class_pattern = rf'"[^"]*?(?:\({target_class_id}\)|{target_class_id})"\s*:\s*\{{([^}}]+)\}}'
            m_cls = re.search(class_pattern, content, re.IGNORECASE)
            if m_cls:
                inner_json = m_cls.group(1)
                f1_m = re.search(r'"f1"\s*:\s*"([\d\.]+)"', inner_json, re.IGNORECASE)
                pa_m = re.search(r'"pa"\s*:\s*"([\d\.]+)"', inner_json, re.IGNORECASE)
                ua_m = re.search(r'"ua"\s*:\s*"([\d\.]+)"', inner_json, re.IGNORECASE)
                
                if f1_m: metrics['f1'] = float(f1_m.group(1))
                if pa_m: metrics['recall'] = float(pa_m.group(1))
                if ua_m: metrics['precision'] = float(ua_m.group(1))
            else:
                row_pattern = rf'<tr[^>]*>.*?<td[^>]*>.*?(?:\({target_class_id}\)|{target_class_id}).*?</td>.*?<td[^>]*>\s*([\d\.,]+)\s*</td>.*?<td[^>]*>\s*([\d\.,]+)\s*</td>.*?<td[^>]*>\s*([\d\.,]+)\s*</td>'
                m_row = re.search(row_pattern, content, re.IGNORECASE | re.DOTALL)
                if m_row:
                    metrics['f1'] = float(m_row.group(1).replace(',', '.'))
                    metrics['recall'] = float(m_row.group(2).replace(',', '.'))
                    metrics['precision'] = float(m_row.group(3).replace(',', '.'))

            if metrics['f1'] == 0.0:
                m_any_f1 = re.search(r'(?:f1|f-score|f1-score)[^\d]*([\d]+[\.,][\d]+)', content, re.IGNORECASE)
                if m_any_f1:
                    metrics['f1'] = float(m_any_f1.group(1).replace(',', '.'))

        except Exception as e:
            QgsMessageLog.logMessage(f"Aviso Extração HTML: {str(e)}", 'Baru Validator', Qgis.Warning)
            
        return metrics

    def run_conformity(self):
        roi_layer = self.combo_roi.currentLayer()
        if not roi_layer:
            QMessageBox.warning(self.dialog, "Erro", "Selecione a camada de ROI (Limites da Área).")
            return
            
        if self.table_vectors.rowCount() == 0:
            QMessageBox.warning(self.dialog, "Erro", "Adicione pelo menos um modelo para gerar o relatório.")
            return

        try:
            target_class = int(self.input_target_id.toPlainText().strip())
        except ValueError:
            QMessageBox.warning(self.dialog, "Erro", "ID da Classe Alvo deve ser inteiro.")
            return
            
        class_field = self.input_class_field.toPlainText().strip()
        da = QgsDistanceArea()
        da.setSourceCrs(roi_layer.crs(), QgsProject.instance().transformContext())
        da.setEllipsoid(QgsProject.instance().ellipsoid())
        
        total_roi_area = 0.0
        for feat in roi_layer.getFeatures():
            if not feat.geometry().isNull():
                total_roi_area += da.measureArea(feat.geometry())
                
        if total_roi_area == 0:
            QMessageBox.warning(self.dialog, "Erro", "A área do ROI calculada é 0.")
            return

        out_path, _ = QFileDialog.getSaveFileName(self.dialog, "Salvar Dashboard Híbrido", "Dashboard_Hibrido_GeoScore.html", "HTML Files (*.html)")
        if not out_path:
            return

        spatial_eval = SpatialConformity()
        hybrid_data = []
        
        for row in range(self.table_vectors.rowCount()):
            model_name = self.table_vectors.item(row, 0).text()
            layer_path = self.table_vectors.item(row, 1).text()
            html_path = self.table_vectors.item(row, 2).text()
            
            metrics_stats = self.extract_metrics_from_html(html_path, target_class)
            
            if layer_path.lower().endswith(('.tif', '.tiff')):
                layer = QgsRasterLayer(layer_path, model_name)
            else:
                layer = QgsVectorLayer(layer_path, model_name, "ogr")
                
            if not layer.isValid():
                continue
                
            metrics_geo = spatial_eval.calculate_geo_score(layer, target_class, total_roi_area, class_field)
            if 'error' in metrics_geo:
                continue
                
            geo_score = metrics_geo['conformity_factor']
            f1_class = metrics_stats['f1']
            hybrid_score = (f1_class + geo_score) / 2.0
            
            hybrid_data.append({
                'name': model_name,
                'oa': metrics_stats['oa'],
                'kappa': metrics_stats['kappa'],
                'f1': f1_class,
                'recall': metrics_stats['recall'],
                'precision': metrics_stats['precision'],
                'geo_score': geo_score,
                'hybrid_score': hybrid_score,
                'area_ha': metrics_geo['total_area_sqm'] / 10000.0,
                'patches': metrics_geo['patch_count']
            })

        if not hybrid_data:
            QMessageBox.critical(self.dialog, "Erro", "Nenhum modelo válido processado.")
            return

        hybrid_data.sort(key=lambda x: x['hybrid_score'], reverse=True)
        best_stat = max(hybrid_data, key=lambda x: x['f1'])
        best_hybrid = hybrid_data[0]
        
        if best_stat['name'] != best_hybrid['name']:
            conclusion = f"<b>ALERTA DE OVERFITTING:</b> O modelo <b>{best_stat['name']}</b> obteve o maior F1-Score cego para a classe alvo (F1: {best_stat['f1']:.2f}), mas sofreu severa penalização espacial (Geo-Score: {best_stat['geo_score']:.2f}) por generalizar e superestimar a área do alvo de forma irrealista.<br><br><b>🥇 CONCLUSÃO:</b> O modelo tecnicamente recomendado é o <b>{best_hybrid['name']}</b>. Ele apresentou o melhor equilíbrio geral (Score Híbrido: {best_hybrid['hybrid_score']:.2f}), garantindo uma precisão estatística sólida combinada com uma distribuição espacial limpa e coerente no terreno."
        else:
            conclusion = f"<b>🥇 CONCLUSÃO PERFEITA:</b> O modelo <b>{best_hybrid['name']}</b> obteve o melhor desempenho absoluto, liderando tanto na precisão estatística para a classe alvo (F1: {best_hybrid['f1']:.2f}) %s tanto no realismo espacial (Geo-Score: {best_hybrid['geo_score']:.2f}). É o algoritmo definitivo para este mapeamento."

        table_rows = ""
        labels = [f"'{m['name']}'" for m in hybrid_data]
        data_f1 = [str(m['f1']) for m in hybrid_data]
        data_geo = [str(m['geo_score']) for m in hybrid_data]
        data_hybrid = [str(m['hybrid_score']) for m in hybrid_data]

        for i, m in enumerate(hybrid_data):
            row_class = "style='background-color: #d4edda; font-weight: bold;'" if i == 0 else ""
            table_rows += f"<tr {row_class}><td>{i+1}º</td><td style='text-align:left;'>{m['name']}</td><td>{m['oa']:.2f}</td><td>{m['kappa']:.2f}</td><td style='color:#a4161a;'><b>{m['f1']:.2f}</b></td><td>{m['recall']:.2f}</td><td>{m['precision']:.2f}</td><td>{m['geo_score']:.2f}</td><td><b style='color:#8e44ad; font-size:16px;'>{m['hybrid_score']:.2f}</b></td><td>{m['area_ha']:.2f}</td><td>{m['patches']}</td></tr>"

        html_content = f"""<!DOCTYPE html>
<html lang='pt-br'>
<head>
    <meta charset='UTF-8'>
    <title>Relatório Híbrido de Conformidade Espacial</title>
    <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #f4f7f6; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        h1, h2 {{ color: #1f4788; margin-top: 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
        th, td {{ padding: 12px; text-align: center; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #1f4788; color: white; }}
        th:nth-child(5) {{ background-color: #a4161a; }}
        th:nth-child(8) {{ background-color: #2ecc71; }}
        th:nth-child(9) {{ background-color: #8e44ad; }}
    </style>
</head>
<body>
    <div class='container'>
        <div class='card' style='border-top: 5px solid #8e44ad;'>
            <h1>🌍 Dashboard Híbrido: F1-Score Específico vs. Realismo Espacial</h1>
            <p><b>Classe Analisada:</b> ID {target_class} | <b>Área Total do Projeto (ROI):</b> {total_roi_area / 10000:.2f} hectares</p>
            <div style='background: #f8f9fa; padding: 15px; border-left: 5px solid #e74c3c; border-radius: 4px; font-size: 16px; line-height: 1.5;'>
                {conclusion}
            </div>
        </div>
        
        <div class='card'>
            <h2>📊 Matriz Comparativa (Ordenada por Score Híbrido)</h2>
            <table>
                <tr>
                    <th>Rank</th>
                    <th style='text-align:left;'>Modelo Analisado</th>
                    <th>OA Global</th>
                    <th>Kappa Global</th>
                    <th>F1-Score (Classe)</th>
                    <th>Recall (Classe)</th>
                    <th>Precision (Classe)</th>
                    <th>Geo-Score (Realismo)</th>
                    <th>SCORE HÍBRIDO FINAL</th>
                    <th>Área Predita (ha)</th>
                    <th>Copas Encontradas</th>
                </tr>
                {table_rows}
            </table>
        </div>
        
        <div class='card'>
            <h2>📈 Gráfico de Equilíbrio</h2>
            <canvas id='hybridChart' height='60'></canvas>
        </div>
    </div>
    <script>
        const ctx = document.getElementById('hybridChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: [{','.join(labels)}],
                datasets: [
                    {{ label: 'F1-Score (Classe Alvo)', data: [{','.join(data_f1)}], backgroundColor: '#e74c3c' }},
                    {{ label: 'Geo-Score (Realismo)', data: [{','.join(data_geo)}], backgroundColor: '#2ecc71' }},
                    {{ label: 'Score Híbrido Final', data: [{','.join(data_hybrid)}], backgroundColor: '#8e44ad' }}
                ]
            }},
            options: {{ scales: {{ y: {{ min: 0, max: 1 }} }} }}
        }});
    </script>
</body>
</html>"""

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        QMessageBox.information(self.dialog, "Sucesso", "Relatório Híbrido gerado com sucesso!")
        webbrowser.open('file://' + os.path.realpath(out_path))

    def update_classified_fields(self, layer):
        self.combo_class_field.clear()
        if layer and layer.type() == QgsMapLayer.VectorLayer:
            self.combo_class_field.setEnabled(True)
            for field in layer.fields():
                self.combo_class_field.addItem(field.name())
        else:
            self.combo_class_field.setEnabled(False)

    def update_validation_fields(self, layer):
        self.combo_val_field.clear()
        if layer:
            for field in layer.fields():
                self.combo_val_field.addItem(field.name())

    def run_validation(self):
        c_layer = self.combo_classified.currentLayer()
        v_layer = self.combo_validation.currentLayer()
        
        if not c_layer or not v_layer:
            QMessageBox.critical(self.dialog, "Error", "Please select both classified and validation layers.")
            return
            
        try:
            self.text_results.setText("Extracting values and matching geometry...\n")
            QApplication.processEvents()
            
            y_true, y_pred = self.extract_samples(c_layer, v_layer)
            
            if len(y_true) == 0:
                raise Exception("No valid overlapping samples found between the layers.")
                
            self.text_results.append(f"Successfully matched {len(y_true)} sample points.\n")
            self.text_results.append("Calculating advanced metrics...\n")
            QApplication.processEvents()
            
            metrics = ValidationMetrics.calculate_all_metrics(y_true, y_pred)
            cm_df = ConfusionMatrix.create_matrix(y_true, y_pred)
            
            self.results = {
                'metrics': metrics,
                'confusion_matrix': cm_df,
                'y_true': y_true,
                'y_pred': y_pred
            }
            
            summary = f"Overall Accuracy: {metrics['overall_accuracy']:.4f}\n"
            summary += f"Kappa Coefficient: {metrics['kappa']:.4f}\n"
            summary += f"QADI Index: {metrics['qadi']:.4f}\n"
            summary += f"MCC: {metrics['mcc']:.4f}\n\n"
            summary += ConfusionMatrix.format_matrix_for_display(cm_df)
            
            self.text_results.append(summary)
            
        except Exception as e:
            QgsMessageLog.logMessage(str(e), 'Baru Validator', Qgis.Critical)
            QgsMessageLog.logMessage(traceback.format_exc(), 'Baru Validator', Qgis.Critical)
            QMessageBox.critical(self.dialog, "Validation Error", str(e))

    def extract_samples(self, classified_layer, validation_layer):
        y_true = []
        y_pred = []
        
        val_field = self.combo_val_field.currentText()
        class_field = self.combo_class_field.currentText()
        
        transform = QgsCoordinateTransform(
            validation_layer.crs(),
            classified_layer.crs(),
            QgsProject.instance()
        )
        
        if classified_layer.type() == QgsMapLayer.RasterLayer:
            provider = classified_layer.dataProvider()
            for feat in validation_layer.getFeatures():
                geom = feat.geometry()
                if geom.isNull(): continue
                geom.transform(transform)
                pt = geom.centroid().asPoint()
                
                val, res = provider.sample(pt, 1)
                if res:
                    y_true.append(int(feat[val_field]))
                    y_pred.append(int(val))
        else:
            idx = QgsSpatialIndex(classified_layer.getFeatures())
            for feat in validation_layer.getFeatures():
                geom = feat.geometry()
                if geom.isNull(): continue
                geom.transform(transform)
                pt = geom.centroid().asPoint()
                
                intersect_ids = idx.intersects(geom.boundingBox())
                for fid in intersect_ids:
                    c_feat = classified_layer.getFeature(fid)
                    if c_feat.geometry().contains(pt):
                        y_true.append(int(feat[val_field]))
                        y_pred.append(int(c_feat[class_field]))
                        break

        return np.array(y_true), np.array(y_pred)

    def generate_report(self):
        if not self.results:
            QMessageBox.warning(self.dialog, "Warning", "Run validation first.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self.dialog, "Save Report", "Validation_Report.html", "HTML Files (*.html)")
        if file_path:
            self.report_generator.generate(file_path, self.results)
            QMessageBox.information(self.dialog, "Success", "Report generated successfully!")
