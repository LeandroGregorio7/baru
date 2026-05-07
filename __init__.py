# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Baru Validator
                                 A QGIS Plugin
 Machine Learning Model Validation for Baru Detection

                              -------------------
        begin                : 2025-05-02
        copyright            : (C) 2025 by Manus AI
        email                : support@manus.im
        license              : GPL v3
 ***************************************************************************/

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""


def classFactory(iface):
    """
    Load BaruValidator class from file baru_validator.py
    
    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .baru_validator import BaruValidator
    return BaruValidator(iface)
