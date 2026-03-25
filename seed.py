import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.services import Service
from app.models.category import Category  # Import the new model
from app.core.security import get_password_hash

async def seed_phase_1():
    async with AsyncSessionLocal() as db:
        print("🚀 Phase 1 Seeding: Categories & Categorized Services...")

        # 1. Create Categories (The Foundation)
        categories_data = [
            {"name": "Home Cleaning", "description": "Professional cleaning for houses and apartments"},
            {"name": "Appliance Repair", "description": "Fixing refrigerators, washing machines, etc."},
            {"name": "Tech Support", "description": "Software help, laptop repairs, and networking"},
        ]
        
        category_objects = []
        for cat in categories_data:
            # Check if category already exists to prevent unique constraint errors
            res = await db.execute(select(Category).where(Category.name == cat["name"]))
            existing = res.scalars().first()
            if not existing:
                new_cat = Category(**cat)
                db.add(new_cat)
                category_objects.append(new_cat)
            else:
                category_objects.append(existing)
        
        await db.commit()
        # Refresh to get IDs
        for cat in category_objects:
            await db.refresh(cat)

        # 2. Get or Create a Provider
        res = await db.execute(select(User).where(User.email == "rahul@tech.com"))
        provider = res.scalars().first()
        if not provider:
            provider = User(
                name="Rahul Tech", 
                email="rahul@tech.com", 
                hashed_password=get_password_hash("tech123"),
                phone="9876543210",
                role=UserRole.PROVIDER
            )
            db.add(provider)
            await db.commit()
            await db.refresh(provider)

        # 3. Create Categorized Services
        services_data = [
            {
                "name": "Laptop Deep Clean", 
                "description": "Internal dust removal and thermal paste replacement", 
                "price": 800.0, 
                "owner_id": provider.id,
                "category_id": category_objects[2].id  # Linked to Tech Support
            },
            {
                "name": "Kitchen Degreasing", 
                "description": "Full kitchen deep cleaning service", 
                "price": 1500.0, 
                "owner_id": provider.id,
                "category_id": category_objects[0].id  # Linked to Home Cleaning
            }
        ]

        for svc in services_data:
            # Check if service exists
            res = await db.execute(select(Service).where(Service.name == svc["name"]))
            if not res.scalars().first():
                db.add(Service(**svc))

        await db.commit()
        print("✅ Seeding successful! Check your categories in Postman.")

if __name__ == "__main__":
    asyncio.run(seed_phase_1())