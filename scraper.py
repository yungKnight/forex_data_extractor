import asyncio
import os
import json
import csv
from typing import List, Optional
from playwright.async_api import async_playwright
from scrapy.http import HtmlResponse
from pydantic import ValidationError

from models import (
    ExtractionRequest, 
    ForexExtractionResult, 
    ExtractionMetadata, 
    PriceDataPoint,
    FileOperationResult,
    OutputFormat,
    create_extraction_request,
    create_result_from_tuples
)
from utils import date_to_unix, parse_date_string


class ForexDataExtractor:
    """
    Enhanced forex data extractor using Pydantic models for type safety and validation.
    """
    
    def __init__(self):
        self.base_url = "https://finance.yahoo.com/quote/{currency_pair}=X/history/?period1={end_date}&period2={start_date}"
    
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
            
            # Convert request to URL parameters
            url_params = request.to_url_params()
            url = self.base_url.format(**url_params)
            
            # Perform web scraping
            raw_data, headers = await self._scrape_yahoo_finance(url, request)
            
            # Create metadata
            metadata = ExtractionMetadata(
                currency_pair=request.currency_pair,
                date_range_start=request.start_date,
                date_range_end=request.end_date,
                request_params=request,
                headers_found=headers,
                url_accessed=url
            )
            
            # Convert raw data to structured data points
            data_points = self._convert_to_data_points(raw_data, request)
            
            # Create result
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
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Block unnecessary resources
            async def handle_request(route, request_obj):
                if request_obj.resource_type in ['image', 'iframe']:
                    await route.abort()
                else:
                    await route.continue_()

            await page.route("**/*", handle_request)

            print(f'Navigating to Yahoo! Finance {request.currency_pair} historical data')
            await page.goto(url, timeout=0)

            await page.wait_for_selector('section.gridLayout > div.container')
            print('Page navigation successful')

            await page.query_selector('div.container > div.table-container')
            print('Table container confirmed')

            await asyncio.sleep(5)

            html_content = await page.content()
            
            if not html_content:
                raise Exception("Failed to retrieve HTML content")

            response = HtmlResponse(url=page.url, body=html_content.encode(), encoding='utf-8')

            headers = response.css('table thead tr th::text').getall()
            headers = [header.strip() for header in headers if header.strip()]
            print(f"Extracted headers: {headers}")

            print('Extracting historical data rows')
            rows = response.css('div.table-container > table.table > tbody tr')
            
            for row in rows:
                date_text = row.css('td:nth-child(1)::text').get()
                close_price = row.css('td:nth-child(5)::text').get()
                
                if not date_text or not close_price:
                    continue
                    
                date_text = date_text.strip()
                close_price = close_price.strip()
                
                print(f"{request.currency_pair} closed at {close_price} on {date_text}")

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
        Save extraction result to file(s) based on request format.
        
        Returns:
            List[FileOperationResult]: Results of save operations
        """
        save_results = []
        
        if request.output_format == OutputFormat.CSV:
            save_result = await self._save_to_csv(result, request)
            save_results.append(save_result)
            
        elif request.output_format == OutputFormat.JSON:
            save_result = await self._save_to_json(result, request)
            save_results.append(save_result)
            
        elif request.output_format == OutputFormat.BOTH:
            csv_result = await self._save_to_csv(result, request)
            save_results.append(csv_result)
            
            json_request = request.model_copy(deep=True)
            if request.output_file:
                if request.output_file.endswith('.csv'):
                    json_request.output_file = request.output_file.replace('.csv', '.json')
                elif not request.output_file.endswith('.json'):
                    json_request.output_file = f"{request.output_file}.json"
            
            json_result = await self._save_to_json(result, json_request)
            save_results.append(json_result)
        
        #for save_result in save_results:
        #    print(save_result.get_summary())
        
        return save_results
    
    async def _save_to_csv(
        self, 
        result: ForexExtractionResult, 
        request: ExtractionRequest
    ) -> FileOperationResult:
        """Save result to CSV file."""
        try:
            # Determine filename
            if request.output_file:
                filename = request.output_file
                if not filename.endswith('.csv'):
                    filename = f"{filename}.csv"
            else:
                filename = request.get_default_filename('csv')
            
            file_exists = os.path.isfile(filename) and request.append_to_file
            mode = 'a' if request.append_to_file else 'w'
            
            rows_written = 0
            
            with open(filename, mode=mode, newline='') as file:
                writer = csv.writer(file)
                
                if not file_exists:
                    writer.writerow(['Date', 'Close'])
                    
                csv_rows = result.to_csv_rows()
                for row_data in csv_rows:
                    writer.writerow([row_data['date'], row_data['close']])
                    rows_written += 1
            
            file_size = os.path.getsize(filename) if os.path.exists(filename) else None
            
            return FileOperationResult(
                file_path=filename,
                format_type=OutputFormat.CSV,
                rows_written=rows_written,
                success=True,
                file_size_bytes=file_size
            )
            
        except Exception as e:
            return FileOperationResult(
                file_path=filename if 'filename' in locals() else "unknown",
                format_type=OutputFormat.CSV,
                success=False,
                error_message=str(e)
            )
    
    async def _save_to_json(
        self, 
        result: ForexExtractionResult, 
        request: ExtractionRequest
    ) -> FileOperationResult:
        """Save result to JSON file."""
        try:
            if request.output_file:
                filename = request.output_file
                if not filename.endswith('.json'):
                    filename = f"{filename}.json"
            else:
                filename = request.get_default_filename('json')
            
            json_data = result.to_json_structure()
            
            if request.append_to_file and os.path.isfile(filename):
                try:
                    with open(filename, 'r') as file:
                        existing_data = json.load(file)
                    
                    if isinstance(existing_data, dict) and "historical_data" in existing_data:
                        existing_data["extraction_date"] = json_data["extraction_date"]
                        existing_data["data_count"] += len(json_data["historical_data"])
                        
                        existing_dates = {item.get('date') for item in existing_data["historical_data"]}
                        for new_item in json_data["historical_data"]:
                            if new_item.get('date') not in existing_dates:
                                existing_data["historical_data"].append(new_item)
                        
                        json_data = existing_data
                    else:
                        json_data = [existing_data, json_data]
                        
                except (json.JSONDecodeError, IOError):
                    pass
            
            with open(filename, 'w') as file:
                json.dump(json_data, file, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(filename) if os.path.exists(filename) else None
            rows_written = len(result.data_points)
            
            return FileOperationResult(
                file_path=filename,
                format_type=OutputFormat.JSON,
                rows_written=rows_written,
                success=True,
                file_size_bytes=file_size
            )
            
        except Exception as e:
            return FileOperationResult(
                file_path=filename if 'filename' in locals() else "unknown",
                format_type=OutputFormat.JSON,
                success=False,
                error_message=str(e)
            )

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
        from models import ExtractionMetadata
        
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