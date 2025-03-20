from pydantic import BaseModel

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