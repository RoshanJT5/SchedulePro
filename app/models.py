from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, Date, Time
from sqlalchemy.orm import relationship
from .database import Base
from sqlalchemy import DateTime
from datetime import datetime


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, nullable=False)
    full_name = Column(String(200), nullable=True)
    hashed_password = Column(String(300), nullable=True)
    role = Column(String(50), nullable=True)
    
    # Relationships
    timetables = relationship("Timetable", back_populates="created_by_user")


class Instructor(Base):
    __tablename__ = "instructors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    department = Column(String(200), nullable=True)
    designation = Column(String(100), nullable=True)  # e.g., "Senior Professor", "Assistant Prof"
    qualification = Column(String(200), nullable=True)  # e.g., "Ph.D. in Mathematics"
    experience = Column(String(50), nullable=True)  # e.g., "12 Years"
    expertise = Column(String(500), nullable=True)  # JSON array string of subjects
    office_location = Column(String(200), nullable=True)  # e.g., "Block A, Room 304"
    profile_image = Column(String(500), nullable=True)  # URL or path to image
    status = Column(String(50), default="Active")  # Active, Inactive, On Leave
    assigned_courses = Column(String(500), nullable=True)  # JSON array string of course names/IDs


class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    capacity = Column(Integer, nullable=True)
    building = Column(String(200), nullable=True)
    room_type = Column(String(100), nullable=True)


class Branch(Base):
    __tablename__ = "branches"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=True)
    degree = Column(String(100), nullable=False)
    hod_name = Column(String(200), nullable=True)
    duration_years = Column(Integer, default=4)
    total_semesters = Column(Integer, default=8)
    
    courses = relationship("Course", back_populates="branch")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), nullable=False, index=True)
    title = Column(String(300), nullable=True)
    name = Column(String(300), nullable=False)
    credits = Column(Integer, nullable=True)
    department = Column(String(200), nullable=True)
    
    # Timetable specific fields
    timetable_id = Column(Integer, ForeignKey("timetables.id"), nullable=True)
    sessions_per_week = Column(Integer, default=0)
    
    # Hierarchy fields
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    semester = Column(Integer, nullable=True)
    subject_type = Column(String(50), default="Theory")
    
    # Relationships
    timetable = relationship("Timetable", back_populates="courses")
    branch = relationship("Branch", back_populates="courses")


class TimeSlot(Base):
    __tablename__ = "timeslots"
    id = Column(Integer, primary_key=True, index=True)
    day = Column(String(20), nullable=True)
    day_of_week = Column(String(20), nullable=False)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    name = Column(String(100), nullable=True)


class ClassSession(Base):
    __tablename__ = "class_sessions"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    instructor_id = Column(Integer, ForeignKey("instructors.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    timeslot_id = Column(Integer, ForeignKey("timeslots.id"))
    notes = Column(Text, nullable=True)

    course = relationship("Course")
    instructor = relationship("Instructor")
    room = relationship("Room")
    timeslot = relationship("TimeSlot")


class PasswordReset(Base):
    __tablename__ = "password_resets"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)

    user = relationship("User")


# ========================================
# Timetable Wizard Models
# ========================================

class Timetable(Base):
    __tablename__ = "timetables"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    term = Column(String(100), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    default_slot_duration = Column(Integer, default=60, nullable=True)  # in minutes
    days_of_week = Column(String(200), nullable=True)  # JSON serialized list of days
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default="draft", nullable=True)  # draft, in_progress, completed, generated
    
    # Relationships
    created_by_user = relationship("User", back_populates="timetables")
    courses = relationship("Course", back_populates="timetable")
    timetable_instructors = relationship("TimetableInstructor", back_populates="timetable")
    timetable_classrooms = relationship("TimetableClassroom", back_populates="timetable")
    timetable_timeslots = relationship("TimetableTimeSlot", back_populates="timetable")
    scheduled_slots = relationship("ScheduledSlot", back_populates="timetable")


class TimetableInstructor(Base):
    __tablename__ = "timetable_instructors"
    id = Column(Integer, primary_key=True, index=True)
    timetable_id = Column(Integer, ForeignKey("timetables.id"), nullable=False)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    expertise = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    timetable = relationship("Timetable", back_populates="timetable_instructors")


class TimetableClassroom(Base):
    __tablename__ = "timetable_classrooms"
    id = Column(Integer, primary_key=True, index=True)
    timetable_id = Column(Integer, ForeignKey("timetables.id"), nullable=False)
    name = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=True)
    room_type = Column(String(100), nullable=True)  # lecture, lab, seminar, etc
    features = Column(Text, nullable=True)  # projector, whiteboard, etc
    created_at = Column(DateTime, default=datetime.utcnow)
    
    timetable = relationship("Timetable", back_populates="timetable_classrooms")


class TimetableTimeSlot(Base):
    __tablename__ = "timetable_timeslots"
    id = Column(Integer, primary_key=True, index=True)
    timetable_id = Column(Integer, ForeignKey("timetables.id"), nullable=False)
    day_of_week = Column(String(20), nullable=False)  # Monday, Tuesday, etc
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_type = Column(String(50), nullable=True)  # lecture, break, lunch, etc
    created_at = Column(DateTime, default=datetime.utcnow)
    
    timetable = relationship("Timetable", back_populates="timetable_timeslots")


class ScheduledSlot(Base):
    __tablename__ = "scheduled_slots"
    id = Column(Integer, primary_key=True, index=True)
    timetable_id = Column(Integer, ForeignKey("timetables.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    instructor_id = Column(Integer, ForeignKey("timetable_instructors.id"), nullable=True)
    classroom_id = Column(Integer, ForeignKey("timetable_classrooms.id"), nullable=True)
    day_of_week = Column(String(20), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    generated_by_ai = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    timetable = relationship("Timetable", back_populates="scheduled_slots")
    course = relationship("Course")
    instructor = relationship("TimetableInstructor")
    classroom = relationship("TimetableClassroom")
