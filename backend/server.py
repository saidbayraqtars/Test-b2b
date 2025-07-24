from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import json
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = "b2b_ecommerce_secret_key_change_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    SUPPLIER = "supplier"
    BUYER = "buyer"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class RFQStatus(str, Enum):
    OPEN = "open"
    QUOTED = "quoted"
    CLOSED = "closed"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    company_name: str
    contact_person: str
    phone: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    company_name: str
    contact_person: str
    phone: str
    role: UserRole

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    parent_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CategoryCreate(BaseModel):
    name: str
    description: str = ""
    parent_id: Optional[str] = None

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category_id: str
    supplier_id: str
    price: float
    stock_quantity: int
    min_order_quantity: int = 1
    specifications: Dict[str, Any] = {}
    images: List[str] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProductCreate(BaseModel):
    name: str
    description: str
    category_id: str
    price: float
    stock_quantity: int
    min_order_quantity: int = 1
    specifications: Dict[str, Any] = {}

class RFQ(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    buyer_id: str
    product_id: str
    quantity: int
    message: str = ""
    status: RFQStatus = RFQStatus.OPEN
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime

class RFQCreate(BaseModel):
    product_id: str
    quantity: int
    message: str = ""
    expires_in_days: int = 7

class Quote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rfq_id: str
    supplier_id: str
    price_per_unit: float
    total_price: float
    delivery_time: str
    message: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class QuoteCreate(BaseModel):
    rfq_id: str
    price_per_unit: float
    delivery_time: str
    message: str = ""

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    buyer_id: str
    supplier_id: str
    product_id: str
    quantity: int
    price_per_unit: float
    total_amount: float
    status: OrderStatus = OrderStatus.PENDING
    shipping_address: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OrderCreate(BaseModel):
    quote_id: str
    shipping_address: str

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"email": email})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)

def require_role(required_role: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Authentication endpoints
@api_router.post("/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict()
    del user_dict['password']
    user = User(**user_dict)
    
    # Store user with hashed password
    user_doc = user.dict()
    user_doc['hashed_password'] = hashed_password
    await db.users.insert_one(user_doc)
    
    return user

@api_router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc or not verify_password(login_data.password, user_doc.get('hashed_password', '')):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user = User(**user_doc)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# Category endpoints
@api_router.post("/categories", response_model=Category)
async def create_category(category_data: CategoryCreate, current_user: User = Depends(require_role(UserRole.ADMIN))):
    category = Category(**category_data.dict())
    await db.categories.insert_one(category.dict())
    return category

@api_router.get("/categories", response_model=List[Category])
async def get_categories():
    categories = await db.categories.find().to_list(1000)
    return [Category(**cat) for cat in categories]

# Product endpoints
@api_router.post("/products", response_model=Product)
async def create_product(product_data: ProductCreate, current_user: User = Depends(require_role(UserRole.SUPPLIER))):
    product_dict = product_data.dict()
    product_dict['supplier_id'] = current_user.id
    product = Product(**product_dict)
    await db.products.insert_one(product.dict())
    return product

@api_router.get("/products", response_model=List[Product])
async def get_products(category_id: Optional[str] = None, supplier_id: Optional[str] = None):
    filter_dict = {"is_active": True}
    if category_id:
        filter_dict["category_id"] = category_id
    if supplier_id:
        filter_dict["supplier_id"] = supplier_id
    
    products = await db.products.find(filter_dict).to_list(1000)
    return [Product(**prod) for prod in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

@api_router.get("/my-products", response_model=List[Product])
async def get_my_products(current_user: User = Depends(require_role(UserRole.SUPPLIER))):
    products = await db.products.find({"supplier_id": current_user.id}).to_list(1000)
    return [Product(**prod) for prod in products]

# RFQ endpoints
@api_router.post("/rfqs", response_model=RFQ)
async def create_rfq(rfq_data: RFQCreate, current_user: User = Depends(require_role(UserRole.BUYER))):
    # Check if product exists
    product = await db.products.find_one({"id": rfq_data.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    rfq_dict = rfq_data.dict()
    rfq_dict['buyer_id'] = current_user.id
    rfq_dict['expires_at'] = datetime.utcnow() + timedelta(days=rfq_data.expires_in_days)
    del rfq_dict['expires_in_days']
    
    rfq = RFQ(**rfq_dict)
    await db.rfqs.insert_one(rfq.dict())
    return rfq

@api_router.get("/rfqs", response_model=List[RFQ])
async def get_rfqs(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.BUYER:
        rfqs = await db.rfqs.find({"buyer_id": current_user.id}).to_list(1000)
    elif current_user.role == UserRole.SUPPLIER:
        # Get RFQs for supplier's products
        supplier_products = await db.products.find({"supplier_id": current_user.id}).to_list(1000)
        product_ids = [prod["id"] for prod in supplier_products]
        rfqs = await db.rfqs.find({"product_id": {"$in": product_ids}, "status": "open"}).to_list(1000)
    else:  # Admin
        rfqs = await db.rfqs.find().to_list(1000)
    
    return [RFQ(**rfq) for rfq in rfqs]

# Quote endpoints
@api_router.post("/quotes", response_model=Quote)
async def create_quote(quote_data: QuoteCreate, current_user: User = Depends(require_role(UserRole.SUPPLIER))):
    # Check if RFQ exists and is open
    rfq = await db.rfqs.find_one({"id": quote_data.rfq_id})
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if rfq["status"] != "open":
        raise HTTPException(status_code=400, detail="RFQ is not open for quotes")
    
    # Check if product belongs to this supplier
    product = await db.products.find_one({"id": rfq["product_id"], "supplier_id": current_user.id})
    if not product:
        raise HTTPException(status_code=403, detail="Product does not belong to you")
    
    quote_dict = quote_data.dict()
    quote_dict['supplier_id'] = current_user.id
    quote_dict['total_price'] = quote_data.price_per_unit * rfq["quantity"]
    
    quote = Quote(**quote_dict)
    await db.quotes.insert_one(quote.dict())
    
    # Update RFQ status to quoted
    await db.rfqs.update_one({"id": quote_data.rfq_id}, {"$set": {"status": "quoted"}})
    
    return quote

@api_router.get("/quotes/{rfq_id}", response_model=List[Quote])
async def get_quotes_for_rfq(rfq_id: str, current_user: User = Depends(get_current_user)):
    # Check if user has access to this RFQ
    rfq = await db.rfqs.find_one({"id": rfq_id})
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    if current_user.role == UserRole.BUYER and rfq["buyer_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    quotes = await db.quotes.find({"rfq_id": rfq_id}).to_list(1000)
    return [Quote(**quote) for quote in quotes]

# Order endpoints
@api_router.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate, current_user: User = Depends(require_role(UserRole.BUYER))):
    # Get quote details
    quote = await db.quotes.find_one({"id": order_data.quote_id})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Get RFQ details
    rfq = await db.rfqs.find_one({"id": quote["rfq_id"]})
    if not rfq or rfq["buyer_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    order = Order(
        buyer_id=current_user.id,
        supplier_id=quote["supplier_id"],
        product_id=rfq["product_id"],
        quantity=rfq["quantity"],
        price_per_unit=quote["price_per_unit"],
        total_amount=quote["total_price"],
        shipping_address=order_data.shipping_address
    )
    
    await db.orders.insert_one(order.dict())
    
    # Update RFQ status to closed
    await db.rfqs.update_one({"id": quote["rfq_id"]}, {"$set": {"status": "closed"}})
    
    return order

@api_router.get("/orders", response_model=List[Order])
async def get_orders(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.BUYER:
        orders = await db.orders.find({"buyer_id": current_user.id}).to_list(1000)
    elif current_user.role == UserRole.SUPPLIER:
        orders = await db.orders.find({"supplier_id": current_user.id}).to_list(1000)
    else:  # Admin
        orders = await db.orders.find().to_list(1000)
    
    return [Order(**order) for order in orders]

# Dashboard stats endpoints
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.ADMIN:
        total_users = await db.users.count_documents({})
        total_products = await db.products.count_documents({})
        total_orders = await db.orders.count_documents({})
        total_rfqs = await db.rfqs.count_documents({})
        
        return {
            "total_users": total_users,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_rfqs": total_rfqs
        }
    elif current_user.role == UserRole.SUPPLIER:
        my_products = await db.products.count_documents({"supplier_id": current_user.id})
        my_orders = await db.orders.count_documents({"supplier_id": current_user.id})
        pending_rfqs = await db.rfqs.count_documents({
            "product_id": {"$in": [p["id"] for p in await db.products.find({"supplier_id": current_user.id}).to_list(1000)]},
            "status": "open"
        })
        
        return {
            "my_products": my_products,
            "my_orders": my_orders,
            "pending_rfqs": pending_rfqs
        }
    else:  # Buyer
        my_rfqs = await db.rfqs.count_documents({"buyer_id": current_user.id})
        my_orders = await db.orders.count_documents({"buyer_id": current_user.id})
        
        return {
            "my_rfqs": my_rfqs,
            "my_orders": my_orders
        }

# Basic health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()