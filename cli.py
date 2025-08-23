import sys
from datetime import datetime
from utils import get_valid_date, parse_date_string, date_to_unix
from scraper import fetch_forex_data


def main():
    if len(sys.argv) >= 5:
        currency_pair = sys.argv[1].upper()
        start_date = sys.argv[2]
        end_date = sys.argv[3]
        output_format = sys.argv[4].lower()

        start_dt = parse_date_string(start_date)
        end_dt = parse_date_string(end_date)
        if not start_dt:
            print(f"Error: Invalid start date '{start_date}'. Use 'MMM DD, YYYY' format.")
            return
        if not end_dt:
            print(f"Error: Invalid end date '{end_date}'. Use 'MMM DD, YYYY' format.")
            return

        try:
            date_to_unix(start_dt)
            date_to_unix(end_dt)
        except Exception as e:
            print(f"Error: Date validation failed - {e}")
            return

        result = fetch_forex_data(currency_pair, start_dt, end_dt, output_format=output_format)
        if result.success:
            print(f"✓ Data saved with {len(result.data_points)} points")
        else:
            print(f"✗ Extraction failed: {result.error_message}")

    else:
        print("Usage: python cli.py USDEUR 'Jan 01, 2024' 'Jan 01, 2023' [csv|json|both]")
        print("Running interactive interface...")

        try:
            currency_pair = input("Enter currency pair (e.g., USDEUR, GBPUSD): ").upper().strip()
            if not currency_pair:
                print("Error: Currency pair cannot be empty")
                return

            max_start_date = datetime.today()
            min_end_date = datetime(2005, 1, 1)

            print(f"\nDate constraints:")
            print(f"- Start date cannot be later than {max_start_date.strftime('%b %d, %Y')}")
            print(f"- End date cannot be earlier than {min_end_date.strftime('%b %d, %Y')}")
            print(f"- Start date must be >= end date (Yahoo Finance requirement)\n")

            start_date = get_valid_date("Enter start date (MMM DD, YYYY): ", max_date=max_start_date, min_date=min_end_date)
            end_date = get_valid_date("Enter end date (MMM DD, YYYY): ", max_date=start_date, min_date=min_end_date)

            output_format = input("Enter output format (csv/json/both) [default=csv]: ").lower().strip() or "csv"
            if output_format not in ["csv", "json", "both"]:
                print(f"Warning: Invalid format '{output_format}', using 'csv' instead")
                output_format = "csv"

            print(f"\nStarting extraction...")
            print(f"Currency Pair: {currency_pair}")
            print(f"Date Range: {end_date.strftime('%b %d, %Y')} to {start_date.strftime('%b %d, %Y')}")
            print(f"Output Format: {output_format}")

            result = fetch_forex_data(currency_pair, start_date, end_date, output_format=output_format)
            if result.success:
                print(f"✓ Extraction completed successfully!")
            else:
                print(f"✗ Extraction failed: {result.error_message}")

        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
        except ValueError as e:
            print(f"\nValidation error: {e}")
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
