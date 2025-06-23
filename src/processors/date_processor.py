from datetime import datetime
from dateutil import parser as date_parser
from typing import Tuple, List
from src.utils.constants import DATE_FORMATS


class DateProcessor:
    def __init__(self):
        self.date_formats = DATE_FORMATS

    def standardize_date(self, date_str: str) -> Tuple[str, List[str]]:
        quality_flags = []

        if not date_str or not isinstance(date_str, str):
            quality_flags.append('original_date_ambiguous')
            return datetime.now().strftime('%Y-%m-%dT00:00:00Z'), quality_flags

        date_str = date_str.strip()

        for date_format in self.date_formats:
            try:
                parsed_date = datetime.strptime(date_str, date_format)
                return parsed_date.strftime('%Y-%m-%dT00:00:00Z'), quality_flags
            except ValueError:
                continue

        try:
            parsed_date = date_parser.parse(date_str, dayfirst=True)
            if parsed_date.year < 100:
                quality_flags.append('original_date_ambiguous')
            return parsed_date.strftime('%Y-%m-%dT00:00:00Z'), quality_flags
        except (ValueError, TypeError):
            quality_flags.append('original_date_ambiguous')
            return datetime.now().strftime('%Y-%m-%dT00:00:00Z'), quality_flags

    def validate_date(self, date_str: str) -> bool:
        try:
            _, flags = self.standardize_date(date_str)
            return 'original_date_ambiguous' not in flags
        except Exception:
            return False
