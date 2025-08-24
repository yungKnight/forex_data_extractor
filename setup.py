"""
Setup configuration for Forex Data Scraper package.
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    """Read README.md file for long description."""
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "A tool for scraping historical forex data from Yahoo Finance"

def read_requirements():
    """Read requirements from requirements.txt file."""
    
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

__version__ = "1.0.0"

setup(
    name="forex-data-extractor",
    version=__version__,
    author="kennery",
    author_email="badoknight1@gmail.com",
    description="A tool for scraping historical forex data from Yahoo Finance",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    
    url="https://github.com/yungKnight/forex_data_extractor",
    project_urls={
        "Bug Reports": "https://github.com/yungKnight/forex_data_extractor/issues",
        "Source": "https://github.com/yungKnight/forex_data_extractor",
        "Documentation": "https://github.com/yungKnight/forex_data_extractor#readme"
    },
    
    packages=find_packages(exclude=["tests", "tests.*", "docs", "docs.*"]),
    
    install_requires=read_requirements(),
    
    python_requires=">=3.8",
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Research",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Typing :: Typed"
    ],
    
    keywords=[
        "forex", "currency", "financial-data", "scraping", 
        "yahoo-finance", "financial-data", "currency", "exchange-rates",
        "historical-data", "web-scraping", "playwright"
    ],
    
    entry_points={
        "console_scripts": [
            "forex-scraper=forex_data_extractor.cli:main",
        ],
    },
    
    include_package_data=True,
    package_data={
        "forex_data_scraper": [
            "*.py"
        ]
    },
    
    license="MIT",
    platforms=["any"],
    
    zip_safe=False,
)