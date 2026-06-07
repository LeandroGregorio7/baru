# B.A.R.U (Batch Accuracy and Reporting Utility) - QGIS Plugin for ML Model Validation 2.0.0 Version ✔️

 **BARU Validator** is a high-performance QGIS plugin designed to automate the validation of image classifications. While it was originally developed for identifying *Dipteryx alata* (Baru) trees in the Brazilian Cerrado, its flexible architecture allows it to be used for any thematic classification project.

## Features

### Supported Input Formats
- **Classified Data**: Raster (GeoTIFF, etc.) or Vector (Shapefile, GeoPackage, etc.)
- **Validation Data**: Vector points or polygons with reference class values
- **Data Types**: Numeric class values (integers)

### Validation Metrics

The plugin calculates the following advanced metrics:

1. **Overall Accuracy (OA)**: Proportion of correctly classified pixels
2. **Cohen's Kappa**: Agreement corrected for chance
3. **QADI Index**: Quantity and Allocation Disagreement Index
   - Identifies if errors are due to quantity (Q) or allocation (A) disagreement
   - More robust than Kappa for imbalanced datasets
4. **Matthews Correlation Coefficient (MCC)**: Balanced measure for imbalanced data
5. **F1-Score**: Per-class harmonic mean of precision and recall
6. **Producer's Accuracy**: Recall per class (ability to detect the class)
7. **User's Accuracy**: Precision per class (reliability of classification)
8. **Confusion Matrix**: Detailed error matrix with per-class metrics

📽️See below how B.A.R.U Works📽️

1- How analyze models and export to html report.
<video src=https://github.com/user-attachments/assets/7f6de455-e43d-4402-a6e8-87cfb854263f controls width="100%"></video>


2- Compare several model and make a intaractive dashboard html
<video src=https://github.com/user-attachments/assets/3e30a23a-1a2e-4712-89e1-7fec2d21fbcf controls width="100%"></video>


### Report Generation

Generate validation reports in multiple formats:
- **PDF**: Professional formatted report with tables and metrics
- **HTML**: Interactive web-based report
- **CSV**: Spreadsheet-compatible data export

## Installation

### Requirements
- QGIS 3.0 or higher
- Python 3.6+
- Dependencies: numpy, pandas, scikit-learn, shapely

### Installation Steps

1. **Locate QGIS plugins directory**:
   - Windows: `C:\Users\<username>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
   - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins`

2. **Copy plugin folder**:
   ```bash
   cp -r baru_validator /path/to/plugins/directory/
   ```

3. **Restart QGIS**

4. **Enable plugin**:
   - Go to Plugins → Manage and Install Plugins
   - Search for "Baru Validator"
   - Check the box to enable it

## Usage

### Basic Workflow

1. **Load Data**:
   - Load your classified layer (raster or vector)
   - Load your validation layer (vector with reference data)
   - Ensure both layers are in the same coordinate reference system (CRS)

2. **Configure Input**:
   - Select the classified layer
   - Choose the field containing class values
   - Select the validation layer
   - Choose the field containing reference class values

3. **Run Validation**:
   - Go to Tab 2: Validation
   - Select desired metrics to calculate
   - Click "Run Validation"
   - Monitor progress with the progress bar

4. **Review Results**:
   - Go to Tab 3: Results
   - View metrics and confusion matrix
   - Interpret the results based on metric descriptions

5. **Generate Report**:
   - Go to Tab 4: Report
   - Choose report format (PDF, HTML, CSV)
   - Select options (confusion matrix, charts)
   - Click "Generate Report" or "Export Results to CSV"

### Interpreting Metrics

#### Cohen's Kappa Scale
- **< 0**: Poor agreement
- **0.0 - 0.2**: Slight agreement
- **0.2 - 0.4**: Fair agreement
- **0.4 - 0.6**: Moderate agreement
- **0.6 - 0.8**: Substantial agreement
- **> 0.8**: Almost perfect agreement

#### QADI Index
- **Range**: 0 to 1
- **Lower is better**: 0 = perfect classification, 1 = worst classification
- **Advantages over Kappa**:
  - Not sensitive to skewed distributions
  - Identifies whether errors are quantity or allocation based
  - More reliable for Object-Based Image Analysis (OBIA)

#### Matthews Correlation Coefficient (MCC)
- **Range**: -1 to 1
- **1**: Perfect prediction
- **0**: Random prediction
- **-1**: Inverse prediction
- **Advantage**: Robust for imbalanced datasets

#### Producer's Accuracy (Recall)
- **Definition**: Proportion of reference pixels correctly classified
- **Formula**: TP / (TP + FN)
- **Interpretation**: Ability of the model to detect the class

#### User's Accuracy (Precision)
- **Definition**: Proportion of classified pixels that are correct
- **Formula**: TP / (TP + FP)
- **Interpretation**: Reliability of the classification for the user

## Model Replication Workflow

This plugin is ideal for validating ML models when replicating them across different geographic areas:

1. **Train Model**: Train your ML model on a control area with collected training samples
2. **Create Validation Dataset**: Collect validation samples in the control area
3. **Validate Control Model**: Use this plugin to validate the model on the control area
4. **Replicate to New Area**: Apply the trained model to a new geographic area WITHOUT collecting new training samples
5. **Validate Replicated Model**: Use this plugin to validate the model on the new area
6. **Compare Results**: Compare metrics between control and replicated areas to assess model generalization

## Technical Details

### Supported Data Types
- **Raster**: GeoTIFF, IMG, TIFF, and other GDAL-supported formats
- **Vector**: Shapefile, GeoPackage, GeoJSON, and other OGR-supported formats

### Coordinate Reference Systems
- Supports any QGIS-compatible CRS
- Automatically handles coordinate transformations if layers have different CRS

### Performance
- Optimized for datasets with up to 1 million validation points
- Larger datasets may require increased processing time

## Troubleshooting

### "No validation results to report"
- Ensure you have run the validation first (Tab 2)
- Check that all required fields are properly selected

### "Classified and validation data have different lengths"
- Ensure validation points/polygons are within the classified layer extent
- Check that both layers are properly loaded and visible

### "Field not found"
- Verify the field exists in the layer
- Ensure the field contains numeric values
- Check layer attribute table for correct field names

### Plugin not appearing in QGIS
- Verify plugin folder is in correct location
- Check QGIS plugin directory settings
- Restart QGIS after installation
- Check QGIS log for error messages

## Citation

If you use this plugin in your research, please cite:

```
Baru Validator - QGIS Plugin for ML Model Validation (2025)
Manus AI
Available at: https://github.com/manus-ai/baru-validator
```

## References

- Bakhtiari Fard, S., Darabi, H., Blaschke, T., & Lakes, T. (2022). QADI as a New Method and Alternative to Kappa for Accuracy Assessment of Remote Sensing-Based Image Classification. Sensors, 22(12), 4506.
- Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. Biometrics, 33(1), 159-174.
- Matthews, B. W. (1975). Comparison of predicted and observed secondary structure of T4 phage lysozyme. Biochimica et Biophysica Acta, 405(2), 442-451.

## License

This plugin is released under the GNU General Public License v3.0. See LICENSE file for details.

## Support

For issues, feature requests, or contributions, please visit:
https://github.com/manus-ai/baru-validator

## Authors

Developed by Leandro da Silva Gregorio
Contact: leandrogeosmart@gmail.com

## Changelog

[1.2.0] - 2026-05-25 (Master Dashboard Update)
✨ Features
New "Consolidated Dashboard (Master)" Module: Added a new tab to the main interface allowing users to load multiple accuracy reports simultaneously.

Side-by-Side Analytical Comparison: The plugin now generates an interactive HTML Dossier containing:

Comparison table of global metrics (Overall Accuracy, Kappa, QADI, MCC).

Target-specific metrics table (F1-Score, Recall, and Precision for Baru).

Confusion Matrices displayed in a grid for comparative spatial analysis.

Automatic integration with SHAP reports (displaying the most influential variable/band per model).

Automated AI Recommendation: The Master Dashboard now mathematically analyzes the F1-Score and generates a dynamic, well-founded conclusion text, recommending the most suitable algorithm for mapping the area.

Interactive Charts (Chart.js): Rendering of a bar chart comparing Global Accuracy and Baru F1-Score across all evaluated models.

Built-in Export: Dedicated buttons added to the top of the Master Dashboard for one-click report export to .PDF and .DOCX (Word) formats.

🛠 Enhancements
New Robust Extractor (HTML Parser): The report reading engine (report_generator.py) was completely rewritten using a "Brute Force" scanning method (Direct Regex). It is now immune to formatting breaks, ensuring absolute backward compatibility with HTML reports generated in previous versions.

JSON Metadata Injection: The new individual reports now discretely inject results via JSON, making communication with the Master Dashboard faster and bulletproof.

Type Protection (_safe_float): Added an absolute value converter. If older tables contain encoding anomalies (like commas instead of dots), the plugin cleans the data and prevents extraction failures (unintentional zeros).

Updated Interface Filters: Layer selection menus in the UI (baru_validator.py) were migrated from native QgsMapLayerComboBox to QgsMapLayerProxyModel, fixing a compatibility bug in QGIS version 3.44.7-Solothurn.

🐛 Bug Fixes
Fixed a bug where QGIS would fatally crash if sections or confusion matrices in individual reports had empty <td> tags or CSS anomalies.

Fixed missing file extensions when saving files (The plugin now automatically forces the .html extension if the operating system ignores it).

NEW Baru Validator v2.0.0 - The Hybrid Geo-Score Update 🚀
We are proud to announce version 2.0.0 of the Baru Validator! This is the biggest update to the tool since its creation. It introduces a groundbreaking validation methodology for Remote Sensing that cross-references traditional statistical metrics with the spatial realism of classifications, actively combating overfitting in Machine Learning algorithms.


🎉 New Features
New Hybrid Module (Geo-Score): Added the "Hybrid Evaluation" tab. The plugin now evaluates the spatial realism (Spatial Conformity) of models by crossing the Target-Class F1-Score with the generated geometry (total predicted area, average canopy patch size, and number of fragments).

Automatic Overfitting Detection: The algorithm now severely penalizes models that overestimate the target or generate unrealistic continuous patches. This reveals the crucial difference between a model that simply "memorized" the validation data (Illusory Accuracy) and a model that actually generalized well across the real landscape.

Interactive Hybrid Dashboard (HTML): Generates a brand new comparative HTML report that ranks models based on their Final Hybrid Score. It includes equilibrium charts (Statistical vs. Spatial) and automated analytical conclusions pointing out the best cartographic model.
<img width="1449" height="727" alt="geoscore1" src="https://github.com/user-attachments/assets/827f298c-9742-4393-ba45-8f4baa0f27b4" />
<img width="1471" height="389" alt="geoscore2" src="https://github.com/user-attachments/assets/d008275d-bc4f-47cf-8fc1-8293d0e0bda1" />

⚡ Enhancements
Universal Support for Rasters and Vectors: The Geo-Score module now natively accepts image files (.tif/.tiff via GDAL/SciPy in-memory processing) in addition to vectors (.shp, .gpkg), eliminating the need for prior vectorization to analyze spatial patches.

Target-Class Focus: The hybrid engine no longer relies on Global Accuracy (OA/Kappa) as its primary weight. It now uses RegEx to extract the exact F1-Score of the specific class of interest, preventing the "background" accuracy from masking the final score.

Dynamic HTML Parsing: The Master Dashboard engine has been rewritten to extract data (Global Metrics, Recall, Precision, and F1 per class) directly from the source code of any Baru Validator report, whether it's legacy HTML or enveloped in JSON.

🐛 Bug Fixes
Individual HTML Export Fix: Resolved a critical bug where metrics (Kappa, F1-Score, OA) appeared as 0.0000 in individual reports due to an internal dictionary misalignment (results['metrics']).

Zero Division Handling: Fixed the Recall and Precision calculations when the algorithm fails to detect any correct sample of the target class (i.e., 100% false negatives), preventing the plugin from crashing.

Dashboard Variables Fix: Corrected a naming mismatch (acc_html vs acc_path) that prevented the generation of the Consolidated Master Dashboard (V12).

Strict indentation alignment (IndentationError) fixed in core class imports to ensure full compatibility with QGIS >= 3.0.0.

💡 Tip for users: After updating, we highly recommend running the new "Hybrid Evaluation (Geo-Score)" module on your old Random Forest, Extra Trees, or CatBoost tests. Baru Validator 2.0.0 will surprise you by showing how models with a 100% statistical F1-Score can completely fail in the real world!
