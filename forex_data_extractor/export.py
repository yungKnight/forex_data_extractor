import os
import json
import csv
from typing import List
from .models import (
    ForexExtractionResult, ExtractionRequest, 
    FileOperationResult, OutputFormat
)
from .config import config

EXTRACTED_DATA_DIR = config.files.DEFAULT_OUTPUT_DIR
os.makedirs(EXTRACTED_DATA_DIR, exist_ok=True)

class ForexDataExporter:
    """
    Dedicated class for exporting forex extraction results to various file formats.
    Handles CSV, JSON, and combined export operations.
    """
    
    def __init__(self, output_directory: str = EXTRACTED_DATA_DIR):
        """
        Initialize the exporter with a specified output directory.
        
        Args:
            output_directory (str): Directory where files will be saved
        """
        self.output_directory = output_directory
        os.makedirs(self.output_directory, exist_ok=True)
    
    async def export_result(
        self, 
        result: ForexExtractionResult, 
        request: ExtractionRequest
    ) -> List[FileOperationResult]:
        """
        Export extraction result to file(s) based on request format.
        
        Args:
            result (ForexExtractionResult): The extraction result to export
            request (ExtractionRequest): Original request with export specifications
            
        Returns:
            List[FileOperationResult]: Results of export operations
        """
        export_results = []
        
        if request.output_format == OutputFormat.CSV:
            export_result = await self._export_to_csv(result, request)
            export_results.append(export_result)
            
        elif request.output_format == OutputFormat.JSON:
            export_result = await self._export_to_json(result, request)
            export_results.append(export_result)
            
        elif request.output_format == OutputFormat.BOTH:
            csv_result = await self._export_to_csv(result, request)
            export_results.append(csv_result)
            
            json_request = request.model_copy(deep=True)
            if request.output_file:
                if request.output_file.endswith('.csv'):
                    json_request.output_file = request.output_file.replace('.csv', '.json')
                elif not request.output_file.endswith('.json'):
                    json_request.output_file = f"{request.output_file}.json"
            
            json_result = await self._export_to_json(result, json_request)
            export_results.append(json_result)

        return export_results
    
    async def _export_to_csv(
        self, 
        result: ForexExtractionResult, 
        request: ExtractionRequest
    ) -> FileOperationResult:
        """
        Export result to CSV file.
        
        Args:
            result (ForexExtractionResult): The extraction result to export
            request (ExtractionRequest): Original request with export specifications
            
        Returns:
            FileOperationResult: Result of the CSV export operation
        """
        try:
            filename = self._get_output_filename(request, 'csv')
            full_path = os.path.join(self.output_directory, os.path.basename(filename))
            
            file_exists = os.path.isfile(full_path) and request.append_to_file
            mode = 'a' if request.append_to_file else 'w'
            
            rows_written = 0
            
            with open(full_path, mode=mode, newline=config.files.CSV_NEWLINE) as file:
                writer = csv.writer(file)
                
                if not file_exists:
                    writer.writerow(config.files.CSV_HEADERS)
                    
                csv_rows = result.to_csv_rows()
                for row_data in csv_rows:
                    writer.writerow([row_data['date'], row_data['close']])
                    rows_written += 1
            
            file_size = os.path.getsize(full_path) if os.path.exists(full_path) else None
            
            return FileOperationResult(
                file_path=full_path,
                format_type=OutputFormat.CSV,
                rows_written=rows_written,
                success=True,
                file_size_bytes=file_size
            )
            
        except Exception as e:
            return FileOperationResult(
                file_path=full_path if 'full_path' in locals() else "unknown",
                format_type=OutputFormat.CSV,
                success=False,
                error_message=str(e)
            )
    
    async def _export_to_json(
        self, 
        result: ForexExtractionResult, 
        request: ExtractionRequest
    ) -> FileOperationResult:
        """
        Export result to JSON file.
        
        Args:
            result (ForexExtractionResult): The extraction result to export
            request (ExtractionRequest): Original request with export specifications
            
        Returns:
            FileOperationResult: Result of the JSON export operation
        """
        try:
            filename = self._get_output_filename(request, 'json')
            full_path = os.path.join(self.output_directory, os.path.basename(filename))
            
            json_data = result.to_json_structure()
            
            if request.append_to_file and os.path.isfile(full_path):
                try:
                    with open(full_path, 'r') as file:
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
            
            with open(full_path, 'w') as file:
                json.dump(json_data, file, 
                     indent=config.files.JSON_INDENT, 
                     ensure_ascii=config.files.JSON_ENSURE_ASCII)
            
            file_size = os.path.getsize(full_path) if os.path.exists(full_path) else 0
            file_size_mb = file_size / 1024
            rows_written = len(result.data_points)
            
            print(f"Number of datapoints collected is {rows_written} and occupies {file_size_mb:.2f} MB")
            
            return FileOperationResult(
                file_path=full_path,
                format_type=OutputFormat.JSON,
                rows_written=rows_written,
                success=True,
                file_size_bytes=file_size
            )
            
        except Exception as e:
            return FileOperationResult(
                file_path=full_path if 'full_path' in locals() else "unknown",
                format_type=OutputFormat.JSON,
                success=False,
                error_message=str(e)
            )
    
    def _get_output_filename(self, request: ExtractionRequest, extension: str) -> str:
        """
        Determine the output filename based on request parameters.
        
        Args:
            request (ExtractionRequest): Original request
            extension (str): File extension (csv or json)
            
        Returns:
            str: Complete filename with extension
        """
        if request.output_file:
            filename = request.output_file
            if not filename.endswith(f'.{extension}'):
                filename = f"{filename}.{extension}"
        else:
            base_name = config.files.DEFAULT_FILENAME_TEMPLATE.format(
                currency_pair=request.currency_pair
            )
            filename = request.get_default_filename(extension)
        
        return filename