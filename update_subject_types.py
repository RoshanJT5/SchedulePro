"""
Update existing subjects with default subject_type values
Run this once to set subject_type for existing subjects
"""

import os
from flask import Flask
from models import db, Course
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.config['MONGO_DBNAME'] = os.getenv('MONGO_DBNAME', 'timetable')

db.init_app(app)

with app.app_context():
    print("🔧 Updating subject types for existing courses...")
    print("=" * 60)
    
    courses = Course.query.all()
    updated = 0
    
    for course in courses:
        # Only update if subject_type is None or empty
        if not getattr(course, 'subject_type', None):
            # Set default to 'major' - you can change this logic
            course.subject_type = 'major'
            course.save()
            print(f"  ✓ Updated {course.code} - {course.name} → major")
            updated += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Updated {updated} courses with default subject_type='major'")
    print("\n💡 Now refresh the courses page to see the Subject Type column!")
    print("\nYou can edit individual subjects later to set them to:")
    print("  - major, minor, md, ae, se, or va")
