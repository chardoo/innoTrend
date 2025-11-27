from fastapi import APIRouter, Depends, status, BackgroundTasks
from typing import List
from app.schemas.contact import ContactCreate, ContactResponse, MessageSend
from app.services.contact_service import ContactService
from app.services.customer_service import CustomerService
from app.services.sms_service import SMSService
from app.services.email_service import EmailService
from app.middleware.auth_middleware import require_admin, get_optional_user
from app.config.firebase import get_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
router = APIRouter(prefix="/api/contacts", tags=["Contact"])

async def notify_admin_contact(contact: ContactResponse):
    """Background task to notify admin about new contact"""
    sms_service = SMSService()
    email_service = EmailService()
    
    await sms_service.notify_admin_contact_form(contact.name, contact.email)
    await email_service.notify_admin_contact_form(
        contact.name,
        contact.email,
        contact.message,
        contact.phone
    )

@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def submit_contact_form(
    contact: ContactCreate,
    background_tasks: BackgroundTasks,
     db: AsyncSession = Depends(get_db),
):
    """Submit contact form (Public endpoint)"""
    contact_service = ContactService()
    new_contact = await contact_service.create_contact(db, contact)
    
    # Notify admin in background
    background_tasks.add_task(notify_admin_contact, new_contact)
    
    return new_contact

@router.get("", response_model=List[ContactResponse])
async def list_contacts(
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False,
     db: AsyncSession = Depends(get_db),
    # current_user: dict = Depends(require_admin)
):
    """List all contact submissions (Admin only)"""
    contact_service = ContactService()
    return await contact_service.list_contacts(db, skip=skip, limit=limit, unread_only=unread_only)

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str,
     db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get contact by ID (Admin only)"""
    contact_service = ContactService()
    return await contact_service.get_contact(db, contact_id)

@router.put("/{contact_id}/read", response_model=ContactResponse)
async def mark_contact_read(
    contact_id: str,
     db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Mark contact as read (Admin only)"""
    contact_service = ContactService()
    return await contact_service.mark_as_read(db, contact_id)

@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: str,
     db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Delete contact (Admin only)"""
    contact_service = ContactService()
    await contact_service.delete_contact(db,contact_id)
    return {"message": "Contact deleted successfully"}

@router.post("/send-message")
async def send_message_to_customers(
    message_data: MessageSend,
     db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Send message to customers via email/SMS (Admin only)"""
    # customer_service = CustomerService()
    sms_service = SMSService()
    email_service = EmailService()
    contact_service = ContactService()
    customer_service = CustomerService()
    
    results = {
        "email": {"success": [], "failed": []},
        "sms": {"success": [], "failed": []}
    }
    customers = []
    contacts =  []
    for customer_id in message_data.customers_ids:
        try:
            customer = await customer_service.get_customer(db, customer_id)
            customers.append(customer)
        except:
            continue
    for contact_id in message_data.contact_ids:
        try:
            contact = await contact_service.get_contact(db, contact_id)
            contacts.append(contact)

        except:
            continue
    if message_data.send_via_email:
        email_list = [c.email for c in customers ]
        cont =[b.email for b in contacts]
        email_list.append(cont[0])
        email_results = await email_service.send_bulk_email(
            email_list,
            message_data.subject,
            message_data.message
        )
        results["email"] = email_results
    
    if message_data.send_via_sms:
              
        phone_list = [*message_data.recipient_contacts, *(customer.phone for customer in customers if customer.phone),
                      *(contact.phone for contact in contacts if contact.phone)
                      ]
       
        sms_message = f"{message_data.subject}\n\n{message_data.message}"
        sms_results = await sms_service.send_bulk_sms(phone_list, sms_message)
        results["sms"] = sms_results
    
    return {
        "message": "Messages sent",
        "results": results
    }
