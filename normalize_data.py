"""
Data Normalization Script - Fix Case Sensitivity Issues

This script normalizes the program and branch fields in courses and student groups
to ensure consistent matching during timetable generation.

Run this script once to fix existing data.
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

def normalize_text(text):
    """Normalize text to Title Case for consistency"""
    if not text:
        return text
    return text.strip().title()

with app.app_context():
    print("🔧 Starting data normalization...")
    print("=" * 50)
    
    # Normalize Courses
    print("\n📚 Normalizing Courses...")
    courses = Course.query.all()
    course_updates = 0
    
    for course in courses:
        updated = False
        
        if course.program:
            normalized_program = normalize_text(course.program)
            if normalized_program != course.program:
                print(f"  Course {course.code}: program '{course.program}' → '{normalized_program}'")
                course.program = normalized_program
                updated = True
        
        if course.branch:
            normalized_branch = normalize_text(course.branch)
            if normalized_branch != course.branch:
                print(f"  Course {course.code}: branch '{course.branch}' → '{normalized_branch}'")
                course.branch = normalized_branch
                updated = True
        
        if updated:
            course.save()
            course_updates += 1
    
    print(f"✅ Updated {course_updates} courses")
    
    # Normalize Student Groups
    print("\n👥 Normalizing Student Groups...")
    groups = StudentGroup.query.all()
    group_updates = 0
    
    for group in groups:
        updated = False
        
        if group.program:
            normalized_program = normalize_text(group.program)
            if normalized_program != group.program:
                print(f"  Group {group.name}: program '{group.program}' → '{normalized_program}'")
                group.program = normalized_program
                updated = True
        
        if group.branch:
            normalized_branch = normalize_text(group.branch)
            if normalized_branch != group.branch:
                print(f"  Group {group.name}: branch '{group.branch}' → '{normalized_branch}'")
                group.branch = normalized_branch
                updated = True
        
        if updated:
            group.save()
            group_updates += 1
    
    print(f"✅ Updated {group_updates} student groups")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Normalization Summary:")
    print(f"   - Courses updated: {course_updates}/{len(courses)}")
    print(f"   - Groups updated: {group_updates}/{len(groups)}")
    print("\n✅ Data normalization complete!")
    print("\n💡 Now courses and student groups should match correctly.")
    print("   Generate timetable again to see the results!")
