import uuid
from typing import List, Dict, Any, Optional
from src.models.transaction_models import (
    RawTransactionInput, 
    StandardizedTransaction, 
    ProcessingResult,
    TransactionType
)
from src.models.parser_models import (
    ParsedFileResult, FileProcessingResult, 
    BatchProcessingResult, TransactionExtractionConfig
)
from src.processors.date_processor import DateProcessor
from src.processors.amount_processor import AmountProcessor
from src.processors.text_processor import TextProcessor
from src.processors.text_extractor import TextTransactionExtractor


class DataStandardizationService:
    def __init__(self, extraction_config: Optional[TransactionExtractionConfig] = None):
        self.date_processor = DateProcessor()
        self.amount_processor = AmountProcessor()
        self.text_processor = TextProcessor()
        self.text_extractor = TextTransactionExtractor(extraction_config)
    
    def process_transaction(self, raw_data: Dict[str, Any]) -> StandardizedTransaction:
        quality_flags = []
        try:
            raw_transaction = RawTransactionInput(**raw_data)
        except Exception as e:
            raise ValueError(f"Неверный формат входных данных: {e}")
        transaction_id = f"gen_uuid_{uuid.uuid4().hex[:8]}"
        standardized_date, date_flags = self.date_processor.standardize_date(
            raw_transaction.transaction_date
        )
        quality_flags.extend(date_flags)
        description_raw, description_clean, text_flags = self.text_processor.clean_description(
            raw_transaction.description
        )
        quality_flags.extend(text_flags)
        if raw_transaction.amount is not None:
            amount, transaction_type, amount_flags = self.amount_processor.process_single_amount_format(
                raw_transaction.amount
            )
        else:
            amount, transaction_type, amount_flags = self.amount_processor.process_debit_credit_format(
                raw_transaction.debit, raw_transaction.credit
            )
        quality_flags.extend(amount_flags)
        currency_source = raw_transaction.currency or str(raw_transaction.debit or raw_transaction.credit or raw_transaction.amount or "")
        currency, currency_flags = self.amount_processor.standardize_currency(
            raw_transaction.currency, currency_source
        )
        quality_flags.extend(currency_flags)
        standardized_transaction = StandardizedTransaction(
            transaction_id=transaction_id,
            transaction_date=standardized_date,
            description_raw=description_raw,
            description_clean=description_clean,
            amount=amount,
            currency=currency,
            transaction_type=TransactionType(transaction_type),
            source_account="Unknown",
            data_quality_flags=list(set(quality_flags))
        )
        return standardized_transaction
    
    def process_batch(self, raw_transactions: List[Dict[str, Any]]) -> ProcessingResult:
        successful_transactions = []
        failed_transactions = []
        for i, raw_data in enumerate(raw_transactions):
            try:
                standardized = self.process_transaction(raw_data)
                successful_transactions.append(standardized)
            except Exception as e:
                failed_transactions.append({
                    'index': i,
                    'original_data': raw_data,
                    'error': str(e),
                    'error_type': type(e).__name__
                })
        processing_summary = {
            'total_transactions': len(raw_transactions),
            'successful_count': len(successful_transactions),
            'failed_count': len(failed_transactions),
            'success_rate': len(successful_transactions) / len(raw_transactions) * 100 if raw_transactions else 0
        }
        return ProcessingResult(
            successful_transactions=successful_transactions,
            failed_transactions=failed_transactions,
            processing_summary=processing_summary
        )
    
    def process_parsed_file(self, parsed_file: ParsedFileResult) -> FileProcessingResult:
        if parsed_file.error:
            return FileProcessingResult(
                filename=parsed_file.filename,
                source_type="error",
                successful_transactions=[],
                failed_transactions=[],
                processing_summary={
                    'total_transactions': 0,
                    'successful_count': 0,
                    'failed_count': 0,
                    'success_rate': 0
                },
                original_error=parsed_file.error
            )
        all_raw_transactions = []
        source_type = "unknown"
        if parsed_file.extracted_tables:
            source_type = "table"
            for table in parsed_file.extracted_tables:
                all_raw_transactions.extend(table)
        if parsed_file.extracted_text:
            text_transactions = self.text_extractor.extract_transactions_from_text(
                parsed_file.extracted_text
            )
            if text_transactions:
                all_raw_transactions.extend(text_transactions)
                source_type = "text" if source_type == "unknown" else "mixed"
        if not all_raw_transactions:
            return FileProcessingResult(
                filename=parsed_file.filename,
                source_type=source_type,
                successful_transactions=[],
                failed_transactions=[],
                processing_summary={
                    'total_transactions': 0,
                    'successful_count': 0,
                    'failed_count': 0,
                    'success_rate': 0,
                    'warning': 'No transactions found in file'
                }
            )
        result = self.process_batch(all_raw_transactions)
        return FileProcessingResult(
            filename=parsed_file.filename,
            source_type=source_type,
            successful_transactions=result.successful_transactions,
            failed_transactions=result.failed_transactions,
            processing_summary=result.processing_summary
        )
    
    def process_parsed_batch(self, parsed_batch: List[ParsedFileResult]) -> BatchProcessingResult:
        file_results = []
        total_transactions = 0
        successful_transactions = 0
        successful_files = 0
        failed_files = 0
        for parsed_file in parsed_batch:
            file_result = self.process_parsed_file(parsed_file)
            file_results.append(file_result)
            file_total = file_result.processing_summary.get('total_transactions', 0)
            file_successful = file_result.processing_summary.get('successful_count', 0)
            total_transactions += file_total
            successful_transactions += file_successful
            if file_result.original_error:
                failed_files += 1
            else:
                successful_files += 1
        processing_summary = {
            'total_files': len(parsed_batch),
            'successful_files': successful_files,
            'failed_files': failed_files,
            'total_transactions': total_transactions,
            'successful_transactions': successful_transactions,
            'file_success_rate': (successful_files / len(parsed_batch) * 100) if parsed_batch else 0,
            'transaction_success_rate': (successful_transactions / total_transactions * 100) if total_transactions else 0,
            'source_type_distribution': self._get_source_type_distribution(file_results)
        }
        return BatchProcessingResult(
            total_files=len(parsed_batch),
            successful_files=successful_files,
            failed_files=failed_files,
            total_transactions=total_transactions,
            successful_transactions=successful_transactions,
            file_results=file_results,
            processing_summary=processing_summary
        )
    
    def process_json_input(self, json_data: List[Dict[str, Any]]) -> BatchProcessingResult:
        parsed_files = []
        for file_data in json_data:
            try:
                parsed_file = ParsedFileResult(**file_data)
                parsed_files.append(parsed_file)
            except Exception as e:
                parsed_files.append(ParsedFileResult(
                    filename=file_data.get('filename', 'unknown'),
                    extracted_tables=[],
                    extracted_text="",
                    error=f"Invalid input format: {e}"
                ))
        return self.process_parsed_batch(parsed_files)
    
    def _get_source_type_distribution(self, file_results: List[FileProcessingResult]) -> Dict[str, int]:
        distribution = {}
        for result in file_results:
            source_type = result.source_type
            distribution[source_type] = distribution.get(source_type, 0) + 1
        return distribution
    
    def get_processing_statistics(self, batch_result: BatchProcessingResult) -> Dict[str, Any]:
        quality_flags_distribution = {}
        transaction_types_distribution = {'DEBIT': 0, 'CREDIT': 0}
        currency_distribution = {}
        for file_result in batch_result.file_results:
            for transaction in file_result.successful_transactions:
                for flag in transaction.data_quality_flags:
                    quality_flags_distribution[flag] = quality_flags_distribution.get(flag, 0) + 1
                transaction_types_distribution[transaction.transaction_type.value] += 1
                currency = transaction.currency
                currency_distribution[currency] = currency_distribution.get(currency, 0) + 1
        return {
            'quality_flags_distribution': quality_flags_distribution,
            'transaction_types_distribution': transaction_types_distribution,
            'currency_distribution': currency_distribution,
            'average_transactions_per_file': (
                batch_result.total_transactions / batch_result.total_files 
                if batch_result.total_files > 0 else 0
            ),
            'files_with_text_extraction': sum(
                1 for result in batch_result.file_results 
                if result.source_type in ['text', 'mixed']
            ),
            'files_with_table_data': sum(
                1 for result in batch_result.file_results 
                if result.source_type in ['table', 'mixed']
            )
        }
    
    def get_health_check(self) -> Dict[str, Any]:
        return {
            'status': 'healthy',
            'version': '1.0.0',
            'processors': {
                'date_processor': 'ready',
                'amount_processor': 'ready',
                'text_processor': 'ready'
            }
        }
