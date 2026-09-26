import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta

# Ensure the root directory is on the python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.services import Service
from app.models.reviews import Review
from app.models.booking import Booking, BookingStatus
from app.core.security import get_password_hash
from app.core.redis import redis_cache

SUPERADMIN_EMAIL = "ritish.ghosh77@gmail.com"
SUPERADMIN_PASSWORD = "AdminPassword123!"
DEMO_PASSWORD = "Password123!"

USERS_DATA = [
    {
        "name": "Ritish Ghosh",
        "email": SUPERADMIN_EMAIL,
        "password": SUPERADMIN_PASSWORD,
        "role": UserRole.CUSTOMER,
        "is_active": True,
        "is_superuser": True,
        "is_verified": True,
        "phone": "+91 9900000001",
        "bio": "LocaBazaar Platform Super Administrator. Full governance and platform oversight.",
        "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80",
    },
    {
        "name": "SparkleClean Pro Services",
        "email": "sparkleclean@locabazaar.com",
        "password": DEMO_PASSWORD,
        "role": UserRole.PROVIDER,
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
        "phone": "+91 9880011223",
        "bio": "Certified deep cleaning and sanitation agency with 8+ years of commercial and residential expertise.",
        "avatar_url": "https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=400&q=80",
    },
    {
        "name": "AquaFix & Plumbing Co.",
        "email": "aquafix@locabazaar.com",
        "password": DEMO_PASSWORD,
        "role": UserRole.PROVIDER,
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
        "phone": "+91 9880022334",
        "bio": "24/7 master plumbing contractor specializing in pipe leak detection, drainage, and modern fixtures.",
        "avatar_url": "https://images.unsplash.com/photo-1581092921461-eab62e97a780?auto=format&fit=crop&w=400&q=80",
    },
    {
        "name": "VoltMasters Electricals",
        "email": "voltmasters@locabazaar.com",
        "password": DEMO_PASSWORD,
        "role": UserRole.PROVIDER,
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
        "phone": "+91 9880033445",
        "bio": "Government-certified electricians for residential wiring, backup power inverters, and surge safety.",
        "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80",
    },
    {
        "name": "Glow & Spa Studio",
        "email": "glowspa@locabazaar.com",
        "password": DEMO_PASSWORD,
        "role": UserRole.PROVIDER,
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
        "phone": "+91 9880044556",
        "bio": "Luxury at-home wellness and beauty treatments by certified cosmetologists and massage therapists.",
        "avatar_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80",
    },
    {
        "name": "HomeFix Appliance & Home Repair",
        "email": "homefix@locabazaar.com",
        "password": DEMO_PASSWORD,
        "role": UserRole.PROVIDER,
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
        "phone": "+91 9880055667",
        "bio": "Local specialists for appliance servicing, furniture assembly, and home repairs.",
        "avatar_url": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&w=400&q=80",
    },
    {
        "name": "Aarav Sharma",
        "email": "aarav.sharma@example.com",
        "password": DEMO_PASSWORD,
        "role": UserRole.CUSTOMER,
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
        "phone": "+91 9770011223",
        "bio": "Homeowner in Indiranagar who regularly books local home care services.",
        "avatar_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=400&q=80",
    },
    {
        "name": "Meera Patel",
        "email": "meera.patel@example.com",
        "password": DEMO_PASSWORD,
        "role": UserRole.CUSTOMER,
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
        "phone": "+91 9770022334",
        "bio": "Designer based in Koramangala looking for quality wellness and tech services.",
        "avatar_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=400&q=80",
    },
]

CATEGORIES_DATA = [
    {
        "name": "Home Cleaning",
        "description": "Professional deep cleaning, kitchen & bathroom sanitization, and upholstery care.",
    },
    {
        "name": "Plumbing",
        "description": "Leak repairs, pipe installations, drain cleaning, tap replacement, and water heater setup.",
    },
    {
        "name": "Electrical",
        "description": "Wiring checks, circuit breaker fixes, lighting installations, and power backup solutions.",
    },
    {
        "name": "Appliance Repair",
        "description": "Certified repair & servicing for ACs, refrigerators, washing machines, and microwave ovens.",
    },
    {
        "name": "Painting & Carpentry",
        "description": "Premium interior/exterior painting, custom furniture assembly, and wooden fixture repairs.",
    },
    {
        "name": "Pest Control",
        "description": "Safe, eco-friendly pest control treatments for termites, bed bugs, and cockroaches.",
    },
    {
        "name": "Beauty & Wellness",
        "description": "Salon-at-home haircuts, glow facials, waxing, manicure, and therapeutic body massage.",
    },
    {
        "name": "Tech Support",
        "description": "High-speed mesh Wi-Fi setup, computer hardware diagnostics, and smart security cameras.",
    },
]

SERVICES_DATA = [
    # Home Cleaning
    {
        "category_name": "Home Cleaning",
        "owner_email": "sparkleclean@locabazaar.com",
        "name": "Complete Home Deep Cleaning",
        "description": "Thorough sanitization of all rooms, scrubbing of tile floors, window cleaning, and high-touch surface disinfection using industrial steam vacuums.",
        "price": 2499,
        "image_url": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    {
        "category_name": "Home Cleaning",
        "owner_email": "sparkleclean@locabazaar.com",
        "name": "Kitchen & Chimney Degreasing",
        "description": "Heavy-duty grease removal for chimney filters, gas stovetops, kitchen tiles, countertop polish, and exhaust vents.",
        "price": 1299,
        "image_url": "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    {
        "category_name": "Home Cleaning",
        "owner_email": "sparkleclean@locabazaar.com",
        "name": "Sofa & Upholstery Shampooing",
        "description": "Deep injection-extraction shampooing that lifts deep-seated stains, pet hair, dust mites, and restores fabric freshness.",
        "price": 899,
        "image_url": "https://images.unsplash.com/photo-1527515637462-cff94eecc1ac?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    # Plumbing
    {
        "category_name": "Plumbing",
        "owner_email": "aquafix@locabazaar.com",
        "name": "Emergency Pipe & Leak Repair",
        "description": "Rapid response diagnosis and repair for burst pipes, concealed wall seepages, dripping angle valves, and faulty joints.",
        "price": 499,
        "image_url": "https://images.unsplash.com/photo-1607472586893-edb57bdc0e39?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    {
        "category_name": "Plumbing",
        "owner_email": "aquafix@locabazaar.com",
        "name": "Bathroom Sanitary & Tap Installation",
        "description": "Precision fitting of overhead showers, mixer taps, ceramic wash basins, health faucets, and dual flush cisterns.",
        "price": 799,
        "image_url": "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    {
        "category_name": "Plumbing",
        "owner_email": "aquafix@locabazaar.com",
        "name": "Clogged Drain Jet Cleaning",
        "description": "Heavy-duty electric rotary snake and hydro-jetting to clear stubborn kitchen sink traps, floor drains, and sewer lines.",
        "price": 649,
        "image_url": "https://images.unsplash.com/photo-1504148455328-c376907d081c?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    # Electrical
    {
        "category_name": "Electrical",
        "owner_email": "voltmasters@locabazaar.com",
        "name": "Home Electrical Safety Audit & Fix",
        "description": "Comprehensive check of MCB trip sensitivity, earthing resistance, load balancing across phases, and replacement of scorched switch sockets.",
        "price": 599,
        "image_url": "https://images.unsplash.com/photo-1621905251189-08b45d6a269e?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    {
        "category_name": "Electrical",
        "owner_email": "voltmasters@locabazaar.com",
        "name": "Ceiling Fan & Decorative Chandelier Mounting",
        "description": "Safe reinforcement, bracket mounting, blade balancing, and regulator connection for high-speed BLDC fans and delicate chandeliers.",
        "price": 399,
        "image_url": "https://images.unsplash.com/photo-1565814329452-e1efa11c5b89?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    {
        "category_name": "Electrical",
        "owner_email": "voltmasters@locabazaar.com",
        "name": "Inverter & Home Battery Installation",
        "description": "Custom cable routing, changeover switch installation, battery electrolyte check, and load isolation for seamless backup during power cuts.",
        "price": 1199,
        "image_url": "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    # Appliance Repair
    {
        "category_name": "Appliance Repair",
        "owner_email": "homefix@locabazaar.com",
        "name": "Split & Window AC Jet Servicing",
        "description": "Deep power jet wash of evaporator coils, condenser fin straightening, blower cleanup, filter replacement, and gas pressure diagnostics.",
        "price": 699,
        "image_url": "https://images.unsplash.com/photo-1621905252507-b35492cc74b4?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    {
        "category_name": "Appliance Repair",
        "owner_email": "homefix@locabazaar.com",
        "name": "Double Door Refrigerator Repair",
        "description": "Complete diagnostic for cooling loss, defroster failure, noisy compressor, relay replacement, and eco-friendly gas recharge.",
        "price": 899,
        "image_url": "https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    # Painting & Carpentry
    {
        "category_name": "Painting & Carpentry",
        "owner_email": "homefix@locabazaar.com",
        "name": "Furniture Assembly & Custom Wood Repair",
        "description": "Fast assembly of IKEA and online flat-pack furniture, hydraulic bed lift adjustments, soft-close hinge fitting, and table repair.",
        "price": 599,
        "image_url": "https://images.unsplash.com/photo-1538688525198-9b88f6f53126?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    {
        "category_name": "Painting & Carpentry",
        "owner_email": "homefix@locabazaar.com",
        "name": "Interior Accent Wall Painting",
        "description": "Crack filling, double primer coating, and two coats of premium luxury emulsion or geometric texture on a feature wall.",
        "price": 1799,
        "image_url": "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    # Pest Control
    {
        "category_name": "Pest Control",
        "owner_email": "sparkleclean@locabazaar.com",
        "name": "Odorless Cockroach & Ant Control",
        "description": "Advanced gel baiting in kitchen cabinets combined with organic botanical surface spray to eradicate cockroaches and ants with 90-day warranty.",
        "price": 999,
        "image_url": "https://images.unsplash.com/photo-1584824486509-112e4181ff6b?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    {
        "category_name": "Pest Control",
        "owner_email": "sparkleclean@locabazaar.com",
        "name": "Subterranean Termite Treatment",
        "description": "Drill-fill-seal barrier injection along skirting boards and door frames to protect structural woodwork against aggressive termite colonies.",
        "price": 2899,
        "image_url": "https://images.unsplash.com/photo-1584622781564-1d987f7333c1?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    # Beauty & Wellness
    {
        "category_name": "Beauty & Wellness",
        "owner_email": "glowspa@locabazaar.com",
        "name": "Relaxing Swedish Aromatherapy Massage",
        "description": "60 minutes of full-body restorative massage using organic lavender essential oils to release knot tension and soothe chronic fatigue.",
        "price": 1499,
        "image_url": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    {
        "category_name": "Beauty & Wellness",
        "owner_email": "glowspa@locabazaar.com",
        "name": "Signature Glow Facial & Hair Spa",
        "description": "Multi-stage fruit enzyme exfoliation, steam extraction, collagen face mask, and deep conditioning scalp hair spa.",
        "price": 1299,
        "image_url": "https://images.unsplash.com/photo-1560750588-73207b1ef5b8?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    # Tech Support
    {
        "category_name": "Tech Support",
        "owner_email": "voltmasters@locabazaar.com",
        "name": "Whole-Home Mesh Wi-Fi & Router Setup",
        "description": "Elimination of dead zones with dual-band mesh node configuration, guest Wi-Fi segregation, security hardening, and speed optimization.",
        "price": 799,
        "image_url": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
    {
        "category_name": "Tech Support",
        "owner_email": "voltmasters@locabazaar.com",
        "name": "Smart Doorbell & CCTV Camera Installation",
        "description": "Neat concealed wiring, weatherproof camera mounting, mobile app live feed pairing, cloud recording setup, and motion alert tuning.",
        "price": 1199,
        "image_url": "https://images.unsplash.com/photo-1557597774-9d273605dfa9?auto=format&fit=crop&w=800&q=80",
        "is_active": True,
    },
]

REVIEWS_DATA = [
    {
        "service_name": "Complete Home Deep Cleaning",
        "customer_email": "aarav.sharma@example.com",
        "rating": 5,
        "comment": "Outstanding cleaning! The team arrived right on schedule and scrubbed the bathrooms and kitchen until they gleamed. Will book monthly!",
    },
    {
        "service_name": "Complete Home Deep Cleaning",
        "customer_email": "meera.patel@example.com",
        "rating": 5,
        "comment": "Immaculate service. Every corner of our apartment was thoroughly sanitized. Very polite staff and great attention to detail.",
    },
    {
        "service_name": "Emergency Pipe & Leak Repair",
        "customer_email": "aarav.sharma@example.com",
        "rating": 5,
        "comment": "AquaFix saved our wooden flooring from a severe pipe leak behind the washing machine. Replaced the valve in under 30 minutes!",
    },
    {
        "service_name": "Home Electrical Safety Audit & Fix",
        "customer_email": "meera.patel@example.com",
        "rating": 5,
        "comment": "Very professional and safe. Fixed our recurring MCB tripping issue and neatly rewired the main distribution board.",
    },
    {
        "service_name": "Split & Window AC Jet Servicing",
        "customer_email": "aarav.sharma@example.com",
        "rating": 4,
        "comment": "Great AC jet cleaning. Cooling efficiency improved immediately and power consumption dropped. Highly recommended.",
    },
    {
        "service_name": "Relaxing Swedish Aromatherapy Massage",
        "customer_email": "meera.patel@example.com",
        "rating": 5,
        "comment": "Incredible at-home spa experience. The therapist brought fresh towels, soothing music, and wonderful essential oils.",
    },
    {
        "service_name": "Whole-Home Mesh Wi-Fi & Router Setup",
        "customer_email": "aarav.sharma@example.com",
        "rating": 5,
        "comment": "No more Wi-Fi drops in our balcony or home office. Setup took 45 minutes and speed is 300 Mbps everywhere now.",
    },
]

BOOKINGS_DATA = [
    {
        "service_name": "Complete Home Deep Cleaning",
        "customer_email": "aarav.sharma@example.com",
        "status": BookingStatus.COMPLETED,
        "provider_note": "Service completed successfully. Customer inspected and verified satisfaction.",
        "days_ago": 3,
    },
    {
        "service_name": "Emergency Pipe & Leak Repair",
        "customer_email": "aarav.sharma@example.com",
        "status": BookingStatus.COMPLETED,
        "provider_note": "Replaced burst coupling valve and verified pressure seal.",
        "days_ago": 2,
    },
    {
        "service_name": "Relaxing Swedish Aromatherapy Massage",
        "customer_email": "meera.patel@example.com",
        "status": BookingStatus.COMPLETED,
        "provider_note": "Completed 60-min session with lavender aroma blend.",
        "days_ago": 1,
    },
    {
        "service_name": "Home Electrical Safety Audit & Fix",
        "customer_email": "meera.patel@example.com",
        "status": BookingStatus.CONFIRMED,
        "provider_note": "Scheduled for tomorrow morning at 10:30 AM.",
        "days_ago": 0,
    },
    {
        "service_name": "Split & Window AC Jet Servicing",
        "customer_email": "aarav.sharma@example.com",
        "status": BookingStatus.PENDING,
        "provider_note": "Customer requested servicing for 2 split AC units.",
        "days_ago": 0,
    },
]

async def seed():
    print("[SEED] Starting LocaBazaar database seed...")

    async with AsyncSessionLocal() as db:
        # Demote the previous demo admin account if the seed is rerun on an existing database.
        legacy_admin_result = await db.execute(
            select(User).where(User.email == "admin@locabazaar.com")
        )
        legacy_admin = legacy_admin_result.scalars().first()
        if legacy_admin:
            legacy_admin.is_superuser = False
            legacy_admin.is_active = False
            legacy_admin.role = UserRole.CUSTOMER

        # 1. Seed Users (Superadmin, Providers, Customers)
        user_cache = {}
        for udata in USERS_DATA:
            res = await db.execute(select(User).where(User.email == udata["email"]))
            user = res.scalars().first()
            if not user:
                hashed_pw = get_password_hash(udata["password"])
                user = User(
                    name=udata["name"],
                    email=udata["email"],
                    hashed_password=hashed_pw,
                    role=udata["role"],
                    is_active=udata["is_active"],
                    is_superuser=udata["is_superuser"],
                    is_verified=udata["is_verified"],
                    phone=udata.get("phone"),
                    bio=udata.get("bio"),
                    avatar_url=udata.get("avatar_url"),
                )
                db.add(user)
                await db.flush()
                print(f"  + Created user: {user.name} ({user.email}) [superuser={user.is_superuser}]")
            else:
                # Ensure superadmin privileges and active status are preserved
                if udata["is_superuser"]:
                    user.is_superuser = True
                    user.name = udata["name"]
                    user.role = udata["role"]
                user.is_active = udata["is_active"]
                user.is_verified = udata["is_verified"]
                if udata.get("avatar_url") and not user.avatar_url:
                    user.avatar_url = udata["avatar_url"]
                if udata.get("phone") and not user.phone:
                    user.phone = udata["phone"]
                if udata.get("bio") and not user.bio:
                    user.bio = udata["bio"]
                print(f"  * User exists: {user.name} ({user.email}) [superuser={user.is_superuser}]")

            user_cache[user.email] = user

        # Also cache existing users
        for email in ["rgcatalyst1@gmail.com"]:
            if email not in user_cache:
                res = await db.execute(select(User).where(User.email == email))
                u = res.scalars().first()
                if u:
                    user_cache[email] = u

        # 3. Seed Categories
        category_cache = {}
        for cdata in CATEGORIES_DATA:
            res = await db.execute(select(Category).where(Category.name == cdata["name"]))
            cat = res.scalars().first()
            if not cat:
                cat = Category(
                    name=cdata["name"],
                    description=cdata["description"]
                )
                db.add(cat)
                await db.flush()
                print(f"  + Created category: {cat.name}")
            else:
                cat.description = cdata["description"]
                print(f"  * Category exists: {cat.name}")
            category_cache[cat.name] = cat

        # 4. Seed Services
        service_cache = {}
        for sdata in SERVICES_DATA:
            res = await db.execute(select(Service).where(Service.name == sdata["name"]))
            srv = res.scalars().first()
            cat = category_cache.get(sdata["category_name"])
            owner = user_cache.get(sdata["owner_email"])

            if not cat:
                print(f"  ! Missing category {sdata['category_name']} for {sdata['name']}")
                continue
            if not owner:
                print(f"  ! Missing owner {sdata['owner_email']} for {sdata['name']}")
                continue

            if not srv:
                srv = Service(
                    name=sdata["name"],
                    description=sdata["description"],
                    price=sdata["price"],
                    category_id=cat.id,
                    owner_id=owner.id,
                    image_url=sdata["image_url"],
                    is_active=sdata["is_active"],
                )
                db.add(srv)
                await db.flush()
                print(f"  + Created service: {srv.name} (Rs. {srv.price}) under [{cat.name}]")
            else:
                srv.description = sdata["description"]
                srv.price = sdata["price"]
                srv.image_url = sdata["image_url"]
                srv.category_id = cat.id
                srv.owner_id = owner.id
                srv.is_active = sdata["is_active"]
                print(f"  * Service exists: {srv.name}")

            service_cache[srv.name] = srv

        # 5. Seed Reviews
        for rdata in REVIEWS_DATA:
            srv = service_cache.get(rdata["service_name"])
            cust = user_cache.get(rdata["customer_email"])
            if not srv or not cust:
                continue

            res = await db.execute(
                select(Review).where(Review.service_id == srv.id, Review.user_id == cust.id)
            )
            review = res.scalars().first()
            if not review:
                review = Review(
                    rating=rdata["rating"],
                    comment=rdata["comment"],
                    service_id=srv.id,
                    user_id=cust.id,
                )
                db.add(review)
                print(f"  + Added review ({rdata['rating']} stars) on {srv.name} by {cust.name}")

        # 6. Seed Bookings
        for bdata in BOOKINGS_DATA:
            srv = service_cache.get(bdata["service_name"])
            cust = user_cache.get(bdata["customer_email"])
            if not srv or not cust:
                continue

            res = await db.execute(
                select(Booking).where(
                    Booking.service_id == srv.id,
                    Booking.user_id == cust.id,
                    Booking.status == bdata["status"]
                )
            )
            booking = res.scalars().first()
            if not booking:
                b_time = datetime.utcnow() - timedelta(days=bdata["days_ago"])
                booking = Booking(
                    service_id=srv.id,
                    user_id=cust.id,
                    status=bdata["status"],
                    booking_time=b_time,
                    update_time=b_time,
                    provider_note=bdata.get("provider_note"),
                )
                db.add(booking)
                print(f"  + Added booking [{bdata['status']}] on {srv.name} by {cust.name}")

        # Commit all changes to PostgreSQL
        await db.commit()
        print("[SUCCESS] All records committed to PostgreSQL database.")

        # 7. Invalidate and refresh Redis Cache
        print("[CACHE] Invalidating Redis caches...")
        try:
            await redis_cache.clear("categories:all")
            await redis_cache.clear_pattern("services:q:*")
            await redis_cache.clear_pattern("service_id:*")
            print("[CACHE] Redis caches purged successfully.")
        except Exception as e:
            print(f"[CACHE NOTICE] Redis cache notice: {e}")

    print("\n=======================================================")
    print("[DONE] LocaBazaar Seed completed successfully!")
    print("=======================================================")
    print(f"SUPERADMIN ACCOUNT:")
    print(f"  Email:    {SUPERADMIN_EMAIL}")
    print(f"  Password: {SUPERADMIN_PASSWORD}")
    print(f"  Role:     CUSTOMER (Superuser)")
    print(f"  Access:   /admin/dashboard (Full governance permissions)")
    print("=======================================================\n")

if __name__ == "__main__":
    asyncio.run(seed())
