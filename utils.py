from datetime import datetime
from typing import Optional

def validate_single_date(
    date: datetime, 
    max_date: Optional[datetime] = None,
    min_date: Optional[datetime] = None,
    date_name: str = "Date"
) -> None:
    """
    Validates a single date against optional min/max constraints.
    
    Args:
        date (datetime): The date to validate
        max_date (datetime, optional): Maximum allowed date
        min_date (datetime, optional): Minimum allowed date
        date_name (str): Name of the date field for error messages
        
    Raises:
        ValueError: If date validation fails
    """
    if max_date and date > max_date:
        raise ValueError(f"{date_name} cannot be later than {max_date.strftime('%b %d, %Y')}.")
    
    if min_date and date < min_date:
        raise ValueError(f"{date_name} cannot be earlier than {min_date.strftime('%b %d, %Y')}.")


def get_valid_date(prompt: str, max_date: Optional[datetime] = None, min_date: Optional[datetime] = None) -> datetime:
    """
    Prompts user for a date input and validates it against optional min/max constraints.
    
    Args:
        prompt (str): The prompt message to display to the user
        max_date (datetime, optional): Maximum allowed date
        min_date (datetime, optional): Minimum allowed date
        
    Returns:
        datetime: Valid datetime object
    """
    while True:
        try:
            date_str = input(prompt)
            date = datetime.strptime(date_str, '%b %d, %Y')
            validate_single_date(date, max_date, min_date)
            return date
        except ValueError as e:
            if "does not match format" in str(e) or "unconverted data remains" in str(e):
                print("Invalid date format. Please use 'MMM DD, YYYY' format (e.g., 'Sep 30, 2024').")
            else:
                print(str(e))


def date_to_unix(date: datetime) -> int:
    """
    Converts a datetime object to Unix timestamp.
    
    Args:
        date (datetime): The datetime object to convert
        
    Returns:
        int: Unix timestamp (seconds since epoch)
    """
    return int(date.timestamp())

def parse_date_string(date_str: str) -> Optional[datetime]:
    """
    Convert date string from Yahoo Finance to datetime object.
    Handles multiple date formats commonly used by Yahoo Finance.
    
    Args:
        date_str (str): Date string to parse
        
    Returns:
        datetime or None: Parsed datetime object, or None if parsing fails
    """
    date_formats = [
        '%b %d, %Y',     
        '%B %d, %Y',     
        '%Y-%m-%d',      
        '%m/%d/%Y',      
        '%d/%m/%Y',      
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    print(f"Could not parse date: {date_str}")
    return None

def format_date_for_display(date: datetime, format_style: str = 'short') -> str:
    """
    Format datetime object for consistent display.
    
    Args:
        date (datetime): Date to format
        format_style (str): 'short' for 'Sep 30, 2024' or 'long' for 'September 30, 2024'
        
    Returns:
        str: Formatted date string
    """
    if format_style == 'long':
        return date.strftime('%B %d, %Y')
    else:
        return date.strftime('%b %d, %Y')