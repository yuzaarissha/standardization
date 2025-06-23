import re
from typing import List, Dict, Any, Optional
from src.models.parser_models import TransactionExtractionConfig
from src.utils.constants import CURRENCY_MAPPING


class TextTransactionExtractor:
    def __init__(self, config: Optional[TransactionExtractionConfig] = None):
        self.config = config or TransactionExtractionConfig()
        self.date_patterns = [
            r'\b\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}\b',
            r'\b\d{4}[./\-]\d{1,2}[./\-]\d{1,2}\b',
            r'\b\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{4}\b'
        ]
        self.amount_patterns = [
            r'\b\d{1,3}(?:\s?\d{3})*(?:[.,]\d{1,2})?\s*(?:₸|тг|тенге|KZT|USD|EUR|RUB|\$|€|₽|руб)\b',
            r'\b\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d{1,2})?\b'
        ]
        self.debit_keywords = [
            'оплата', 'покупка', 'расход', 'списание', 'перевод', 'платеж',
            'оплачено', 'потрачено', 'снято', 'дебет', 'трата'
        ]
        self.credit_keywords = [
            'поступление', 'доход', 'зачисление', 'получено', 'кредит',
            'зарплата', 'возврат', 'пополнение', 'приход'
        ]

    def extract_transactions_from_text(self, text: str) -> List[Dict[str, Any]]:
        if not text or not self.config.extract_from_text:
            return []
        transactions = []
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            dates = self._extract_dates(line)
            amounts = self._extract_amounts(line)
            if dates and amounts:
                transaction = self._build_transaction_from_line(line, dates[0], amounts[0])
                if transaction:
                    transactions.append(transaction)
            elif dates:
                context_lines = self._get_context_lines(lines, i, 2)
                context_amounts = self._extract_amounts(' '.join(context_lines))
                if context_amounts:
                    transaction = self._build_transaction_from_context(context_lines, dates[0], context_amounts[0])
                    if transaction:
                        transactions.append(transaction)
        return self._deduplicate_transactions(transactions)

    def _extract_dates(self, text: str) -> List[str]:
        dates = []
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        return dates

    def _extract_amounts(self, text: str) -> List[str]:
        amounts = []
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend(matches)
        return amounts

    def _build_transaction_from_line(self, line: str, date: str, amount: str) -> Optional[Dict[str, Any]]:
        transaction_type = self._determine_transaction_type(line)
        description = self._extract_description(line, date, amount)
        currency = self._extract_currency_from_amount(amount)
        return {
            'transaction_date': date,
            'description': description,
            'amount': amount if transaction_type == 'CREDIT' else None,
            'debit': amount if transaction_type == 'DEBIT' else None,
            'credit': amount if transaction_type == 'CREDIT' else None,
            'currency': currency
        }

    def _build_transaction_from_context(self, context_lines: List[str], date: str, amount: str) -> Optional[Dict[str, Any]]:
        full_context = ' '.join(context_lines)
        transaction_type = self._determine_transaction_type(full_context)
        description = self._extract_description(full_context, date, amount)
        currency = self._extract_currency_from_amount(amount)
        return {
            'transaction_date': date,
            'description': description,
            'amount': amount if transaction_type == 'CREDIT' else None,
            'debit': amount if transaction_type == 'DEBIT' else None,
            'credit': amount if transaction_type == 'CREDIT' else None,
            'currency': currency
        }

    def _determine_transaction_type(self, text: str) -> str:
        text_lower = text.lower()
        debit_score = sum(1 for keyword in self.debit_keywords if keyword in text_lower)
        credit_score = sum(1 for keyword in self.credit_keywords if keyword in text_lower)
        if '-' in text or 'минус' in text_lower:
            debit_score += 2
        return 'DEBIT' if debit_score >= credit_score else 'CREDIT'

    def _extract_description(self, text: str, date: str, amount: str) -> str:
        description = text
        for date_pattern in self.date_patterns:
            description = re.sub(date_pattern, '', description, flags=re.IGNORECASE)
        for amount_pattern in self.amount_patterns:
            description = re.sub(amount_pattern, '', description, flags=re.IGNORECASE)
        description = re.sub(r'\s+', ' ', description).strip()
        return text if len(description) < self.config.min_description_length else description

    def _extract_currency_from_amount(self, amount: str) -> Optional[str]:
        amount_lower = amount.lower()
        for symbol, currency in CURRENCY_MAPPING.items():
            if symbol in amount_lower:
                return currency
        currency_codes = ['KZT', 'USD', 'EUR', 'RUB']
        for code in currency_codes:
            if code.lower() in amount_lower or code in amount:
                return code
        return None

    def _get_context_lines(self, lines: List[str], index: int, radius: int) -> List[str]:
        start = max(0, index - radius)
        end = min(len(lines), index + radius + 1)
        return lines[start:end]

    def _deduplicate_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        unique_transactions = []
        for transaction in transactions:
            key = (
                transaction.get('transaction_date', ''),
                transaction.get('description', ''),
                transaction.get('amount', '') or transaction.get('debit', '') or transaction.get('credit', '')
            )
            if key not in seen:
                seen.add(key)
                unique_transactions.append(transaction)
        return unique_transactions
