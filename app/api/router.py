from fastapi import APIRouter

from app.api.routes import admin, booking_sessions, bookings, health, locations, payments, searches

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(locations.router)
api_router.include_router(searches.router)
api_router.include_router(booking_sessions.router)
api_router.include_router(bookings.router)
api_router.include_router(payments.router)
api_router.include_router(admin.router)
