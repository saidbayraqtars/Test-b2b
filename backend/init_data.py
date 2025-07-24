#!/usr/bin/env python3
"""
Script to initialize the B2B e-commerce platform with sample data
"""

import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import uuid

# Load environment variables
load_dotenv()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def init_sample_data():
    """Initialize the database with sample data"""
    
    print("🚀 Initializing B2B E-commerce Platform with sample data...")
    
    # Clear existing data
    print("🧹 Clearing existing data...")
    await db.users.delete_many({})
    await db.categories.delete_many({})
    await db.products.delete_many({})
    await db.rfqs.delete_many({})
    await db.quotes.delete_many({})
    await db.orders.delete_many({})
    
    # Create admin user
    admin_id = str(uuid.uuid4())
    admin_user = {
        "id": admin_id,
        "email": "admin@b2bcommerce.com",
        "hashed_password": pwd_context.hash("admin123"),
        "company_name": "B2B Commerce Admin",
        "contact_person": "Admin User",
        "phone": "+1-555-0001",
        "role": "admin",
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    await db.users.insert_one(admin_user)
    print("👤 Created admin user: admin@b2bcommerce.com / admin123")
    
    # Create supplier users
    supplier1_id = str(uuid.uuid4())
    supplier1 = {
        "id": supplier1_id,
        "email": "supplier@chemcorp.com",
        "hashed_password": pwd_context.hash("supplier123"),
        "company_name": "ChemCorp Industries",
        "contact_person": "John Smith",
        "phone": "+1-555-0002",
        "role": "supplier",
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    await db.users.insert_one(supplier1)
    
    supplier2_id = str(uuid.uuid4())
    supplier2 = {
        "id": supplier2_id,
        "email": "supplier@hardwareplus.com",
        "hashed_password": pwd_context.hash("supplier123"),
        "company_name": "Hardware Plus Ltd",
        "contact_person": "Sarah Johnson",
        "phone": "+1-555-0003",
        "role": "supplier",
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    await db.users.insert_one(supplier2)
    print("🏭 Created supplier users: supplier@chemcorp.com / supplier123 and supplier@hardwareplus.com / supplier123")
    
    # Create buyer users
    buyer1_id = str(uuid.uuid4())
    buyer1 = {
        "id": buyer1_id,
        "email": "buyer@manufacturing.com",
        "hashed_password": pwd_context.hash("buyer123"),
        "company_name": "ABC Manufacturing",
        "contact_person": "Mike Davis",
        "phone": "+1-555-0004",
        "role": "buyer",
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    await db.users.insert_one(buyer1)
    
    buyer2_id = str(uuid.uuid4())
    buyer2 = {
        "id": buyer2_id,
        "email": "buyer@construction.com",
        "hashed_password": pwd_context.hash("buyer123"),
        "company_name": "XYZ Construction",
        "contact_person": "Lisa Brown",
        "phone": "+1-555-0005",
        "role": "buyer",
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    await db.users.insert_one(buyer2)
    print("🏢 Created buyer users: buyer@manufacturing.com / buyer123 and buyer@construction.com / buyer123")
    
    # Create categories
    chemical_cat_id = str(uuid.uuid4())
    chemical_category = {
        "id": chemical_cat_id,
        "name": "Chemicals",
        "description": "Industrial and laboratory chemicals",
        "parent_id": None,
        "created_at": datetime.utcnow()
    }
    await db.categories.insert_one(chemical_category)
    
    hardware_cat_id = str(uuid.uuid4())
    hardware_category = {
        "id": hardware_cat_id,
        "name": "Hardware & Tools",
        "description": "Industrial hardware and tools",
        "parent_id": None,
        "created_at": datetime.utcnow()
    }
    await db.categories.insert_one(hardware_category)
    
    safety_cat_id = str(uuid.uuid4())
    safety_category = {
        "id": safety_cat_id,
        "name": "Safety Equipment",
        "description": "Personal protective equipment and safety gear",
        "parent_id": None,
        "created_at": datetime.utcnow()
    }
    await db.categories.insert_one(safety_category)
    print("📂 Created product categories")
    
    # Create products
    products = [
        {
            "id": str(uuid.uuid4()),
            "name": "Industrial Grade Sulfuric Acid",
            "description": "High purity sulfuric acid (H2SO4) 98% concentration for industrial applications",
            "category_id": chemical_cat_id,
            "supplier_id": supplier1_id,
            "price": 125.50,
            "stock_quantity": 500,
            "min_order_quantity": 10,
            "specifications": {
                "concentration": "98%",
                "purity": "Industrial Grade",
                "packaging": "25L containers",
                "cas_number": "7664-93-9",
                "hazard_class": "8"
            },
            "images": [],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Sodium Hydroxide (Caustic Soda)",
            "description": "Food grade sodium hydroxide pellets for industrial cleaning and processing",
            "category_id": chemical_cat_id,
            "supplier_id": supplier1_id,
            "price": 85.75,
            "stock_quantity": 750,
            "min_order_quantity": 25,
            "specifications": {
                "form": "Pellets",
                "purity": "Food Grade",
                "packaging": "25kg bags",
                "cas_number": "1310-73-2",
                "pH": "14"
            },
            "images": [],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Industrial Ball Bearings Set",
            "description": "Precision steel ball bearings for heavy machinery applications",
            "category_id": hardware_cat_id,
            "supplier_id": supplier2_id,
            "price": 45.99,
            "stock_quantity": 200,
            "min_order_quantity": 1,
            "specifications": {
                "material": "Chrome Steel",
                "grade": "ABEC-5",
                "size_range": "6mm-25mm",
                "load_rating": "High",
                "application": "Industrial Machinery"
            },
            "images": [],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Heavy Duty Safety Helmets",
            "description": "ANSI/OSHA compliant hard hats for construction and industrial use",
            "category_id": safety_cat_id,
            "supplier_id": supplier2_id,
            "price": 28.50,
            "stock_quantity": 1000,
            "min_order_quantity": 50,
            "specifications": {
                "standard": "ANSI Z89.1",
                "material": "HDPE",
                "colors": "White, Yellow, Orange",
                "suspension": "4-point",
                "weight": "350g"
            },
            "images": [],
            "is_active": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Precision Cutting Tools",
            "description": "Carbide-tipped cutting tools for machining operations",
            "category_id": hardware_cat_id,
            "supplier_id": supplier2_id,
            "price": 156.00,
            "stock_quantity": 150,
            "min_order_quantity": 5,
            "specifications": {
                "material": "Tungsten Carbide",
                "coating": "TiN",
                "diameter_range": "1mm-20mm",
                "application": "CNC Machining",
                "hardness": "HRC 62-65"
            },
            "images": [],
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    for product in products:
        await db.products.insert_one(product)
    print("📦 Created 5 sample products")
    
    # Create sample RFQs
    rfq1_id = str(uuid.uuid4())
    rfq1 = {
        "id": rfq1_id,
        "buyer_id": buyer1_id,
        "product_id": products[0]["id"],  # Sulfuric Acid
        "quantity": 100,
        "message": "Need bulk quantity for manufacturing process. Looking for competitive pricing.",
        "status": "open",
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=7)
    }
    await db.rfqs.insert_one(rfq1)
    
    rfq2_id = str(uuid.uuid4())
    rfq2 = {
        "id": rfq2_id,
        "buyer_id": buyer2_id,
        "product_id": products[3]["id"],  # Safety Helmets
        "quantity": 500,
        "message": "Urgent requirement for construction project. Need ANSI compliant helmets.",
        "status": "open",
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=5)
    }
    await db.rfqs.insert_one(rfq2)
    print("📋 Created 2 sample RFQs")
    
    print("✅ Sample data initialization completed!")
    print("\n🎯 Ready to test the B2B E-commerce Platform!")
    print("\n👥 Test Users:")
    print("   Admin: admin@b2bcommerce.com / admin123")
    print("   Supplier 1: supplier@chemcorp.com / supplier123")
    print("   Supplier 2: supplier@hardwareplus.com / supplier123")
    print("   Buyer 1: buyer@manufacturing.com / buyer123")
    print("   Buyer 2: buyer@construction.com / buyer123")
    print("\n🌟 Key Features to Test:")
    print("   ✓ Multi-role authentication")
    print("   ✓ Product catalog browsing")
    print("   ✓ RFQ creation and management")
    print("   ✓ Quote submission by suppliers")
    print("   ✓ Role-based dashboards")
    print("   ✓ Order creation from quotes")

if __name__ == "__main__":
    asyncio.run(init_sample_data())