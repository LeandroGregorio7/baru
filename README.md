# B.A.R.U (Batch Accuracy and Reporting Utility) - QGIS Plugin for ML Model Validation ✔️

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


https://github.com/user-attachments/assets/a799fb2c-0135-4e07-969d-01d0097b98b3



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
