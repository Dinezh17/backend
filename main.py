from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import SessionLocal
from models import EvaluationStatus, User, Department
from schemas import UserCreate, UserLogin, DepartmentCreate, DepartmentResponse
from security import hash_password, verify_password, create_access_token, verify_access_token
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Competency, User
from schemas import CompetencyCreate, CompetencyResponse
from security import verify_access_token
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Employee, EmployeeCompetency, Department
from schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeWithCompetencies, EmployeeCompetencyCreate
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow your frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)
# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Protected Route (Requires Authentication)
@app.get("/me")
def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token missing")

    token = authorization.split(" ")[1] if "Bearer" in authorization else authorization
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.username == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {"id": user.id, "username": user.username, "role": user.role}  #

# Create Employee
@app.post("/employees", response_model=EmployeeWithCompetencies)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check user authorization
    if current_user["role"] != "HR":
        raise HTTPException(status_code=403, detail="Only HR can create employees")
    
    # Check for existing employee
    existing_emp = db.query(Employee).filter(
        (Employee.emp_number == employee.emp_number) | 
        (Employee.job_code == employee.job_code)
    ).first()
    if existing_emp:
        raise HTTPException(status_code=400, detail="Employee number or job code already exists")

    # Verify department exists
    department = db.query(Department).filter(Department.id == employee.department_id).first()
    if not department:
        raise HTTPException(status_code=400, detail="Invalid department ID")
    
    # Verify all competencies exist
    competency_ids = [comp.competency_id for comp in employee.competencies]
    if competency_ids:
        found_competencies = db.query(Competency).filter(Competency.id.in_(competency_ids)).count()
        if found_competencies != len(competency_ids):
            raise HTTPException(status_code=400, detail="One or more competency IDs are invalid")
    
    # Create employee without competencies first
    employee_data = employee.dict(exclude={"competencies"})
    new_employee = Employee(**employee_data)
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    
    # Add competency requirements
    for comp in employee.competencies:
        new_competency = EmployeeCompetency(
            employee_id=new_employee.id,
            competency_id=comp.competency_id,
            required_score=comp.required_score,
            actual_score=None  # HR does not set actual scores
        )
        db.add(new_competency)
    
    db.commit()
    db.refresh(new_employee)
    
    return new_employee

# Get All Employees
@app.get("/employees", response_model=list[EmployeeResponse])
def get_all_employees(db: Session = Depends(get_db)):
    return db.query(Employee).all()

# Get Employee by ID
@app.get("/employees/{emp_id}", response_model=EmployeeWithCompetencies)
def get_employee(emp_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    return employee

# Update Employee
@app.put("/employees/{emp_id}", response_model=EmployeeResponse)
def update_employee(emp_id: int, update_data: EmployeeUpdate, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(employee, key, value)

    db.commit()
    db.refresh(employee)
    return employee

# Delete Employee
@app.delete("/employees/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.delete(employee)
    db.commit()
    return {"message": "Employee deleted successfully"}

# Assign Competencies to Employee
@app.post("/employees/{emp_id}/competencies")
def assign_competencies(emp_id: int, competencies: list[EmployeeCompetencyCreate], db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    for comp in competencies:
        new_competency = EmployeeCompetency(employee_id=emp_id, **comp.dict())
        db.add(new_competency)

    db.commit()
    return {"message": "Competencies assigned successfully"}




# Create Department
@app.post("/departments", response_model=DepartmentResponse)
def create_department(department: DepartmentCreate, db: Session = Depends(get_db)):
    existing_department = db.query(Department).filter(Department.name == department.name).first()
    if existing_department:
        raise HTTPException(status_code=400, detail="Department already exists")

    new_department = Department(name=department.name)
    db.add(new_department)
    db.commit()
    db.refresh(new_department)
    
    return new_department

# Get Departments
@app.get("/departments", response_model=list[DepartmentResponse])
def get_departments(db: Session = Depends(get_db)):
    return db.query(Department).all()

# Register User
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if the username already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash the password
    hashed_password = hash_password(user.password)

    # Create the new user
    new_user = User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role,
        department_name=user.department_name  # Use department_name here
    )

    # Add the user to the database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully"}

# User Login (JWT Authentication)
@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": db_user.username, "role": db_user.role}, timedelta(minutes=30))
    
    return {"access_token": access_token, "token_type": "bearer"}


# HR: Create Competency
@app.post("/competencies", response_model=CompetencyResponse)
def create_competency(competency: CompetencyCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] != "HR":
        raise HTTPException(status_code=403, detail="Only HR can create competencies")

    new_competency = Competency(code=competency.code, name=competency.name)
    db.add(new_competency)
    db.commit()
    db.refresh(new_competency)

    return new_competency

# HR: Edit Competency
@app.put("/competencies/{competency_id}", response_model=CompetencyResponse)
def update_competency(competency_id: int, competency_data: CompetencyCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"]!= "HR":
        raise HTTPException(status_code=403, detail="Only HR can edit competencies")

    competency = db.query(Competency).filter(Competency.id == competency_id).first()
    if not competency:
        raise HTTPException(status_code=404, detail="Competency not found")

    competency.code = competency_data.code  
    competency.name = competency_data.name
    db.commit()
    db.refresh(competency)

    return competency

# HR: Delete Competency
@app.delete("/competencies/{competency_id}")
def delete_competency(competency_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] != "HR":
        raise HTTPException(status_code=403, detail="Only HR can delete competencies")

    competency = db.query(Competency).filter(Competency.id == competency_id).first()
    if not competency:
        raise HTTPException(status_code=404, detail="Competency not found")

    db.delete(competency)
    db.commit()

    return {"message": "Competency deleted successfully"}

@app.get("/competencies", response_model=list[CompetencyResponse])
def get_competencies(db: Session = Depends(get_db)):
    return db.query(Competency).all()

    
@app.put("/employees/evaluation-status")
def update_evaluation_status(
    employee_ids: List[int], 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Check user authorization
    if current_user["role"] != "HR":
        raise HTTPException(status_code=403, detail="Only HR can update evaluation status")
    
    # Find all requested employees
    employees = db.query(Employee).filter(Employee.id.in_(employee_ids)).all()
    
    # Check if all employees were found
    if len(employees) != len(employee_ids):
        raise HTTPException(status_code=404, detail="One or more employees not found")
    
    # Update status for each employee
    for employee in employees:
        employee.evaluation_status = EvaluationStatus.PENDING
    
    db.commit()
    return {"message": f"Evaluation status updated for {len(employees)} employees"}

@app.get("/employees/filter", response_model=List[EmployeeResponse])
def filter_employees(
    department_id: Optional[int] = None,
    job_role: Optional[str] = None,
    evaluation_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Start with base query
    query = db.query(Employee)
    
    # Apply filters
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    
    if job_role:
        query = query.filter(Employee.job_role == job_role)
    
    if evaluation_status:
        query = query.filter(Employee.evaluation_status == evaluation_status)
    
    # Return filtered results
    return query.all()
# HOD endpoints for viewing and updating employee competencies

@app.get("/hod/employees", response_model=List[EmployeeResponse])
def get_department_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify user is an HOD
    if current_user["role"] != "HOD":
        raise HTTPException(status_code=403, detail="Only HOD can access this endpoint")
    
    # Get HOD's department ID
    user = db.query(User).filter(User.username == current_user["sub"]).first()
    if not user or not user.department_id:
        raise HTTPException(status_code=400, detail="Department information missing")
    
    # Get all employees in HOD's department
    employees = db.query(Employee).filter(
        Employee.department_id == user.department_id,
        Employee.evaluation_status == EvaluationStatus.PENDING
    ).all()
    
    return employees

@app.get("/hod/employees/{employee_id}", response_model=EmployeeWithCompetencies)
def get_employee_competencies(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify user is an HOD
    if current_user["role"] != "HOD":
        raise HTTPException(status_code=403, detail="Only HOD can access this endpoint")
    
    # Get HOD's department ID
    user = db.query(User).filter(User.username == current_user["sub"]).first()
    if not user or not user.department_id:
        raise HTTPException(status_code=400, detail="Department information missing")
    
    # Verify employee exists and belongs to HOD's department
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.department_id == user.department_id
    ).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found or not in your department")
    
    return employee

@app.put("/hod/employees/{employee_id}/score")
def update_competency_scores(
    employee_id: int,
    competency_scores: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify user is an HOD
    if current_user["role"] != "HOD":
        raise HTTPException(status_code=403, detail="Only HOD can update scores")
    
    # Get HOD's department ID
    user = db.query(User).filter(User.username == current_user["sub"]).first()
    if not user or not user.department_id:
        raise HTTPException(status_code=400, detail="Department information missing")
    
    # Verify employee exists and belongs to HOD's department
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.department_id == user.department_id
    ).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found or not in your department")
    
    # Update scores for each competency
    for score_data in competency_scores:
        competency_id = score_data.get("competency_id")
        actual_score = score_data.get("actual_score")
        
        if not competency_id or actual_score is None:
            continue
        
        # Find employee's competency record
        emp_competency = db.query(EmployeeCompetency).filter(
            EmployeeCompetency.employee_id == employee_id,
            EmployeeCompetency.competency_id == competency_id
        ).first()
        
        if emp_competency:
            emp_competency.actual_score = actual_score
    
    # Update evaluation status and date
    employee.evaluation_status = EvaluationStatus.FINISHED
    employee.last_evaluated_date = datetime.utcnow()
    
    db.commit()
    return {"message": "Competency scores updated successfully"}