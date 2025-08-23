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
            
            print(result.get_summary())
            
            # Save data if requested
            if request.output_file is not None or len(data_points) > 0:
                await self._save_result(result, request)
            
            return result
            
        except Exception as e:
            # Return failed result with error information
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

            # Navigate to Yahoo Finance
            print(f'Navigating to Yahoo! Finance {request.currency_pair} historical data')
            await page.goto(url, timeout=0)

            # Wait for page elements to load
            await page.wait_for_selector('section.gridLayout > div.container')
            print('Page navigation successful')

            await page.query_selector('div.container > div.table-container')
            print('Table container confirmed')

            await asyncio.sleep(5)  # Wait for dynamic content

            # Get page content and parse with Scrapy
            html_content = await page.content()
            
            if not html_content:
                raise Exception("Failed to retrieve HTML content")

            response = HtmlResponse(url=page.url, body=html_content.encode(), encoding='utf-8')

            # Extract table headers
            headers = response.css('table thead tr th::text').getall()
            headers = [header.strip() for header in headers if header.strip()]
            print(f"Extracted headers: {headers}")

            # Extract table rows
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

                # Parse and validate date
                row_date = parse_date_string(date_text)
                if row_date is None:
                    continue

                # Check if date is within specified range
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
        
        # Sort chronologically
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
            # Save CSV
            csv_result = await self._save_to_csv(result, request)
            save_results.append(csv_result)
            
            # Save JSON with modified filename
            json_request = request.model_copy(deep=True)
            if request.output_file:
                if request.output_file.endswith('.csv'):
                    json_request.output_file = request.output_file.replace('.csv', '.json')
                elif not request.output_file.endswith('.json'):
                    json_request.output_file = f"{request.output_file}.json"
            
            json_result = await self._save_to_json(result, json_request)
            save_results.append(json_result)
        
        # Print save summaries
        for save_result in save_results:
            print(save_result.get_summary())
        
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
                
                # Write headers if new file or overwriting
                if not file_exists:
                    writer.writerow(['Date', 'Close'])
                    
                # Write data
                csv_rows = result.to_csv_rows()
                for row_data in csv_rows:
                    writer.writerow([row_data['date'], row_data['close']])
                    rows_written += 1
            
            # Get file size
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
            # Determine filename
            if request.output_file:
                filename = request.output_file
                if not filename.endswith('.json'):
                    filename = f"{filename}.json"
            else:
                filename = request.get_default_filename('json')
            
            # Get JSON structure
            json_data = result.to_json_structure()
            
            # Handle append mode for JSON
            if request.append_to_file and os.path.isfile(filename):
                try:
                    with open(filename, 'r') as file:
                        existing_data = json.load(file)
                    
                    # If existing file has the same structure, merge data
                    if isinstance(existing_data, dict) and "historical_data" in existing_data:
                        # Update metadata
                        existing_data["extraction_date"] = json_data["extraction_date"]
                        existing_data["data_count"] += len(json_data["historical_data"])
                        
                        # Merge historical data (avoid duplicates)
                        existing_dates = {item.get('date') for item in existing_data["historical_data"]}
                        for new_item in json_data["historical_data"]:
                            if new_item.get('date') not in existing_dates:
                                existing_data["historical_data"].append(new_item)
                        
                        json_data = existing_data
                    else:
                        # If structure is different, create array of datasets
                        json_data = [existing_data, json_data]
                        
                except (json.JSONDecodeError, IOError):
                    # If can't read/parse existing file, overwrite
                    pass
            
            # Write JSON data
            with open(filename, 'w') as file:
                json.dump(json_data, file, indent=2, ensure_ascii=False)
            
            # Get file size
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


# Enhanced convenience function using models
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
        # Create validated request
        request = create_extraction_request(
            currency_pair=currency_pair,
            start_date=start_date,
            end_date=end_date,
            output_file=output_file,
            append_to_file=append_to_file,
            output_format=output_format
        )
        
        # Execute extraction
        extractor = ForexDataExtractor()
        return await extractor.extract_forex_data(request)
        
    except ValidationError as e:
        # Return failed result for validation errors
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


# Example usage with models
if __name__ == "__main__":
    import sys
    from datetime import datetime
    from utils import get_valid_date
    
    async def main():
        if len(sys.argv) >= 5:
            # Command line usage
            currency_pair = sys.argv[1].upper()
            start_date = parse_date_string(sys.argv[2])
            end_date = parse_date_string(sys.argv[3])
            output_format = sys.argv[4].lower()
            
            # Validate dates using utils function
            if not start_date:
                print(f"Error: Invalid start date '{sys.argv[2]}'. Use 'MMM DD, YYYY' format.")
                return
            if not end_date:
                print(f"Error: Invalid end date '{sys.argv[3]}'. Use 'MMM DD, YYYY' format.")
                return
            
            # Additional validation using utils
            try:
                from utils import date_to_unix  # Test if dates can be converted
                date_to_unix(start_date)
                date_to_unix(end_date)
            except Exception as e:
                print(f"Error: Date validation failed - {e}")
                return
            
            result = await get_forex_data(
                currency_pair, start_date, end_date, output_format=output_format
            )
            
            if result.success:
                print(f"✓ {result.get_summary()}")
                print(f"✓ Data saved with {len(result.data_points)} points")
            else:
                print(f"✗ Extraction failed: {result.error_message}")
                
        else:
            # Interactive example with utils validation
            print("Usage: python forex_extractor.py USDEUR 'Jan 01, 2024' 'Jan 01, 2023' [csv|json|both]")
            print("Running interactive example...")
            
            try:
                # Get currency pair
                currency_pair = input("Enter currency pair (e.g., USDEUR, GBPUSD): ").upper().strip()
                if not currency_pair:
                    print("Error: Currency pair cannot be empty")
                    return
                
                # Get dates using utils validation with business constraints
                max_start_date = datetime.today()
                min_end_date = datetime(2005, 1, 1)
                
                print(f"\nDate constraints:")
                print(f"- Start date cannot be later than {max_start_date.strftime('%b %d, %Y')}")
                print(f"- End date cannot be earlier than {min_end_date.strftime('%b %d, %Y')}")
                print(f"- Start date must be >= end date (Yahoo Finance requirement)\n")
                
                # Get start date with validation
                start_date = get_valid_date(
                    "Enter start date (MMM DD, YYYY): ", 
                    max_date=max_start_date,
                    min_date=min_end_date
                )
                
                # Get end date with validation (ensuring it's not later than start date)
                end_date = get_valid_date(
                    "Enter end date (MMM DD, YYYY): ", 
                    max_date=start_date,  # End date can't be later than start date
                    min_date=min_end_date
                )
                
                # Get output format
                output_format = input("Enter output format (csv/json/both) [default=csv]: ").lower().strip() or "csv"
                
                # Validate output format
                valid_formats = ['csv', 'json', 'both']
                if output_format not in valid_formats:
                    print(f"Warning: Invalid format '{output_format}', using 'csv' instead")
                    output_format = 'csv'
                
                print(f"\nStarting extraction...")
                print(f"Currency Pair: {currency_pair}")
                print(f"Date Range: {end_date.strftime('%b %d, %Y')} to {start_date.strftime('%b %d, %Y')}")
                print(f"Output Format: {output_format}")
                
                result = await get_forex_data(
                    currency_pair=currency_pair,
                    start_date=start_date,
                    end_date=end_date,
                    output_format=output_format
                )
                
                if result.success:
                    print(f"\n✓ {result.get_summary()}")
                    print(f"✓ Extraction completed successfully!")
                    
                    # Show sample data
                    if result.data_points:
                        print(f"\nSample data points:")
                        sample_count = min(5, len(result.data_points))
                        for i, point in enumerate(result.data_points[:sample_count]):
                            print(f"  {point.date_string}: {point.close_price}")
                        if len(result.data_points) > sample_count:
                            print(f"  ... and {len(result.data_points) - sample_count} more points")
                            
                        # Show date range summary
                        if len(result.data_points) > 1:
                            print(f"\nData range: {result.data_points[-1].date_string} to {result.data_points[0].date_string}")
                    else:
                        print("\nNo data points found for the specified criteria")
                        
                else:
                    print(f"\n✗ Extraction failed: {result.error_message}")
                    
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
            except ValueError as e:
                print(f"\nValidation error: {e}")
            except Exception as e:
                print(f"\nUnexpected error: {e}")
                import traceback
                traceback.print_exc()
    
    asyncio.run(main())