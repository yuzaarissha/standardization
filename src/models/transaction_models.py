from typing import Optional, List, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TransactionType(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class RawTransactionInput(BaseModel):
    transaction_date: str
    description: str
    debit: Optional[Union[str, float]] = None
    credit: Optional[Union[str, float]] = None
    amount: Optional[Union[str, float]] = None
    currency: Optional[str] = None


class StandardizedTransaction(BaseModel):
    transaction_id: str = Field(...)
    transaction_date: str = Field(...)
    description_raw: str = Field(...)
    description_clean: str = Field(...)
    amount: float = Field(...)
    currency: str = Field(...)
    transaction_type: TransactionType = Field(...)
    source_account: str = Field(default="Unknown")
    data_quality_flags: List[str] = Field(default_factory=list)


class ProcessingResult(BaseModel):
    successful_transactions: List[StandardizedTransaction]
    failed_transactions: List[dict]
    processing_summary: dict
