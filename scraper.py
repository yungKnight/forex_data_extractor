import asyncio
from playwright.async_api import async_playwright
import scrapy
from scrapy.http import HtmlResponse
import csv
import json
import os
import re
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from utils import date_to_unix as to_unix, parse_date_string


class ForexDataExtractor:
    """
    A class to extract historical forex data from Yahoo Finance.
    """
    
    def __init__(self):
        self.base_url = "https://finance.yahoo.com/quote/{currency_pair}=X/history/?period1={end_date}&period2={start_date}"
        self.min_end_date = datetime(2005, 1, 1)
        self.max_start_date = datetime.today()
    
    async def extract_forex_data(
        self, 
        currency_pair: str, 
        start_date: datetime, 
        end_date: datetime,
        output_file: Optional[str] = None,
        append_to_file: bool = True,
        output_format: str = "csv"
    ) -> List[Tuple[str, str]]:
        """
        Extract historical forex data for a given currency pair and date range.
        
        Args:
            currency_pair (str): Currency pair (e.g., 'USDEUR', 'GBPUSD')
            start_date (datetime): Start date for data extraction
            end_date (datetime): End date for data extraction  
            output_file (str, optional): Output file to save data. If None, uses default naming
            append_to_file (bool): Whether to append to existing file or overwrite
            output_format (str): Output format - 'csv', 'json', or 'both' (default: 'csv')
            
        Returns:
            List[Tuple[str, str]]: List of tuples containing (date, close_price)
            
        Raises:
            ValueError: If dates are invalid or outside allowed range
        """
        currency_pair = currency_pair.upper()
        
        # Validate date constraints (matching your original utils logic)
        if start_date > self.max_start_date:
            raise ValueError(f"Start date cannot be later than {self.max_start_date.strftime('%b %d, %Y')}.")
        
        if end_date < self.min_end_date:
            raise ValueError(f"End date cannot be earlier than {self.min_end_date.strftime('%b %d, %Y')}.")
        
        # Validate date range relationship
        if start_date < end_date:
            raise ValueError("Start date cannot be earlier than the end date.")
        
        # Convert dates to Unix timestamps
        start_date_secs = to_unix(start_date)
        end_date_secs = to_unix(end_date)
        
        print(f"Extracting {currency_pair} data from {end_date.strftime('%b %d, %Y')} to {start_date.strftime('%b %d, %Y')}")
        
        price_data = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Block unnecessary resources for faster loading
            async def handle_request(route, request):
                if request.resource_type in ['image', 'iframe']:
                    await route.abort()
                else:
                    await route.continue_()

            await page.route("**/*", handle_request)

            # Navigate to Yahoo Finance
            url = self.base_url.format(
                currency_pair=currency_pair,
                end_date=end_date_secs,
                start_date=start_date_secs
            )
            
            print(f'Navigating to Yahoo! Finance {currency_pair} historical data')
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
                print("Failed to retrieve HTML content")
                return price_data

            response = HtmlResponse(url=page.url, body=html_content.encode(), encoding='utf-8')

            # Extract table headers
            headers = response.css('table thead tr th::text').getall()
            headers = [header.strip() for header in headers if header.strip()]
            print(f"Extracted headers: {headers}")

            # Find date and close price columns
            date_header = next((h for h in headers if h == 'Date'), 'Date')
            close_header = next((h for h in headers if h == 'Close'), 'Close')

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
                
                print(f"{currency_pair} closed at {close_price} on {date_text}")

                # Parse and validate date
                row_date = parse_date_string(date_text)
                if row_date is None:
                    continue

                # Check if date is within specified range
                if row_date <= start_date and row_date >= end_date:
                    price_data.append((date_text, close_price))

            print(f"Total data points collected: {len(price_data)}")
            
            # Sort data chronologically
            price_data.sort(key=lambda x: parse_date_string(x[0]))

            # Save to file if requested
            if output_file is not None or len(price_data) > 0:
                await self._save_data(
                    price_data, 
                    currency_pair, 
                    date_header, 
                    close_header, 
                    output_file, 
                    append_to_file,
                    output_format
                )

            await page.close()
            await browser.close()

        return price_data

    async def _save_data(
        self, 
        price_data: List[Tuple[str, str]], 
        currency_pair: str,
        date_header: str,
        close_header: str,
        output_file: Optional[str] = None,
        append_to_file: bool = True,
        output_format: str = "csv"
    ) -> None:
        """
        Save price data to file(s) in specified format(s).
        
        Args:
            price_data: List of (date, price) tuples
            currency_pair: Currency pair name
            date_header: Header for date column
            close_header: Header for close price column
            output_file: Output file name (optional)
            append_to_file: Whether to append to existing file
            output_format: Format to save - 'csv', 'json', or 'both'
        """
        if output_format.lower() == "csv":
            await self._save_to_csv(
                price_data, currency_pair, date_header, close_header, output_file, append_to_file
            )
        elif output_format.lower() == "json":
            await self._save_to_json(
                price_data, currency_pair, date_header, close_header, output_file, append_to_file
            )
        elif output_format.lower() == "both":
            # Save CSV
            csv_file = output_file
            if csv_file and not csv_file.endswith('.csv'):
                csv_file = f"{csv_file}.csv"
            await self._save_to_csv(
                price_data, currency_pair, date_header, close_header, csv_file, append_to_file
            )
            
            # Save JSON
            json_file = output_file
            if json_file:
                if json_file.endswith('.csv'):
                    json_file = json_file.replace('.csv', '.json')
                elif not json_file.endswith('.json'):
                    json_file = f"{json_file}.json"
            await self._save_to_json(
                price_data, currency_pair, date_header, close_header, json_file, append_to_file
            )
        else:
            raise ValueError("output_format must be 'csv', 'json', or 'both'")

    async def _save_to_csv(
        self, 
        price_data: List[Tuple[str, str]], 
        currency_pair: str,
        date_header: str,
        close_header: str,
        output_file: Optional[str] = None,
        append_to_file: bool = True
    ) -> None:
        """
        Save price data to CSV file.
        
        Args:
            price_data: List of (date, price) tuples
            currency_pair: Currency pair name
            date_header: Header for date column
            close_header: Header for close price column
            output_file: Output file name (optional)
            append_to_file: Whether to append to existing file
        """
        if output_file is None:
            output_file = f'{currency_pair}_historical_data.csv'
        elif not output_file.endswith('.csv'):
            output_file = f'{output_file}.csv'
        
        file_exists = os.path.isfile(output_file) and append_to_file
        mode = 'a' if append_to_file else 'w'

        with open(output_file, mode=mode, newline='') as file:
            writer = csv.writer(file)

            # Write headers if new file or overwriting
            if not file_exists:
                writer.writerow([date_header, close_header])

            # Write data
            for date_str, price in price_data:
                writer.writerow([date_str, price])

        print(f"CSV data saved to {output_file}")
        print(f"Total rows written: {len(price_data)}")

    async def _save_to_json(
        self, 
        price_data: List[Tuple[str, str]], 
        currency_pair: str,
        date_header: str,
        close_header: str,
        output_file: Optional[str] = None,
        append_to_file: bool = True
    ) -> None:
        """
        Save price data to JSON file.
        
        Args:
            price_data: List of (date, price) tuples
            currency_pair: Currency pair name
            date_header: Header for date column
            close_header: Header for close price column
            output_file: Output file name (optional)
            append_to_file: Whether to append to existing file
        """
        if output_file is None:
            output_file = f'{currency_pair}_historical_data.json'
        elif not output_file.endswith('.json'):
            output_file = f'{output_file}.json'
        
        # Create JSON structure
        json_data = {
            "currency_pair": currency_pair,
            "extraction_date": datetime.now().isoformat(),
            "data_count": len(price_data),
            "historical_data": []
        }
        
        # Convert data to JSON format
        for date_str, price in price_data:
            json_data["historical_data"].append({
                date_header.lower(): date_str,
                close_header.lower(): price
            })
        
        # Handle append mode for JSON
        if append_to_file and os.path.isfile(output_file):
            try:
                with open(output_file, 'r') as file:
                    existing_data = json.load(file)
                
                # If existing file has the same structure, merge data
                if isinstance(existing_data, dict) and "historical_data" in existing_data:
                    # Update metadata
                    existing_data["extraction_date"] = json_data["extraction_date"]
                    existing_data["data_count"] += len(price_data)
                    
                    # Merge historical data
                    existing_dates = {item.get(date_header.lower()) for item in existing_data["historical_data"]}
                    for new_item in json_data["historical_data"]:
                        if new_item.get(date_header.lower()) not in existing_dates:
                            existing_data["historical_data"].append(new_item)
                    
                    json_data = existing_data
                else:
                    # If structure is different, create array of datasets
                    json_data = [existing_data, json_data]
                    
            except (json.JSONDecodeError, IOError):
                # If can't read/parse existing file, overwrite
                pass
        
        # Write JSON data
        with open(output_file, 'w') as file:
            json.dump(json_data, file, indent=2, ensure_ascii=False)
        
        print(f"JSON data saved to {output_file}")
        print(f"Total data points written: {len(price_data)}")


# Convenience function for direct usage
async def get_forex_data(
    currency_pair: str,
    start_date: datetime,
    end_date: datetime,
    output_file: Optional[str] = None,
    append_to_file: bool = True,
    output_format: str = "csv"
) -> List[Tuple[str, str]]:
    """
    Convenience function to extract forex data without instantiating the class.
    
    Args:
        currency_pair (str): Currency pair (e.g., 'USDEUR', 'GBPUSD')
        start_date (datetime): Start date for data extraction
        end_date (datetime): End date for data extraction
        output_file (str, optional): Output file to save data
        append_to_file (bool): Whether to append to existing file
        output_format (str): Output format - 'csv', 'json', or 'both' (default: 'csv')
        
    Returns:
        List[Tuple[str, str]]: List of (date, close_price) tuples
    """
    extractor = ForexDataExtractor()
    return await extractor.extract_forex_data(
        currency_pair, start_date, end_date, output_file, append_to_file, output_format
    )


# Example usage
if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) >= 5:
            # Command line usage: python forex_extractor.py USDEUR "Jan 01, 2024" "Jan 01, 2023" json
            currency_pair = sys.argv[1].upper()
            start_date = parse_date_string(sys.argv[2])
            end_date = parse_date_string(sys.argv[3])
            output_format = sys.argv[4].lower()
            
            if not start_date or not end_date:
                print("Error: Invalid date format. Use 'MMM DD, YYYY' format.")
                return
            
            data = await get_forex_data(
                currency_pair, start_date, end_date, output_format=output_format
            )
            print(f"Retrieved {len(data)} data points for {currency_pair}")
        else:
            # Default example usage
            print("Usage: python forex_extractor.py USDEUR 'Jan 01, 2024' 'Jan 01, 2023' [csv|json|both]")
            print("Running default example...")
            
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2023, 1, 1)
            currency_pair = input("Enter the currency pair (e.g., USDEUR, GBPUSD): ").upper()
            output_format = input("Enter output format (csv/json/both) [default=csv]: ").lower() or "csv"
            
            data = await get_forex_data(
                currency_pair=currency_pair,
                start_date=start_date,
                end_date=end_date,
                output_format=output_format
            )
            
            print(f"Retrieved {len(data)} data points")
    
    asyncio.run(main())