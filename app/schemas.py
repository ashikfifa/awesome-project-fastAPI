from pydantic import BaseModel, Field, condecimal
from typing import Optional
from datetime import datetime


# ---------- CREATE / UPDATE INPUT ----------
class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    price: condecimal(max_digits=12, decimal_places=2) = Field(..., ge=0)
    in_stock: bool = True


class ProductUpdate(BaseModel):
    # All optional: partial updates supported
    sku: Optional[str] = Field(None, min_length=2, max_length=64)
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    price: Optional[condecimal(max_digits=12, decimal_places=2)] = Field(None, ge=0)
    in_stock: Optional[bool] = None


# ---------- OUTPUT ----------
class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    description: Optional[str]
    price: condecimal(max_digits=12, decimal_places=2)
    in_stock: bool
    created_at: datetime

    class Config:
        from_attributes = True  # for SQLAlchemy objects
