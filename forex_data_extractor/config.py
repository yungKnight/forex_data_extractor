"""
Configuration settings for the Forex Data Scraper application.
Centralizes all configurable parameters for easy maintenance and customization.
"""
import os
from datetime import datetime
from typing import List
from pathlib import Path


class ScraperConfig:
    """Configuration settings for the web scraper."""
    
    BASE_URL = "https://finance.yahoo.com/quote/{currency_pair}=X/history/?period1={end_date}&period2={start_date}"
    
    BROWSER_HEADLESS = True
    BROWSER_TIMEOUT = 0 
    PAGE_WAIT_DELAY = 5
    
    BLOCKED_RESOURCE_TYPES = ['image', 'iframe']
    
    SELECTORS = {
        'main_container': 'section.gridLayout > div.container',
        'table_container': 'div.container > div.table-container',
        'table_headers': 'table thead tr th::text',
        'table_rows': 'div.table-container > table.table > tbody tr',
        'date_cell': 'td:nth-child(1)::text',
        'close_price_cell': 'td:nth-child(5)::text'
    }


class DateConfig:
    """Configuration for date handling and validation."""
    
    MIN_END_DATE = datetime(2005, 1, 1)
    MAX_START_DATE = datetime.today()
    
    SUPPORTED_DATE_FORMATS = [
        '%b %d, %Y',     # Sep 30, 2024
        '%B %d, %Y',     # September 30, 2024
        '%Y-%m-%d',      # 2024-09-30
        '%m/%d/%Y',      # 09/30/2024
        '%d/%m/%Y',      # 30/09/2024
    ]
    
    DEFAULT_DISPLAY_FORMAT = '%b %d, %Y'
    LONG_DISPLAY_FORMAT = '%B %d, %Y'


class FileConfig:
    """Configuration for file operations and output."""
    
    DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Extracted_Data")
    
    @classmethod
    def ensure_output_dir(cls, path: str = None) -> str:
        """Ensure the output directory exists and return its path."""
        output_path = path or cls.DEFAULT_OUTPUT_DIR
        os.makedirs(output_path, exist_ok=True)
        return output_path
    
    CSV_EXTENSION = "csv"
    JSON_EXTENSION = "json"

    INVALID_FILENAME_CHARS = '<>:"/\\|?*'
    
    DEFAULT_FILENAME_TEMPLATE = "{currency_pair}_historical_data"
    
    CSV_HEADERS = ['Date', 'Close']
    CSV_NEWLINE = ''  

    JSON_INDENT = 2
    JSON_ENSURE_ASCII = False


class ValidationConfig:
    """Configuration for data validation."""
    
    CURRENCY_PAIR_LENGTH = 6
    
    # Price validation
    MIN_PRICE_VALUE = 0.0001
    MAX_PRICE_DIGITS = 10


class CLIConfig:
    """Configuration for command-line interface."""
    
    USAGE_MESSAGE = "Usage: python cli.py USDEUR 'Jan 01, 2024' 'Jan 01, 2023' [csv|json|both]"
    
    PROMPTS = {
        'currency_pair': "Enter currency pair (e.g., USDEUR, GBPUSD): ",
        'start_date': "Enter start date (MMM DD, YYYY): ",
        'end_date': "Enter end date (MMM DD, YYYY): ",
        'output_format': "Enter output format (csv/json/both) [default=csv]: "
    }
    
    VALID_OUTPUT_FORMATS = ["csv", "json", "both"]
    DEFAULT_OUTPUT_FORMAT = "csv"
    
    SUCCESS_SYMBOL = "✓"
    ERROR_SYMBOL = "✗"

class LoggingConfig:
    """Configuration for logging (future enhancement)."""
    
    # Log levels
    DEFAULT_LOG_LEVEL = "INFO"
    DEBUG_LOG_LEVEL = "DEBUG"
    
    # Log format
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # Log file settings
    LOG_DIR = "logs"
    LOG_FILENAME = "forex_scraper.log"
    MAX_LOG_SIZE = 10 * 1024 * 1024
    BACKUP_COUNT = 5

class AppConfig:
    """Main application configuration that aggregates all settings."""
    
    APP_NAME = "Forex Data Extractor"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "A tool for scraping historical forex data from Yahoo Finance"
    
    scraper = ScraperConfig()
    dates = DateConfig()
    files = FileConfig()
    validation = ValidationConfig()
    cli = CLIConfig()
    logging = LoggingConfig()
    
    @classmethod
    def get_app_info(cls) -> dict:
        """Get basic application information."""
        return {
            "name": cls.APP_NAME,
            "version": cls.APP_VERSION,
            "description": cls.APP_DESCRIPTION
        }

config = AppConfig()