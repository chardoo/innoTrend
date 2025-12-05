
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.firebase import get_db
from app.middleware.auth_middleware import require_admin
from app.models.postgress_model import Payment, PaymentType, PaymentStatus
from app.schemas.payments import (
    PaymentRequest,
    PaymentInitializeResponse,
    PaymentVerifyRequest,
    PaymentResponse
)
from app.services.payment_service import PaymentService
from app.controller.student_controller import get_current_student

payment_router = APIRouter(prefix="/payments", tags=["Payments"])

# ========== Student Endpoints ==========

@payment_router.post("/initialize", response_model=PaymentInitializeResponse)
async def initialize_payment(
    payment_request: PaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_student = Depends(get_current_student)
):
    """Initialize a payment for the current student"""
    return await PaymentService.initialize_payment(
        db, current_student.id, payment_request
    )

@payment_router.post("/verify")
async def verify_payment(
    verify_request: PaymentVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_student = Depends(get_current_student)
):
    """Verify a payment for the current student"""
    return await PaymentService.verify_payment(
        db, verify_request.payment_reference, current_student.id
    )

@payment_router.get("/my-payments", response_model=List[PaymentResponse])
async def get_my_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[PaymentStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_student = Depends(get_current_student)
):
    """Get all payments for the current student"""
    return await PaymentService.get_student_payments(
        db, current_student.id, skip, limit, status_filter
    )

@payment_router.get("/my-payments/{payment_id}", response_model=PaymentResponse)
async def get_my_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    current_student = Depends(get_current_student)
):
    """Get a specific payment for the current student"""
    return await PaymentService.get_payment(db, payment_id, current_student.id)

# ========== Public Endpoints (for payment callback) ==========

@payment_router.get("/callback")
async def payment_callback(
    reference: str = Query(..., description="Payment reference"),
    trxref: str = Query(None, description="Transaction reference"),
):
    """
    Payment callback endpoint - Paystack redirects here after payment
    This should render a success page and trigger verification
    """
    try:
        with open("templates/payment/successfullpayment.html", "r") as f:
            html_content = f.read()
            # You can inject the reference into the HTML if needed
            html_content = html_content.replace("{{reference}}", reference)
            return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Payment Successful</title></head>
                <body>
                    <h1>Payment Successful!</h1>
                    <p>Reference: {reference}</p>
                    <p>Please verify your payment in your account.</p>
                    <a href="/students/my-payments">View My Payments</a>
                </body>
            </html>
            """
        )

@payment_router.get("/", response_model=List[PaymentResponse])
async def get_all_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[PaymentStatus] = None,
    payment_type_filter: Optional[PaymentType] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get all payments (Admin only)"""
    return await PaymentService.get_all_payments(
        db, skip, limit, status_filter, payment_type_filter
    )

@payment_router.get("/statistics")
async def get_payment_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get payment statistics (Admin only)"""
    return await PaymentService.get_payment_statistics(db)

@payment_router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment_by_id(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get payment by ID (Admin only)"""
    result = await db.execute(
        select(Payment).where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return payment