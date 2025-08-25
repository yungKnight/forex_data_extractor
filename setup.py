"""
Setup configuration for Forex Data Scraper package.
"""

from setuptools import setup, find_packages

def read_readme():
    """Read README.md file for long description."""
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "A tool for scraping historical forex data from Yahoo Finance"

__version__ = "1.0.1"

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

    install_requires=[
        "annotated-types==0.7.0",
        "attrs==25.3.0",
        "Automat==25.4.16",
        "certifi==2025.8.3",
        "cffi==1.17.1",
        "charset-normalizer==3.4.3",
        "constantly==23.10.4",
        "cryptography==45.0.6",
        "cssselect==1.3.0",
        "defusedxml==0.7.1",
        "filelock==3.19.1",
        "greenlet==3.2.4",
        "hyperlink==21.0.0",
        "idna==3.10",
        "incremental==24.7.2",
        "itemadapter==0.12.1",
        "itemloaders==1.3.2",
        "jmespath==1.0.1",
        "lxml==6.0.1",
        "packaging==25.0",
        "parsel==1.10.0",
        "playwright==1.54.0",
        "Protego==0.5.0",
        "pyasn1==0.6.1",
        "pyasn1_modules==0.4.2",
        "pycparser==2.22",
        "pydantic==2.11.7",
        "pydantic_core==2.33.2",
        "PyDispatcher==2.0.7",
        "pyee==13.0.0",
        "pyOpenSSL==25.1.0",
        "queuelib==1.8.0",
        "requests==2.32.5",
        "requests-file==2.1.0",
        "Scrapy==2.13.3",
        "scrapy-playwright==0.0.44",
        "service-identity==24.2.0",
        "setuptools==80.9.0",
        "tldextract==5.3.0",
        "Twisted==25.5.0",
        "typing-inspection==0.4.1",
        "typing_extensions==4.14.1",
        "urllib3==2.5.0",
        "w3lib==2.3.1",
        "zope.interface==7.2",
    ],
    
    python_requires=">=3.8",
    
    classifiers=[
        "Development Status :: 5 - Production/Stable",
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
        "Topic :: Office/Business :: Financial",
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
        "forex_data_extractor": [
            "*.py"
        ]
    },
    
    license="MIT",
    license_files=[],
    platforms=["any"],
    
    zip_safe=False,
)
