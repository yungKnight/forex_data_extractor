from pydantic import BaseModel, Field, validator, model_validator
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Literal
from decimal import Decimal
import decimal
from enum import Enum


class OutputFormat(str, Enum):
    """Enum for supported output formats"""
    CSV = "csv"
    JSON = "json" 
    BOTH = "both"


class ExtractionRequest(BaseModel):
    """Request model for forex data extraction with comprehensive validation"""
    currency_pair: str = Field(..., description="Currency pair code (e.g., USDEUR, GBPUSD)")
    start_date: datetime = Field(..., description="Start date for data extraction")
    end_date: datetime = Field(..., description="End date for data extraction")
    output_file: Optional[str] = Field(None, description="Optional output file name")
    append_to_file: bool = Field(True, description="Whether to append to existing file")
    output_format: OutputFormat = Field(OutputFormat.CSV, description="Output format")

    min_end_date: datetime = Field(default_factory=lambda: datetime(2005, 1, 1))
    max_start_date: datetime = Field(default_factory=datetime.today)
    
    @validator('currency_pair')
    def validate_currency_pair(cls, ticker):
        """Validate currency pair format"""
        if not ticker:
            raise ValueError("Currency pair cannot be empty")
        
        ticker = ticker.upper().strip()
        
        if not ticker.isalpha():
            raise ValueError("Currency pair must contain only letters")
        
        return ticker
    
    @validator('start_date')
    def validate_start_date_constraints(cls, date, values):
        """Validate start date against maximum allowed date"""
        max_start_date = values.get('max_start_date', datetime.today())
        if date > max_start_date:
            raise ValueError(f"Start date cannot be later than {max_start_date.strftime('%b %d, %Y')}.")
        return date
    
    @validator('end_date')
    def validate_end_date_constraints(cls, date, values):
        """Validate end date against minimum allowed date"""
        min_end_date = values.get('min_end_date', datetime(2005, 1, 1))
        if date < min_end_date:
            raise ValueError(f"End date cannot be earlier than {min_end_date.strftime('%b %d, %Y')}.")
        return date
    
    @model_validator(mode='after')
    def validate_date_range(self):
        """Validate that start_date >= end_date (Yahoo Finance logic)"""
        if self.start_date and self.end_date and self.start_date < self.end_date:
            raise ValueError("Start date cannot be earlier than the end date.")
        
        return self
    
    @validator('output_file')
    def validate_output_file(cls, file_name):
        """Validate output file name if provided"""
        if file_name is not None:
            file_name = file_name.strip()
            if not file_name:
                return None
            
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                if char in file_name:
                    raise ValueError(f"Output filename cannot contain '{char}'")
        return file_name
    
    def get_default_filename(self, extension: str = None) -> str:
        """Generate default filename based on currency pair"""
        if extension is None:
            if self.output_format == OutputFormat.JSON:
                extension = "json"
            elif self.output_format == OutputFormat.CSV:
                extension = "csv"
            else:
                extension = "csv" 
        
        return f"{self.currency_pair}_historical_data.{extension}"
    
    def to_url_params(self) -> Dict[str, Any]:
        """Convert to URL parameters for Yahoo Finance"""
        from utils import date_to_unix
        
        return {
            'currency_pair': self.currency_pair,
            'start_date': date_to_unix(self.start_date),
            'end_date': date_to_unix(self.end_date)
        }


class PriceDataPoint(BaseModel):
    """Individual forex price data point"""
    date: datetime = Field(..., description="Date of the price point")
    close_price: Decimal = Field(..., description="Closing price for the currency pair")
    date_string: str = Field(..., description="Original date string from Yahoo Finance")
    
    @validator('close_price', pre=True)
    def parse_close_price(cls, price):
        """Parse and validate close price from string or numeric input"""
        if isinstance(price, str):
            price = price.replace(',', '').strip()
            if not price:
                raise ValueError("Close price cannot be empty")
        
        try:
            price = Decimal(str(price))
            if price <= 0:
                raise ValueError("Close price must be positive")
            return price
        except (ValueError, decimal.InvalidOperation) as e:
            raise ValueError(f"Invalid close price format: {price}")
    
    @validator('date_string')
    def validate_date_string(cls, v):
        """Ensure date string is not empty"""
        if not v or not v.strip():
            raise ValueError("Date string cannot be empty")
        return v.strip()
    
    def to_tuple(self) -> Tuple[str, str]:
        """Convert to tuple format for backward compatibility"""
        return (self.date_string, str(self.close_price))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "date": self.date.isoformat(),
            "close_price": str(self.close_price),
            "date_string": self.date_string
        }


class ExtractionMetadata(BaseModel):
    """Metadata about the extraction process"""
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    total_points: int = Field(0, description="Total number of data points extracted")
    currency_pair: str = Field(..., description="Currency pair that was extracted")
    date_range_start: datetime = Field(..., description="Actual start date of data")
    date_range_end: datetime = Field(..., description="Actual end date of data")
    request_params: ExtractionRequest = Field(..., description="Original request parameters")
    headers_found: List[str] = Field(default_factory=list, description="Table headers found on page")
    url_accessed: Optional[str] = Field(None, description="URL that was scraped")
    
    @validator('total_points')
    def validate_total_points(cls, v):
        """Ensure total points is non-negative"""
        if v < 0:
            raise ValueError("Total points cannot be negative")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "extraction_timestamp": self.extraction_timestamp.isoformat(),
            "total_points": self.total_points,
            "currency_pair": self.currency_pair,
            "date_range_start": self.date_range_start.isoformat(),
            "date_range_end": self.date_range_end.isoformat(),
            "headers_found": self.headers_found,
            "url_accessed": self.url_accessed,
            "request_params": {
                "currency_pair": self.request_params.currency_pair,
                "start_date": self.request_params.start_date.isoformat(),
                "end_date": self.request_params.end_date.isoformat(),
                "output_format": self.request_params.output_format.value,
                "append_to_file": self.request_params.append_to_file
            }
        }


class ForexExtractionResult(BaseModel):
    """Complete result of forex data extraction process"""
    data_points: List[PriceDataPoint] = Field(default_factory=list, description="Extracted price data points")
    metadata: ExtractionMetadata = Field(..., description="Extraction metadata")
    success: bool = Field(True, description="Whether extraction was successful")
    error_message: Optional[str] = Field(None, description="Error message if extraction failed")
    
    @validator('data_points')
    def sort_data_points(cls, v):
        """Ensure data points are sorted chronologically"""
        if v:
            v.sort(key=lambda point: point.date)
        return v
    
    @model_validator(mode='after')
    def update_metadata_total(self):
        """Update metadata total points based on actual data points"""
        data_points = self.data_points
        metadata = self.metadata
        
        if metadata:
            metadata.total_points = len(data_points)
            
            if data_points:
                dates = [point.date for point in data_points]
                metadata.date_range_start = max(dates)
                metadata.date_range_end = min(dates)
        
        return self
    
    def to_tuple_list(self) -> List[Tuple[str, str]]:
        """Convert to list of tuples for backward compatibility"""
        return [point.to_tuple() for point in self.data_points]
    
    def to_csv_rows(self) -> List[Dict[str, str]]:
        """Convert to list of dictionaries suitable for CSV writing"""
        return [
            {
                "date": point.date_string,
                "close": str(point.close_price)
            }
            for point in self.data_points
        ]
    
    def to_json_structure(self) -> Dict[str, Any]:
        """Convert to JSON structure matching your extractor format"""
        return {
            "currency_pair": self.metadata.currency_pair,
            "extraction_date": self.metadata.extraction_timestamp.isoformat(),
            "data_count": len(self.data_points),
            "historical_data": [
                {
                    "date": point.date_string,
                    "close": str(point.close_price)
                }
                for point in self.data_points
            ],
            "metadata": self.metadata.to_dict()
        }
    
    def get_summary(self) -> str:
        """Get a summary string of the extraction results"""
        if not self.success:
            return f"Extraction failed: {self.error_message}"
        
        return (f"Successfully extracted {len(self.data_points)} data points for "
                f"{self.metadata.currency_pair} from "
                f"{self.metadata.date_range_end.strftime('%b %d, %Y')} to "
                f"{self.metadata.date_range_start.strftime('%b %d, %Y')}")


class FileOperationResult(BaseModel):
    """Result of a file save operation"""
    file_path: str = Field(..., description="Path where file was saved")
    format_type: OutputFormat = Field(..., description="Format of the saved file")
    rows_written: int = Field(0, description="Number of data rows written")
    success: bool = Field(True, description="Whether save operation was successful")
    error_message: Optional[str] = Field(None, description="Error message if save failed")
    file_size_bytes: Optional[int] = Field(None, description="Size of saved file in bytes")
    
    def get_summary(self) -> str:
        """Get a summary of the file operation"""
        if not self.success:
            return f"File save failed: {self.error_message}"
        
        size_info = f" ({self.file_size_bytes} bytes)" if self.file_size_bytes else ""
        return f"{self.format_type.value.upper()} data saved to {self.file_path}{size_info} - {self.rows_written} rows"

def create_extraction_request(
    currency_pair: str,
    start_date: datetime,
    end_date: datetime,
    output_file: Optional[str] = None,
    append_to_file: bool = True,
    output_format: str = "csv"
) -> ExtractionRequest:
    """Factory function to create ExtractionRequest from parameters"""
    
    if isinstance(output_format, str):
        output_format = OutputFormat(output_format.lower())
    
    return ExtractionRequest(
        currency_pair=currency_pair,
        start_date=start_date,
        end_date=end_date,
        output_file=output_file,
        append_to_file=append_to_file,
        output_format=output_format
    )