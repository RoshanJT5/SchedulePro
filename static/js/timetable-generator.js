// AI Timetable Generator with Grok Integration
// PlanSphere.AI - Intelligent Timetable Automation

const API_BASE = '/v1';
const TOKEN_KEY = 'plansphere_token';
// SECURITY: API keys should NEVER be in frontend code
// Grok API calls are now handled by backend endpoint: /v1/generate-timetable-ai

// State Management
let branches = [];
let availableSubjects = [];
let availableInstructors = [];
let availableClassrooms = [];
let timetableData = {};
let currentSelection = { degree: '', branchId: null, semester: null };
let currentEditingSlot = null;

// Time slots configuration
const TIME_SLOTS = [
    '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00'
];

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

// Helper Functions
function getAuthToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function getAuthHeaders() {
    const token = getAuthToken();
    return {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
    };
}

// ==========================================
// INITIALIZATION
// ==========================================

window.initTimetableGenerator = async function() {
    console.log('Initializing AI Timetable Generator');
    
    // Load initial data
    await loadBranches();
    await loadClassrooms();
    
    // Initialize drag and drop
    initializeDragAndDrop();
};

// ==========================================
// DATA LOADING
// ==========================================

async function loadBranches() {
    try {
        const response = await fetch(`${API_BASE}/branches`);
        if (response.ok) {
            branches = await response.json();
            console.log('Loaded branches:', branches);
        }
    } catch (error) {
        console.error('Error loading branches:', error);
    }
}

async function loadClassrooms() {
    try {
        const response = await fetch(`${API_BASE}/classrooms`);
        if (response.ok) {
            availableClassrooms = await response.json();
            console.log('Loaded classrooms:', availableClassrooms);
        }
    } catch (error) {
        console.error('Error loading classrooms:', error);
        // If no classrooms endpoint, create dummy data
        availableClassrooms = [
            { id: 1, name: 'Room 101', capacity: 60, room_type: 'Lecture Hall' },
            { id: 2, name: 'Room 102', capacity: 60, room_type: 'Lecture Hall' },
            { id: 3, name: 'Lab 201', capacity: 40, room_type: 'Computer Lab' },
            { id: 4, name: 'Lab 202', capacity: 40, room_type: 'Computer Lab' },
            { id: 5, name: 'Room 301', capacity: 50, room_type: 'Seminar Hall' }
        ];
    }
}

// ==========================================
// DROPDOWN HANDLERS
// ==========================================

function handleDegreeChange() {
    const degree = document.getElementById('degree-select').value;
    currentSelection.degree = degree;
    
    // Filter branches by degree
    const filteredBranches = branches.filter(b => b.degree === degree);
    
    const branchSelect = document.getElementById('branch-select');
    branchSelect.innerHTML = '<option value="">Select Branch</option>';
    
    filteredBranches.forEach(branch => {
        const option = document.createElement('option');
        option.value = branch.id;
        option.textContent = `${branch.name} (${branch.code})`;
        branchSelect.appendChild(option);
    });
    
    // Reset semester
    document.getElementById('semester-select').innerHTML = '<option value="">Select Semester</option>';
    currentSelection.branchId = null;
    currentSelection.semester = null;
}

function handleBranchChange() {
    const branchId = document.getElementById('branch-select').value;
    currentSelection.branchId = parseInt(branchId);
    
    if (!branchId) return;
    
    // Find branch and populate semesters
    const branch = branches.find(b => b.id === currentSelection.branchId);
    if (!branch) return;
    
    const semesterSelect = document.getElementById('semester-select');
    semesterSelect.innerHTML = '<option value="">Select Semester</option>';
    
    for (let i = 1; i <= (branch.total_semesters || 8); i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = `Semester ${i}`;
        semesterSelect.appendChild(option);
    }
}

// ==========================================
// AI TIMETABLE GENERATION WITH GROK
// ==========================================

async function generateTimetable() {
    // Validate selection
    const semester = document.getElementById('semester-select').value;
    if (!currentSelection.degree || !currentSelection.branchId || !semester) {
        alert('Please select Degree, Branch, and Semester');
        return;
    }
    
    currentSelection.semester = parseInt(semester);
    
    // Show loading
    document.getElementById('loading-overlay').classList.remove('hidden');
    
    try {
        // Step 1: Fetch subjects for this branch and semester
        await loadSubjectsForSemester();
        
        // Step 2: Fetch instructors for these subjects
        await loadInstructorsForSubjects();
        
        // Step 3: Call Grok AI to generate optimal schedule
        await generateScheduleWithAI();
        
        // Step 4: Render the timetable
        renderTimetableGrid();
        
        // Enable save and clear buttons
        document.getElementById('save-btn').disabled = false;
        document.getElementById('clear-btn').disabled = false;
        
    } catch (error) {
        console.error('Error generating timetable:', error);
        alert('Failed to generate timetable. See console for details.');
    } finally {
        document.getElementById('loading-overlay').classList.add('hidden');
    }
}

async function loadSubjectsForSemester() {
    try {
        const response = await fetch(`${API_BASE}/branches/${currentSelection.branchId}/courses`);
        if (!response.ok) throw new Error('Failed to fetch courses');
        
        const allCourses = await response.json();
        
        // Filter by semester
        availableSubjects = allCourses.filter(course => 
            course.semester === currentSelection.semester
        );
        
        console.log(`Loaded ${availableSubjects.length} subjects for semester ${currentSelection.semester}`);
    } catch (error) {
        console.error('Error loading subjects:', error);
        availableSubjects = [];
    }
}

async function loadInstructorsForSubjects() {
    try {
        const response = await fetch(`${API_BASE}/instructors`);
        if (!response.ok) throw new Error('Failed to fetch instructors');
        
        const allInstructors = await response.json();
        
        // Filter instructors who teach these subjects
        const subjectIds = availableSubjects.map(s => s.id);
        
        availableInstructors = allInstructors.filter(instructor => {
            if (!instructor.assigned_courses) return false;
            
            let assignedCourseIds = [];
            try {
                assignedCourseIds = JSON.parse(instructor.assigned_courses);
            } catch (e) {
                return false;
            }
            
            // Check if instructor teaches any of our subjects
            return assignedCourseIds.some(id => subjectIds.includes(parseInt(id)));
        });
        
        console.log(`Found ${availableInstructors.length} instructors for these subjects`);
    } catch (error) {
        console.error('Error loading instructors:', error);
        availableInstructors = [];
    }
}

async function generateScheduleWithAI() {
    // Prepare data for AI generation
    const prompt = buildPromptForGrok();
    
    try {
        // Call our BACKEND endpoint (which securely calls Grok API)
        const response = await fetch(`${API_BASE}/generate-timetable-ai`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                prompt: prompt,
                subjects: availableSubjects,
                instructors: availableInstructors,
                classrooms: availableClassrooms
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Backend AI API Error:', errorText);
            throw new Error('AI generation request failed');
        }
        
        const data = await response.json();
        const aiResponse = data.ai_response || data.content;
        
        console.log('AI Response received from backend:', aiResponse);
        
        // Parse AI response and build timetable
        timetableData = parseAIResponse(aiResponse);
        
    } catch (error) {
        console.error('Error calling AI generation:', error);
        console.log('Falling back to rule-based algorithm...');
        // Fallback to rule-based generation
        timetableData = generateScheduleRuleBased();
    }
}

function buildPromptForGrok() {
    const subjectsInfo = availableSubjects.map(s => 
        `${s.code}: ${s.name} (${s.subject_type}, ${s.credits || 3} credits, ${s.sessions_per_week || 3} sessions/week)`
    ).join('\n');
    
    const instructorsInfo = availableInstructors.map(i => {
        let courses = [];
        try {
            const courseIds = JSON.parse(i.assigned_courses);
            courses = availableSubjects
                .filter(s => courseIds.includes(s.id))
                .map(s => s.code);
        } catch (e) {}
        return `${i.name}: ${courses.join(', ')}`;
    }).join('\n');
    
    const classroomsInfo = availableClassrooms.map(c => 
        `${c.name} (${c.room_type}, capacity: ${c.capacity})`
    ).join('\n');
    
    return `Generate a weekly timetable for a college class.

SUBJECTS:
${subjectsInfo}

INSTRUCTORS:
${instructorsInfo}

CLASSROOMS:
${classroomsInfo}

CONSTRAINTS:
- Days: Monday to Saturday
- Time Slots: 9 AM to 5 PM (1-hour slots)
- No instructor should have overlapping classes
- Lab sessions should be minimum 2 hours consecutive
- Theory classes: 1 hour each
- Lunch break: 12 PM - 1 PM (keep free)
- Balance workload across days

Return a JSON object with this structure:
{
  "Monday": {
    "09:00": {"subject": "CS301", "instructor": "Dr. Astha", "classroom": "Room 101"},
    "10:00": {"subject": "MATH201", ...},
    "11:00": "FREE",
    ...
  },
  "Tuesday": { ... },
  ...
}

USE ONLY the subject codes, instructor names, and classroom names provided above. Return ONLY the JSON object, no explanations.`;
}

function parseAIResponse(aiResponse) {
    try {
        // Remove markdown code blocks if present
        let jsonStr = aiResponse.trim();
        if (jsonStr.startsWith('```json')) {
            jsonStr = jsonStr.replace(/```json\n?/g, '').replace(/```\n?/g, '');
        } else if (jsonStr.startsWith('```')) {
            jsonStr = jsonStr.replace(/```\n?/g, '');
        }
        
        const parsed = JSON.parse(jsonStr);
        
        // Validate and transform the structure
        const timetable = {};
        for (const day of DAYS) {
            if (parsed[day]) {
                timetable[day] = {};
                for (const time of TIME_SLOTS) {
                    const slot = parsed[day][time];
                    if (slot && typeof slot === 'object' && slot.subject) {
                        // Map subject code to full subject object
                        const subject = availableSubjects.find(s => 
                            s.code === slot.subject || s.name === slot.subject
                        );
                        const instructor = availableInstructors.find(i => 
                            i.name === slot.instructor || i.name.includes(slot.instructor)
                        );
                        const classroom = availableClassrooms.find(c => 
                            c.name === slot.classroom
                        );
                        
                        if (subject) {
                            timetable[day][time] = {
                                subjectId: subject.id,
                                subjectName: subject.name,
                                subjectCode: subject.code,
                                subjectType: subject.subject_type,
                                instructorId: instructor?.id || null,
                                instructorName: instructor?.name || 'TBA',
                                classroomId: classroom?.id || null,
                                classroomName: classroom?.name || 'TBA'
                            };
                        }
                    } else {
                        timetable[day][time] = 'FREE';
                    }
                }
            }
        }
        
        return timetable;
    } catch (error) {
        console.error('Error parsing AI response:', error);
        throw error;
    }
}

// Fallback: Rule-based algorithm
function generateScheduleRuleBased() {
    const timetable = {};
    
    // Initialize empty timetable
    DAYS.forEach(day => {
        timetable[day] = {};
        TIME_SLOTS.forEach(time => {
            timetable[day][time] = 'FREE';
        });
    });
    
    // Track instructor usage
    const instructorSchedule = {};
    
    // Assign subjects to slots
    let dayIndex = 0;
    let slotIndex = 0;
    
    availableSubjects.forEach(subject => {
        const sessionsNeeded = subject.sessions_per_week || 3;
        const isLab = subject.subject_type === 'Lab';
        const slotDuration = isLab ? 2 : 1; // Labs take 2 hours
        
        // Find instructor for this subject
        const instructor = availableInstructors.find(i => {
            try {
                const courseIds = JSON.parse(i.assigned_courses || '[]');
                return courseIds.includes(subject.id);
            } catch (e) {
                return false;
            }
        });
        
        // Find available classroom
        const classroom = availableClassrooms[Math.floor(Math.random() * availableClassrooms.length)];
        
        let sessionsAssigned = 0;
        
        while (sessionsAssigned < sessionsNeeded && dayIndex < DAYS.length) {
            const day = DAYS[dayIndex];
            const time = TIME_SLOTS[slotIndex];
            
            // Skip lunch hour
            if (time === '12:00') {
                slotIndex++;
                if (slotIndex >= TIME_SLOTS.length) {
                    slotIndex = 0;
                    dayIndex++;
                }
                continue;
            }
            
            // Check if instructor is free
            const instructorKey = `${instructor?.id}-${day}-${time}`;
            if (!instructorSchedule[instructorKey] && slotIndex + slotDuration <= TIME_SLOTS.length) {
                // Assign this slot
                for (let i = 0; i < slotDuration; i++) {
                    const currentTime = TIME_SLOTS[slotIndex + i];
                    timetable[day][currentTime] = {
                        subjectId: subject.id,
                        subjectName: subject.name,
                        subjectCode: subject.code,
                        subjectType: subject.subject_type,
                        instructorId: instructor?.id || null,
                        instructorName: instructor?.name || 'TBA',
                        classroomId: classroom?.id || null,
                        classroomName: classroom?.name || 'TBA'
                    };
                    
                    // Mark instructor as busy
                    if (instructor) {
                        instructorSchedule[`${instructor.id}-${day}-${currentTime}`] = true;
                    }
                }
                
                sessionsAssigned += slotDuration;
            }
            
            // Move to next slot
            slotIndex++;
            if (slotIndex >= TIME_SLOTS.length) {
                slotIndex = 0;
                dayIndex++;
            }
        }
    });
    
    return timetable;
}

// ==========================================
// TIMETABLE RENDERING
// ==========================================

function renderTimetableGrid() {
    const container = document.getElementById('timetable-grid');
    
    // Update title
    const branch = branches.find(b => b.id === currentSelection.branchId);
    document.getElementById('timetable-title').textContent = 
        `${currentSelection.degree} - ${branch?.name || 'Branch'} - Semester ${currentSelection.semester}`;
    
    // Create grid HTML
    let html = '<div class="grid-container">';
    
    // Header row
    html += '<div class="grid grid-cols-[100px_repeat(6,1fr)] gap-0 border-b-2 border-gray-300">';
    html += '<div class="bg-gray-100 p-3 font-semibold text-gray-700 border-r border-gray-300">Time</div>';
    DAYS.forEach(day => {
        html += `<div class="bg-gray-100 p-3 font-semibold text-gray-700 text-center border-r border-gray-300">${day}</div>`;
    });
    html += '</div>';
    
    // Time slot rows
    TIME_SLOTS.forEach(time => {
        html += '<div class="grid grid-cols-[100px_repeat(6,1fr)] gap-0 border-b border-gray-200">';
        html += `<div class="bg-gray-50 p-3 font-medium text-gray-600 border-r border-gray-300 flex items-center justify-center">${formatTime(time)}</div>`;
        
        DAYS.forEach(day => {
            const slot = timetableData[day]?.[time];
            html += createSlotHTML(day, time, slot);
        });
        
        html += '</div>';
    });
    
    html += '</div>';
    
    container.innerHTML = html;
    
    // Re-initialize drag and drop
    initializeDragAndDrop();
}

function createSlotHTML(day, time, slot) {
    if (!slot || slot === 'FREE') {
        return `<div class="slot-cell free-slot border-r border-gray-200 p-2 min-h-[80px] cursor-pointer hover:bg-gray-50" 
                    data-day="${day}" data-time="${time}" onclick="openEditModal('${day}', '${time}')">
                    <span class="text-gray-400 text-xs">Free</span>
                </div>`;
    }
    
    const typeColor = slot.subjectType === 'Lab' ? 'bg-green-50 border-green-300' : 'bg-blue-50 border-blue-300';
    const dragId = `${day}-${time}`;
    
    return `<div class="slot-cell ${typeColor} border-r border-2 p-2 min-h-[80px] cursor-move hover:shadow-lg transition-shadow"
                data-day="${day}" data-time="${time}" 
                draggable="true" 
                ondragstart="handleDragStart(event)" 
                ondragover="handleDragOver(event)" 
                ondrop="handleDrop(event)"
                onclick="openEditModal('${day}', '${time}')">
                <div class="font-semibold text-gray-900 text-sm mb-1">${slot.subjectCode}</div>
                <div class="text-xs text-gray-700 mb-1">${slot.subjectName}</div>
                <div class="flex items-center gap-1 text-xs text-gray-600 mb-1">
                    <span class="material-symbols-outlined text-xs">person</span>
                    <span>${slot.instructorName}</span>
                </div>
                <div class="flex items-center gap-1">
                    <span class="inline-block px-2 py-0.5 rounded text-xs ${slot.subjectType === 'Lab' ? 'bg-green-200 text-green-800' : 'bg-blue-200 text-blue-800'}">${slot.classroomName}</span>
                </div>
            </div>`;
}

function formatTime(time) {
    const [hour, min] = time.split(':');
    const h = parseInt(hour);
    return `${h > 12 ? h - 12 : h}:${min} ${h >= 12 ? 'PM' : 'AM'}`;
}

// ==========================================
// DRAG AND DROP
// ==========================================

let draggedSlot = null;

function initializeDragAndDrop() {
    // Drag and drop is handled by inline event handlers in the HTML
}

function handleDragStart(event) {
    const cell = event.target.closest('.slot-cell');
    const day = cell.dataset.day;
    const time = cell.dataset.time;
    
    draggedSlot = { day, time, data: timetableData[day][time] };
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/html', cell.innerHTML);
    cell.style.opacity = '0.5';
}

function handleDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    return false;
}

function handleDrop(event) {
    event.stopPropagation();
    event.preventDefault();
    
    const targetCell = event.target.closest('.slot-cell');
    const targetDay = targetCell.dataset.day;
    const targetTime = targetCell.dataset.time;
    
    if (draggedSlot && (draggedSlot.day !== targetDay || draggedSlot.time !== targetTime)) {
        // Swap slots
        const temp = timetableData[targetDay][targetTime];
        timetableData[targetDay][targetTime] = draggedSlot.data;
        timetableData[draggedSlot.day][draggedSlot.time] = temp;
        
        // Re-render
        renderTimetableGrid();
    }
    
    // Reset opacity
    document.querySelectorAll('.slot-cell').forEach(cell => {
        cell.style.opacity = '1';
    });
    
    draggedSlot = null;
    return false;
}

// ==========================================
// EDIT MODAL
// ==========================================

function openEditModal(day, time) {
    currentEditingSlot = { day, time };
    
    const slot = timetableData[day][time];
    
    // Set modal title
    document.getElementById('edit-modal-time').textContent = `${day}, ${formatTime(time)}`;
    
    // Populate subject dropdown
    const subjectSelect = document.getElementById('edit-subject');
    subjectSelect.innerHTML = '<option value="">Free Slot</option>';
    availableSubjects.forEach(subject => {
        const option = document.createElement('option');
        option.value = subject.id;
        option.textContent = `${subject.code} - ${subject.name}`;
        if (slot && slot !== 'FREE' && slot.subjectId === subject.id) {
            option.selected = true;
        }
        subjectSelect.appendChild(option);
    });
    
    // Populate instructor dropdown (filtered by selected subject)
    updateInstructorDropdown(slot && slot !== 'FREE' ? slot.subjectId : null, slot && slot !== 'FREE' ? slot.instructorId : null);
    
    // Populate classroom dropdown
    const classroomSelect = document.getElementById('edit-classroom');
    classroomSelect.innerHTML = '<option value="">Select Classroom</option>';
    availableClassrooms.forEach(classroom => {
        const option = document.createElement('option');
        option.value = classroom.id;
        option.textContent = `${classroom.name} (${classroom.room_type})`;
        if (slot && slot !== 'FREE' && slot.classroomId === classroom.id) {
            option.selected = true;
        }
        classroomSelect.appendChild(option);
    });
    
    // Add subject change listener
    subjectSelect.onchange = () => {
        updateInstructorDropdown(subjectSelect.value, null);
    };
    
    // Show modal
    document.getElementById('edit-slot-modal').classList.remove('hidden');
}

function updateInstructorDropdown(subjectId, selectedInstructorId) {
    const instructorSelect = document.getElementById('edit-instructor');
    instructorSelect.innerHTML = '<option value="">Select Instructor</option>';
    
    if (!subjectId) return;
    
    // Filter instructors who can teach this subject
    const filteredInstructors = availableInstructors.filter(instructor => {
        try {
            const courseIds = JSON.parse(instructor.assigned_courses || '[]');
            return courseIds.includes(parseInt(subjectId));
        } catch (e) {
            return false;
        }
    });
    
    filteredInstructors.forEach(instructor => {
        const option = document.createElement('option');
        option.value = instructor.id;
        option.textContent = instructor.name;
        if (selectedInstructorId && instructor.id === selectedInstructorId) {
            option.selected = true;
        }
        instructorSelect.appendChild(option);
    });
}

function closeEditModal() {
    document.getElementById('edit-slot-modal').classList.add('hidden');
    currentEditingSlot = null;
}

function saveSlotEdit() {
    if (!currentEditingSlot) return;
    
    const { day, time } = currentEditingSlot;
    const subjectId = parseInt(document.getElementById('edit-subject').value);
    const instructorId = parseInt(document.getElementById('edit-instructor').value);
    const classroomId = parseInt(document.getElementById('edit-classroom').value);
    
    if (!subjectId) {
        timetableData[day][time] = 'FREE';
    } else {
        const subject = availableSubjects.find(s => s.id === subjectId);
        const instructor = availableInstructors.find(i => i.id === instructorId);
        const classroom = availableClassrooms.find(c => c.id === classroomId);
        
        timetableData[day][time] = {
            subjectId: subject.id,
            subjectName: subject.name,
            subjectCode: subject.code,
            subjectType: subject.subject_type,
            instructorId: instructor?.id || null,
            instructorName: instructor?.name || 'TBA',
            classroomId: classroom?.id || null,
            classroomName: classroom?.name || 'TBA'
        };
    }
    
    renderTimetableGrid();
    closeEditModal();
}

function clearSlot() {
    if (!currentEditingSlot) return;
    
    const { day, time } = currentEditingSlot;
    timetableData[day][time] = 'FREE';
    
    renderTimetableGrid();
    closeEditModal();
}

// ==========================================
// SAVE & CLEAR
// ==========================================

async function saveTimetable() {
    if (!currentSelection.branchId || !currentSelection.semester) {
        alert('No timetable to save');
        return;
    }
    
    const token = getAuthToken();
    if (!token) {
        alert('You need to be logged in to save timetables');
        window.location.href = '/';
        return;
    }
    
    try {
        // Save to database (you'll need to create this endpoint)
        const response = await fetch(`${API_BASE}/timetables`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                branch_id: currentSelection.branchId,
                semester: currentSelection.semester,
                schedule_data: JSON.stringify(timetableData),
                academic_year: new Date().getFullYear()
            })
        });
        
        if (response.ok) {
            alert('Timetable saved successfully!');
        } else {
            const errorText = await response.text();
            alert('Failed to save timetable: ' + errorText);
        }
    } catch (error) {
        console.error('Error saving timetable:', error);
        alert('Error saving timetable. See console for details.');
    }
}

function clearTimetable() {
    if (!confirm('Are you sure you want to clear the timetable?')) return;
    
    timetableData = {};
    document.getElementById('timetable-grid').innerHTML = `
        <div class="p-12 text-center text-gray-400">
            <span class="material-symbols-outlined text-6xl mb-4">calendar_month</span>
            <p class="text-lg">Select a class and click "Generate" to create a timetable</p>
        </div>
    `;
    
    document.getElementById('save-btn').disabled = true;
    document.getElementById('clear-btn').disabled = true;
}
