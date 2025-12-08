"""
Debug Data - Show current program/branch/semester values
"""

import os
from flask import Flask
from models import db, Course, StudentGroup
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.config['MONGO_DBNAME'] = os.getenv('MONGO_DBNAME', 'timetable')

db.init_app(app)

with app.app_context():
    print("\n📚 COURSES:")
    print("=" * 80)
    courses = Course.query.all()
    for c in courses:
        print(f"  Code: {c.code:10} | Program: '{c.program}' | Branch: '{c.branch}' | Semester: {c.semester}")
    
    print("\n👥 STUDENT GROUPS:")
    print("=" * 80)
    groups = StudentGroup.query.all()
    for g in groups:
        print(f"  Name: {g.name:15} | Program: '{g.program}' | Branch: '{g.branch}' | Semester: {g.semester}")
    
    print("\n🔍 MATCHING ANALYSIS:")
    print("=" * 80)
    for c in courses:
        matches = [g for g in groups if 
                   g.program == c.program and 
                   g.branch == c.branch and 
                   g.semester == c.semester]
        print(f"  Course {c.code}: {len(matches)} matches - {[g.name for g in matches]}")
