import os
import time
from flask import Flask
from models import db
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.config['MONGO_DBNAME'] = os.getenv('MONGO_DBNAME', 'timetable')

db.init_app(app)

with app.app_context():
    print("Creating MongoDB indexes for performance optimization...")
    start = time.time()
    
    try:
        # TimetableEntry indexes - CRITICAL for fast queries
        db._db['timetableentry'].create_index([('student_group', 1)])
        db._db['timetableentry'].create_index([('faculty_id', 1)])
        db._db['timetableentry'].create_index([('time_slot_id', 1)])
        db._db['timetableentry'].create_index([('course_id', 1)])
        db._db['timetableentry'].create_index([('room_id', 1)])
        
        # Compound indexes for common queries
        db._db['timetableentry'].create_index([('student_group', 1), ('time_slot_id', 1)])
        db._db['timetableentry'].create_index([('faculty_id', 1), ('time_slot_id', 1)])
        
        # StudentGroup indexes for fast filtering
        db._db['studentgroup'].create_index([('program', 1)])
        db._db['studentgroup'].create_index([('branch', 1)])
        db._db['studentgroup'].create_index([('semester', 1)])
        db._db['studentgroup'].create_index([('program', 1), ('branch', 1), ('semester', 1)])
        
        # Course indexes for fast filtering
        db._db['course'].create_index([('program', 1)])
        db._db['course'].create_index([('branch', 1)])
        db._db['course'].create_index([('semester', 1)])
        db._db['course'].create_index([('program', 1), ('branch', 1), ('semester', 1)])
        
        # TimeSlot indexes for fast lookups
        db._db['timeslot'].create_index([('day', 1), ('period', 1)])
        
        print(f"✅ Indexes created successfully in {time.time() - start:.2f}s")
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
