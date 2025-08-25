# Forex Data Extractor

![Forex Data Extractor Banner](./images/data_extractor.png)

[![PyPI version](https://badge.fury.io/py/forex-data-extractor.svg)](https://badge.fury.io/py/forex-data-extractor)
[![Python versions](https://img.shields.io/pypi/pyversions/forex-data-extractor.svg)](https://pypi.org/project/forex-data-extractor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/yungKnight/forex_data_extractor)

A robust, type-safe Python package for extracting historical forex data from Yahoo Finance. Built with enterprise-grade architecture using Pydantic validation, async/await support, and comprehensive error handling.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Requirements](#requirements)
- [Usage Examples](#usage-examples)
  - [Command Line Interface](#command-line-interface)
  - [Programmatic Usage](#programmatic-usage)
- [Use Cases](#use-cases)
- [API Reference](#api-reference)
- [Screenshots](#screenshots)
- [Comparison](#comparison)
- [Configuration](#configuration)
- [License](#license)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)
- [Contact](#contact)

## Features

✨ **Professional-Grade Architecture**
- Type-safe Pydantic models with comprehensive validation
- Async/await support for high-performance data extraction
- Robust error handling and detailed logging

📊 **Flexible Data Export**
- Multiple output formats: CSV, JSON, or both simultaneously
- Smart file operations with append/overwrite capabilities
- Configurable output directories and naming conventions

🎯 **Precision Financial Data**
- Decimal precision for accurate price handling
- Comprehensive date validation and constraint checking
- Yahoo Finance integration with reliable scraping

⚡ **Developer Experience**
- Interactive CLI with guided prompts
- Command-line interface for automation and scripting
- Extensive configuration options for customization

🔧 **Enterprise Features**
- Playwright-based browser automation for reliability
- Resource optimization with selective content blocking
- Comprehensive metadata tracking and export statistics

## Quick Start

Get up and running in 30 seconds:

```bash
# Install the package
pip install forex-data-extractor

# Extract USD/EUR data for the last year (interactive mode)
forex-scraper --interactive

# Or use direct command-line
forex-scraper USDEUR "Jan 01, 2024" "Dec 31, 2023" csv
```

That's it! Your forex data will be saved to `./Extracted_Data/USDEUR_historical_data.csv`

## Installation

### From PyPI (Recommended)

```bash
pip install forex-data-extractor
```

### From GitHub (Latest Development)

```bash
pip install git+https://github.com/yungKnight/forex_data_extractor.git
```

### For Development

```bash
git clone https://github.com/yungKnight/forex_data_extractor.git
cd forex_data_extractor
pip install -e .
```

## Requirements

- **Python**: >= 3.8
- **Operating System**: Cross-platform (Windows, macOS, Linux)
- **Dependencies**: Automatically installed with package
  - Playwright (browser automation)
  - Scrapy (web scraping framework)
  - Pydantic (data validation)
  - Additional dependencies listed in [requirements.txt](requirements.txt)

## Usage Examples

### Command Line Interface

#### Basic Usage
```bash
# Extract EUR/JPY data for Q1 2024
forex-scraper EURJPY "Mar 31, 2024" "Jan 01, 2024" csv

# Get GBP/USD data in JSON format
forex-scraper GBPUSD "Dec 31, 2023" "Jan 01, 2023" json

# Export both CSV and JSON formats
forex-scraper USDCAD "Jun 30, 2024" "Jan 01, 2024" both
```

#### Interactive Mode
```bash
forex-scraper --interactive
# Follow the guided prompts for currency pair, dates, and format selection
```

#### Advanced CLI Options
```bash
# Show help and all available options
forex-scraper --help

# Check version
forex-scraper --version
```

### Programmatic Usage

#### Basic Extraction
```python
from forex_data_extractor import fetch_forex_data
from datetime import datetime

# Simple synchronous extraction
result = fetch_forex_data(
    currency_pair="USDEUR",
    start_date=datetime(2024, 3, 31),
    end_date=datetime(2024, 1, 1),
    output_format="json"
)

if result.success:
    print(f"Extracted {len(result.data_points)} data points")
    for point in result.data_points[:5]:  # Show first 5 points
        print(f"{point.date_string}: {point.close_price}")
else:
    print(f"Extraction failed: {result.error_message}")
```

#### Advanced Async Usage
```python
import asyncio
from forex_data_extractor import ForexDataExtractor, create_extraction_request
from datetime import datetime

async def advanced_extraction():
    # Create a structured request
    request = create_extraction_request(
        currency_pair="GBPUSD",
        start_date=datetime(2024, 12, 31),
        end_date=datetime(2024, 1, 1),
        output_file="gbp_usd_2024.json",
        output_format="both"
    )
    
    # Use the extractor class for full control
    extractor = ForexDataExtractor()
    result = await extractor.extract_forex_data(request)
    
    # Access comprehensive metadata
    print(f"URL accessed: {result.metadata.url_accessed}")
    print(f"Headers found: {result.metadata.headers_found}")
    print(f"Extraction time: {result.metadata.extraction_timestamp}")
    
    return result

# Run the async extraction
result = asyncio.run(advanced_extraction())
```

#### Data Processing and Analysis
```python
from forex_data_extractor import get_forex_data
import pandas as pd
from datetime import datetime

async def analyze_forex_data():
    # Extract data
    result = await get_forex_data("EURUSD", datetime(2024, 6, 30), datetime(2024, 1, 1))
    
    # Convert to DataFrame for analysis
    data = [(point.date, float(point.close_price)) for point in result.data_points]
    df = pd.DataFrame(data, columns=['Date', 'Close'])
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Basic analytics
    print(f"Average rate: {df['Close'].mean():.4f}")
    print(f"Min rate: {df['Close'].min():.4f}")
    print(f"Max rate: {df['Close'].max():.4f}")
    print(f"Volatility (std): {df['Close'].std():.4f}")
    
    return df

# Usage
df = asyncio.run(analyze_forex_data())
```

## Use Cases

### 📈 **Financial Research & Analysis**
- Historical exchange rate analysis for academic research
- Currency trend analysis and statistical modeling
- Risk assessment and volatility calculations
- Economic indicator correlation studies

### 🏦 **Fintech Development**
- Building financial dashboards and applications
- Currency conversion service data feeds
- Algorithmic trading strategy backtesting
- Financial data pipeline integration

### 💼 **Business Intelligence**
- Multi-currency business performance analysis
- International trade impact assessment  
- Foreign exchange exposure reporting
- Economic forecasting and planning

### 🔬 **Data Science Projects**
- Machine learning model training data
- Time series forecasting experiments
- Financial data preprocessing pipelines
- Cross-currency correlation analysis

## API Reference

### Key Functions

#### `fetch_forex_data(currency_pair, start_date, end_date, output_format="csv")` 
**Synchronous** data extraction function - ideal for simple use cases.

#### `get_forex_data(currency_pair, start_date, end_date, output_format="csv")`
**Async** data extraction function - use for high-performance applications.

#### `create_extraction_request(currency_pair, start_date, end_date, **kwargs)`
Factory function for creating validated extraction requests.

### Core Classes

#### `ForexDataExtractor`
Main extraction engine with async support and comprehensive error handling.

#### `ForexDataExporter` 
Handles file operations and supports multiple output formats with metadata.

#### `ExtractionRequest`
Pydantic model for type-safe request validation and parameter handling.

#### `ForexExtractionResult`
Comprehensive result container with data points, metadata, and operation status.

### Data Models

All data models use **Pydantic** for runtime validation and type safety:
- `PriceDataPoint` - Individual forex price with date and decimal precision
- `ExtractionMetadata` - Complete extraction context and statistics
- `FileOperationResult` - File save operation results and diagnostics

## Screenshots

### Interactive CLI Mode
![Interactive CLI Screenshot](https://via.placeholder.com/600x400/2d3748/ffffff?text=Interactive+CLI+Mode+Screenshot)
*The interactive CLI guides users through currency pair selection, date ranges, and output format choices*

### Command Line Usage
![Command Line Usage](https://via.placeholder.com/600x300/1a202c/ffffff?text=Command+Line+Usage+Screenshot)  
*Direct command-line execution with comprehensive help and error messages*

### Data Output Examples  
![CSV Output Example](https://via.placeholder.com/600x350/f7fafc/2d3748?text=CSV+Output+Example)
*Clean, professional CSV output with proper date formatting and decimal precision*

## Comparison

| Feature | Forex Data Extractor | yfinance | investpy | Alpha Vantage API |
|---------|---------------------|----------|-----------|-------------------|
| **Type Safety** | ✅ Pydantic Models | ❌ Basic | ❌ Basic | ❌ Basic |
| **Async Support** | ✅ Full async/await | ❌ Sync only | ❌ Sync only | ✅ Some |
| **Data Validation** | ✅ Comprehensive | ⚠️ Limited | ⚠️ Limited | ⚠️ Limited |
| **Error Handling** | ✅ Robust | ⚠️ Basic | ⚠️ Basic | ✅ Good |
| **CLI Interface** | ✅ Professional | ❌ None | ❌ None | ❌ None |
| **Export Formats** | ✅ CSV, JSON, Both | ⚠️ Limited | ⚠️ Limited | ✅ JSON |
| **Date Flexibility** | ✅ Multiple formats | ✅ Good | ✅ Good | ⚠️ Limited |
| **Free Usage** | ✅ Unlimited | ✅ Unlimited | ⚠️ Limited | ⚠️ API limits |
| **Decimal Precision** | ✅ Financial-grade | ⚠️ Float | ⚠️ Float | ✅ Good |

## Configuration

### For Developers: Customization Options

The package offers extensive configuration through the `config` module:

```python
from forex_data_extractor.config import config

# Customize scraping behavior
config.scraper.BROWSER_HEADLESS = False  # Show browser during scraping
config.scraper.PAGE_WAIT_DELAY = 10      # Wait longer for page loads

# Modify output settings
config.files.DEFAULT_OUTPUT_DIR = "/custom/path/data"
config.files.JSON_INDENT = 4

# Adjust date constraints
from datetime import datetime
config.dates.MIN_END_DATE = datetime(2010, 1, 1)  # Allow older data

# CLI customization
config.cli.DEFAULT_OUTPUT_FORMAT = "json"
```

### Environment Variables

Set environment variables for system-wide configuration:

```bash
export FOREX_OUTPUT_DIR="/data/forex"
export FOREX_DEFAULT_FORMAT="json"
export FOREX_BROWSER_HEADLESS="true"
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Here's how you can help:

### Development Setup
```bash
git clone https://github.com/yungKnight/forex_data_extractor.git
cd forex_data_extractor
pip install -e ".[dev]"
```

### Running Tests
```bash
pytest tests/ -v
```

### Code Quality
```bash
black forex_data_extractor/
flake8 forex_data_extractor/
mypy forex_data_extractor/
```

### Contributing Guidelines
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure all tests pass and code follows the project's style guidelines.

## Acknowledgments

- **Yahoo Finance** for providing reliable financial data
- **Playwright Team** for robust browser automation capabilities  
- **Pydantic** for excellent data validation and serialization
- **Scrapy** for the powerful and flexible scraping framework
- **Open Source Community** for inspiration and continuous improvement

Special thanks to the financial data community for feedback and feature suggestions.

## Contact

**Developer**: kennery  
**Email**: badoknight1@gmail.com  
**GitHub**: [@yungKnight](https://github.com/yungKnight)  
**Project**: [forex_data_extractor](https://github.com/yungKnight/forex_data_extractor)

### Support & Issues 
- 📖 **Documentation**: [Project Wiki](https://github.com/yungKnight/forex_data_extractor#readme)
- ⭐ **Show Support**: Star the repository if you find it helpful!

---

Built with ❤️ for the financial data community. Happy trading! 📈