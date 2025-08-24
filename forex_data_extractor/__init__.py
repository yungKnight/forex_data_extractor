"""
Forex Data Scraper - A tool for extracting historical forex data from Yahoo Finance.

This package provides functionality to scrape, validate, and export historical
forex data with comprehensive error handling and multiple output formats.
"""

from .scraper import ForexDataExtractor, fetch_forex_data, get_forex_data
from .export import ForexDataExporter
from .models import (
    ExtractionRequest, 
    ForexExtractionResult, 
    PriceDataPoint, 
    ExtractionMetadata,
    FileOperationResult,
    OutputFormat,
    create_extraction_request
)
from .utils import (
    parse_date_string,
    date_to_unix,
    get_valid_date,
    validate_single_date,
    format_date_for_display
)
from .config import config, AppConfig

__version__ = "1.0.0"
__author__ = "kennery"
__email__ = "badoknight1@gmail.com"
__description__ = "A tool for scraping historical forex data from Yahoo Finance"

# Package metadata
__all__ = [
    # Main classes
    "ForexDataExtractor",
    "ForexDataExporter",
    
    # Data models
    "ExtractionRequest",
    "ForexExtractionResult", 
    "PriceDataPoint",
    "ExtractionMetadata",
    "FileOperationResult",
    "OutputFormat",
    
    # Convenience functions
    "fetch_forex_data",
    "get_forex_data",
    "create_extraction_request",

    # Utilities
    "parse_date_string",
    "date_to_unix", 
    "get_valid_date",
    "validate_single_date",
    "format_date_for_display",
    
    # Configuration
    "config",
    "AppConfig"
]

# Version info
def get_version():
    """Get the current version of the package."""
    return __version__

def get_package_info():
    """Get comprehensive package information."""
    return {
        "name": "forex-data-extractor-toolkit",
        "version": __version__,
        "author": __author__,
        "email": __email__,
        "description": __description__,
        "python_requires": ">=3.8"
    }