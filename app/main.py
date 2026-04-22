import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import halls, products, bookings, stock, orders, users, categories, loyalty, staff

app = FastAPI(
    title="Kinorum API",
    description=(
        "Backend для управления залами, бронированием и складом.\n\n"
        "## Основные флоу\n"
        "1. **Бронирование зала** — `POST /bookings/` → activate → complete/cancel\n"
        "2. **Заказ товаров** — создать заказ для активной брони → добавить позиции → complete\n"
        "3. **Склад** — загрузить товар в зал → резерв при заказе → списание при выполнении\n"
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/v1")
app.include_router(halls.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(bookings.router, prefix="/api/v1")
app.include_router(stock.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(loyalty.router, prefix="/api/v1")
app.include_router(staff.router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}


# Serve operator panel
_operator_file = os.path.join(os.path.dirname(__file__), "..", "operator.html")
if os.path.isfile(_operator_file):
    @app.get("/operator.html", include_in_schema=False)
    async def operator_panel():
        return FileResponse(_operator_file)

# Serve setup page
_setup_file = os.path.join(os.path.dirname(__file__), "..", "setup.html")
if os.path.isfile(_setup_file):
    @app.get("/setup.html", include_in_schema=False)
    async def setup_panel():
        return FileResponse(_setup_file)

# Serve Mini App frontend (must be last to not shadow API routes)
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/app", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
