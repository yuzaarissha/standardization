from src.processors.main_processor import DataStandardizationService
from src.models.parser_models import TransactionExtractionConfig
import json

def main():
    extraction_config = TransactionExtractionConfig(
        extract_from_text=True,
        min_description_length=3
    )
    service = DataStandardizationService(extraction_config)
    
    health = service.get_health_check()
    print("=== СТАТУС СЕРВИСА СТАНДАРТИЗАЦИИ ===")
    print(json.dumps(health, indent=2, ensure_ascii=False))
    print()
    
    parser_output = [
        {
            "filename": "bank_statement.csv",
            "extracted_tables": [
                [
                    {
                        "transaction_date": "19.06.2025",
                        "description": "Оплата за хостинг PS.KZ ",
                        "debit": "15 000 тг",
                        "credit": None,
                        "currency": "KZT"
                    },
                    {
                        "transaction_date": "20.06.2025",
                        "description": "Получение зарплаты",
                        "debit": None,
                        "credit": "500000 ₸",
                        "currency": "KZT"
                    }
                ]
            ],
            "extracted_text": "",
            "error": None
        },
        {
            "filename": "receipt_scan.pdf",
            "extracted_tables": [],
            "extracted_text": """
            Чек No. 12345
            Дата: 21.06.2025
            Магазин: METRO Cash & Carry

            Покупка продуктов:
            Итого к оплате: 4600 тг
            Способ оплаты: Наличные
            """,
            "error": None
        },
        {
            "filename": "corrupted_file.xlsx",
            "extracted_tables": [],
            "extracted_text": "",
            "error": "Файл поврежден, не удается прочитать"
        },
        {
            "filename": "mixed_content.pdf",
            "extracted_tables": [
                [
                    {
                        "transaction_date": "22.06.2025",
                        "description": "Платеж поставщику",
                        "amount": "-75000",
                        "currency": "KZT"
                    }
                ]
            ],
            "extracted_text": """
            Дополнительные операции:
            23.06.2025 - Возврат товара 2500 тенге
            24.06.2025 - Комиссия банка 150 тг
            """,
            "error": None
        }
    ]
    
    print("=== ИСХОДНЫЕ ДАННЫЕ ОТ ДВИЖКА ПАРСИНГА ===")
    for i, file_data in enumerate(parser_output):
        print(f"Файл {i+1}: {file_data['filename']}")
        if file_data['error']:
            print(f"  Ошибка: {file_data['error']}")
        else:
            print(f"  Таблиц: {len(file_data['extracted_tables'])}")
            if file_data['extracted_tables']:
                total_rows = sum(len(table) for table in file_data['extracted_tables'])
                print(f"  Строк в таблицах: {total_rows}")
            print(f"  Текст: {len(file_data['extracted_text'])} символов")
        print()
    
    result = service.process_json_input(parser_output)
    
    print("=== ОБЩИЕ РЕЗУЛЬТАТЫ ОБРАБОТКИ ===")
    print(f"Всего файлов: {result.total_files}")
    print(f"Успешно обработано файлов: {result.successful_files}")
    print(f"Файлов с ошибками: {result.failed_files}")
    print(f"Всего транзакций: {result.total_transactions}")
    print(f"Успешно обработано транзакций: {result.successful_transactions}")
    print(f"Процент успеха по файлам: {result.processing_summary['file_success_rate']:.1f}%")
    print(f"Процент успеха по транзакциям: {result.processing_summary['transaction_success_rate']:.1f}%")
    print()
    
    print("=== ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ ПО ФАЙЛАМ ===")
    for file_result in result.file_results:
        print(f"Файл: {file_result.filename}")
        print(f"  Тип источника: {file_result.source_type}")
        if file_result.original_error:
            print(f"  Ошибка парсера: {file_result.original_error}")
        else:
            print(f"  Найдено транзакций: {file_result.processing_summary.get('total_transactions', 0)}")
            print(f"  Успешно обработано: {file_result.processing_summary.get('successful_count', 0)}")
            if file_result.successful_transactions:
                print("  Примеры транзакций:")
                for i, transaction in enumerate(file_result.successful_transactions[:2]):
                    print(f"    {i+1}. {transaction.description_clean} - {transaction.amount} {transaction.currency} ({transaction.transaction_type.value})")
        print()
    
    stats = service.get_processing_statistics(result)
    print("=== ДЕТАЛЬНАЯ СТАТИСТИКА ===")
    print("Распределение по типам источников:")
    for source_type, count in result.processing_summary['source_type_distribution'].items():
        print(f"  {source_type}: {count} файлов")
    
    print("\nРаспределение по типам транзакций:")
    for tx_type, count in stats['transaction_types_distribution'].items():
        print(f"  {tx_type}: {count}")
    
    print("\nРаспределение по валютам:")
    for currency, count in stats['currency_distribution'].items():
        print(f"  {currency}: {count}")
    
    if stats['quality_flags_distribution']:
        print("\nФлаги качества данных:")
        for flag, count in stats['quality_flags_distribution'].items():
            print(f"  {flag}: {count}")
    
    print(f"\nСреднее количество транзакций на файл: {stats['average_transactions_per_file']:.1f}")
    print(f"Файлов с извлечением из текста: {stats['files_with_text_extraction']}")
    print(f"Файлов с табличными данными: {stats['files_with_table_data']}")
    
    print("\n=== ВСЕ СТАНДАРТИЗИРОВАННЫЕ ТРАНЗАКЦИИ ===")
    transaction_counter = 1
    for file_result in result.file_results:
        if file_result.successful_transactions:
            print(f"\nИз файла: {file_result.filename}")
            for transaction in file_result.successful_transactions:
                print(f"{transaction_counter}. ID: {transaction.transaction_id}")
                print(f"   Дата: {transaction.transaction_date}")
                print(f"   Описание: '{transaction.description_clean}'")
                print(f"   Сумма: {transaction.amount} {transaction.currency}")
                print(f"   Тип: {transaction.transaction_type.value}")
                if transaction.data_quality_flags:
                    print(f"   Флаги качества: {', '.join(transaction.data_quality_flags)}")
                print()
                transaction_counter += 1
    
    print("=== ДЕМОНСТРАЦИЯ API ===")
    from src.api_interface import standardize_data
    simple_test = [
        {
            "filename": "test.csv",
            "extracted_tables": [
                [
                    {
                        "transaction_date": "25.06.2025",
                        "description": "Тестовая транзакция",
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
    
    api_result = standardize_data(simple_test)
    print("API результат:")
    print(f"Статус: {api_result['status']}")
    print(f"Транзакций обработано: {len(api_result['standardized_transactions'])}")
    if api_result['standardized_transactions']:
        tx = api_result['standardized_transactions'][0]
        print(f"Пример: {tx['description_clean']} - {tx['amount']} {tx['currency']}")

if __name__ == "__main__":
    main()
