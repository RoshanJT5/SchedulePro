# 🎓 Branch-Based Course Management System - Complete Guide

## 📊 Overview

Your AI Timetable Generator now has a **hierarchical course management system** that matches your UI design:

```
Program (e.g., B.Tech)
  └─ Branch (e.g., Computer Science)
      └─ Semester 1
          ├─ Subject: Introduction to Programming (CS101)
          └─ Subject: Mathematics (MATH101)
      └─ Semester 2
          ├─ Subject: Data Structures (CS201)
          └─ ...
```

## 🚀 Quick Start

### 1. If You Have Existing Courses (Migration)

```bash
# Run the migration script to create branches from existing courses
python migrate_to_branches.py
```

This will:
- Scan all existing courses
- Create branches automatically
- Organize courses under their respective branches

### 2. Starting Fresh

Just go to `http://localhost:5000/courses` and start adding branches!

## 📖 User Guide

### Creating a New Branch

1. Navigate to `/courses`
2. Click **"Add Course/Branch"**
3. Fill in the form:
   - **Degree Program**: Select (B.Tech, M.Tech, etc.)
   - **Branch Name**: e.g., "Computer Science"
   - **Branch Code**: e.g., "CSE"
   - **HOD Name**: e.g., "Dr. Smith" (optional)
   - **Duration**: e.g., 4 years
   - **Total Semesters**: e.g., 8
4. Click **"Create"**

### Adding Subjects to a Branch

1. Click on any **branch card** (e.g., "Computer Science")
2. A modal opens showing **Semester 1-8** in the left sidebar
3. Select the semester (e.g., **Semester 3**)
4. Click **"+ Add Subject"**
5. Fill in:
   - **Subject Name**: e.g., "Data Structures"
   - **Subject Code**: e.g., "CS301"
   - **Type**: Theory or Practical
   - **Credits**: e.g., 4
   - **Hours Per Week**: e.g., 3
6. Click **"Add Subject"**

### Managing Subjects

- **View Subjects**: Click branch → Select semester
- **Delete Subject**: Click "Delete" next to any subject
- **Delete Branch**: Hover over branch card → Click trash icon

## 🎯 Timetable Generation (Still Works Perfectly!)

The **genetic algorithm** and **all existing logic** remain **100% intact**.

### How to Generate

1. Go to `/timetable`
2. Select filters:
   - **Program**: B.Tech
   - **Branch**: Computer Science
   - **Semester**: 3
3. Click **"Generate Timetable"**

### What Happens

The system will:
- ✅ Only use courses from **B.Tech → Computer Science → Semester 3**
- ✅ Only assign these courses to **Semester 3 student groups**
- ✅ Apply all constraints (faculty availability, workload, no consecutive duplicates, lab priority, etc.)
- ✅ Use the **genetic algorithm** for optimization

### Semester Matching (Hard Constraint)

The system **enforces strict semester matching**:
- "Data Structures" (Semester 3) will **NEVER** be assigned to Freshman (Semester 1)
- This is checked in the **fitness function** with a **massive penalty (10,000)**
- The genetic algorithm automatically eliminates such combinations

## 🔧 Technical Details

### New Database Model

**Branch Model** (`models.py`):
```python
class Branch(BaseModel):
    program: str              # e.g., "B.Tech"
    name: str                 # e.g., "Computer Science"
    code: str                 # e.g., "CSE" (unique)
    hod_name: str            # e.g., "Dr. Smith"
    duration_years: int      # e.g., 4
    total_semesters: int     # e.g., 8
```

### API Endpoints

**Branch Management:**
- `GET /branches` - List all branches
- `POST /branches/add` - Create branch
- `GET /branches/<code>` - Get branch details with subjects
- `POST /branches/<code>/delete` - Delete branch

**Subject Management:**
- `POST /branches/<code>/subjects/add` - Add subject to semester
- `POST /branches/<code>/subjects/<id>/delete` - Delete subject

### Data Flow

```
User adds branch:
  "B.Tech - Computer Science (CSE)" 
  → Stored in Branch collection

User adds subject:
  "CS301 - Data Structures" to Semester 3
  → Stored in Course collection with:
     - program = "B.Tech"
     - branch = "Computer Science"
     - semester = 3

Timetable generation:
  → Genetic algorithm reads Course collection
  → Enforces semester matching
  → Generates assignments
```

## 🎨 UI Structure

### Main Page (`/courses`)
- Shows all branches grouped by program
- Branch cards display: Name, Code, Duration, Semesters, HOD
- Search and filter by program

### Branch Detail Modal
- **Left sidebar**: Semesters 1-8 (or total_semesters)
- **Main area**: Subjects table for selected semester
- Columns: Code, Subject Name, Type, Credits, Delete

### Add Branch Modal
- Degree Program dropdown
- Branch Name, Code inputs
- HOD Name (optional)
- Duration and Total Semesters spinners

### Add Subject Modal
- Subject Name, Code
- Type dropdown (Theory/Practical)
- Credits spinner
- Hours Per Week

## 🔒 Preserved Features

### ✅ What DIDN'T Change

1. **Genetic Algorithm** - `scheduler.py` untouched
2. **JWT Authentication** - All auth logic intact
3. **Timetable Generation** - Core logic unchanged
4. **Faculty Management** - Works as before
5. **Room Management** - Works as before
6. **Student Groups** - Works as before
7. **All Constraints**:
   - Faculty workload (min/max hours)
   - Lab priority
   - Availability respect
   - No consecutive duplicates
   - Overwork detection

### ✅ New Features

1. **Hierarchical Structure** - Program → Branch → Semester
2. **Semester-Based Organization** - Easy to see subjects by semester
3. **Intuitive UI** - Click branch → See semesters → Manage subjects
4. **Strict Semester Matching** - Courses only assigned to correct semester

## 📝 Example Workflow

### Scenario: Create B.Tech Computer Science

**Step 1: Create Branch**
```
Program: B.Tech
Name: Computer Science
Code: CSE
HOD: Dr. Sarah Johnson
Duration: 4 years
Total Semesters: 8
```

**Step 2: Add Semester 1 Subjects**
```
CS101 - Introduction to Programming (Theory, 4 credits)
MATH101 - Calculus I (Theory, 4 credits)
PHY101 - Physics (Theory, 3 credits)
PHYL101 - Physics Lab (Practical, 1 credit)
```

**Step 3: Add Semester 3 Subjects**
```
CS301 - Data Structures (Theory, 4 credits)
CS302 - Database Management (Theory, 4 credits)
CS303 - Computer Networks (Theory, 3 credits)
CSL301 - DS Lab (Practical, 2 credits)
```

**Step 4: Generate Timetable**
```
Filters:
- Program: B.Tech
- Branch: Computer Science
- Semester: 3

Result:
→ Only CS301, CS302, CS303, CSL301 are scheduled
→ Only for Sem 3 student groups
→ Optimized by genetic algorithm
```

## 🐛 Troubleshooting

### "Branch not found" error
- Make sure the branch code matches exactly
- Check that the branch exists in the database

### Subjects not showing up
- Verify the subject's `program` and `branch` fields match the Branch
- Check the `semester` field is within 1 to `total_semesters`

### Timetable generation issues
- The genetic algorithm works the same as before
- Make sure you have:
  - Student groups with matching program/branch/semester
  - Faculty assigned to courses
  - Rooms configured
  - Time slots created

## 🔗 Related Files

- **models.py** - Branch model definition
- **app_with_navigation.py** - Backend routes
- **templates/courses_v2.html** - Frontend UI
- **scheduler.py** - Timetable generation (unchanged!)
- **migrate_to_branches.py** - Migration script

## 📞 Support

If you encounter any issues:
1. Check the browser console for JavaScript errors
2. Check the Flask logs for backend errors
3. Verify database connection
4. Ensure all models are properly imported

---

**Everything is ready to use!** 🎉

Your branch-based course management system is now live with full timetable generation support!
