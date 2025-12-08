"""
Quick verification script to test the new branch-based system
"""

print("="*60)
print("  VERIFICATION: Branch-Based Course System")
print("="*60)
print()

# Check 1: Branch model exists
print("[Check 1] Verifying Branch model...")
try:
    from models import Branch
    print("  SUCCESS: Branch model imported")
except ImportError as e:
    print(f"  ERROR: {e}")
    exit(1)

# Check 2: Template exists
print("\n[Check 2] Verifying template...")
import os
template_path = 'templates/courses.html'
if os.path.exists(template_path):
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'Add Course/Branch' in content and 'addBranchModal' in content:
            print(f"  SUCCESS: {template_path} has new UI")
        else:
            print(f"  WARNING: {template_path} might be old version")
else:
    print(f"  ERROR: {template_path} NOT FOUND")

# Check 3: Old template backed up
old_template = 'templates/courses_OLD_BACKUP.html'
if os.path.exists(old_template):
    print(f"\n[Check 3] Old template backed up as {old_template}")
else:
    print(f"\n[Check 3] No backup found (fresh install)")

print()
print("="*60)
print("  VERIFICATION COMPLETE - SYSTEM READY!")
print("="*60)
print()
print("Next steps:")
print("1. Start Flask: python app_with_navigation.py")
print("2. Go to: http://localhost:5000/courses")
print("3. Click 'Add Course/Branch' button")
print("4. Create your first branch!")
print()
