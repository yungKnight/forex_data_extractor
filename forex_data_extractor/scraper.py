import asyncio
import os
import json
import csv
from typing import List, Optional
from playwright.async_api import async_playwright
from scrapy.http import HtmlResponse
from pydantic import ValidationError
from .models import ( FileOperationResult,
    ExtractionRequest, ForexExtractionResult, ExtractionMetadata, 
    PriceDataPoint, create_extraction_request
)
from .config import config
from .utils import date_to_unix, parse_date_string
from .export import ForexDataExporter

class ForexDataExtractor:
    """
    Enhanced forex data extractor using Pydantic models for type safety and validation.
    """
    
    def __init__(self):
        self.base_url = config.scraper.BASE_URL
    
    async def extract_forex_data(self, request: ExtractionRequest) -> ForexExtractionResult:
        """
        Extract historical forex data using structured request model.
        
        Args:
            request (ExtractionRequest): Validated extraction request
            
        Returns:
            ForexExtractionResult: Complete extraction result with metadata
        """
        try:
            print(f"Extracting {request.currency_pair} data from "
                  f"{request.end_date.strftime('%b %d, %Y')} to "
                  f"{request.start_date.strftime('%b %d, %Y')}")
            
            url_params = request.to_url_params()
            url = self.base_url.format(**url_params)
            
            raw_data, headers = await self._scrape_yahoo_finance(url, request)
            
            metadata = ExtractionMetadata(
                currency_pair=request.currency_pair,
                date_range_start=request.start_date,
                date_range_end=request.end_date,
                request_params=request,
                headers_found=headers,
                url_accessed=url
            )
            
            data_points = self._convert_to_data_points(raw_data, request)
            
            result = ForexExtractionResult(
                data_points=data_points,
                metadata=metadata,
                success=True
            )
            
            if request.output_file is not None or len(data_points) > 0:
                await self._save_result(result, request)
            
            return result
            
        except Exception as e:
            
            metadata = ExtractionMetadata(
                currency_pair=request.currency_pair,
                date_range_start=request.start_date,
                date_range_end=request.end_date,
                request_params=request,
                url_accessed=self.base_url.format(**request.to_url_params())
            )
            
            return ForexExtractionResult(
                data_points=[],
                metadata=metadata,
                success=False,
                error_message=str(e)
            )
    
    async def _scrape_yahoo_finance(
        self, 
        url: str, 
        request: ExtractionRequest
    ) -> tuple[List[tuple[str, str]], List[str]]:
        """
        Perform the actual web scraping of Yahoo Finance.
        
        Returns:
            tuple: (raw_data_tuples, headers_found)
        """
        raw_data = []
        headers = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=config.scraper.BROWSER_HEADLESS)
            page = await browser.new_page()

            async def handle_request(route, request_obj):
                if request_obj.resource_type in config.scraper.BLOCKED_RESOURCE_TYPES:
                    await route.abort()
                else:
                    await route.continue_()

            await page.route("**/*", handle_request)

            print(f'Navigating to Yahoo! Finance {request.currency_pair} historical data')
            await page.goto(url, timeout=0)

            await page.wait_for_selector(config.scraper.SELECTORS['main_container'])
            print('Page navigation successful')

            await page.query_selector(config.scraper.SELECTORS['table_container'])
            print('Table container confirmed')

            await asyncio.sleep(config.scraper.PAGE_WAIT_DELAY)

            html_content = await page.content()
            
            if not html_content:
                raise Exception("Failed to retrieve HTML content")

            response = HtmlResponse(url=page.url, body=html_content.encode(), encoding='utf-8')

            headers = response.css(config.scraper.SELECTORS['table_headers']).getall()
            headers = [header.strip() for header in headers if header.strip()]

            print('Extracting historical data rows')
            rows = response.css(config.scraper.SELECTORS['table_rows'])
            
            for row in rows:
                date_text = row.css(config.scraper.SELECTORS['date_cell']).get()
                close_price = row.css(config.scraper.SELECTORS['close_price_cell']).get()
                
                if not date_text or not close_price:
                    continue
                    
                date_text = date_text.strip()
                close_price = close_price.strip()
                
                row_date = parse_date_string(date_text)
                if row_date is None:
                    continue

                if row_date <= request.start_date and row_date >= request.end_date:
                    raw_data.append((date_text, close_price))

            await page.close()
            await browser.close()

        return raw_data, headers
    
    def _convert_to_data_points(
        self, 
        raw_data: List[tuple[str, str]], 
        request: ExtractionRequest
    ) -> List[PriceDataPoint]:
        """
        Convert raw scraped data to validated PriceDataPoint objects.
        """
        data_points = []
        
        for date_str, price_str in raw_data:
            try:
                parsed_date = parse_date_string(date_str)
                if parsed_date:
                    point = PriceDataPoint(
                        date=parsed_date,
                        close_price=price_str,
                        date_string=date_str
                    )
                    data_points.append(point)
            except ValidationError as e:
                print(f"Warning: Invalid data point ({date_str}, {price_str}): {e}")
                continue
            except Exception as e:
                print(f"Warning: Could not process data point ({date_str}, {price_str}): {e}")
                continue
        
        data_points.sort(key=lambda x: x.date)
        
        return data_points

    async def _save_result(
        self, 
        result: ForexExtractionResult, 
        request: ExtractionRequest
    ) -> List[FileOperationResult]:
        """
        Save extraction result using the dedicated export module.
        """
        exporter = ForexDataExporter()
        return await exporter.export_result(result, request)
    
async def get_forex_data(
    currency_pair: str,
    start_date,
    end_date,
    output_file: Optional[str] = None,
    append_to_file: bool = True,
    output_format: str = "csv"
) -> ForexExtractionResult:
    """
    Enhanced convenience function that returns structured result.
    
    Args:
        currency_pair (str): Currency pair (e.g., 'USDEUR', 'GBPUSD')
        start_date (datetime): Start date for data extraction
        end_date (datetime): End date for data extraction
        output_file (str, optional): Output file to save data
        append_to_file (bool): Whether to append to existing file
        output_format (str): Output format - 'csv', 'json', or 'both'
        
    Returns:
        ForexExtractionResult: Complete extraction result with metadata and validation
    """
    try:
        request = create_extraction_request(
            currency_pair=currency_pair,
            start_date=start_date,
            end_date=end_date,
            output_file=output_file,
            append_to_file=append_to_file,
            output_format=output_format
        )
        
        extractor = ForexDataExtractor()
        return await extractor.extract_forex_data(request)
        
    except ValidationError as e:
        from .models import ExtractionMetadata
        
        metadata = ExtractionMetadata(
            currency_pair=currency_pair,
            date_range_start=start_date,
            date_range_end=end_date,
            request_params=create_extraction_request(
                currency_pair, start_date, end_date, output_file, append_to_file, output_format
            )
        )
        
        return ForexExtractionResult(
            data_points=[],
            metadata=metadata,
            success=False,
            error_message=f"Request validation failed: {e}"
        )

def fetch_forex_data(
    currency_pair: str,
    start_date,
    end_date,
    output_file: Optional[str] = None,
    append_to_file: bool = True,
    output_format: str = "csv"
) -> ForexExtractionResult:
    """
    Synchronous wrapper around get_forex_data.
    Accepts datetime objects or strings (format: 'MMM DD, YYYY') for dates.
    """
    from .utils import parse_date_string

    if isinstance(start_date, str):
        start_date = parse_date_string(start_date)
        if not start_date:
            raise ValueError(f"Invalid start_date string: {start_date}")
    if isinstance(end_date, str):
        end_date = parse_date_string(end_date)
        if not end_date:
            raise ValueError(f"Invalid end_date string: {end_date}")

    return asyncio.run(
        get_forex_data(
            currency_pair=currency_pair,
            start_date=start_date,
            end_date=end_date,
            output_file=output_file,
            append_to_file=append_to_file,
            output_format=output_format
        )
    )
