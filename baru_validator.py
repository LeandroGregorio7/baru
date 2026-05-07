# -*- coding: utf-8 -*-
"""
Baru Validator - QGIS Plugin for ML Model Validation
Main plugin class with validation metrics and UI
"""

import os
import sys
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QTimer
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import (
    QAction, QFileDialog, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QPushButton, QSpinBox, QGroupBox, QCheckBox,
    QTabWidget, QWidget, QTextEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QProgressBar, QScrollArea, QApplication
)

from qgis.core import (
    QgsRasterLayer, QgsVectorLayer, QgsProject, QgsFeature, QgsGeometry,
    QgsField, QgsMessageLog, Qgis, QgsMapLayer, QgsWkbTypes, QgsApplication,
    QgsRectangle, QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsMapLayerProxyModel, QgsRaster
)
from qgis.gui import QgsMapCanvas, QgsMapLayerComboBox
from osgeo import gdal

# ---------------------------------------------------------------------------
# GESTÃO DE DEPENDÊNCIAS
# Evita que o plugin quebre na inicialização se o usuário não tiver as libs
# ---------------------------------------------------------------------------
DEPENDENCIES_MISSING = False
MISSING_ERROR = ""

try:
    import numpy as np
    import pandas as pd
    from .validation_metrics import ValidationMetrics
    from .confusion_matrix import ConfusionMatrix
    from .report_generator import ReportGenerator
except ImportError as e:
    DEPENDENCIES_MISSING = True
    MISSING_ERROR = str(e)


class BaruValidator:
    """QGIS Plugin for ML Model Validation in Baru Detection"""

    def __init__(self, iface):
        """Initialize the plugin"""
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.log_message("Plugin directory: {}".format(self.plugin_dir))

        # Load translator
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', 'BaruValidator_{}.qm'.format(locale))
        
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
            self.log_message("Translator loaded successfully.")

        self.actions = []
        self.menu = self.tr(u'&Baru Validator')
        self.toolbar = None
        self.first_start = None
        self.dialog = None

        # -------------------------------------------------------------------
        # CORREÇÃO 1: Uso de tempfile para evitar erros de permissão de escrita
        # -------------------------------------------------------------------
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'baru_validator_temp')
        if not os.path.exists(self.temp_dir):
            try:
                os.makedirs(self.temp_dir)
                self.log_message("Temp directory created at: {}".format(self.temp_dir))
            except OSError as e:
                self.log_message("Failed to create temp directory: {}".format(e), Qgis.Warning)

        self.reset_plugin_state(silent=True)
        self.log_message("Plugin initialized successfully.")

    def tr(self, message):
        """Translate message"""
        return QCoreApplication.translate('BaruValidator', message)

    def log_message(self, message, level=Qgis.Info):
        """Log message to QGIS message log"""
        QgsMessageLog.logMessage(message, 'BaruValidator', level)

    def reset_plugin_state(self, silent=False):
        """Reset plugin state"""
        self.classified_layer = None
        self.validation_layer = None
        self.classification_field = None
        self.validation_field = None
        self.metrics = None
        self.confusion_matrix = None
        self.report_path = None
        self.results = {}

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI"""
        icon_path = os.path.join(self.plugin_dir, 'icons', 'baru_icon.png')
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        # Create action
        self.action = QAction(icon, u'Baru Validator', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.action.setStatusTip(u'Validate ML models for Baru detection')
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.menu, self.action)
        self.actions.append(self.action)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI"""
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    # -----------------------------------------------------------------------
    # CORREÇÃO 2: Instalador Automático de Dependências (scikit-learn, etc)
    # -----------------------------------------------------------------------
    def show_dependency_dialog(self):
        """Show a dialog offering to install missing dependencies automatically"""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Dependências Ausentes / Missing Dependencies")
        text = (
            "O Baru Validator requer bibliotecas adicionais do Python que não estão "
            "instaladas no seu QGIS (numpy, pandas, scikit-learn, shapely).\n\n"
            f"Detalhe do Erro: {MISSING_ERROR}\n\n"
            "Deseja que o plugin tente instalar essas dependências automaticamente agora? "
            "(Necessita conexão com a internet)"
        )
        msg_box.setText(text)
        
        btn_install = msg_box.addButton("Instalar Automaticamente", QMessageBox.AcceptRole)
        btn_cancel = msg_box.addButton("Cancelar", QMessageBox.RejectRole)
        
        msg_box.exec_()
        
        if msg_box.clickedButton() == btn_install:
            self.install_dependencies()

    def install_dependencies(self):
        """Run pip install using the QGIS Python executable"""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.log_message("Iniciando instalação de dependências via pip...")
            # sys.executable garante que estamos usando o Python embutido do QGIS (OSGeo4W)
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "numpy", "pandas", "scikit-learn", "shapely"]
            )
            QApplication.restoreOverrideCursor()
            QMessageBox.information(
                None, 
                "Instalação Concluída", 
                "As dependências foram instaladas com sucesso!\n\n"
                "Por favor, REINICIE O QGIS completamente para poder utilizar o Baru Validator."
            )
        except Exception as e:
            QApplication.restoreOverrideCursor()
            self.log_message(f"Erro ao instalar dependências: {str(e)}", Qgis.Critical)
            QMessageBox.critical(
                None, 
                "Erro de Instalação", 
                "Ocorreu um erro ao tentar instalar as bibliotecas automaticamente.\n\n"
                "Por favor, abra o OSGeo4W Shell (se estiver no Windows) ou seu terminal e execute:\n"
                "python -m pip install numpy pandas scikit-learn shapely"
            )

    def run(self):
        """Run method that performs all the real work"""
        # Checa dependências antes de tentar instanciar a UI (que usa numpy/pandas)
        if DEPENDENCIES_MISSING:
            self.show_dependency_dialog()
            return

        if self.dialog is None:
            self.dialog = BaruValidatorDialog(self.iface, self)
        self.dialog.show()


class BaruValidatorDialog(QDialog):
    """Main dialog for Baru Validator"""

    def __init__(self, iface, plugin):
        """Initialize the dialog"""
        super().__init__()
        self.iface = iface
        self.plugin = plugin
        self.setWindowTitle("Baru Validator - ML Model Validation")
        self.setGeometry(100, 100, 900, 700)
        self.setModal(False)

        # Initialize metrics calculator
        self.metrics = ValidationMetrics()
        self.confusion_matrix = ConfusionMatrix()
        self.report_generator = ReportGenerator()

        # Create UI
        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout()

        # Create tabs
        self.tabs = QTabWidget()
        
        # Tab 1: Input Selection
        self.tab_input = self.create_input_tab()
        self.tabs.addTab(self.tab_input, "1. Input Data")

        # Tab 2: Validation
        self.tab_validation = self.create_validation_tab()
        self.tabs.addTab(self.tab_validation, "2. Validation")

        # Tab 3: Results
        self.tab_results = self.create_results_tab()
        self.tabs.addTab(self.tab_results, "3. Results")

        # Tab 4: Report
        self.tab_report = self.create_report_tab()
        self.tabs.addTab(self.tab_report, "4. Report")

        layout.addWidget(self.tabs)

        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.clicked.connect(self.reset_form)
        button_layout.addWidget(self.btn_reset)

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        button_layout.addWidget(self.btn_close)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def create_input_tab(self):
        """Create input data tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Classified layer selection
        group_classified = QGroupBox("Classified Layer (Raster or Vector)")
        group_layout = QVBoxLayout()
        
        label_classified = QLabel("Select classified layer:")
        self.combo_classified = QgsMapLayerComboBox()
        self.combo_classified.setAllowEmptyLayer(False)
        
        group_layout.addWidget(label_classified)
        group_layout.addWidget(self.combo_classified)
        group_classified.setLayout(group_layout)
        layout.addWidget(group_classified)

        # Classification field
        group_field_class = QGroupBox("Classification Field")
        field_layout = QVBoxLayout()
        
        label_field = QLabel("Field with class values (numeric):")
        self.combo_class_field = QComboBox()
        self.combo_classified.layerChanged.connect(self.update_class_fields)
        
        field_layout.addWidget(label_field)
        field_layout.addWidget(self.combo_class_field)
        group_field_class.setLayout(field_layout)
        layout.addWidget(group_field_class)

        # Validation layer selection
        group_validation = QGroupBox("Validation Layer (Vector: Points or Polygons)")
        val_layout = QVBoxLayout()
        
        label_validation = QLabel("Select validation layer:")
        self.combo_validation = QgsMapLayerComboBox()
        self.combo_validation.setAllowEmptyLayer(False)
        self.combo_validation.setFilters(QgsMapLayerProxyModel.VectorLayer)
        
        val_layout.addWidget(label_validation)
        val_layout.addWidget(self.combo_validation)
        group_validation.setLayout(val_layout)
        layout.addWidget(group_validation)

        # Validation field
        group_field_val = QGroupBox("Validation Field")
        val_field_layout = QVBoxLayout()
        
        label_val_field = QLabel("Field with reference class values (numeric):")
        self.combo_val_field = QComboBox()
        self.combo_validation.layerChanged.connect(self.update_validation_fields)
        
        val_field_layout.addWidget(label_val_field)
        val_field_layout.addWidget(self.combo_val_field)
        group_field_val.setLayout(val_field_layout)
        layout.addWidget(group_field_val)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_validation_tab(self):
        """Create validation tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Validation options
        group_options = QGroupBox("Validation Options")
        options_layout = QVBoxLayout()

        self.check_kappa = QCheckBox("Calculate Cohen's Kappa")
        self.check_kappa.setChecked(True)
        options_layout.addWidget(self.check_kappa)

        self.check_qadi = QCheckBox("Calculate QADI Index")
        self.check_qadi.setChecked(True)
        options_layout.addWidget(self.check_qadi)

        self.check_f1 = QCheckBox("Calculate F1-Score (per class)")
        self.check_f1.setChecked(True)
        options_layout.addWidget(self.check_f1)

        self.check_mcc = QCheckBox("Calculate Matthews Correlation Coefficient (MCC)")
        self.check_mcc.setChecked(True)
        options_layout.addWidget(self.check_mcc)

        self.check_producer = QCheckBox("Calculate Producer's Accuracy (Recall)")
        self.check_producer.setChecked(True)
        options_layout.addWidget(self.check_producer)

        self.check_user = QCheckBox("Calculate User's Accuracy (Precision)")
        self.check_user.setChecked(True)
        options_layout.addWidget(self.check_user)

        self.check_confusion = QCheckBox("Generate Confusion Matrix")
        self.check_confusion.setChecked(True)
        options_layout.addWidget(self.check_confusion)

        group_options.setLayout(options_layout)
        layout.addWidget(group_options)

        self.btn_validate = QPushButton("Run Validation")
        self.btn_validate.clicked.connect(self.run_validation)
        layout.addWidget(self.btn_validate)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_results_tab(self):
        """Create results tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Results text area
        label_results = QLabel("Validation Results:")
        self.text_results = QTextEdit()
        self.text_results.setReadOnly(True)
        
        layout.addWidget(label_results)
        layout.addWidget(self.text_results)

        # Results table
        label_table = QLabel("Confusion Matrix:")
        self.table_confusion = QTableWidget()
        self.table_confusion.setColumnCount(0)
        self.table_confusion.setRowCount(0)
        
        layout.addWidget(label_table)
        layout.addWidget(self.table_confusion)

        widget.setLayout(layout)
        return widget

    def create_report_tab(self):
        """Create report tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Report options
        group_report = QGroupBox("Report Generation")
        report_layout = QVBoxLayout()

        label_format = QLabel("Report Format:")
        self.combo_format = QComboBox()
        self.combo_format.addItems(["PDF", "HTML", "CSV"])
        report_layout.addWidget(label_format)
        report_layout.addWidget(self.combo_format)

        self.check_include_confusion = QCheckBox("Include Confusion Matrix")
        self.check_include_confusion.setChecked(True)
        report_layout.addWidget(self.check_include_confusion)

        self.check_include_charts = QCheckBox("Include Charts and Graphs")
        self.check_include_charts.setChecked(True)
        report_layout.addWidget(self.check_include_charts)

        group_report.setLayout(report_layout)
        layout.addWidget(group_report)

        # Generate report button
        self.btn_generate_report = QPushButton("Generate Report")
        self.btn_generate_report.clicked.connect(self.generate_report)
        layout.addWidget(self.btn_generate_report)

        # Export button
        self.btn_export = QPushButton("Export Results to CSV")
        self.btn_export.clicked.connect(self.export_results)
        layout.addWidget(self.btn_export)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def update_class_fields(self):
        """Update classification field combo box"""
        layer = self.combo_classified.currentLayer()
        self.combo_class_field.clear()
        
        if layer:
            if layer.type() == QgsMapLayer.VectorLayer:
                for field in layer.fields():
                    if field.type() in [1, 2, 3, 4, 6]:  # Integer and Real types
                        self.combo_class_field.addItem(field.name())
            elif layer.type() == QgsMapLayer.RasterLayer:
                self.combo_class_field.addItem("Band 1")
                for i in range(2, layer.bandCount() + 1):
                    self.combo_class_field.addItem("Band {}".format(i))

    def update_validation_fields(self):
        """Update validation field combo box"""
        layer = self.combo_validation.currentLayer()
        self.combo_val_field.clear()
        
        if layer and layer.type() == QgsMapLayer.VectorLayer:
            for field in layer.fields():
                if field.type() in [1, 2, 3, 4, 6]:  # Integer and Real types
                    self.combo_val_field.addItem(field.name())

    def run_validation(self):
        """Run validation analysis"""
        try:
            classified_layer = self.combo_classified.currentLayer()
            validation_layer = self.combo_validation.currentLayer()
            class_field = self.combo_class_field.currentText()
            val_field = self.combo_val_field.currentText()

            if not classified_layer or not validation_layer or not class_field or not val_field:
                QMessageBox.warning(self, "Warning", "Please select all required layers and fields.")
                return

            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            # Perform point-by-point validation
            y_true = []
            y_pred = []
            
            # Setup coordinate transformation if needed
            crs_project = QgsProject.instance().crs()
            crs_val = validation_layer.crs()
            crs_class = classified_layer.crs()
            
            xform_val = QgsCoordinateTransform(crs_val, crs_class, QgsProject.instance())
            
            features = list(validation_layer.getFeatures())
            total = len(features)
            
            if total == 0:
                QMessageBox.warning(self, "Warning", "Validation layer has no features.")
                return

            # Extract data
            for i, feat in enumerate(features):
                # Get reference value
                val_ref = feat[val_field]
                if val_ref is None:
                    continue
                
                # Get point for sampling
                geom = feat.geometry()
                if geom.isMultipart():
                    point = geom.asMultiPoint()[0] if geom.wkbType() == QgsWkbTypes.MultiPoint else geom.centroid().asPoint()
                else:
                    point = geom.asPoint() if geom.wkbType() == QgsWkbTypes.Point else geom.centroid().asPoint()
                
                # Transform point to classified layer CRS
                point_trans = xform_val.transform(point)
                
                # Sample classified layer
                val_class = None
                try:
                    if classified_layer.type() == QgsMapLayer.RasterLayer:
                        # Robust Raster Sampling using identify()
                        # This is more reliable than sample() across different QGIS versions
                        band_idx = int(class_field.split(" ")[1]) if "Band" in class_field else 1
                        
                        # Use identify method which is what the "Identify Tool" uses
                        ident = classified_layer.dataProvider().identify(point_trans, QgsRaster.IdentifyFormatValue)
                        if ident.isValid():
                            results = ident.results()
                            if band_idx in results:
                                val_raw = results[band_idx]
                                if val_raw is not None:
                                    val_class = val_raw
                        
                        # Fallback to sample if identify fails
                        if val_class is None:
                            sample_res = classified_layer.dataProvider().sample(point_trans, band_idx)
                            if isinstance(sample_res, tuple):
                                res_ok, val_dict = sample_res
                                if res_ok: val_class = val_dict.get(band_idx)
                            elif isinstance(sample_res, dict):
                                val_class = sample_res.get(band_idx)
                            elif isinstance(sample_res, (int, float)):
                                val_class = sample_res

                    else:
                        # Sample vector (spatial join/intersection)
                        from qgis.core import QgsFeatureRequest
                        request = QgsFeatureRequest().setFilterRect(QgsRectangle(point_trans, point_trans))
                        for c_feat in classified_layer.getFeatures(request):
                            if c_feat.geometry().contains(point_trans):
                                val_class = c_feat[class_field]
                                break
                except Exception as e:
                    self.plugin.log_message("Sampling error at point {}: {}".format(i, str(e)), Qgis.Warning)
                    continue
                
                if val_class is not None:
                    y_true.append(int(val_ref))
                    y_pred.append(int(val_class))
                
                if i % 10 == 0:
                    self.progress_bar.setValue(int(30 * (i / total)))

            y_true = np.array(y_true)
            y_pred = np.array(y_pred)

            if len(y_true) == 0:
                QMessageBox.warning(self, "Warning", "No overlapping data found between layers.")
                return

            self.progress_bar.setValue(50)

            # Calculate metrics
            results = {}
            
            if self.check_kappa.isChecked():
                results['kappa'] = self.metrics.calculate_kappa(y_true, y_pred)
                self.progress_bar.setValue(60)

            if self.check_qadi.isChecked():
                results['qadi'] = self.metrics.calculate_qadi(y_true, y_pred)
                self.progress_bar.setValue(70)

            if self.check_f1.isChecked():
                results['f1_scores'] = self.metrics.calculate_f1_scores(y_true, y_pred)
                self.progress_bar.setValue(75)

            if self.check_mcc.isChecked():
                results['mcc'] = self.metrics.calculate_mcc(y_true, y_pred)
                self.progress_bar.setValue(80)

            if self.check_producer.isChecked():
                results['producer_accuracy'] = self.metrics.calculate_producer_accuracy(y_true, y_pred)
                self.progress_bar.setValue(85)

            if self.check_user.isChecked():
                results['user_accuracy'] = self.metrics.calculate_user_accuracy(y_true, y_pred)
                self.progress_bar.setValue(90)

            if self.check_confusion.isChecked():
                results['confusion_matrix'] = self.confusion_matrix.create_matrix(y_true, y_pred)
                self.progress_bar.setValue(95)

            # Store results
            self.plugin.results = results
            
            # Display results
            self.display_results(results)
            self.progress_bar.setValue(100)
            
            QMessageBox.information(self, "Success", "Validation completed with {} points!".format(len(y_true)))

        except Exception as e:
            self.plugin.log_message("Error during validation: {}".format(str(e)), Qgis.Critical)
            import traceback
            self.plugin.log_message(traceback.format_exc(), Qgis.Critical)
            QMessageBox.critical(self, "Error", "Validation failed: {}".format(str(e)))
        finally:
            self.progress_bar.setVisible(False)

    def display_results(self, results):
        """Display validation results"""
        text = "=== BARU VALIDATOR - RESULTS ===\n\n"
        text += "Validation Date: {}\n\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if 'kappa' in results:
            text += "Cohen's Kappa: {:.4f}\n".format(results['kappa'])
            text += "  Interpretation: "
            kappa = results['kappa']
            if kappa < 0:
                text += "Poor agreement\n"
            elif kappa < 0.2:
                text += "Slight agreement\n"
            elif kappa < 0.4:
                text += "Fair agreement\n"
            elif kappa < 0.6:
                text += "Moderate agreement\n"
            elif kappa < 0.8:
                text += "Substantial agreement\n"
            else:
                text += "Almost perfect agreement\n"

        if 'qadi' in results:
            text += "\nQADI Index: {:.4f}\n".format(results['qadi'])
            text += "  (Lower is better; 0 = perfect, 1 = worst)\n"

        if 'mcc' in results:
            text += "\nMatthews Correlation Coefficient: {:.4f}\n".format(results['mcc'])
            text += "  (Range: -1 to 1; 1 = perfect, 0 = random)\n"

        if 'f1_scores' in results:
            text += "\nF1-Scores (per class):\n"
            for class_id, f1 in results['f1_scores'].items():
                text += "  Class {}: {:.4f}\n".format(class_id, f1)

        if 'producer_accuracy' in results:
            text += "\nProducer's Accuracy (Recall per class):\n"
            for class_id, acc in results['producer_accuracy'].items():
                text += "  Class {}: {:.4f}\n".format(class_id, acc)

        if 'user_accuracy' in results:
            text += "\nUser's Accuracy (Precision per class):\n"
            for class_id, acc in results['user_accuracy'].items():
                text += "  Class {}: {:.4f}\n".format(class_id, acc)

        self.text_results.setText(text)

        # Display confusion matrix
        if 'confusion_matrix' in results:
            self.display_confusion_matrix(results['confusion_matrix'])

    def display_confusion_matrix(self, cm):
        """Display confusion matrix in table"""
        classes = sorted(set(cm.index) | set(cm.columns))
        n_classes = len(classes)
        
        self.table_confusion.setRowCount(n_classes + 1)
        self.table_confusion.setColumnCount(n_classes + 1)

        # Header
        self.table_confusion.setItem(0, 0, QTableWidgetItem("Reference \\ Classified"))
        for i, cls in enumerate(classes):
            self.table_confusion.setItem(0, i + 1, QTableWidgetItem(str(cls)))
            self.table_confusion.setItem(i + 1, 0, QTableWidgetItem(str(cls)))

        # Data
        for i, ref_cls in enumerate(classes):
            for j, cls_cls in enumerate(classes):
                value = cm.loc[ref_cls, cls_cls] if ref_cls in cm.index and cls_cls in cm.columns else 0
                self.table_confusion.setItem(i + 1, j + 1, QTableWidgetItem(str(int(value))))

    def generate_report(self):
        """Generate validation report"""
        if not self.plugin.results:
            QMessageBox.warning(self, "Warning", "No validation results to report. Run validation first.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", "", 
            "HTML Files (*.html);;CSV Files (*.csv)"
        )

        if file_path:
            try:
                report_format = self.combo_format.currentText().lower()
                self.report_generator.generate(
                    file_path, 
                    self.plugin.results,
                    report_format,
                    include_confusion=self.check_include_confusion.isChecked(),
                    include_charts=self.check_include_charts.isChecked()
                )
                QMessageBox.information(self, "Success", "Report generated successfully!")
                self.plugin.log_message("Report saved to: {}".format(file_path))
            except Exception as e:
                QMessageBox.critical(self, "Error", "Failed to generate report: {}".format(str(e)))

    def export_results(self):
        """Export results to CSV"""
        if not self.plugin.results:
            QMessageBox.warning(self, "Warning", "No results to export. Run validation first.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Results", "", "CSV Files (*.csv)")
        
        if file_path:
            try:
                self.report_generator.export_csv(file_path, self.plugin.results)
                QMessageBox.information(self, "Success", "Results exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", "Failed to export results: {}".format(str(e)))

    def reset_form(self):
        """Reset the form"""
        self.combo_classified.setLayer(None)
        self.combo_validation.setLayer(None)
        self.combo_class_field.clear()
        self.combo_val_field.clear()
        self.text_results.clear()
        self.table_confusion.setRowCount(0)
        self.table_confusion.setColumnCount(0)
        self.plugin.reset_plugin_state()