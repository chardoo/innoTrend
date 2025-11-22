from datetime import datetime
from typing import Optional, List
from fastapi import HTTPException, status
from app.config.firebase import db
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse

class EmployeeService:
    def __init__(self):
        self.collection = db.collection('employees')
    
    async def create_employee(self, employee: EmployeeCreate) -> EmployeeResponse:
        """Create a new employee"""
        employee_data = {
            **employee.model_dump(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        doc_ref = self.collection.document()
        doc_ref.set(employee_data)
        
        return EmployeeResponse(id=doc_ref.id, **employee_data)
    
    async def get_employee(self, employee_id: str) -> EmployeeResponse:
        """Get employee by ID"""
        doc = self.collection.document(employee_id).get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        data = doc.to_dict()
        return EmployeeResponse(id=doc.id, **data)
    
    async def list_employees(self, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[EmployeeResponse]:
        """List all employees"""
        query = self.collection
        
        if search:
            all_employees = query.stream()
            employees = []
            count = 0
            for doc in all_employees:
                data = doc.to_dict()
                if (search.lower() in data["name"].lower() or 
                    search.lower() in data["job_title"].lower()):
                    if count >= skip and len(employees) < limit:
                        employees.append(EmployeeResponse(id=doc.id, **data))
                    count += 1
        else:
            docs = query.offset(skip).limit(limit).stream()
            employees = [EmployeeResponse(id=doc.id, **doc.to_dict()) for doc in docs]
        
        return employees
    
    async def update_employee(self, employee_id: str, employee: EmployeeUpdate) -> EmployeeResponse:
        """Update employee"""
        doc_ref = self.collection.document(employee_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        update_data = employee.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        doc_ref.update(update_data)
        
        updated_doc = doc_ref.get()
        data = updated_doc.to_dict()
        return EmployeeResponse(id=updated_doc.id, **data)
    
    async def delete_employee(self, employee_id: str) -> bool:
        """Delete employee"""
        doc_ref = self.collection.document(employee_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        doc_ref.delete()
        return True

