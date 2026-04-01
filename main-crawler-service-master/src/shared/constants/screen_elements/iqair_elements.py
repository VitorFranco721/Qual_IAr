"""
IQAir Screen Elements Constants - Shared Layer
Contains constants for IQAir website UI element selectors used in automation
"""
from enum import Enum


class IQAirElements(Enum):
    """Constants for IQAir page elements"""
    # Main AQI data element
    AQI_BOX_SHADOW_GREEN = '.aqi-box-shadow-green'
    
    # Alternative selectors (fallback)
    AQI_BOX = "[class*='aqi-box']"
    AQI_ELEMENT = "[class*='aqi']"
    AQI_VALUE = '.aqi-value'
    AQI_NUMBER = '.aqi-number'
    
    # Base URL for IQAir
    BASE_URL = 'https://www.iqair.com'
    
    # Default target URL - Brasília
    DEFAULT_TARGET_URL = 'https://www.iqair.com/brazil/federal-district/brasilia'

