import re
from typing import Tuple, List, Union, Optional
from src.utils.constants import CURRENCY_MAPPING, SUPPORTED_CURRENCIES, NUMERIC_CLEANUP_CHARS


class AmountProcessor:
    def __init__(self):
        self.currency_mapping = CURRENCY_MAPPING
        self.supported_currencies = SUPPORTED_CURRENCIES
        self.cleanup_chars = NUMERIC_CLEANUP_CHARS

    def clean_amount(self, amount_str: Union[str, float, int]) -> Tuple[float, List[str]]:
        quality_flags = []

        if isinstance(amount_str, (int, float)):
            return float(amount_str), quality_flags

        if not amount_str or amount_str in ['', 'null', 'None']:
            return 0.0, ['missing_required_field']

        amount_str = str(amount_str).strip()
        is_negative = amount_str.startswith('-')
        cleaned = re.sub(r'[^\d.,\-]', '', amount_str)

        if ',' in cleaned and '.' in cleaned:
            if cleaned.rfind(',') > cleaned.rfind('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            comma_parts = cleaned.split(',')
            if len(comma_parts) == 2 and len(comma_parts[1]) <= 2:
                cleaned = cleaned.replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')

        cleaned = re.sub(r'-+', '-', cleaned)

        try:
            amount = float(cleaned)
            if is_negative and amount > 0:
                amount = -amount
            return abs(amount), quality_flags
        except (ValueError, TypeError):
            quality_flags.append('amount_format_unclear')
            return 0.0, quality_flags

    def standardize_currency(self, currency_str: Optional[str], amount_str: str = "") -> Tuple[str, List[str]]:
        quality_flags = []

        if currency_str:
            currency_clean = currency_str.strip().lower()
            if currency_clean in self.currency_mapping:
                return self.currency_mapping[currency_clean], quality_flags
            elif currency_clean.upper() in self.supported_currencies:
                return currency_clean.upper(), quality_flags

        if amount_str:
            amount_lower = str(amount_str).lower()
            for symbol, code in self.currency_mapping.items():
                if symbol in amount_lower:
                    if not currency_str:
                        quality_flags.append('currency_assumed')
                    return code, quality_flags

        quality_flags.append('currency_assumed')
        return 'KZT', quality_flags

    def process_debit_credit_format(self, debit: Union[str, float, None], credit: Union[str, float, None]) -> Tuple[float, str, List[str]]:
        quality_flags = []

        if debit and (not credit or credit == 0):
            amount, amount_flags = self.clean_amount(debit)
            quality_flags.extend(amount_flags)
            return amount, 'DEBIT', quality_flags
        elif credit and (not debit or debit == 0):
            amount, amount_flags = self.clean_amount(credit)
            quality_flags.extend(amount_flags)
            return amount, 'CREDIT', quality_flags
        elif debit and credit:
            debit_amount, _ = self.clean_amount(debit)
            credit_amount, _ = self.clean_amount(credit)
            if debit_amount >= credit_amount:
                return debit_amount, 'DEBIT', quality_flags
            else:
                return credit_amount, 'CREDIT', quality_flags
        else:
            quality_flags.append('missing_required_field')
            return 0.0, 'DEBIT', quality_flags

    def process_single_amount_format(self, amount: Union[str, float]) -> Tuple[float, str, List[str]]:
        quality_flags = []

        if not amount:
            quality_flags.append('missing_required_field')
            return 0.0, 'DEBIT', quality_flags

        is_negative = str(amount).strip().startswith('-')
        cleaned_amount, amount_flags = self.clean_amount(amount)
        quality_flags.extend(amount_flags)

        transaction_type = 'DEBIT' if is_negative else 'CREDIT'

        return cleaned_amount, transaction_type, quality_flags
