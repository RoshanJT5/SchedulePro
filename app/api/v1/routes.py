# app/api/v1/routes.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ... import models, schemas
from ...auth import get_current_user

from .auth_routes import router as auth_router

router = APIRouter(prefix="/v1")

# include auth routes (they already have prefix /auth)
router.include_router(auth_router)


@router.get("/health")
def health():
    return {"status": "ok"}


# expose a simple /v1/me endpoint (dashboard JS expects /v1/me)
@router.get("/me", response_model=schemas.UserOut)
def read_me(current_user=Depends(get_current_user)):
    return current_user


### Courses
@router.get("/courses", response_model=List[schemas.CourseOut])
def list_courses(db: Session = Depends(get_db)):
    return db.query(models.Course).all()


@router.post("/courses", response_model=schemas.CourseOut, status_code=201)
def create_course(course_in: schemas.CourseCreate, db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    course = models.Course(
        code=course_in.code,
        name=course_in.name or course_in.title or "Unnamed",
        title=course_in.title or course_in.name or "Unnamed",
        credits=course_in.credits,
        department=course_in.department,
        branch_id=course_in.branch_id,
        semester=course_in.semester,
        subject_type=course_in.subject_type
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("/courses/{course_id}", response_model=schemas.CourseOut)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.put("/courses/{course_id}", response_model=schemas.CourseOut)
def update_course(course_id: int, course_in: schemas.CourseCreate, db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    course = db.query(models.Course).get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course.code = course_in.code
    course.name = course_in.name or course_in.title or course.name
    course.title = course_in.title or course_in.name or course.title
    course.credits = course_in.credits or course.credits
    course.department = course_in.department or course.department
    course.branch_id = course_in.branch_id or course.branch_id
    course.semester = course_in.semester or course.semester
    course.subject_type = course_in.subject_type or course.subject_type
    
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.delete("/courses/{course_id}", status_code=204)
def delete_course(course_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    course = db.query(models.Course).get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    return None


### Instructors
@router.get("/instructors", response_model=List[schemas.InstructorOut])
def list_instructors(db: Session = Depends(get_db)):
    return db.query(models.Instructor).all()


@router.post("/instructors", response_model=schemas.InstructorOut, status_code=201)
def create_instructor(inst_in: schemas.InstructorCreate, db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    inst = models.Instructor(
        name=inst_in.name,
        email=inst_in.email,
        phone=inst_in.phone,
        department=inst_in.department,
        designation=inst_in.designation,
        qualification=inst_in.qualification,
        experience=inst_in.experience,
        expertise=inst_in.expertise,
        office_location=inst_in.office_location,
        profile_image=inst_in.profile_image,
        status=inst_in.status,
        assigned_courses=inst_in.assigned_courses
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst



@router.get("/instructors/{inst_id}", response_model=schemas.InstructorOut)
def get_instructor(inst_id: int, db: Session = Depends(get_db)):
    inst = db.query(models.Instructor).get(inst_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instructor not found")
    return inst


@router.put("/instructors/{inst_id}", response_model=schemas.InstructorOut)
def update_instructor(inst_id: int, inst_in: schemas.InstructorCreate, db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    inst = db.query(models.Instructor).get(inst_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instructor not found")
    inst.name = inst_in.name
    inst.email = inst_in.email or inst.email
    inst.phone = inst_in.phone or inst.phone
    inst.department = inst_in.department or inst.department
    inst.designation = inst_in.designation or inst.designation
    inst.qualification = inst_in.qualification or inst.qualification
    inst.experience = inst_in.experience or inst.experience
    inst.expertise = inst_in.expertise or inst.expertise
    inst.office_location = inst_in.office_location or inst.office_location
    inst.profile_image = inst_in.profile_image or inst.profile_image
    inst.status = inst_in.status or inst.status
    inst.assigned_courses = inst_in.assigned_courses or inst.assigned_courses
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst



@router.delete("/instructors/{inst_id}", status_code=204)
def delete_instructor(inst_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    inst = db.query(models.Instructor).get(inst_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instructor not found")
    db.delete(inst)
    db.commit()
    return None


### Rooms
@router.get("/rooms", response_model=List[schemas.RoomOut])
def list_rooms(db: Session = Depends(get_db)):
    return db.query(models.Room).all()


@router.post("/rooms", response_model=schemas.RoomOut, status_code=201)
def create_room(room_in: schemas.RoomCreate, db: Session = Depends(get_db),
                current_user=Depends(get_current_user)):
    room = models.Room(
        name=room_in.name,
        capacity=room_in.capacity,
        building=room_in.building,
        room_type=room_in.room_type
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.get("/rooms/{room_id}", response_model=schemas.RoomOut)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(models.Room).get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.put("/rooms/{room_id}", response_model=schemas.RoomOut)
def update_room(room_id: int, room_in: schemas.RoomCreate, db: Session = Depends(get_db),
                current_user=Depends(get_current_user)):
    room = db.query(models.Room).get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    room.name = room_in.name
    room.capacity = room_in.capacity or room.capacity
    room.building = room_in.building or room.building
    room.room_type = room_in.room_type or room.room_type
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.delete("/rooms/{room_id}", status_code=204)
def delete_room(room_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    room = db.query(models.Room).get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    db.delete(room)
    db.commit()
    return None


### TimeSlots
@router.get("/timeslots", response_model=List[schemas.TimeSlotOut])
def list_timeslots(db: Session = Depends(get_db)):
    return db.query(models.TimeSlot).all()


@router.post("/timeslots", response_model=schemas.TimeSlotOut, status_code=201)
def create_timeslot(ts_in: schemas.TimeSlotCreate, db: Session = Depends(get_db),
                    current_user=Depends(get_current_user)):
    ts = models.TimeSlot(
        day=ts_in.day or ts_in.day_of_week,
        day_of_week=ts_in.day_of_week or ts_in.day or "Monday",
        start_time=ts_in.start_time,
        end_time=ts_in.end_time,
        name=ts_in.name
    )
    db.add(ts)
    db.commit()
    db.refresh(ts)
    return ts


@router.get("/timeslots/{ts_id}", response_model=schemas.TimeSlotOut)
def get_timeslot(ts_id: int, db: Session = Depends(get_db)):
    ts = db.query(models.TimeSlot).get(ts_id)
    if not ts:
        raise HTTPException(status_code=404, detail="TimeSlot not found")
    return ts


@router.put("/timeslots/{ts_id}", response_model=schemas.TimeSlotOut)
def update_timeslot(ts_id: int, ts_in: schemas.TimeSlotCreate, db: Session = Depends(get_db),
                    current_user=Depends(get_current_user)):
    ts = db.query(models.TimeSlot).get(ts_id)
    if not ts:
        raise HTTPException(status_code=404, detail="TimeSlot not found")
    ts.day = ts_in.day or ts_in.day_of_week or ts.day
    ts.day_of_week = ts_in.day_of_week or ts_in.day or ts.day_of_week
    ts.start_time = ts_in.start_time
    ts.end_time = ts_in.end_time
    ts.name = ts_in.name or ts.name
    db.add(ts)
    db.commit()
    db.refresh(ts)
    return ts


@router.delete("/timeslots/{ts_id}", status_code=204)
def delete_timeslot(ts_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    ts = db.query(models.TimeSlot).get(ts_id)
    if not ts:
        raise HTTPException(status_code=404, detail="TimeSlot not found")
    db.delete(ts)
    db.commit()
    return None


### Class Sessions (schedule entries)
@router.get("/sessions", response_model=List[schemas.ClassSessionOut])
def list_sessions(db: Session = Depends(get_db)):
    return db.query(models.ClassSession).all()


@router.post("/sessions", response_model=schemas.ClassSessionOut, status_code=201)
def create_session(s_in: schemas.ClassSessionCreate, db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    # validate references
    course = db.query(models.Course).get(s_in.course_id)
    instructor = db.query(models.Instructor).get(s_in.instructor_id)
    room = db.query(models.Room).get(s_in.room_id)
    timeslot = db.query(models.TimeSlot).get(s_in.timeslot_id)
    if not course or not instructor or not room or not timeslot:
        raise HTTPException(status_code=400, detail="Invalid foreign key reference")
    sess = models.ClassSession(
        course_id=s_in.course_id,
        instructor_id=s_in.instructor_id,
        room_id=s_in.room_id,
        timeslot_id=s_in.timeslot_id,
        notes=s_in.notes,
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


@router.get("/sessions/{sess_id}", response_model=schemas.ClassSessionOut)
def get_session(sess_id: int, db: Session = Depends(get_db)):
    sess = db.query(models.ClassSession).get(sess_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    return sess


@router.put("/sessions/{sess_id}", response_model=schemas.ClassSessionOut)
def update_session(sess_id: int, s_in: schemas.ClassSessionCreate, db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    sess = db.query(models.ClassSession).get(sess_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    sess.course_id = s_in.course_id
    sess.instructor_id = s_in.instructor_id
    sess.room_id = s_in.room_id
    sess.timeslot_id = s_in.timeslot_id
    sess.notes = s_in.notes
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


@router.delete("/sessions/{sess_id}", status_code=204)
def delete_session(sess_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    sess = db.query(models.ClassSession).get(sess_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(sess)
    db.commit()
    return None


# ========================================
# Timetable Wizard API Endpoints
# ========================================

# Create a new timetable
@router.post("/timetables", status_code=201)
def create_timetable(data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Create a new timetable (start wizard)"""
    name = data.get("name") or "New Timetable"
    term = data.get("term")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    days_of_week = data.get("days_of_week")
    default_slot_duration = data.get("default_slot_duration", 60)
    
    timetable = models.Timetable(
        name=name,
        term=term,
        start_date=start_date,
        end_date=end_date,
        days_of_week=days_of_week,
        default_slot_duration=default_slot_duration,
        created_by=current_user.id,
        status="draft"
    )
    db.add(timetable)
    db.commit()
    db.refresh(timetable)
    
    return {
        "id": timetable.id,
        "name": timetable.name,
        "term": timetable.term,
        "status": timetable.status,
        "created_at": timetable.created_at.isoformat() if timetable.created_at else None
    }


# Get timetable details
@router.get("/timetables/{tid}")
def get_timetable(tid: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get timetable with all related data"""
    timetable = db.query(models.Timetable).filter(models.Timetable.id == tid).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    
    if timetable.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this timetable")
    
    return {
        "id": timetable.id,
        "name": timetable.name,
        "term": timetable.term,
        "start_date": timetable.start_date,
        "end_date": timetable.end_date,
        "status": timetable.status,
        "created_at": timetable.created_at.isoformat() if timetable.created_at else None,
        "courses_count": len(timetable.courses),
        "instructors_count": len(timetable.timetable_instructors),
        "classrooms_count": len(timetable.timetable_classrooms),
        "timeslots_count": len(timetable.timetable_timeslots)
    }


@router.put("/timetables/{tid}")
def update_timetable(tid: int, data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Update basic timetable fields (used by wizard steps)"""
    timetable = db.query(models.Timetable).filter(models.Timetable.id == tid).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")

    if timetable.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this timetable")

    # Update allowed fields
    timetable.name = data.get('name', timetable.name)
    timetable.term = data.get('term', timetable.term)
    timetable.start_date = data.get('start_date', timetable.start_date)
    timetable.end_date = data.get('end_date', timetable.end_date)
    if 'days_of_week' in data:
        timetable.days_of_week = data.get('days_of_week')
    if 'default_slot_duration' in data:
        timetable.default_slot_duration = data.get('default_slot_duration')
    if 'status' in data:
        timetable.status = data.get('status')

    db.add(timetable)
    db.commit()
    db.refresh(timetable)

    return {
        'id': timetable.id,
        'name': timetable.name,
        'term': timetable.term,
        'start_date': timetable.start_date,
        'end_date': timetable.end_date,
        'days_of_week': timetable.days_of_week,
        'default_slot_duration': timetable.default_slot_duration
    }


# Get courses for a timetable
@router.get("/timetables/{tid}/courses")
def get_timetable_courses(tid: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get all courses for a timetable"""
    timetable = db.query(models.Timetable).filter(models.Timetable.id == tid).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    
    if timetable.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    courses = db.query(models.Course).filter(models.Course.timetable_id == tid).all()
    return [
        {
            "id": c.id,
            "code": c.code,
            "title": c.title,
            "credits": c.credits,
            "sessions_per_week": c.sessions_per_week,
            "name": c.name
        }
        for c in courses
    ]


# Add course to timetable
@router.post("/timetables/{tid}/courses", status_code=201)
def add_course_to_timetable(tid: int, data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Add a course to timetable"""
    timetable = db.query(models.Timetable).filter(models.Timetable.id == tid).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    
    if timetable.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    course = models.Course(
        timetable_id=tid,
        code=data.get("code"),
        title=data.get("title"),
        name=data.get("name", data.get("title", "")),
        credits=data.get("credits", 0),
        sessions_per_week=data.get("sessions_per_week", 0),
        department=data.get("department")
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    
    return {
        "id": course.id,
        "code": course.code,
        "title": course.title,
        "credits": course.credits,
        "sessions_per_week": course.sessions_per_week,
        "name": course.name
    }


# Update course
@router.put("/timetables/{tid}/courses/{cid}")
def update_course(tid: int, cid: int, data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Update a course in timetable"""
    timetable = db.query(models.Timetable).filter(models.Timetable.id == tid).first()
    if not timetable or timetable.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    course = db.query(models.Course).filter(models.Course.id == cid, models.Course.timetable_id == tid).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course.code = data.get("code", course.code)
    course.title = data.get("title", course.title)
    course.credits = data.get("credits", course.credits)
    course.sessions_per_week = data.get("sessions_per_week", course.sessions_per_week)
    
    db.commit()
    db.refresh(course)
    
    return {"id": course.id, "code": course.code, "title": course.title, "credits": course.credits}


# Delete course
@router.delete("/timetables/{tid}/courses/{cid}", status_code=204)
def delete_course(tid: int, cid: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Delete a course from timetable"""
    timetable = db.query(models.Timetable).filter(models.Timetable.id == tid).first()
    if not timetable or timetable.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    course = db.query(models.Course).filter(models.Course.id == cid, models.Course.timetable_id == tid).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db.delete(course)
    db.commit()


# Get instructors for a timetable
@router.get("/timetables/{tid}/instructors")
def get_timetable_instructors(tid: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get all instructors for a timetable"""
    timetable = db.query(models.Timetable).filter(models.Timetable.id == tid).first()
    if not timetable or timetable.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    instructors = db.query(models.TimetableInstructor).filter(models.TimetableInstructor.timetable_id == tid).all()
    return [
        {
            "id": i.id,
            "name": i.name,
            "email": i.email,
            "phone": i.phone,
            "notes": i.notes
        }
        for i in instructors
    ]


# Add instructor to timetable
@router.post("/timetables/{tid}/instructors", status_code=201)
def add_instructor_to_timetable(tid: int, data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Add instructor to timetable"""
    timetable = db.query(models.Timetable).filter(models.Timetable.id == tid).first()
    if not timetable or timetable.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    instructor = models.TimetableInstructor(
        timetable_id=tid,
        name=data.get("name"),
        email=data.get("email"),
        phone=data.get("phone"),
        expertise=data.get("expertise"),
        notes=data.get("notes")
    )
    db.add(instructor)
    db.commit()
    db.refresh(instructor)
    
    return {
        "id": instructor.id,
        "name": instructor.name,
        "email": instructor.email,
        "phone": instructor.phone,
        "expertise": instructor.expertise,
        "notes": instructor.notes
    }


# Delete instructor
@router.delete("/timetables/{tid}/instructors/{iid}", status_code=204)
def delete_instructor(tid: int, iid: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Delete instructor from timetable"""
    timetable = db.query(models.Timetable).filter(models.Timetable.id == tid).first()
    if not timetable or timetable.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    instructor = db.query(models.TimetableInstructor).filter(models.TimetableInstructor.id == iid).first()
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    
    db.delete(instructor)
    db.commit()


# Get classrooms for a timetable
@router.get("/timetables/{tid}/classrooms")
def get_timetable_classrooms(tid: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get all classrooms for a timetable"""
    timetable = db.query(models.Timetable).filter(models.Timetable.id == tid).first()
    if not timetable or timetable.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    classrooms = db.query(models.TimetableClassroom).filter(models.TimetableClassroom.timetable_id == tid).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "capacity": c.capacity,
            "room_type": c.room_type,
            "features": c.features
        }
        for c in classrooms
    ]


# Add classroom to timetable
@router.post("/timetables/{tid}/classrooms", status_code=201)
def add_classroom_to_timetable(tid: int, data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Add classroom to timetable"""
    timetable = db.query(models.Timetable).filter(models.Timetable.id == tid).first()
    if not timetable or timetable.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    classroom = models.TimetableClassroom(
        timetable_id=tid,
        name=data.get("name"),
        capacity=data.get("capacity"),
        room_type=data.get("room_type"),
        features=data.get("features")
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    
    return {
        "id": classroom.id,
        "name": classroom.name,
        "capacity": classroom.capacity,
        "room_type": classroom.room_type,
        "features": classroom.features
    }


# Delete classroom
@router.delete("/timetables/{tid}/classrooms/{cid}", status_code=204)
def delete_classroom(tid: int, cid: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Delete classroom from timetable"""
    timetable = db.query(models.Timetable).filter(models.Timetable.id == tid).first()
    if not timetable or timetable.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    classroom = db.query(models.TimetableClassroom).filter(models.TimetableClassroom.id == cid).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    db.delete(classroom)
    db.commit()


# Get timeslots for a timetable
@router.get("/timetables/{tid}/timeslots")
def get_timetable_timeslots(tid: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get all timeslots for a timetable"""
    timetable = db.query(models.Timetable).filter(models.Timetable.id == tid).first()
    if not timetable or timetable.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    timeslots = db.query(models.TimetableTimeSlot).filter(models.TimetableTimeSlot.timetable_id == tid).all()
    return [
        {
            "id": ts.id,
            "day_of_week": ts.day_of_week,
            "start_time": ts.start_time.isoformat() if ts.start_time else None,
            "end_time": ts.end_time.isoformat() if ts.end_time else None,
            "slot_type": ts.slot_type
        }
        for ts in timeslots
    ]


# Add timeslot to timetable
@router.post("/timetables/{tid}/timeslots", status_code=201)
def add_timeslot_to_timetable(tid: int, data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Add timeslot to timetable"""
    timetable = db.query(models.Timetable).filter(models.Timetable.id == tid).first()
    if not timetable or timetable.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    import datetime
    start_time_str = data.get("start_time")
    end_time_str = data.get("end_time")
    
    # Parse time strings (format: HH:MM)
    start_time = datetime.datetime.strptime(start_time_str, "%H:%M").time() if start_time_str else None
    end_time = datetime.datetime.strptime(end_time_str, "%H:%M").time() if end_time_str else None
    
    timeslot = models.TimetableTimeSlot(
        timetable_id=tid,
        day_of_week=data.get("day_of_week"),
        start_time=start_time,
        end_time=end_time,
        slot_type=data.get("slot_type", "lecture")
    )
    db.add(timeslot)
    db.commit()
    db.refresh(timeslot)
    
    return {
        "id": timeslot.id,
        "day_of_week": timeslot.day_of_week,
        "start_time": timeslot.start_time.isoformat() if timeslot.start_time else None,
        "end_time": timeslot.end_time.isoformat() if timeslot.end_time else None,
        "slot_type": timeslot.slot_type
    }



@router.delete("/timetables/{tid}/timeslots/{tsid}", status_code=204)
def delete_timeslot(tid: int, tsid: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Delete timeslot from timetable"""
    timetable = db.query(models.Timetable).filter(models.Timetable.id == tid).first()
    if not timetable or timetable.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    timeslot = db.query(models.TimetableTimeSlot).filter(models.TimetableTimeSlot.id == tsid).first()
    if not timeslot:
        raise HTTPException(status_code=404, detail="Timeslot not found")
    
    db.delete(timeslot)
    db.commit()


### Branches (New Module)
@router.get("/branches", response_model=List[schemas.BranchOut])
def list_branches(db: Session = Depends(get_db)):
    return db.query(models.Branch).all()


@router.post("/branches", response_model=schemas.BranchOut, status_code=201)
def create_branch(branch_in: schemas.BranchCreate, db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    branch = models.Branch(
        name=branch_in.name,
        code=branch_in.code,
        degree=branch_in.degree,
        hod_name=branch_in.hod_name,
        duration_years=branch_in.duration_years,
        total_semesters=branch_in.total_semesters
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


@router.get("/branches/{branch_id}", response_model=schemas.BranchOut)
def get_branch(branch_id: int, db: Session = Depends(get_db)):
    branch = db.query(models.Branch).get(branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch


@router.put("/branches/{branch_id}", response_model=schemas.BranchOut)
def update_branch(branch_id: int, branch_in: schemas.BranchCreate, db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    branch = db.query(models.Branch).get(branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    branch.name = branch_in.name
    branch.code = branch_in.code
    branch.degree = branch_in.degree
    branch.hod_name = branch_in.hod_name
    branch.duration_years = branch_in.duration_years
    branch.total_semesters = branch_in.total_semesters
    
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


@router.delete("/branches/{branch_id}", status_code=204)
def delete_branch(branch_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    branch = db.query(models.Branch).get(branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    db.delete(branch)
    db.commit()
    return None


@router.get("/branches/{branch_id}/courses", response_model=List[schemas.CourseOut])
def get_branch_courses(branch_id: int, db: Session = Depends(get_db)):
    """Get all courses for a specific branch"""
    return db.query(models.Course).filter(models.Course.branch_id == branch_id).all()

