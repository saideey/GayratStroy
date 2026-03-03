"""
G'ayrat Stroy House ERP System - Main Application

Qurilish mollari do'koni uchun ERP tizimi.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from database import init_db, db
from database.seed import seed_all
from core.config import settings
from routers import (
    auth_router, users_router, products_router,
    customers_router, warehouse_router, sales_router,
    reports_router, sms_router
)
from routers.settings import router as settings_router
from routers.sync import router as sync_router
from routers import printers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Starting G'ayrat Stroy House ERP API...")

    # Initialize database
    try:
        init_db()
        logger.info("✅ Database initialized")

        # Seed initial data
        with db.get_session() as session:
            seed_all(session)
        logger.info("✅ Database seeded")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

    logger.info("✅ G'ayrat Stroy House ERP API started successfully!")

    yield

    # Shutdown
    logger.info("👋 Shutting down G'ayrat Stroy House ERP API...")


# Create FastAPI application
app = FastAPI(
    title="G'ayrat Stroy House ERP API",
    description="""
    Qurilish mollari do'koni uchun ERP tizimi.
    
    ## Asosiy modullar:
    
    * **Auth** - Kirish, chiqish, token yangilash
    * **Users** - Foydalanuvchilar boshqaruvi
    * **Products** - Tovarlar, kategoriyalar, narxlar
    * **Warehouse** - Qoldiq, kirim-chiqim, inventarizatsiya
    * **Sales** - Sotuv, chegirmalar, qarzga sotish
    * **Customers** - Mijozlar, VIP, qarz hisobi
    * **Reports** - Hisobotlar, eksport
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "detail": str(exc) if settings.debug else None
        }
    )


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """API root endpoint."""
    return {
        "message": "G'ayrat Stroy House ERP API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Docker/Kubernetes."""
    from sqlalchemy import text
    try:
        # Test database connection
        with db.get_session() as session:
            session.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )




# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(products_router, prefix="/api/v1/products", tags=["Products"])
app.include_router(customers_router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(warehouse_router, prefix="/api/v1/warehouse", tags=["Warehouse"])
app.include_router(sales_router, prefix="/api/v1/sales", tags=["Sales"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(sms_router, prefix="/api/v1/sms", tags=["SMS"])
app.include_router(settings_router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(sync_router, prefix="/api/v1/sync", tags=["Sync"])
app.include_router(printers.router, prefix="/api/v1/printers", tags=["Printers"])






if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )