from typing import List, Dict, Any
from src.processors.main_processor import DataStandardizationService
from src.models.parser_models import TransactionExtractionConfig


class DataStandardizationAPI:
    def __init__(self, extraction_config: TransactionExtractionConfig = None):
        self.service = DataStandardizationService(extraction_config)
    
    def process_parser_output(self, parser_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            result = self.service.process_json_input(parser_data)
            response = {
                "status": "success",
                "summary": {
                    "total_files": result.total_files,
                    "successful_files": result.successful_files,
                    "failed_files": result.failed_files,
                    "total_transactions": result.total_transactions,
                    "successful_transactions": result.successful_transactions,
                    "processing_summary": result.processing_summary
                },
                "file_results": [],
                "standardized_transactions": []
            }
            for file_result in result.file_results:
                file_data = {
                    "filename": file_result.filename,
                    "source_type": file_result.source_type,
                    "transaction_count": len(file_result.successful_transactions),
                    "failed_count": len(file_result.failed_transactions),
                    "original_error": file_result.original_error,
                    "processing_summary": file_result.processing_summary
                }
                response["file_results"].append(file_data)
            for file_result in result.file_results:
                for transaction in file_result.successful_transactions:
                    transaction_data = {
                        "source_file": file_result.filename,
                        "transaction_id": transaction.transaction_id,
                        "transaction_date": transaction.transaction_date,
                        "description_raw": transaction.description_raw,
                        "description_clean": transaction.description_clean,
                        "amount": transaction.amount,
                        "currency": transaction.currency,
                        "transaction_type": transaction.transaction_type.value,
                        "source_account": transaction.source_account,
                        "data_quality_flags": transaction.data_quality_flags
                    }
                    response["standardized_transactions"].append(transaction_data)
            return response
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e),
                "error_type": type(e).__name__
            }
    
    def process_single_file(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.process_parser_output([file_data])
    
    def health_check(self) -> Dict[str, Any]:
        try:
            health = self.service.get_health_check()
            return {
                "status": "healthy",
                "service_info": health,
                "capabilities": {
                    "text_extraction": True,
                    "table_processing": True,
                    "multi_file_batch": True,
                    "quality_control": True
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_supported_formats(self) -> Dict[str, Any]:
        return {
            "input_formats": {
                "date_formats": [
                    "DD.MM.YYYY", "DD/MM/YYYY", "YYYY-MM-DD",
                    "DD.MM.YY", "DD месяц YYYY"
                ],
                "currency_symbols": {
                    "KZT": ["₸", "тг", "тенге"],
                    "USD": ["$", "доллар"],
                    "EUR": ["€", "евро"],
                    "RUB": ["₽", "руб", "рубль"]
                },
                "amount_formats": [
                    "15 000 тг", "1,500.50", "1.500,50", "-25000"
                ]
            },
            "output_format": {
                "transaction_id": "UUID string",
                "transaction_date": "ISO 8601 UTC",
                "description_clean": "normalized lowercase",
                "amount": "positive float",
                "currency": "ISO 4217 3-letter code",
                "transaction_type": "DEBIT or CREDIT"
            }
        }


def standardize_data(parser_output: List[Dict[str, Any]], 
                    config: TransactionExtractionConfig = None) -> Dict[str, Any]:
    api = DataStandardizationAPI(config)
    return api.process_parser_output(parser_output)


if __name__ == "__main__":
    sample_data = [
        {
            "filename": "test.csv",
            "extracted_tables": [
                [
                    {
                        "transaction_date": "19.06.2025",
                        "description": "Тест",
                        "debit": "1000 тг",
                        "credit": None,
                        "currency": "KZT"
                    }
                ]
            ],
            "extracted_text": "",
            "error": None
        }
    ]
    result = standardize_data(sample_data)
    print("API результат:")
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
