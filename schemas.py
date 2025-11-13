"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal

# Core domain schemas for this app

class ButcherItem(BaseModel):
    title: str = Field(..., description="Cut name, e.g., Ribeye, Lamb Chops")
    description: Optional[str] = Field(None, description="Short description")
    price_per_kg: float = Field(..., ge=0, description="Price per kilogram in local currency")
    available: bool = Field(True, description="Whether item is available")
    image: Optional[str] = Field(None, description="Image URL")

class GroceryItem(BaseModel):
    title: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Short description")
    price: float = Field(..., ge=0, description="Fixed price per unit")
    available: bool = Field(True, description="Whether item is available")
    image: Optional[str] = Field(None, description="Image URL")

class OrderItem(BaseModel):
    type: Literal["butcher", "grocery"]
    item_id: str = Field(..., description="Referenced item _id as string")
    title: str
    unit_price: float = Field(..., ge=0)
    quantity: Optional[int] = Field(None, ge=1, description="For grocery items")
    weight_kg: Optional[float] = Field(None, ge=0.1, description="For butcher items in kg")
    subtotal: float = Field(..., ge=0)

class Order(BaseModel):
    customer_name: str
    phone: str
    address: str
    payment_method: Literal["Cash on Delivery", "Card on Delivery"]
    status: Literal["Pending", "Confirmed", "Ready for Pickup", "Delivered"] = "Pending"
    items: List[OrderItem]
    total: float = Field(..., ge=0)

# Example schemas kept for reference
class User(BaseModel):
    name: str
    email: str
    address: str
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
