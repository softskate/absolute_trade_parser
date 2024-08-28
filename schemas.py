from pydantic import BaseModel, ConfigDict
from typing import Optional


class ProductSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    productId: str
    name: str
    price: int
    qty: int
    category: str
    image: str
    brandName: Optional[str] = None


class ProductDetailsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    productId: str
    imageUrls: list
    details: Optional[dict] = None
    description: str
    name: str
    price: int
    qty: int
    category: str
    brandName: Optional[str] = None
