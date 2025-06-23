from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ParsedFileResult(BaseModel):
    filename: str = Field(...)
    extracted_tables: List[List[Dict[str, Any]]] = Field(default_factory=list)
    extracted_text: str = Field(default="")
    error: Optional[str] = Field(None)


class ParsedBatchResult(BaseModel):
    results: List[ParsedFileResult] = Field(...)


class FileProcessingResult(BaseModel):
    filename: str = Field(...)
    source_type: str = Field(...)
    successful_transactions: List = Field(default_factory=list)
    failed_transactions: List[Dict[str, Any]] = Field(default_factory=list)
    processing_summary: Dict[str, Any] = Field(default_factory=dict)
    original_error: Optional[str] = Field(None)


class BatchProcessingResult(BaseModel):
    total_files: int = Field(...)
    successful_files: int = Field(...)
    failed_files: int = Field(...)
    total_transactions: int = Field(...)
    successful_transactions: int = Field(...)
    file_results: List[FileProcessingResult] = Field(...)
    processing_summary: Dict[str, Any] = Field(default_factory=dict)


class TransactionExtractionConfig(BaseModel):
    date_keywords: List[str] = Field(default_factory=lambda: [
        "дата", "date", "число", "когда", "время"
    ])
    amount_keywords: List[str] = Field(default_factory=lambda: [
        "сумма", "amount", "деньги", "тенге", "рубль", "доллар", "евро",
        "оплата", "платеж", "перевод", "покупка", "расход", "доход"
    ])
    description_keywords: List[str] = Field(default_factory=lambda: [
        "описание", "комментарий", "назначение", "за что", "детали",
        "магазин", "услуга", "товар", "покупка"
    ])
    min_description_length: int = Field(default=3)
    extract_from_text: bool = Field(default=True)
