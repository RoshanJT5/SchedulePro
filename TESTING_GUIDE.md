# PlanSphere Timetable Wizard - Testing Guide

## Overview
This guide walks you through testing the complete timetable creation wizard flow, which includes creating courses, instructors with expertise, classrooms, and timeslots.

## Prerequisites
1. **Database**: PostgreSQL running at `localhost:5432`
   - Database: `plansphere`
   - User: `plansphere`
   - Password: `plansphere`
   - (Or update `.env` with your DB credentials)

2. **Backend**: FastAPI server running
   ```bash
   cd "c:\Users\Roshan Talreja\Desktop\SIH project\PLANSPHERE.AI"
   python -m uvicorn app.main:app --reload --port 8000
   ```
   - The server will auto-create all database tables on first run
   - Visit http://localhost:8000/health to verify it's running

3. **Frontend**: Open the app in your browser
   - http://localhost:8000/ (or http://localhost:8000/index.html)

## Step-by-Step Testing Flow

### Step 1: Login / Registration
1. Open http://localhost:8000/index.html
2. **Register** (Tab 2):
   - Full Name: `John Doe`
   - Email: `john@example.com`
   - Password: `password123`
   - Role: `admin`
   - Click "Register"
3. **Or Login** (Tab 1) if already registered:
   - Email: `john@example.com`
   - Password: `password123`
   - Click "Sign In"
4. **Expected**: Redirected to Dashboard (`/common_layout.html#dashboard`)
5. **Verify**: Token stored in localStorage
   - Open DevTools → Application → Storage → localStorage
   - Look for `plansphere_token` key (should have a JWT value)

### Step 2: Create New Timetable
1. From Dashboard, click **"New Timetable"** button (blue button, top-left)
2. **Expected**: 
   - Browser URL changes to `#timetable-setup-{id}` (e.g., `#timetable-setup-1`)
   - Wizard loads at **Step 1: Basic Info**
   - A new row appears in the `timetables` DB table
3. **Verify in DevTools → Network tab**:
   - POST `/v1/timetables` should return 201 with `{"id": 1, "name": "New Timetable", ...}`

### Step 3: Step 1 - Basic Information
1. Fill in the form:
   - **Timetable Name**: `Fall 2024 Schedule` (required)
   - **Academic Term**: `Fall 2024`
   - **Start Date**: Pick a date (e.g., 2024-09-01)
   - **End Date**: Pick a date (e.g., 2024-12-15)
   - **Default Slot Duration**: 60 (minutes)
2. **Expected**: Form auto-saves as you type
3. Click **"Next →"** button
4. **Expected**: Moves to Step 2 (Courses)

### Step 4: Step 2 - Add Courses
1. Click **"+ Add Course"** button
2. Fill in the Add Course modal:
   - **Course Code**: `CS101` (required)
   - **Course Title**: `Introduction to Programming` (required)
   - **Credits**: `3`
   - **Sessions per Week**: `3`
3. Click **"Save Course"** button
4. **Expected**:
   - Modal closes
   - Course appears in the list below
   - List shows: "CS101: Introduction to Programming | Credits: 3 | Sessions/Week: 3"
5. **Verify in DevTools → Network**:
   - POST `/v1/timetables/{id}/courses` should return 201
6. **Add 2-3 more courses** for completeness
7. Click **"Next →"** button
8. **Expected**: Moves to Step 3 (Instructors)

### Step 5: Step 3 - Add Instructors
1. Click **"+ Add Instructor"** button
2. Fill in the Add Instructor modal:
   - **Name**: `Dr. Alice Johnson` (required)
   - **Email**: `alice@university.edu`
   - **Phone**: `+1-555-0101`
   - **Expertise/Specialization**: `Data Science, Machine Learning, Python` (textarea)
   - **Notes**: `Available for office hours on Tuesdays`
3. Click **"Save Instructor"** button
4. **Expected**:
   - Modal closes
   - Instructor appears in the list with:
     - Name
     - Email and Phone info
     - **Two buttons**: "View Profile" (blue) and "Delete" (red)
5. Click **"View Profile"** button
6. **Expected**: Profile modal opens showing:
   - Name: `Dr. Alice Johnson`
   - Email: `alice@university.edu`
   - Phone: `+1-555-0101`
   - Expertise/Specialization: `Data Science, Machine Learning, Python`
   - Notes: `Available for office hours on Tuesdays`
7. Close the profile modal
8. **Add 2-3 more instructors** for completeness
9. Click **"Next →"** button
10. **Expected**: Moves to Step 4 (Classrooms)

### Step 6: Step 4 - Add Classrooms
1. Click **"+ Add Classroom"** button
2. Fill in the Add Classroom modal:
   - **Room Name**: `A101` (required)
   - **Capacity**: `50`
   - **Room Type**: `Lecture Hall`
   - **Features**: `projector, whiteboard, air conditioning`
3. Click **"Save Classroom"** button
4. **Expected**:
   - Modal closes
   - Classroom appears in the list showing:
     - Room name: `A101`
     - Capacity, Type, and Features
5. **Add 2-3 more classrooms** (e.g., `B205 (Lab)`, `C301 (Seminar)`)
6. Click **"Next →"** button
7. **Expected**: Moves to Step 5 (Timeslots)

### Step 7: Step 5 - Add Timeslots
1. Click **"+ Add Timeslot"** button
2. Fill in the Add Timeslot modal:
   - **Day of Week**: `Monday`
   - **Start Time**: `09:00` (9 AM)
   - **End Time**: `11:00` (11 AM)
   - **Slot Type**: `Lecture`
3. Click **"Save Timeslot"** button
4. **Expected**:
   - Modal closes
   - Timeslot appears in the list: `Monday: 09:00 - 11:00 | Type: Lecture`
5. **Add 5-10 more timeslots** covering the week:
   - Monday 11:00-13:00 (Lecture)
   - Monday 14:00-15:00 (Break)
   - Tuesday 09:00-11:00 (Practical)
   - Wednesday 09:00-11:00 (Lecture)
   - etc.
6. **Expected**: List updates with each addition

### Step 8: Finalize Timetable
1. All steps should now show as "completed" (✓) in the progress indicator
2. Click **"Complete ✓"** button (was "Next →" on Step 5)
3. **Expected**:
   - Status message: "Finalizing timetable..."
   - After ~1 second: "Timetable created successfully!"
   - Redirects to Dashboard (`#dashboard`)

### Step 9: Verify Data Persistence
1. From Dashboard, open DevTools → Application → Storage
2. Check database by running SQL queries (if you have DB access):
   ```sql
   SELECT * FROM timetables;
   SELECT * FROM courses WHERE timetable_id = 1;
   SELECT * FROM timetable_instructors WHERE timetable_id = 1;
   SELECT * FROM timetable_classrooms WHERE timetable_id = 1;
   SELECT * FROM timetable_timeslots WHERE timetable_id = 1;
   ```
3. **Expected**: All data should be saved

## Troubleshooting

### Issue: 401 Unauthorized errors
- **Cause**: Token not being sent or token expired
- **Fix**: 
  - Check DevTools → Application → localStorage for `plansphere_token`
  - Log out and log back in
  - Clear browser cache

### Issue: "Failed to create timetable" on New Timetable click
- **Cause**: Backend API not running or DB issue
- **Fix**:
  - Verify backend is running: `python -m uvicorn app.main:app --reload --port 8000`
  - Check database connectivity
  - Look at server logs for errors

### Issue: Add form doesn't persist (items disappear after refresh)
- **Cause**: DB table doesn't exist or migration not run
- **Fix**:
  - Restart backend (tables should be auto-created)
  - Check DB: `SELECT * FROM information_schema.tables;`
  - Verify new tables exist: `timetables`, `courses`, `timetable_instructors`, etc.

### Issue: "View Profile" button doesn't show or modal is blank
- **Cause**: Expertise field not saved in backend response
- **Fix**:
  - Check backend response in DevTools → Network → add instructor POST
  - Should include: `{"id": ..., "name": ..., "email": ..., "phone": ..., "expertise": ..., "notes": ...}`

### Issue: 304 Not Modified responses
- **Cause**: Browser caching
- **Fix**:
  - Already handled in code (cache: 'no-store', Cache-Control: no-cache)
  - If persists, clear browser cache and restart frontend

## API Endpoints Quick Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/v1/timetables` | Create new timetable |
| GET | `/v1/timetables/{tid}` | Get timetable details |
| POST | `/v1/timetables/{tid}/courses` | Add course to timetable |
| GET | `/v1/timetables/{tid}/courses` | List courses in timetable |
| DELETE | `/v1/timetables/{tid}/courses/{cid}` | Delete course |
| POST | `/v1/timetables/{tid}/instructors` | Add instructor to timetable |
| GET | `/v1/timetables/{tid}/instructors` | List instructors in timetable |
| DELETE | `/v1/timetables/{tid}/instructors/{iid}` | Delete instructor |
| POST | `/v1/timetables/{tid}/classrooms` | Add classroom to timetable |
| GET | `/v1/timetables/{tid}/classrooms` | List classrooms in timetable |
| DELETE | `/v1/timetables/{tid}/classrooms/{cid}` | Delete classroom |
| POST | `/v1/timetables/{tid}/timeslots` | Add timeslot to timetable |
| GET | `/v1/timetables/{tid}/timeslots` | List timeslots in timetable |
| DELETE | `/v1/timetables/{tid}/timeslots/{tid}` | Delete timeslot |

## Success Criteria ✓

- [ ] Login works and token is stored
- [ ] New Timetable button creates timetable and redirects
- [ ] Wizard displays all 5 steps
- [ ] Can add courses with credits
- [ ] Can add instructors with email, phone, expertise
- [ ] Can view instructor profile with full details
- [ ] Can add classrooms with all fields
- [ ] Can add timeslots for each day/time
- [ ] Next/Previous navigation works
- [ ] Completion redirects to dashboard
- [ ] All data persists in database
- [ ] No 304/caching issues
- [ ] No auth errors (401/403)

## Notes

- Database tables are auto-created on app startup (see `app/main.py`)
- All wizard data is scoped to the timetable ID
- User must be authenticated (token required)
- User can only access/modify their own timetables
- Expertise field for instructors is new and stored as TEXT in DB
