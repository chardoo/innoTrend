from datetime import datetime
from typing import List
from fastapi import HTTPException, status
from app.config.firebase import db
from app.schemas.contact import ContactCreate, ContactResponse

class ContactService:
    def __init__(self):
        self.collection = db.collection('contacts')
    
    async def create_contact(self, contact: ContactCreate) -> ContactResponse:
        """Create a new contact submission"""
        contact_data = {
            **contact.model_dump(),
            "is_read": False,
            "created_at": datetime.utcnow()
        }
        
        doc_ref = self.collection.document()
        doc_ref.set(contact_data)
        
        return ContactResponse(id=doc_ref.id, **contact_data)
    
    async def get_contact(self, contact_id: str) -> ContactResponse:
        """Get contact by ID"""

        doc = self.collection.document(contact_id).get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        data = doc.to_dict()
        return ContactResponse(id=doc.id, **data)
    
    async def list_contacts(self, skip: int = 0, limit: int = 100, unread_only: bool = False) -> List[ContactResponse]:
        """List all contacts"""
        query = self.collection
        
        if unread_only:
            query = query.where('is_read', '==', False)
        
        docs = query.order_by('created_at', direction='DESCENDING').offset(skip).limit(limit).stream()
        contacts = [ContactResponse(id=doc.id, **doc.to_dict()) for doc in docs]
        
        return contacts
    
    async def mark_as_read(self, contact_id: str) -> ContactResponse:
        """Mark contact as read"""
        doc_ref = self.collection.document(contact_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        doc_ref.update({"is_read": True})
        
        updated_doc = doc_ref.get()
        data = updated_doc.to_dict()
        return ContactResponse(id=updated_doc.id, **data)
    
    async def delete_contact(self, contact_id: str) -> bool:
        """Delete contact"""
        doc_ref = self.collection.document(contact_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        doc_ref.delete()
        return True
