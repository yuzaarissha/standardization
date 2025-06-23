DATE_FORMATS = [
    '%d.%m.%Y',
    '%d/%m/%Y',
    '%d-%m-%Y',
    '%Y-%m-%d',
    '%d.%m.%y',
    '%d/%m/%y',
    '%d-%m-%y',
]

CURRENCY_MAPPING = {
    '₸': 'KZT',
    'тг': 'KZT',
    'тенге': 'KZT',
    '$': 'USD',
    'доллар': 'USD',
    '€': 'EUR',
    'евро': 'EUR',
    '₽': 'RUB',
    'руб': 'RUB',
    'рубль': 'RUB',
    'kzt': 'KZT',
    'usd': 'USD',
    'eur': 'EUR',
    'rub': 'RUB',
}

SUPPORTED_CURRENCIES = ['KZT', 'USD', 'EUR', 'RUB']

NUMERIC_CLEANUP_CHARS = [' ', ',', '₸', 'тг', '$', '€', '₽', 'руб']

TRANSACTION_TYPES = ['DEBIT', 'CREDIT']

DATA_QUALITY_FLAGS = [
    'original_date_ambiguous',
    'amount_format_unclear',
    'currency_assumed',
    'description_contains_special_chars',
    'missing_required_field'
]
