## Возможности извлечения из текста

Сервис автоматически извлекает транзакции из неструктурированного текста:

**Поддерживаемые паттерны:**
- Даты: `19.06.2025`, `2025-06-19`, `19 июня 2025`
- Суммы: `15 000 тг`, `1,500.50`, `-25000`
- Типы: автоматическое определение по ключевым словам

**Пример извлечения:**
```
Входной текст:
"21.06.2025 Покупка в магазине METRO 4600 тг"

Извлеченная транзакция:
{
  "transaction_date": "21.06.2025",
  "description": "Покупка в магазине METRO",
  "debit": "4600 тг",
  "currency": "KZT"
}
```# Сервис стандартизации и очистки данных

Микросервис для стандартизации и очистки данных транзакций в рамках бэкенд-конвейера обработки данных.

## Описание

Этот сервис принимает результаты работы движка парсинга и OCR в формате JSON, извлекает транзакции из табличных данных и неструктурированного текста, и преобразует каждую запись в стандартизированную "золотую запись" для последующего AI-анализа.

## Основные возможности

- **Обработка выхода парсера**: Работа с JSON от движка парсинга (таблицы + текст)
- **Извлечение из текста**: Автоматическое извлечение транзакций из неструктурированного текста
- **Стандартизация дат**: Распознавание множественных форматов дат и преобразование в ISO 8601
- **Очистка сумм**: Удаление нечисловых символов и стандартизация в float
- **Стандартизация валют**: Преобразование в 3-буквенные коды ISO 4217
- **Очистка текста**: Нормализация описаний транзакций
- **Унификация типов**: Стандартизация DEBIT/CREDIT транзакций
- **Контроль качества**: Флаги для отслеживания проблем в данных
- **Пакетная обработка**: Обработка множества файлов в одном запросе

## Структура проекта

```
data-standardization-service/
├── .gitignore                  
├── requirements.txt           
├── README.md
├── main.py                    # Демонстрационный скрипт
├── venv/                      
├── src/                       
│   ├── __init__.py
│   ├── api_interface.py           # API интерфейс
│   ├── models/                
│   │   ├── __init__.py
│   │   ├── transaction_models.py  # Модели транзакций
│   │   └── parser_models.py       # Модели для парсера
│   ├── processors/            
│   │   ├── __init__.py
│   │   ├── date_processor.py      # Обработка дат
│   │   ├── amount_processor.py    # Обработка сумм и валют
│   │   ├── text_processor.py      # Очистка текста
│   │   ├── text_extractor.py      # Извлечение из текста
│   │   └── main_processor.py      # Основной координатор
│   └── utils/                 
│       ├── __init__.py
│       └── constants.py           # Константы и маппинги
└── tests/                     
    ├── __init__.py
    └── test_basic.py              # Базовые тесты
```

## Установка и запуск

1. **Создание виртуального окружения:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

2. **Установка зависимостей:**
```bash
pip install -r requirements.txt
```

3. **Запуск демонстрации:**
```bash
python main.py
```

4. **Запуск тестов:**
```bash
python -m pytest tests/
# или
python -m unittest tests.test_basic
```

## Использование

### Работа с выходом движка парсинга (основной режим)

```python
from src.processors.main_processor import DataStandardizationService
from src.api_interface import standardize_data

# Пример данных от движка парсинга
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
                }
            ]
        ],
        "extracted_text": "",
        "error": None
    },
    {
        "filename": "receipt.pdf",
        "extracted_tables": [],
        "extracted_text": "21.06.2025 Покупка в магазине 4600 тг",
        "error": None
    }
]

# Обработка через простой API
result = standardize_data(parser_output)

# Или через сервис напрямую
service = DataStandardizationService()
result = service.process_json_input(parser_output)
```

### Прямая обработка транзакций

```python
from src.processors.main_processor import DataStandardizationService

# Создание сервиса
service = DataStandardizationService()

# Обработка одной транзакции
raw_data = {
    "transaction_date": "19.06.2025",
    "description": "Оплата за хостинг PS.KZ ",
    "debit": "15 000 тг",
    "credit": None,
    "currency": "KZT"
}

standardized = service.process_transaction(raw_data)

# Обработка батча транзакций
raw_transactions = [raw_data1, raw_data2, ...]
result = service.process_batch(raw_transactions)
```_transactions)
```

### Входные данные

**Формат движка парсинга (основной):**
```json
[
  {
    "filename": "file.csv",
    "extracted_tables": [
      [
        {
          "transaction_date": "19.06.2025",
          "description": "Описание",
          "debit": "15 000 тг",
          "credit": null,
          "currency": "KZT"
        }
      ]
    ],
    "extracted_text": "дополнительный текст",
    "error": null
  }
]
```

**Прямой формат транзакций:**
- `transaction_date` (str): Дата в различных форматах
- `description` (str): Описание транзакции
- `debit` (str/float, optional): Сумма дебета
- `credit` (str/float, optional): Сумма кредита
- `amount` (str/float, optional): Сумма (альтернативный формат)
- `currency` (str, optional): Валюта

### Выходные данные

**Результат обработки батча:**
```json
{
  "status": "success",
  "summary": {
    "total_files": 2,
    "successful_files": 2,
    "total_transactions": 3,
    "successful_transactions": 3
  },
  "standardized_transactions": [
    {
      "source_file": "file.csv",
      "transaction_id": "gen_uuid_12345",
      "transaction_date": "2025-06-19T00:00:00Z",
      "description_raw": "Оплата за хостинг PS.KZ ",
      "description_clean": "оплата за хостинг ps.kz",
      "amount": 15000.0,
      "currency": "KZT",
      "transaction_type": "DEBIT",
      "source_account": "Unknown",
      "data_quality_flags": []
    }
  ]
}
```

**Стандартизированная "золотая запись":**
- `transaction_id` (str): Уникальный UUID
- `transaction_date` (str): Дата в ISO 8601 UTC
- `description_raw` (str): Оригинальное описание
- `description_clean` (str): Очищенное описание
- `amount` (float): Стандартизированная сумма
- `currency` (str): 3-буквенный код валюты ISO 4217
- `transaction_type` (str): DEBIT или CREDIT
- `source_account` (str): Исходный счет (по умолчанию "Unknown")
- `data_quality_flags` (list): Флаги проблем качества данных

## Поддерживаемые форматы

### Даты
- `DD.MM.YYYY` (19.06.2025)
- `DD/MM/YYYY` (19/06/2025)  
- `YYYY-MM-DD` (2025-06-19)
- `DD.MM.YY` (19.06.25)
- И другие через dateutil

### Валюты
- `₸`, `тг`, `тенге` → KZT
- `$`, `доллар` → USD
- `€`, `евро` → EUR
- `₽`, `руб`, `рубль` → RUB

### Суммы
- `15 000 тг` → 15000.0
- `1,500.50` → 1500.5
- `1.500,50` → 1500.5
- `-25000` → 25000.0 (с типом DEBIT)

## Контроль качества

Система флагов качества данных:
- `original_date_ambiguous`: Неоднозначная дата
- `amount_format_unclear`: Неясный формат суммы
- `currency_assumed`: Валюта определена автоматически
- `description_contains_special_chars`: Спецсимволы в описании
- `missing_required_field`: Отсутствует обязательное поле

## Разработка

### Добавление новых процессоров
1. Создайте новый файл в `src/processors/`
2. Реализуйте класс с методами обработки
3. Интегрируйте в `enhanced_main_processor.py`
4. Добавьте тесты в `tests/`

### Расширение извлечения из текста
1. Обновите паттерны в `text_extractor.py`
2. Добавьте новые ключевые слова в `TransactionExtractionConfig`
3. Протестируйте на реальных данных

### Расширение форматов
1. Добавьте новые константы в `src/utils/constants.py`
2. Обновите соответствующие процессоры
3. Добавьте тесты для новых форматов

## Технологический стек

- **Python 3.9+**
- **pandas**: Обработка данных
- **python-dateutil**: Парсинг дат
- **pydantic**: Валидация данных
- **uuid**: Генерация уникальных ID
