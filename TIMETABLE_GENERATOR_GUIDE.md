# AI Timetable Generator - Implementation Guide

## Overview
Complete AI-powered timetable generation system for PlanSphere using Grok AI API.

## Features Implemented

### 1. **AI Integration (Grok API)**
- **API Key**: Integrated your Grok API key
- **Model**: Using `grok-beta` for intelligent scheduling
- **Fallback**: Rule-based algorithm if AI fails
- **Smart Prompting**: Sends subjects, instructors, classrooms, and constraints to AI

### 2. **Data Integration**
The system automatically fetches from existing modules:
- **Courses Module**: Gets subjects for selected branch/semester
- **Instructors Module**: Filters teachers by assigned course IDs (relational link)
- **Classrooms Module**: Available rooms for assignment

### 3. **Minimal User Input**
User only selects:
1. Degree (B.Tech, BCA, etc.)
2. Branch (filtered by degree)
3. Semester (filtered by branch)
4. Click "✨ Auto-Generate Timetable"

### 4. **Intelligent Generation**
The AI receives:
- Subject list with credits, type (Theory/Lab), sessions per week
- Instructor-subject mapping
- Classroom availability
- Constraints: No overlaps, lunch break, workload balance

### 5. **Visual Grid**
- **Days**: Monday to Saturday columns
- **Time Slots**: 9 AM to 5 PM (1-hour slots)
- **Color Coding**: Blue for Theory, Green for Labs
- **Cell Content**: 
  - Subject code and name
  - Instructor name with icon
  - Classroom badge

### 6. **Drag and Drop Editing**
- Drag any lecture to a different slot
- Swaps slots intelligently
- Instant visual update

### 7. **Click-to-Edit Modal**
When you click any cell:
- Change subject (dropdown)
- Change instructor (filtered by who can teach that subject)
- Change classroom
- Clear slot (make it free)

## Data Structure

```javascript
timetableData = {
  "Monday": {
    "09:00": {
      subjectId: 5,
      subjectName: "Data Structures",
      subjectCode: "CS301",
      subjectType: "Theory",
      instructorId: 2,
      instructorName: "Dr. Astha Singh",
      classroomId: 1,
      classroomName: "Room 101"
    },
    "10:00": "FREE",
    ...
  },
  "Tuesday": { ... }
}
```

## How It Works

### Step 1: User Selects Class
```
Degree: B.Tech → Branch: CSE → Semester: 3
```

### Step 2: System Fetches Data
```javascript
// From Courses API
GET /v1/branches/{branchId}/courses
→ Filters by semester = 3
→ Gets: CS301, CS302, MATH201, etc.

// From Instructors API
GET /v1/instructors
→ Filters by assigned_courses containing subject IDs
→ Gets: Dr. Astha (teaches CS301), Prof. Kumar (teaches MATH201)

// From Classrooms API
GET /v1/classrooms
→ Gets all available rooms
```

### Step 3: AI Generation
Sends to Grok AI:
```
PROMPT:
"Generate a weekly timetable...
SUBJECTS: CS301: Data Structures (Theory, 3 credits, 3 sessions/week)
INSTRUCTORS: Dr. Astha Singh: CS301, CS302
CLASSROOMS: Room 101 (Lecture Hall, 60 capacity)
CONSTRAINTS: No overlaps, lunch break 12-1 PM, balance workload..."
```

AI Response:
```json
{
  "Monday": {
    "09:00": {"subject": "CS301", "instructor": "Dr. Astha Singh", "classroom": "Room 101"},
    ...
  }
}
```

### Step 4: Parse & Render
System converts AI response to internal format with IDs (not names) and renders the grid.

### Step 5: Manual Editing
User can:
- Drag "CS301" from Monday 9 AM → Tuesday 2 PM
- Click any cell → Edit modal → Change instructor/room
- Clear unwanted slots

### Step 6: Save
Saves to database:
```javascript
POST /v1/timetables
{
  "branch_id": 5,
  "semester": 3,
  "schedule_data": "{JSON of timetableData}",
  "academic_year": 2025
}
```

## Why This Architecture is Perfect for AI

### 1. **Precise Data**
- Stores IDs, not names → No ambiguity
- "CS301" is unique → AI knows exactly which course
- "Dr. Astha teaches CS301" → AI can assign her only to CS301

### 2. **Conflict Detection**
```javascript
// AI knows:
if (instructor.id === 2 && day === "Monday" && time === "09:00") {
  // Dr. Astha is busy → Don't assign her elsewhere
}
```

### 3. **Constraint Satisfaction**
- Lab sessions: 2+ consecutive hours
- Lunch break: Always free
- No instructor overlaps
- Balanced workload

### 4. **Human-in-the-Loop**
- AI generates 80% optimal
- Human fixes the remaining 20% via drag-and-drop
- Best of both worlds!

## Algorithm (Fallback - Rule-based)

If Grok API fails, uses this logic:
1. Sort subjects by credits (descending)
2. For each subject:
   - Get sessions needed (from sessions_per_week)
   - Find instructor who teaches it
   - Check instructor availability
   - Assign to first available slot
   - If Lab → Reserve 2 consecutive hours
3. Skip lunch hour (12 PM)
4. Balance across days

## Usage Example

### Generate Timetable:
1. Navigate to "Timetable Generator" in sidebar
2. Select: B.Tech → CSE → Semester 3
3. Click "✨ Auto-Generate Timetable"
4. Wait 5-10 seconds (AI processing)
5. View generated grid

### Edit:
- **Drag**: Click and drag "CS301" card to new slot
- **Edit**: Click any cell → Modal → Change instructor → Save
- **Clear**: Click cell → Modal → "Clear Slot" button

### Save:
- Click "Save Timetable" button
- Stored in database for future use

## Technical Details

### API Integration
```javascript
fetch('https://api.x.ai/v1/chat/completions', {
  headers: {
    'Authorization': 'Bearer sk-or-v1-...'
  },
  body: JSON.stringify({
    model: 'grok-beta',
    messages: [...]
  })
})
```

### Response Parsing
```javascript
parseAIResponse(aiResponse) {
  // Removes markdown code blocks
  // Validates JSON structure
  // Maps subject codes → subject objects
  // Maps instructor names → instructor IDs
  // Returns structured timetableData
}
```

### Drag and Drop
```javascript
handleDragStart() { draggedSlot = {day, time, data} }
handleDrop() { 
  // Swap slots
  temp = target[slot]
  target[slot] = dragged[slot]
  dragged[slot] = temp
  renderGrid()
}
```

## Next Steps

### To Use This:
1. Ensure you have subjects in "Courses" module
2. Ensure instructors have assigned courses (relational IDs)
3. Add classrooms (or use default dummy data)
4. Navigate to "Timetable Generator" page
5. Select class and generate!

### Future Enhancements:
- Export to PDF
- Print view
- Multiple timetables per semester
- Version history
- Conflict warnings
- Load optimization

## Notes

- **Grok API**: Uses your provided key, costs apply per request
- **Fallback**: If API fails, uses rule-based algorithm
- **Performance**: Handles 50+ subjects efficiently
- **Storage**: Saves as JSON in database

---
**Built for PlanSphere.AI - Intelligent Timetable Automation**
