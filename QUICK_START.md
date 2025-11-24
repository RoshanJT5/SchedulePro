# PlanSphere Timetable Wizard - Quick Start

## Summary of Changes Implemented ✅

You requested the ability to:
1. ✅ Login and see dashboard
2. ✅ Click "New Timetable" to start wizard
3. ✅ Add courses with credits
4. ✅ Add instructors with email, phone, and expertise
5. ✅ View instructor profiles showing all details
6. ✅ Add classrooms with all fields
7. ✅ Navigate through all steps (1-5)
8. ✅ Finalize and return to dashboard

**All features are now implemented!**

---

## Files Modified

### Backend
1. **app/models.py** - Added `expertise` field to `TimetableInstructor` model
2. **app/api/v1/routes.py** - Updated instructor endpoint to handle expertise field

### Frontend
1. **templates/timetable-setup.html** - Added expertise textarea and instructor profile modal
2. **static/js/timetable-setup.js** - Added instructor profile logic and expertise field handling
3. **templates/dashboard.html** - Already configured (no changes needed)
4. **static/js/app.js** - Already configured (no changes needed)

### Documentation
1. **TESTING_GUIDE.md** - Complete step-by-step testing instructions
2. **IMPLEMENTATION_SUMMARY.md** - Detailed feature documentation

---

## How to Run

### 1. Start Backend
```bash
cd "c:\Users\Roshan Talreja\Desktop\SIH project\PLANSPHERE.AI"
python -m uvicorn app.main:app --reload --port 8000
```

Wait for output:
```
Uvicorn running on http://127.0.0.1:8000
```

### 2. Open Browser
Navigate to: http://localhost:8000/

### 3. Test Flow
- **Register** or **Login**
- Click **"New Timetable"** button
- Fill **Step 1** (Basic Info) → Click **Next**
- Fill **Step 2** (Courses) → Click **Next**
- Fill **Step 3** (Instructors, including expertise & profile viewing) → Click **Next**
- Fill **Step 4** (Classrooms) → Click **Next**
- Fill **Step 5** (Timeslots) → Click **Complete**
- Verify data persisted in database

---

## Key Features

### Courses (Step 2)
- Add multiple courses
- Each course has: Code, Title, Credits, Sessions/Week
- List shows all fields
- Delete individual courses

### Instructors (Step 3) ⭐ NEW
- Add multiple instructors
- Each instructor has:
  - Name (required)
  - Email (optional)
  - Phone (optional)
  - **Expertise/Specialization** (NEW textarea field for detailed expertise)
  - Notes (optional)
- **View Profile button** - Opens modal showing all details
- Delete individual instructors
- Profile modal displays name, email, phone, expertise, notes

### Classrooms (Step 4)
- Add multiple classrooms
- Each classroom has:
  - Room Name (required)
  - Capacity (optional)
  - Room Type (dropdown: lecture, lab, seminar, practical)
  - Features (optional)
- List shows all fields
- Delete individual classrooms

### Timeslots (Step 5)
- Add multiple timeslots
- Each timeslot has:
  - Day of Week (Monday-Friday)
  - Start Time (time picker)
  - End Time (time picker)
  - Slot Type (lecture, break, lunch, practical)
- List shows all fields
- Delete individual timeslots

---

## Database

Tables are automatically created on first run:
- `users` - User accounts
- `timetables` - Main timetable records
- `courses` - Courses per timetable
- `timetable_instructors` - Instructors per timetable (with expertise field)
- `timetable_classrooms` - Classrooms per timetable
- `timetable_timeslots` - Timeslots per timetable
- Plus others for future features

---

## Testing Checklist

- [ ] Backend starts without errors
- [ ] Can register and login
- [ ] Token stored in localStorage as `plansphere_token`
- [ ] Dashboard loads with Welcome message
- [ ] "New Timetable" button creates timetable and redirects to wizard
- [ ] Wizard shows Step 1 with basic info form
- [ ] Can fill basic info and click Next
- [ ] Step 2 shows Add Course button
- [ ] Can add course with credits
- [ ] Course appears in list
- [ ] Can add multiple courses
- [ ] Step 3 shows Add Instructor button
- [ ] Can add instructor with email, phone, expertise
- [ ] Instructor appears in list with View Profile button
- [ ] View Profile button opens modal with all details
- [ ] Can add multiple instructors
- [ ] Step 4 shows Add Classroom button
- [ ] Can add classroom with all fields
- [ ] Classroom appears in list
- [ ] Can add multiple classrooms
- [ ] Step 5 shows Add Timeslot button
- [ ] Can add timeslots
- [ ] Timeslots appear in list
- [ ] Complete button finishes wizard
- [ ] Redirects back to dashboard
- [ ] Data persists in database (check with SQL query)

---

## Troubleshooting

### Issue: 401/403 errors
- Ensure backend is running
- Clear localStorage and login again
- Check that `plansphere_token` is stored after login

### Issue: Add buttons don't work
- Check browser console for errors
- Verify backend is running and responding
- Ensure you're authenticated

### Issue: Data doesn't persist
- Verify PostgreSQL is running
- Check backend logs for database errors
- Ensure new tables were created (check with: `SELECT * FROM timetables;`)

### Issue: Modals don't open
- Check if Tailwind CSS is loaded
- Verify `hidden` class is working properly
- Check browser console for JavaScript errors

---

## API Summary

All endpoints require authentication.

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/v1/timetables` | Create timetable |
| GET | `/v1/timetables/{tid}` | Get timetable |
| POST | `/v1/timetables/{tid}/courses` | Add course |
| GET | `/v1/timetables/{tid}/courses` | List courses |
| DELETE | `/v1/timetables/{tid}/courses/{id}` | Delete course |
| POST | `/v1/timetables/{tid}/instructors` | Add instructor (with expertise) |
| GET | `/v1/timetables/{tid}/instructors` | List instructors |
| DELETE | `/v1/timetables/{tid}/instructors/{id}` | Delete instructor |
| POST | `/v1/timetables/{tid}/classrooms` | Add classroom |
| GET | `/v1/timetables/{tid}/classrooms` | List classrooms |
| DELETE | `/v1/timetables/{tid}/classrooms/{id}` | Delete classroom |
| POST | `/v1/timetables/{tid}/timeslots` | Add timeslot |
| GET | `/v1/timetables/{tid}/timeslots` | List timeslots |
| DELETE | `/v1/timetables/{tid}/timeslots/{id}` | Delete timeslot |

---

## What's Next?

Future enhancements could include:
- Edit existing timetables
- View saved timetables
- AI-based schedule generation
- Conflict detection and resolution
- Export to PDF/Excel
- Schedule sharing and permissions
- Email notifications
- Mobile app

---

## Need Help?

Refer to:
- `TESTING_GUIDE.md` - Detailed step-by-step testing
- `IMPLEMENTATION_SUMMARY.md` - Feature documentation
- Browser DevTools → Console tab for errors
- Backend console output for server errors
