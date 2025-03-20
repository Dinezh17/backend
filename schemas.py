from pydantic import BaseModel
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional



class EmployeeBase(BaseModel):
    emp_number: str
    job_code: str
    emp_name: str
    job_role: str
    department_id: int



class EmployeeUpdate(BaseModel):
    job_role: Optional[str] = None
    evaluation_status: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    id: int
    evaluation_status: str
    last_evaluated_date: Optional[datetime]

    class Config:
        orm_mode = True

class EmployeeCompetencyCreate(BaseModel):
    competency_id: int
    required_score: int
    actual_score: Optional[int] = None

class EmployeeWithCompetencies(EmployeeResponse):
    competencies: List[EmployeeCompetencyCreate] = []



class DepartmentCreate(BaseModel):
    name: str

class DepartmentResponse(BaseModel):
    id: int
    name: str
    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    username: str
    password: str
    role: str  # HR or HOD
    department_id: int

class UserLogin(BaseModel):
    username: str
    password: str
class CompetencyCreate(BaseModel):
    code: str
    name: str

class CompetencyResponse(BaseModel):
    id: int
    code: str
    name: str

    class Config:
        orm_mode = True

class CompetencyRequirement(BaseModel):
    competency_id: int
    required_score: int
    
class EmployeeCreate(BaseModel):
    emp_number: str
    job_code: str
    emp_name: str
    job_role: str
    department_id: int
    competencies: List[CompetencyRequirement] = []
