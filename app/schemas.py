from pydantic import BaseModel, Field
from typing import Optional


# User schemas
class UserCreate(BaseModel):
    email: str
    full_name: Optional[str] = None
    password: str = Field(..., min_length=6, max_length=256)
    role: Optional[str] = "teacher"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: Optional[str] = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# Password reset schemas
class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=256)


# Input schemas for creating resources
class InstructorCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None  # e.g., "Senior Professor", "Assistant Prof"
    qualification: Optional[str] = None  # e.g., "Ph.D. in Mathematics"
    experience: Optional[str] = None  # e.g., "12 Years"
    expertise: Optional[str] = None  # JSON string array of subjects
    office_location: Optional[str] = None  # e.g., "Block A, Room 304"
    profile_image: Optional[str] = None
    status: Optional[str] = "Active"
    assigned_courses: Optional[str] = None  # JSON string array



class RoomCreate(BaseModel):
    name: str
    capacity: Optional[int] = None
    building: Optional[str] = None
    room_type: Optional[str] = None


class BranchCreate(BaseModel):
    name: str
    code: Optional[str] = None
    degree: str
    hod_name: Optional[str] = None
    duration_years: Optional[int] = 4
    total_semesters: Optional[int] = 8


class CourseCreate(BaseModel):
    code: str
    title: Optional[str] = None
    name: Optional[str] = None
    credits: Optional[int] = None
    department: Optional[str] = None
    branch_id: Optional[int] = None
    semester: Optional[int] = None
    subject_type: Optional[str] = "Theory"


class TimeSlotCreate(BaseModel):
    day: Optional[str] = None
    day_of_week: Optional[str] = None
    start_time: str
    end_time: str
    name: Optional[str] = None


class ClassSessionCreate(BaseModel):
    course_id: int
    instructor_id: int
    room_id: int
    timeslot_id: int
    notes: Optional[str] = None


# Output schemas
class InstructorOut(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    qualification: Optional[str] = None
    experience: Optional[str] = None
    expertise: Optional[str] = None
    office_location: Optional[str] = None
    profile_image: Optional[str] = None
    status: Optional[str] = None
    assigned_courses: Optional[str] = None

    class Config:
        orm_mode = True



class RoomOut(BaseModel):
    id: int
    name: str
    capacity: Optional[int] = None

    class Config:
        orm_mode = True


class BranchOut(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    degree: str
    hod_name: Optional[str] = None
    duration_years: int
    total_semesters: int

    class Config:
        orm_mode = True


class CourseOut(BaseModel):
    id: int
    code: str
    title: Optional[str] = None
    branch_id: Optional[int] = None
    semester: Optional[int] = None
    subject_type: Optional[str] = None

    class Config:
        orm_mode = True


class TimeSlotOut(BaseModel):
    id: int
    day: str
    start_time: str
    end_time: str

    class Config:
        orm_mode = True


class ClassSessionOut(BaseModel):
    id: int
    course: CourseOut
    instructor: InstructorOut
    room: RoomOut
    timeslot: TimeSlotOut
    notes: Optional[str] = None

    class Config:
        orm_mode = True
