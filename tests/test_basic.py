import unittest
from src.processors.main_processor import DataStandardizationService
from src.processors.date_processor import DateProcessor
from src.processors.amount_processor import AmountProcessor
from src.processors.text_processor import TextProcessor


class TestDateProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = DateProcessor()
    
    def test_standard_date_formats(self):
        test_cases = [
            ("19.06.2025", "2025-06-19T00:00:00Z"),
            ("2025-06-19", "2025-06-19T00:00:00Z"),
            ("19/06/2025", "2025-06-19T00:00:00Z"),
            ("19.06.25", "2025-06-19T00:00:00Z"),
        ]
        for input_date, expected in test_cases:
            with self.subTest(input_date=input_date):
                result, flags = self.processor.standardize_date(input_date)
                self.assertEqual(result, expected)
                self.assertEqual(flags, [])
    
    def test_invalid_dates(self):
        invalid_dates = ["invalid_date", "", None, "32.13.2025"]
        for invalid_date in invalid_dates:
            with self.subTest(invalid_date=invalid_date):
                result, flags = self.processor.standardize_date(invalid_date)
                self.assertIn('original_date_ambiguous', flags)


class TestAmountProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = AmountProcessor()
    
    def test_clean_amount(self):
        test_cases = [
            ("15 000 тг", 15000.0),
            ("500000 ₸", 500000.0),
            ("-25000", 25000.0),
            ("1,500.50", 1500.50),
            ("1.500,50", 1500.50),
        ]
        for input_amount, expected in test_cases:
            with self.subTest(input_amount=input_amount):
                result, flags = self.processor.clean_amount(input_amount)
                self.assertEqual(result, expected)
    
    def test_currency_standardization(self):
        test_cases = [
            ("KZT", "KZT"),
            ("₸", "KZT"),
            ("тг", "KZT"),
            ("$", "USD"),
            ("usd", "USD"),
        ]
        for input_currency, expected in test_cases:
            with self.subTest(input_currency=input_currency):
                result, flags = self.processor.standardize_currency(input_currency)
                self.assertEqual(result, expected)
    
    def test_debit_credit_format(self):
        amount, tx_type, flags = self.processor.process_debit_credit_format("15000", None)
        self.assertEqual(amount, 15000.0)
        self.assertEqual(tx_type, 'DEBIT')
        amount, tx_type, flags = self.processor.process_debit_credit_format(None, "25000")
        self.assertEqual(amount, 25000.0)
        self.assertEqual(tx_type, 'CREDIT')


class TestTextProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = TextProcessor()
    
    def test_clean_description(self):
        test_cases = [
            ("Оплата за хостинг PS.KZ ", "Оплата за хостинг PS.KZ", "оплата за хостинг ps.kz"),
            ("  Покупка в магазине  ", "Покупка в магазине", "покупка в магазине"),
            ("Тест\tс\nсимволами", "Тест с символами", "тест с символами"),
        ]
        for input_desc, expected_raw, expected_clean in test_cases:
            with self.subTest(input_desc=input_desc):
                raw, clean, flags = self.processor.clean_description(input_desc)
                self.assertEqual(clean, expected_clean)


class TestDataStandardizationService(unittest.TestCase):
    def setUp(self):
        self.service = DataStandardizationService()
    
    def test_process_transaction_example_from_tz(self):
        raw_data = {
            "transaction_date": "19.06.2025",
            "description": "Оплата за хостинг PS.KZ ",
            "debit": "15 000 тг",
            "credit": None,
            "currency": "KZT"
        }
        result = self.service.process_transaction(raw_data)
        self.assertEqual(result.transaction_date, "2025-06-19T00:00:00Z")
        self.assertEqual(result.description_raw, "Оплата за хостинг PS.KZ ")
        self.assertEqual(result.description_clean, "оплата за хостинг ps.kz")
        self.assertEqual(result.amount, 15000.0)
        self.assertEqual(result.currency, "KZT")
        self.assertEqual(result.transaction_type.value, "DEBIT")
        self.assertEqual(result.source_account, "Unknown")
        self.assertTrue(result.transaction_id.startswith("gen_uuid_"))
    
    def test_process_batch(self):
        raw_transactions = [
            {
                "transaction_date": "19.06.2025",
                "description": "Тест 1",
                "debit": "1000",
                "credit": None,
                "currency": "KZT"
            },
            {
                "transaction_date": "20.06.2025",
                "description": "Тест 2",
                "debit": "2000",
                "credit": None,
                "currency": "KZT"
            }
        ]
        result = self.service.process_batch(raw_transactions)
        self.assertEqual(len(result.successful_transactions), 2)
        self.assertEqual(result.processing_summary['total_transactions'], 2)
        self.assertEqual(result.processing_summary['successful_count'], 2)
    
    def test_process_batch_with_errors(self):
        raw_transactions = [
            {
                "transaction_date": "19.06.2025",
                "description": "Успешная транзакция",
                "debit": "1000",
                "credit": None,
                "currency": "KZT"
            },
            {
                "transaction_date": "invalid_date",
                "description": "",
                "debit": "invalid_amount",
                "credit": None,
                "currency": "KZT"
            }
        ]
        result = self.service.process_batch(raw_transactions)
        self.assertEqual(result.processing_summary['total_transactions'], 2)
        self.assertGreaterEqual(len(result.successful_transactions), 1)
    
    def test_process_json_input(self):
        parser_data = [
            {
                "filename": "test.csv",
                "extracted_tables": [
                    [
                        {
                            "transaction_date": "19.06.2025",
                            "description": "Тест транзакция",
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
        result = self.service.process_json_input(parser_data)
        self.assertEqual(result.total_files, 1)
        self.assertEqual(result.successful_files, 1)
        self.assertEqual(len(result.file_results), 1)
        file_result = result.file_results[0]
        self.assertEqual(file_result.filename, "test.csv")
        self.assertEqual(file_result.source_type, "table")
        self.assertEqual(len(file_result.successful_transactions), 1)
    
    def test_health_check(self):
        health = self.service.get_health_check()
        self.assertEqual(health['status'], 'healthy')
        self.assertIn('processors', health)
        self.assertEqual(health['processors']['date_processor'], 'ready')


if __name__ == '__main__':
    unittest.main()
