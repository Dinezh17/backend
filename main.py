from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import timedelta
from database import SessionLocal
from models import User, Department
from schemas import UserCreate, UserLogin, DepartmentCreate, DepartmentResponse
from security import hash_password, verify_password, create_access_token, verify_access_token

app = FastAPI()

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    department = db.query(Department).filter(Department.id == user.department_id).first()
    if not department:
        raise HTTPException(status_code=400, detail="Invalid department ID")

    hashed_password = hash_password(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password, role=user.role, department_id=user.department_id)
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

# Protected Route (Requires Authentication)
@app.get("/me")
def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token missing")

    token = authorization.split(" ")[1] if "Bearer" in authorization else authorization
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {"username": payload["sub"], "role": payload["role"]}
