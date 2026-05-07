# BARU Validator (Batch Accuracy and Reporting Utility)

**BARU Validator** is a high-performance QGIS plugin designed to automate the validation of image classifications. While it was originally developed for identifying *Dipteryx alata* (Baru) trees in the Brazilian Cerrado, its flexible architecture allows it to be used for any thematic classification project.

## 🚀 Key Features

- **Multi-format Input:** Supports both raster and polygon classified layers.
- **Validation Methods:** Validate results using point or polygon ground-truth data.
- **Advanced Metrics:** Generates Confusion Matrix, Kappa Index, F1-Score, Overall Accuracy, Producer's and User's Accuracy.
- **Comprehensive Reporting:** Export your results in **PDF**, **CSV**, and **HTML** formats.

## 🛠️ Requirements

This plugin requires external Python libraries to perform advanced statistical calculations and report generation.
The following packages are necessary:
- `pandas`
- `matplotlib`
- `jinja2` (for HTML reports)
- `fpdf` (for PDF generation)

## 📥 Installation

1. Download the latest release from the [QGIS Python Plugins Repository](https://plugins.qgis.org/).
2. In QGIS, go to `Plugins` > `Manage and Install Plugins`.
3. If installing manually, extract the `.zip` content into your QGIS plugins folder (usually `%AppData%\Roaming\QGIS\QGIS3\profiles\default\python\plugins`).

## 📖 How to Use

1. Load your **Classified Layer** (Raster or Vector).
2. Load your **Validation Layer** (Points or Polygons).
3. Open the **BARU Validator** tool from the Toolbar.
4. Map the classification fields and run the assessment.
5. Check the generated reports in the output folder.

## 📄 License

This project is licensed under the GNU General Public License (GPL) v2 or later.
