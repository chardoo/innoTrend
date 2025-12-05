
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict
from fastapi import HTTPException, status
import httpx
import json
import os

from app.models.postgress_model import Payment, PaymentType, PaymentStatus, Student
from app.schemas.payments import PaymentRequest

PAYSTACK_SECRET_KEY = os.getenv("Paystack")

class PaymentService:
    
    # Payment amount configuration (in your currency)
    PAYMENT_AMOUNTS = {
        PaymentType.ADMISSION_FEE: 5000.00,
        PaymentType.TUITION_MONTHLY: 200.00,
        PaymentType.TUITION_YEARLY: 1000.00,
    }
    
    @staticmethod
    def get_payment_amount(payment_type: PaymentType, custom_amount: Optional[float] = None) -> float:
        """Get payment amount based on type"""
        if payment_type == PaymentType.OTHER and custom_amount:
            return custom_amount
        return PaymentService.PAYMENT_AMOUNTS.get(payment_type, 0.0)
    
    @staticmethod
    async def initialize_payment(
        db: AsyncSession,
        student_id: str,
        payment_request: PaymentRequest
    ) -> Dict:
        """Initialize payment with Paystack"""
        
        # Verify student exists
        result = await db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = result.scalar_one_or_none()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Get payment amount
        amount = PaymentService.get_payment_amount(
            payment_request.payment_type,
            payment_request.amount
        )
        
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment amount"
            )
        
        try:
            # Paystack API endpoint
            url = "https://api.paystack.co/transaction/initialize"
            
            headers = {
                "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json"
            }
            
            # Convert amount to kobo (Paystack expects smallest currency unit)
            amount_in_kobo = int(amount * 100)
            
            # Prepare data for Paystack
            data = {
                "amount": amount_in_kobo,
                "email": student.email,
                "callback_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/payment/callback",
                "metadata": {
                    "student_id": student_id,
                    "payment_type": payment_request.payment_type.value,
                    "student_name": student.full_name
                }
            }
            
            # Send request to Paystack
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Error initializing payment with Paystack"
                )
            
            # Get response from Paystack
            response_data = response.json()
            payment_url = response_data["data"]["authorization_url"]
            payment_reference = response_data["data"]["reference"]
            
            # Calculate expiry time (1 hour from now)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            # Store payment in database
            payment = Payment(
                student_id=student_id,
                payment_reference=payment_reference,
                amount=amount,
                payment_type=payment_request.payment_type,
                status=PaymentStatus.PENDING,
                payment_url=payment_url,
                description=payment_request.description,
                metadata=json.dumps(data["metadata"]),
                expires_at=expires_at
            )
            
            db.add(payment)
            await db.commit()
            await db.refresh(payment)
            
            return {
                "payment_url": payment_url,
                "payment_reference": payment_reference,
                "amount": amount,
                "expires_at": expires_at
            }
        
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment gateway error: {str(e)}"
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error initializing payment: {str(e)}"
            )
    
    @staticmethod
    async def verify_payment(
        db: AsyncSession,
        payment_reference: str,
        student_id: str
    ) -> Dict:
        """Verify payment with Paystack and update database"""
        
        # Get payment from database
        result = await db.execute(
            select(Payment).where(
                and_(
                    Payment.payment_reference == payment_reference,
                    Payment.student_id == student_id
                )
            )
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # If already verified, return status
        if payment.status == PaymentStatus.SUCCESS:
            return {
                "status": "success",
                "message": "Payment already verified",
                "payment": payment
            }
        
        try:
            # Verify with Paystack
            url = f"https://api.paystack.co/transaction/verify/{payment_reference}"
            
            headers = {
                "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Error verifying payment with Paystack"
                )
            
            # Check payment status
            response_data = response.json()
            paystack_status = response_data["data"]["status"]
            
            # Update payment status in database
            if paystack_status == "success":
                payment.status = PaymentStatus.SUCCESS
                payment.verified_at = datetime.utcnow()
            elif paystack_status == "failed":
                payment.status = PaymentStatus.FAILED
            else:
                payment.status = PaymentStatus.PENDING
            
            payment.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(payment)
            
            return {
                "status": paystack_status,
                "message": "Payment verification completed",
                "payment": payment
            }
        
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment gateway error: {str(e)}"
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying payment: {str(e)}"
            )
    
    @staticmethod
    async def get_payment(
        db: AsyncSession,
        payment_id: str,
        student_id: str
    ) -> Payment:
        """Get payment by ID for a specific student"""
        result = await db.execute(
            select(Payment).where(
                and_(
                    Payment.id == payment_id,
                    Payment.student_id == student_id
                )
            )
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        return payment
    
    @staticmethod
    async def get_student_payments(
        db: AsyncSession,
        student_id: str,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[PaymentStatus] = None
    ) -> List[Payment]:
        """Get all payments for a student"""
        query = select(Payment).where(Payment.student_id == student_id)
        
        if status_filter:
            query = query.where(Payment.status == status_filter)
        
        query = query.order_by(desc(Payment.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_all_payments(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[PaymentStatus] = None,
        payment_type_filter: Optional[PaymentType] = None
    ) -> List[Payment]:
        """Get all payments (Admin only)"""
        query = select(Payment).order_by(desc(Payment.created_at))
        
        filters = []
        if status_filter:
            filters.append(Payment.status == status_filter)
        if payment_type_filter:
            filters.append(Payment.payment_type == payment_type_filter)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_payment_statistics(db: AsyncSession) -> Dict:
        """Get payment statistics (Admin only)"""
        from sqlalchemy import func
        
        # Total revenue by status
        status_query = select(
            Payment.status,
            func.count(Payment.id).label('count'),
            func.sum(Payment.amount).label('total')
        ).group_by(Payment.status)
        
        status_results = await db.execute(status_query)
        
        by_status = {}
        total_revenue = 0.0
        successful_payments = 0
        
        for payment_status, count, total in status_results:
            amount = float(total) if total else 0.0
            by_status[payment_status.value] = {
                "count": count,
                "total": amount
            }
            if payment_status == PaymentStatus.SUCCESS:
                total_revenue = amount
                successful_payments = count
        
        # Revenue by payment type
        type_query = select(
            Payment.payment_type,
            func.count(Payment.id).label('count'),
            func.sum(Payment.amount).label('total')
        ).where(Payment.status == PaymentStatus.SUCCESS).group_by(Payment.payment_type)
        
        type_results = await db.execute(type_query)
        
        by_type = {}
        for payment_type, count, total in type_results:
            by_type[payment_type.value] = {
                "count": count,
                "total": float(total) if total else 0.0
            }
        
        return {
            "total_revenue": total_revenue,
            "successful_payments": successful_payments,
            "by_status": by_status,
            "by_type": by_type
        }

