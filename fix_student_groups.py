"""
Fix Student Groups - Set program, branch, and semester based on group names

This script infers the correct values from group names like "CSE-A", "ECE-B", etc.
"""

import os
from flask import Flask
from models import db, StudentGroup
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.config['MONGO_DBNAME'] = os.getenv('MONGO_DBNAME', 'timetable')

db.init_app(app)

# Mapping of branch codes to full names
BRANCH_MAP = {
    'CSE': 'Computer Science',
    'CS': 'Computer Science',
    'ECE': 'Electronics And Communication',
    'EEE': 'Electrical And Electronics',
    'MECH': 'Mechanical Engineering',
    'CIVIL': 'Civil Engineering',
    'CHEM': 'Chemical Engineering',
    'IT': 'Information Technology',
}

with app.app_context():
    print("🔧 Fixing Student Groups...")
    print("=" * 60)
    
    groups = StudentGroup.query.all()
    
    if not groups:
        print("❌ No student groups found!")
        print("\n💡 Create student groups first with:")
        print("   - Program: B.Tech")
        print("   - Branch: Computer Science (or other branch)")
        print("   - Semester: 1-8")
        exit(0)
    
    updates = 0
    
    for group in groups:
        print(f"\nProcessing: {group.name}")
        
        # Set default program if None
        if not group.program or group.program == 'None':
            group.program = 'B.Tech'
            print(f"  ✓ Set program: B.Tech")
        
        # Infer branch from group name
        if not group.branch or group.branch == 'None':
            # Extract branch code from name (e.g., "CSE-A" -> "CSE")
            parts = group.name.split('-')
            if parts:
                branch_code = parts[0].upper()
                branch_name = BRANCH_MAP.get(branch_code, 'Computer Science')
                group.branch = branch_name
                print(f"  ✓ Set branch: {branch_name} (from {branch_code})")
        
        # Set default semester if not set
        if not group.semester or group.semester == 0:
            group.semester = 1
            print(f"  ✓ Set semester: 1")
        
        group.save()
        updates += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Updated {updates} student groups")
    
    # Verify
    print("\n📊 VERIFICATION:")
    print("=" * 60)
    groups = StudentGroup.query.all()
    for g in groups:
        print(f"  {g.name:15} | Program: {g.program:10} | Branch: {g.branch:25} | Semester: {g.semester}")
    
    print("\n✅ Student groups fixed!")
    print("\n💡 Now generate the timetable - courses should match groups!")
