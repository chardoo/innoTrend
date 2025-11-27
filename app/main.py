from fastapi import FastAPI
from app.config.config import settings
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.config.config import settings
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.requests import Request
from fastapi.staticfiles import StaticFiles


middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS if settings.ALLOW_ORIGINS != ["*"] else ["*"],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
]


app = FastAPI(title=settings.APP_NAME,middleware=middleware)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Validation error: {exc.errors()}"}
    )

templates = Jinja2Templates(directory="dist")
app.mount("/dist", StaticFiles(directory="dist"), name="dist")
# Mount the static directory for serving CSS, JS, images, etc.
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

@app.get("/", response_class=HTMLResponse)
async def get_home():
    with open("dist/index.html", "r") as f:
        return HTMLResponse(content=f.read())
    
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "InnoTrend API"}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event"""


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    print("Shutting down InnoTrend API...")

from app.controller import auth_controller, contact_controller, order_controller,  employee_controller, customer_controller,service_controller

app.include_router(auth_controller.router)
app.include_router(contact_controller.router)
app.include_router(order_controller.router)
app.include_router(employee_controller.router)
app.include_router(customer_controller.router)
app.include_router(service_controller.router)
