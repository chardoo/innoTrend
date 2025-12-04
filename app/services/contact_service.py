from typing import List
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgress_model import Contact
from app.schemas.contact import ContactCreate, ContactResponse

class ContactService:
    @staticmethod
    async def create_contact(db: AsyncSession, contact: ContactCreate) -> ContactResponse:
        """Create a new contact submission"""
        print('hey am here 3')
        db_contact = Contact(**contact.model_dump(), is_read=False)
        print('hey am here 4')
        db.add(db_contact)
        await db.commit()
        await db.refresh(db_contact)
        print('hey am here 5')
        # print("Created contact:", db_contact.)
        return ContactResponse.model_validate(db_contact)
    
    @staticmethod
    async def get_contact(db: AsyncSession, contact_id: str) -> ContactResponse:
        """Get contact by ID"""
        result = await db.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        return ContactResponse.model_validate(contact)
    
    @staticmethod
    async def list_contacts(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        unread_only: bool = False
    ) -> List[ContactResponse]:
        """List all contacts with optional filters"""
        query = select(Contact)
        
        if unread_only:
            query = query.where(Contact.is_read == False)
        
        query = query.order_by(Contact.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        contacts = result.scalars().all()
        
        return [ContactResponse.model_validate(c) for c in contacts]
    
    @staticmethod
    async def mark_as_read(db: AsyncSession, contact_id: str) -> ContactResponse:
        """Mark contact as read"""
        result = await db.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        contact.is_read = True
        await db.commit()
        await db.refresh(contact)
        
        return ContactResponse.model_validate(contact)
    
    @staticmethod
    async def delete_contact(db: AsyncSession, contact_id: str) -> bool:
        """Delete contact"""
        result = await db.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        await db.delete(contact)
        await db.commit()
        return True