from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base






class EvaluationStatus(enum.Enum):
    PENDING = "Pending"
    FINISHED = "Finished"

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    emp_number = Column(String, unique=True, nullable=False)
    job_code = Column(String, unique=True, nullable=False)
    emp_name = Column(String, nullable=False)
    job_role = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    evaluation_status = Column(Enum(EvaluationStatus), default=EvaluationStatus.PENDING, nullable=False)
    last_evaluated_date = Column(DateTime, nullable=True)

    # Relationships
    department = relationship("Department", back_populates="employees")  # Ensure this matches
    competencies = relationship("EmployeeCompetency", back_populates="employee")

class EmployeeCompetency(Base):
    __tablename__ = "employee_competencies"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    required_score = Column(Integer, nullable=False)
    actual_score = Column(Integer, nullable=True)

    employee = relationship("Employee", back_populates="competencies")




    

class Competency(Base):
    __tablename__ = "competencies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)



class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

 
    employees = relationship("Employee", back_populates="department")  # Add this line

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'HR' or 'HOD'
    department_name = Column(String, nullable=False)  # Change this to a string

    
