from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional

from .database import Base, engine, get_db
from .models import Product
from .schemas import ProductCreate, ProductUpdate, ProductOut

app = FastAPI(title="FastAPI CRUD Example", version="1.0.0")

# Create tables on startup (simple dev approach)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# ------- CREATE -------
@app.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    # ensure unique SKU
    existing = db.scalar(select(Product).where(Product.sku == payload.sku))
    if existing:
        raise HTTPException(status_code=409, detail="SKU already exists")

    product = Product(
        sku=payload.sku,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        in_stock=payload.in_stock,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


# ------- READ (LIST with filters) -------
@app.get("/products", response_model=List[ProductOut])
def list_products(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Search by name or SKU"),
    in_stock: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort: str = Query("created_at:desc", description="Format: field:asc|desc"),
):
    stmt = select(Product)

    if q:
        like = f"%{q}%"
        stmt = stmt.where((Product.name.ilike(like)) | (Product.sku.ilike(like)))

    if in_stock is not None:
        stmt = stmt.where(Product.in_stock == in_stock)

    # simple sort parsing
    field, _, direction = sort.partition(":")
    field = field.strip() or "created_at"
    direction = (direction or "desc").lower()

    sortable = {
        "id": Product.id,
        "sku": Product.sku,
        "name": Product.name,
        "price": Product.price,
        "created_at": Product.created_at,
    }
    sort_col = sortable.get(field, Product.created_at)
    if direction == "asc":
        stmt = stmt.order_by(sort_col.asc())
    else:
        stmt = stmt.order_by(sort_col.desc())

    stmt = stmt.offset(skip).limit(limit)

    rows = db.scalars(stmt).all()
    return rows


# ------- READ (ONE) -------
@app.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ------- UPDATE (PARTIAL) -------
@app.patch("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    data = payload.model_dump(exclude_unset=True)

    # Unique SKU check if changing
    if "sku" in data and data["sku"] != product.sku:
        exists = db.scalar(select(Product).where(Product.sku == data["sku"]))
        if exists:
            raise HTTPException(status_code=409, detail="SKU already exists")

    for k, v in data.items():
        setattr(product, k, v)

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


# ------- DELETE -------
@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return None




# from typing import Union

# from fastapi import FastAPI
# from pydantic import BaseModel

# app = FastAPI()


# class Item(BaseModel):
#     name: str
#     price: float
#     is_offer: Union[bool, None] = None


# @app.get("/")
# def read_root():
#     return {"Hello": "World"}


# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}


# @app.put("/items/{item_id}")
# def update_item(item_id: int, item: Item):
#     return {"item_name": item.name,"item_price": item.price, "item_id": item_id}

# @app.get("/get/items")
# def get_all_items():
#     return []