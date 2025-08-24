import sys
from datetime import datetime
from .utils import get_valid_date, parse_date_string, date_to_unix
from .scraper import fetch_forex_data
from .config import config

def show_help():
    """Display comprehensive help information."""
    help_text = f"""
{config.APP_NAME} v{config.APP_VERSION}
{config.APP_DESCRIPTION}

USAGE:
    forex-scraper <currency_pair> <start_date> <end_date> [format]
    forex-scraper [OPTIONS]

ARGUMENTS:
    currency_pair    Currency pair code (e.g., USDEUR, GBPUSD)
    start_date       Start date in 'MMM DD, YYYY' format (e.g., 'Jan 01, 2024')
    end_date         End date in 'MMM DD, YYYY' format (e.g., 'Jan 01, 2023')
    format           Output format: csv, json, or both (default: csv)

OPTIONS:
    -h, --help       Show this help message and exit
    -v, --version    Show version information and exit
    -i, --interactive Run in interactive mode

EXAMPLES:
    # Basic usage
    forex-scraper USDEUR 'Jan 01, 2024' 'Jan 01, 2023' csv
    
    # JSON output
    forex-scraper GBPUSD 'Dec 31, 2023' 'Jan 01, 2023' json
    
    # Both formats
    forex-scraper EURJPY 'Mar 15, 2024' 'Jan 01, 2024' both
    
    # Interactive mode
    forex-scraper --interactive

DATE CONSTRAINTS:
    • Start date cannot be later than {config.dates.MAX_START_DATE.strftime('%b %d, %Y')}
    • End date cannot be earlier than {config.dates.MIN_END_DATE.strftime('%b %d, %Y')}
    • Start date must be >= end date (Yahoo Finance requirement)

SUPPORTED FORMATS:
    • CSV: Comma-separated values with Date,Close columns
    • JSON: Structured JSON with metadata
    • BOTH: Creates both CSV and JSON files

OUTPUT:
    Files are saved to: {config.files.DEFAULT_OUTPUT_DIR}/
    Default naming: <currency_pair>_historical_data.<ext>

For more information, visit: https://github.com/yungKnight/forex_data_extractor
"""
    print(help_text.strip())

def show_version():
    """Display version information."""
    print(f"{config.APP_NAME} v{config.APP_VERSION}")

def main():
    """Main CLI entry point with help support."""
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['-h', '--help', 'help']:
            show_help()
            return
        elif arg in ['-v', '--version', 'version']:
            show_version()
            return
        elif arg in ['-i', '--interactive', 'interactive']:
            sys.argv = [sys.argv[0]]
    
    if len(sys.argv) >= 5:
        currency_pair = sys.argv[1].upper()
        start_date = sys.argv[2]
        end_date = sys.argv[3]
        output_format = sys.argv[4].lower()
        
        start_dt = parse_date_string(start_date)
        end_dt = parse_date_string(end_date)
        
        if not start_dt:
            print(f"{config.cli.ERROR_SYMBOL} Error: Invalid start date '{start_date}'. Use 'MMM DD, YYYY' format.")
            print("Use 'forex-scraper --help' for more information.")
            return
            
        if not end_dt:
            print(f"{config.cli.ERROR_SYMBOL} Error: Invalid end date '{end_date}'. Use 'MMM DD, YYYY' format.")
            print("Use 'forex-scraper --help' for more information.")
            return
        
        if output_format not in config.cli.VALID_OUTPUT_FORMATS:
            print(f"{config.cli.ERROR_SYMBOL} Error: Invalid format '{output_format}'. Use: {', '.join(config.cli.VALID_OUTPUT_FORMATS)}")
            print("Use 'forex-scraper --help' for more information.")
            return
        
        try:
            date_to_unix(start_dt)
            date_to_unix(end_dt)
        except Exception as e:
            print(f"{config.cli.ERROR_SYMBOL} Error: Date validation failed - {e}")
            print("Use 'forex-scraper --help' for more information.")
            return
        
        result = fetch_forex_data(currency_pair, start_dt, end_dt, output_format=output_format)
        
        if result.success:
            print(f"{config.cli.SUCCESS_SYMBOL} Data saved with {len(result.data_points)} points")
        else:
            print(f"{config.cli.ERROR_SYMBOL} Extraction failed: {result.error_message}")
    
    elif len(sys.argv) > 1:
        print(f"{config.cli.ERROR_SYMBOL} Error: Invalid number of arguments.")
        print(config.cli.USAGE_MESSAGE)
        print("Use 'forex-scraper --help' for detailed information.")
    
    else:
        print("Running interactive interface...")
        print("(Tip: Use 'forex-scraper --help' to see command-line options)")
        
        try:
            currency_pair = input(config.cli.PROMPTS['currency_pair']).upper().strip()
            if not currency_pair:
                print("Error: Currency pair cannot be empty")
                return
            
            print(f"\nDate constraints:")
            print(f"- Start date cannot be later than {config.dates.MAX_START_DATE.strftime('%b %d, %Y')}")
            print(f"- End date cannot be earlier than {config.dates.MIN_END_DATE.strftime('%b %d, %Y')}")
            print(f"- Start date must be >= end date (Yahoo Finance requirement)\n")
            
            start_date = get_valid_date(
                config.cli.PROMPTS['start_date'], 
                max_date=config.dates.MAX_START_DATE, 
                min_date=config.dates.MIN_END_DATE
            )
            end_date = get_valid_date(
                config.cli.PROMPTS['end_date'], 
                max_date=start_date, 
                min_date=config.dates.MIN_END_DATE
            )
            
            output_format = input(config.cli.PROMPTS['output_format']).lower().strip() or config.cli.DEFAULT_OUTPUT_FORMAT
            
            if output_format not in config.cli.VALID_OUTPUT_FORMATS:
                print(f"Warning: Invalid format '{output_format}', using '{config.cli.DEFAULT_OUTPUT_FORMAT}' instead")
                output_format = config.cli.DEFAULT_OUTPUT_FORMAT
            
            print(f"\nStarting extraction...")
            print(f"Currency Pair: {currency_pair}")
            print(f"Date Range: {end_date.strftime('%b %d, %Y')} to {start_date.strftime('%b %d, %Y')}")
            print(f"Output Format: {output_format}")
            
            result = fetch_forex_data(currency_pair, start_date, end_date, output_format=output_format)
            
            if result.success:
                print(f"{config.cli.SUCCESS_SYMBOL} Extraction completed successfully!")
            else:
                print(f"{config.cli.ERROR_SYMBOL} Extraction failed: {result.error_message}")
        
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
        except ValueError as e:
            print(f"\nValidation error: {e}")
            print("Use 'forex-scraper --help' for more information.")
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            print("Use 'forex-scraper --help' for more information.")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()