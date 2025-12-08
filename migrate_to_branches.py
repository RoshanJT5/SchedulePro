"""
Migration Script: Create Branches from Existing Courses
Run this ONCE if you have existing courses in your database.
"""

from models import db, Course, Branch

def migrate_courses_to_branches():
    print("Starting migration...")
    
    # Get all unique (program, branch) combinations from existing courses
    branch_combinations = {}
    for course in Course.query.all():
        program = getattr(course, 'program', None)
        branch_name = getattr(course, 'branch', None)
        
        if not program or not branch_name:
            continue
        
        key = (program, branch_name)
        if key not in branch_combinations:
            branch_combinations[key] = {
                'courses': [],
                'max_semester': 0
            }
        
        branch_combinations[key]['courses'].append(course)
        semester = getattr(course, 'semester', 0) or 0
        if semester > branch_combinations[key]['max_semester']:
            branch_combinations[key]['max_semester'] = semester
    
    print(f"Found {len(branch_combinations)} unique branches to create")
    
    # Create Branch for each combination
    created_count = 0
    for (program, branch_name), data in branch_combinations.items():
        # Check if branch already exists
        existing = Branch.query.filter_by(program=program, name=branch_name).first()
        if existing:
            print(f"  ✓ Branch already exists: {program} - {branch_name}")
            continue
        
        # Generate code from branch name
        # E.g., "Computer Science" → "CSE"
        #       "Information Technology" → "IT"
        words = branch_name.split()
        if len(words) == 1:
            code = branch_name[:3].upper()
        else:
            code = ''.join([word[0].upper() for word in words if word])
        
        # Ensure code is unique
        base_code = code
        counter = 1
        while Branch.query.filter_by(code=code).first():
            code = f"{base_code}{counter}"
            counter += 1
        
        # Calculate total semesters (use max found, default to 8)
        max_semester = data['max_semester']
        total_semesters = max(max_semester, 8)
        
        # Create the branch
        new_branch = Branch(
            program=program,
            name=branch_name,
            code=code,
            hod_name='',  # Can be filled in manually later
            duration_years=total_semesters // 2,
            total_semesters=total_semesters
        )
        
        db.session.add(new_branch)
        created_count += 1
        print(f"  ✓ Created branch: {program} - {branch_name} (Code: {code}, {total_semesters} semesters)")
    
    # Commit all changes
    db.session.commit()
    
    print(f"\nMigration complete! Created {created_count} branches.")
    print("\nYour existing courses will now appear under their respective branches.")
    print("You can now use the new UI at /courses to manage them.")

if __name__ == '__main__':
    print("="*60)
    print("  COURSE TO BRANCH MIGRATION")
    print("="*60)
    print()
    
    # Safety check
    existing_branches = Branch.query.count()
    if existing_branches > 0:
        print(f"⚠️  WARNING: {existing_branches} branches already exist in the database.")
        response = input("Continue anyway? This might create duplicates. (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            exit(0)
    
    migrate_courses_to_branches()
    
    print()
    print("="*60)
    print("  Next Steps:")
    print("  1. Go to http://localhost:5000/courses")
    print("  2. You should see all your branches organized by program")
    print("  3. Click on any branch to see its subjects by semester")
    print("  4. Edit HOD names and other details as needed")
    print("="*60)
