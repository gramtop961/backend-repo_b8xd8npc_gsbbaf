import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import ButcherItem, GroceryItem, Order, OrderItem

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility to convert Mongo docs to JSON serializable

def serialize_doc(doc):
    if not doc:
        return doc
    doc["_id"] = str(doc["_id"]) if "_id" in doc else None
    # Convert datetime fields if present
    for k in ["created_at", "updated_at"]:
        if k in doc and hasattr(doc[k], "isoformat"):
            doc[k] = doc[k].isoformat()
    return doc


@app.get("/")
def read_root():
    return {"message": "E-commerce API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response

# ----------------------- Admin Auth -----------------------
# Simple password (from env ADMIN_PASSWORD) for dashboard actions

class AdminLoginRequest(BaseModel):
    password: str


def verify_admin(password: str):
    admin_pw = os.getenv("ADMIN_PASSWORD", "admin123")
    if password != admin_pw:
        raise HTTPException(status_code=401, detail="Invalid admin password")

# ----------------------- Inventory Endpoints -----------------------

@app.get("/api/butcher", response_model=List[ButcherItem])
def list_butcher_items():
    docs = get_documents("butcheritem")
    # Return plain list without _id for response model, but include id on separate endpoint
    items = []
    for d in docs:
        items.append(ButcherItem(**{k: d.get(k) for k in ["title","description","price_per_kg","available","image"]}))
    return items

@app.get("/api/butcher/raw")
def list_butcher_items_raw():
    docs = get_documents("butcheritem")
    return [serialize_doc(d) for d in docs]

@app.post("/api/admin/butcher")
def create_butcher_item(item: ButcherItem, auth: AdminLoginRequest):
    verify_admin(auth.password)
    new_id = create_document("butcheritem", item)
    return {"_id": new_id}

@app.get("/api/grocery", response_model=List[GroceryItem])
def list_grocery_items():
    docs = get_documents("groceryitem")
    items = []
    for d in docs:
        items.append(GroceryItem(**{k: d.get(k) for k in ["title","description","price","available","image"]}))
    return items

@app.get("/api/grocery/raw")
def list_grocery_items_raw():
    docs = get_documents("groceryitem")
    return [serialize_doc(d) for d in docs]

@app.post("/api/admin/grocery")
def create_grocery_item(item: GroceryItem, auth: AdminLoginRequest):
    verify_admin(auth.password)
    new_id = create_document("groceryitem", item)
    return {"_id": new_id}

# ----------------------- Orders -----------------------

@app.post("/api/orders")
def create_order(order: Order):
    # Basic validation: ensure item references exist would be ideal; for simplicity, trust frontend for now
    # Enforce payment method
    if order.payment_method not in ["Cash on Delivery", "Card on Delivery"]:
        raise HTTPException(status_code=400, detail="Unsupported payment method")
    order_id = create_document("order", order)
    return {"_id": order_id}

@app.get("/api/admin/orders")
def list_orders(auth_password: str):
    verify_admin(auth_password)
    docs = get_documents("order")
    return [serialize_doc(d) for d in docs]

class UpdateStatusRequest(BaseModel):
    password: str
    status: str

@app.post("/api/admin/orders/{order_id}/status")
def update_order_status(order_id: str, body: UpdateStatusRequest):
    verify_admin(body.password)
    if body.status not in ["Pending", "Confirmed", "Ready for Pickup", "Delivered"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        result = db["order"].update_one({"_id": ObjectId(order_id)}, {"$set": {"status": body.status, "updated_at": None}})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Order not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order id")
    return {"ok": True}

# ----------------------- Schema endpoint for viewer -----------------------

@app.get("/schema")
def get_schema_list():
    return {
        "collections": [
            "butcheritem",
            "groceryitem",
            "order",
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
