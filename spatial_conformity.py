# -*- coding: utf-8 -*-
"""
Módulo de Conformidade Espacial (Geo-Score)
Motor Duplo: Suporta análise de imagens Raster e polígonos Vector.
"""
import numpy as np
from osgeo import gdal
from qgis.core import QgsProject, QgsFeatureRequest, QgsDistanceArea, QgsMapLayer, QgsGeometry

class SpatialConformity:
    def __init__(self):
        self.da = QgsDistanceArea()
        self.da.setSourceCrs(QgsProject.instance().crs(), QgsProject.instance().transformContext())
        self.da.setEllipsoid(QgsProject.instance().ellipsoid())

    def calculate_geo_score(self, layer, target_class_value, roi_area_sqm, class_field='classe'):
        """Direciona para o motor correto dependendo do tipo da camada"""
        if layer.type() == QgsMapLayer.VectorLayer:
            return self._calculate_vector(layer, target_class_value, roi_area_sqm, class_field)
        elif layer.type() == QgsMapLayer.RasterLayer:
            return self._calculate_raster(layer, target_class_value, roi_area_sqm)
        else:
            return {'error': 'Formato não suportado'}

    def _calculate_vector(self, layer, target_class_value, roi_area_sqm, class_field):
        """Motor para arquivos Vector (Shapefile, GeoPackage)"""
        if layer.fields().lookupField(class_field) == -1:
            return {'error': f'Campo "{class_field}" não encontrado no vetor.'}
            
        total_target_area = 0.0
        patch_count = 0
        
        request = QgsFeatureRequest().setFilterExpression(f'"{class_field}" = {target_class_value}')
        for feat in layer.getFeatures(request):
            geom = feat.geometry()
            if not geom.isNull():
                total_target_area += self.da.measureArea(geom)
                patch_count += 1
                
        return self._compute_metrics(total_target_area, patch_count, roi_area_sqm)

    def _calculate_raster(self, layer, target_class_value, roi_area_sqm):
        """Motor de Alta Velocidade para arquivos Raster (.TIF) usando SciPy"""
        geom_extent = QgsGeometry.fromRect(layer.extent())
        total_extent_area = self.da.measureArea(geom_extent)
        pixel_area_sqm = total_extent_area / (layer.width() * layer.height())
        
        ds = gdal.Open(layer.source())
        if not ds:
            ds = gdal.Open(layer.dataProvider().dataSourceUri())
        
        band = ds.GetRasterBand(1)
        arr = band.ReadAsArray()
        
        target_mask = (arr == target_class_value).astype(int)
        
        pixel_count = np.sum(target_mask)
        total_target_area = pixel_count * pixel_area_sqm
        
        try:
            from scipy.ndimage import label
            structure = np.ones((3, 3), dtype=int)
            _, patch_count = label(target_mask, structure=structure)
        except ImportError:
            patch_count = pixel_count
            
        return self._compute_metrics(total_target_area, patch_count, roi_area_sqm)

    def _compute_metrics(self, total_target_area, patch_count, roi_area_sqm):
        """Calcula o Geo-Score final usando as métricas extraídas"""
        if patch_count == 0 or roi_area_sqm <= 0:
            return {'conformity_factor': 0.1, 'patch_count': 0, 'total_area_sqm': 0, 'mean_patch_size': 0, 'area_proportion': 0}
            
        area_proportion = total_target_area / roi_area_sqm
        mean_patch_size = total_target_area / patch_count
        
        penalty = 1.0
        
        if area_proportion > 0.15:
            penalty -= (area_proportion - 0.15) * 2
            
        if mean_patch_size > 250:
            penalty -= 0.3
            
        if patch_count < 5 and area_proportion > 0.05:
            penalty -= 0.4
            
        conformity_factor = max(0.1, min(1.0, penalty))
        
        return {
            'conformity_factor': conformity_factor,
            'patch_count': patch_count,
            'total_area_sqm': total_target_area,
            'mean_patch_size': mean_patch_size,
            'area_proportion': area_proportion
        }