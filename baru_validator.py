# -*- coding: utf-8 -*-
"""
Baru Validator - QGIS Plugin for ML Model Validation
Main plugin class with validation metrics, UI and Master Dashboard
"""

import os
import traceback
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import (
    QAction, QFileDialog, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox, QCheckBox,
    QTabWidget, QWidget, QTextEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QInputDialog
)

from qgis.core import (
    QgsRasterLayer, QgsVectorLayer, QgsProject, QgsFeature, QgsGeometry,
    QgsField, QgsMessageLog, Qgis, QgsMapLayer, QgsWkbTypes, QgsApplication,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsMapLayerProxyModel,
    QgsSpatialIndex
)
from qgis.gui import QgsMapLayerComboBox
from osgeo import gdal

from .validation_metrics import ValidationMetrics
from .confusion_matrix import ConfusionMatrix
from .report_generator import ReportGenerator

class BaruValidator:
    """QGIS Plugin for ML Model Validation in Baru Detection"""

    def __init__(self, iface):
        """Initialize the plugin"""
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = u'&Baru Validator'
        self.dialog = None
        self.results = {}
        self.report_generator = ReportGenerator()

    def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=True, add_to_toolbar=True):
        icon = QIcon(icon_path)
        action = QAction(icon, text, self.iface.mainWindow())
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icons', 'baru_icon.png')
        self.add_action(icon_path, text=u'Validate ML Models', callback=self.run)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        if not self.dialog:
            self.dialog = QDialog(self.iface.mainWindow())
            self.dialog.setWindowTitle("Baru Validator - ML Validation Suite")
            self.dialog.resize(900, 700)
            
            main_layout = QVBoxLayout()
            self.tabs = QTabWidget()
            
            # Aba 1: Validação Individual
            self.tab_individual = QWidget()
            self.setup_individual_tab()
            self.tabs.addTab(self.tab_individual, "Validação Individual")
            
            # Aba 2: Dashboard Consolidado
            self.tab_dashboard = QWidget()
            self.setup_dashboard_tab()
            self.tabs.addTab(self.tab_dashboard, "Dashboard Consolidado (Master)")
            
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
        
        group_reports = QGroupBox("Report Options")
        hbox_reports = QHBoxLayout()
        self.check_include_confusion = QCheckBox("Include Confusion Matrix")
        self.check_include_confusion.setChecked(True)
        hbox_reports.addWidget(self.check_include_confusion)
        group_reports.setLayout(hbox_reports)
        
        hbox_buttons = QHBoxLayout()
        btn_validate = QPushButton("Run Validation")
        btn_validate.clicked.connect(self.run_validation)
        btn_report = QPushButton("Generate HTML Report")
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
            QMessageBox.warning(self.dialog, "Aviso", "Adicione pelo menos um modelo à tabela!")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self.dialog, "Salvar Dashboard", "Dashboard_Master.html", "HTML Files (*.html)")
        if not file_path: return
            
        models_data = []
        # EXTRAÇÃO SEGURA (Evita crash se a célula for nula)
        for row in range(self.table_models.rowCount()):
            i_name = self.table_models.item(row, 0)
            i_acc = self.table_models.item(row, 1)
            i_shap = self.table_models.item(row, 2)
            
            name = i_name.text().strip() if i_name and i_name.text() else f"Modelo {row+1}"
            acc_path = i_acc.text().strip() if i_acc else ""
            shap_path = i_shap.text().strip() if i_shap else ""
            
            models_data.append({'name': name, 'acc_path': acc_path, 'shap_path': shap_path})
            
        try:
            self.report_generator.generate_master_dashboard(file_path, models_data)
            QMessageBox.information(self.dialog, "Sucesso", "Dashboard Consolidado gerado com sucesso!")
        except Exception as e:
            # RASTREAMENTO DE ERRO: Mostra a linha exata onde falhou
            QMessageBox.critical(self.dialog, "Erro Fatal", f"Ocorreu um erro ao processar o Dashboard:\n{str(e)}\n\nDetalhes Técnicos:\n{traceback.format_exc()}")

    def update_classified_fields(self, layer):
        self.combo_class_field.clear()
        if isinstance(layer, QgsVectorLayer):
            self.combo_class_field.setEnabled(True)
            self.combo_class_field.addItems([f.name() for f in layer.fields()])
        else:
            self.combo_class_field.setEnabled(False)

    def update_validation_fields(self, layer):
        self.combo_val_field.clear()
        if isinstance(layer, QgsVectorLayer):
            self.combo_val_field.addItems([f.name() for f in layer.fields()])

    def run_validation(self):
        classified_layer = self.combo_classified.currentLayer()
        validation_layer = self.combo_validation.currentLayer()
        val_field = self.combo_val_field.currentText()
        
        if not classified_layer or not validation_layer or not val_field:
            QMessageBox.warning(self.dialog, "Warning", "Please select all required layers and fields.")
            return

        self.text_results.setText("Extracting samples and calculating metrics... Please wait.")
        QgsApplication.processEvents()

        try:
            y_true, y_pred = self.extract_samples(classified_layer, validation_layer, val_field)
            if len(y_true) == 0:
                self.text_results.setText("Error: No intersecting samples found.")
                return

            metrics = ValidationMetrics.calculate_all_metrics(y_true, y_pred)
            cm_df = ConfusionMatrix.create_matrix(y_true, y_pred)
            self.results = metrics
            self.results['confusion_matrix'] = cm_df

            report_text = f"Overall Accuracy: {metrics['overall_accuracy']:.4f}\n"
            report_text += f"Kappa: {metrics['kappa']:.4f}\n"
            report_text += f"QADI: {metrics['qadi']:.4f}\n"
            report_text += f"MCC: {metrics['mcc']:.4f}\n\n"
            report_text += ConfusionMatrix.format_matrix_for_display(cm_df)
            
            self.text_results.setText(report_text)
            
        except Exception as e:
            self.text_results.setText(f"Error during validation: {str(e)}")

    def extract_samples(self, classified_layer, validation_layer, val_field):
        y_true, y_pred = [], []
        class_field = self.combo_class_field.currentText()
        
        crs_src = validation_layer.crs()
        crs_dest = classified_layer.crs()
        transform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())

        is_raster = isinstance(classified_layer, QgsRasterLayer)
        
        if is_raster:
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
