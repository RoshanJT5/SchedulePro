// Instructors Management Module with Relational Course Links
(function() {
    'use strict';

const API_BASE = '/v1';
const TOKEN_KEY = 'plansphere_token';
let instructors = [];
let allCourses = [];  // Cache for all courses from the Courses module
let selectedCourseIds = [];  // IDs of selected courses for current instructor
let currentInstructor = null;
let expertiseTags = [];
let editMode = false;

// Helper to get auth token
function getAuthToken() {
    return localStorage.getItem(TOKEN_KEY);
}

// Helper to get auth headers
function getAuthHeaders() {
    const token = getAuthToken();
    return {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
    };
}

// ==========================================
// RELATIONAL DATA HELPER FUNCTIONS
// ==========================================

/**
 * getAllSubjects() - Fetches and flattens all subjects from the Courses module
 * Returns: Array of subjects with context
 * Format: [{ id, code, name, branchName, semester }, ...]
 */
async function getAllSubjects() {
    try {
        // Fetch all branches
        const branchesResponse = await fetch(`${API_BASE}/branches`);
        if (!branchesResponse.ok) throw new Error('Failed to fetch branches');
        const branches = await branchesResponse.json();
        
        const subjects = [];
        
        // For each branch, fetch its courses
        for (const branch of branches) {
            const coursesResponse = await fetch(`${API_BASE}/branches/${branch.id}/courses`);
            if (coursesResponse.ok) {
                const courses = await coursesResponse.json();
                
                // Add each course with its context
                courses.forEach(course => {
                    subjects.push({
                        id: course.id,
                        code: course.code,
                        name: course.name || course.title,
                        branchName: `${branch.code || branch.name}`,
                        branchDegree: branch.degree,
                        semester: course.semester || 'N/A',
                        subjectType: course.subject_type || 'Theory'
                    });
                });
            }
        }
        
        return subjects;
    } catch (error) {
        console.error('Error fetching subjects:', error);
        return [];
    }
}

/**
 * getSubjectById(subjectId) - Get full subject details by ID
 * Returns: Subject object or null
 */
function getSubjectById(subjectId) {
    return allCourses.find(course => course.id === parseInt(subjectId));
}

/**
 * getInstructorSubjects(instructorId) - Get full subject details for an instructor
 * Returns: Array of subject objects with full details
 */
async function getInstructorSubjects(instructorId) {
    const instructor = instructors.find(i => i.id === instructorId);
    if (!instructor || !instructor.assigned_courses) return [];
    
    let courseIds = [];
    try {
        courseIds = JSON.parse(instructor.assigned_courses);
    } catch (e) {
        courseIds = instructor.assigned_courses.split(',').map(id => id.trim());
    }
    
    // Ensure allCourses is loaded
    if (allCourses.length === 0) {
        allCourses = await getAllSubjects();
    }
    
    return courseIds.map(id => getSubjectById(id)).filter(Boolean);
}

// ==========================================
// INITIALIZATION
// ==========================================

window.initInstructors = async function() {
    console.log('Initializing Instructors Module');
    
    // Load all available courses first
    allCourses = await getAllSubjects();
    console.log(`Loaded ${allCourses.length} courses from Courses module`);
    
    fetchInstructors();
    
    // Search listener
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            renderInstructors(e.target.value, document.getElementById('dept-filter').value);
        });
    }

    // Filter listener
    const deptFilter = document.getElementById('dept-filter');
    if (deptFilter) {
        deptFilter.addEventListener('change', (e) => {
            renderInstructors(document.getElementById('search-input').value, e.target.value);
        });
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        const dropdown = document.getElementById('course-dropdown');
        const searchInput = document.getElementById('course-search-input');
        if (dropdown && !dropdown.contains(e.target) && e.target !== searchInput) {
            dropdown.classList.add('hidden');
        }
    });
};

// Fetch Instructors
async function fetchInstructors() {
    try {
        const response = await fetch(`${API_BASE}/instructors`);
        if (!response.ok) throw new Error('Failed to fetch instructors');
        instructors = await response.json();
        renderInstructors();
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('instructors-container').innerHTML = 
            '<div class="col-span-full text-center text-red-500 py-12">Error loading instructors. Please try again.</div>';
    }
}

// Render Instructors
function renderInstructors(searchTerm = '', deptFilter = '') {
    const container = document.getElementById('instructors-container');
    container.innerHTML = '';

    // Filter instructors
    const filtered = instructors.filter(instructor => {
        const matchesSearch = (
            instructor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (instructor.department && instructor.department.toLowerCase().includes(searchTerm.toLowerCase())) ||
            (instructor.expertise && instructor.expertise.toLowerCase().includes(searchTerm.toLowerCase()))
        );
        const matchesDept = deptFilter ? instructor.department === deptFilter : true;
        return matchesSearch && matchesDept;
    });

    if (filtered.length === 0) {
        container.innerHTML = '<div class="col-span-full text-center text-gray-500 py-12">No instructors found.</div>';
        return;
    }

    // Render Cards
    filtered.forEach(instructor => {
        const card = createInstructorCard(instructor);
        container.appendChild(card);
    });
}

function createInstructorCard(instructor) {
    const div = document.createElement('div');
    div.className = 'bg-white border border-gray-200 rounded-lg shadow-sm p-6 flex flex-col items-center text-center hover:shadow-md transition-shadow';

    // Parse expertise
    let expertise = [];
    try {
        expertise = instructor.expertise ? JSON.parse(instructor.expertise) : [];
    } catch (e) {
        expertise = instructor.expertise ? instructor.expertise.split(',').map(s => s.trim()) : [];
    }

    // Parse assigned courses - now IDs
    let courseIds = [];
    try {
        courseIds = instructor.assigned_courses ? JSON.parse(instructor.assigned_courses) : [];
    } catch (e) {
        courseIds = instructor.assigned_courses ? instructor.assigned_courses.split(',').map(s => s.trim()) : [];
    }

    const coursesCount = courseIds.length;

    // Profile Image
    const profileImage = instructor.profile_image || `https://ui-avatars.com/api/?name=${encodeURIComponent(instructor.name)}&background=2563eb&color=fff&size=128`;

    div.innerHTML = `
        <img src="${profileImage}" alt="${instructor.name}" 
            class="w-24 h-24 rounded-full object-cover mb-4 border-4 border-gray-100"
            onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(instructor.name)}&background=2563eb&color=fff&size=128'">
        <h3 class="font-semibold text-gray-900 text-lg">${instructor.name}</h3>
        <p class="text-sm text-gray-500 mb-4">${instructor.department || 'No Department'} Dept.</p>
        
        <div class="w-full space-y-2 mb-4 text-sm text-gray-600">
            <div class="flex items-center justify-center gap-2">
                <span class="material-symbols-outlined text-gray-400 text-base">mail</span>
                <span class="truncate">${instructor.email || 'No email'}</span>
            </div>
            <div class="flex items-center justify-center gap-2">
                <span class="material-symbols-outlined text-gray-400 text-base">school</span>
                <span>${coursesCount} Course${coursesCount !== 1 ? 's' : ''} Assigned</span>
            </div>
        </div>

        <button onclick="viewProfile(${instructor.id})" 
            class="w-full px-4 py-2 text-sm font-medium text-blue-600 bg-white border border-blue-600 rounded-md hover:bg-blue-50 transition-colors">
            View Profile
        </button>
    `;
    return div;
}

// ==========================================
// COURSE SELECTION DROPDOWN LOGIC
// ==========================================

function showCourseDropdown() {
    populateCourseDropdown('');
    document.getElementById('course-dropdown').classList.remove('hidden');
}

function filterCourses(event) {
    const searchTerm = event.target.value.toLowerCase();
    populateCourseDropdown(searchTerm);
}

function populateCourseDropdown(searchTerm) {
    const optionsContainer = document.getElementById('course-options');
    optionsContainer.innerHTML = '';
    
    const filteredCourses = allCourses.filter(course => {
        if (selectedCourseIds.includes(course.id)) return false; // Don't show already selected
        
        const matchesSearch = (
            course.name.toLowerCase().includes(searchTerm) ||
            course.code.toLowerCase().includes(searchTerm) ||
            course.branchName.toLowerCase().includes(searchTerm)
        );
        return matchesSearch;
    });
    
    if (filteredCourses.length === 0) {
        optionsContainer.innerHTML = '<div class="px-4 py-2 text-sm text-gray-500">No courses found</div>';
        return;
    }
    
    filteredCourses.slice(0, 20).forEach(course => {
        const option = document.createElement('div');
        option.className = 'px-4 py-2 hover:bg-blue-50 cursor-pointer text-sm';
        option.innerHTML = `
            <div class="font-medium text-gray-900">${course.name} (${course.code})</div>
            <div class="text-xs text-gray-500">${course.branchName} - ${course.branchDegree} - Sem ${course.semester}</div>
        `;
        option.onclick = () => selectCourse(course);
        optionsContainer.appendChild(option);
    });
}

function selectCourse(course) {
    if (!selectedCourseIds.includes(course.id)) {
        selectedCourseIds.push(course.id);
        renderSelectedCourses();
        document.getElementById('course-search-input').value = '';
        populateCourseDropdown('');
    }
}

function removeSelectedCourse(courseId) {
    selectedCourseIds = selectedCourseIds.filter(id => id !== courseId);
    renderSelectedCourses();
    populateCourseDropdown(document.getElementById('course-search-input').value.toLowerCase());
}

function renderSelectedCourses() {
    const container = document.getElementById('assigned-courses-tags');
    container.innerHTML = '';
    
    if (selectedCourseIds.length === 0) {
        container.innerHTML = '<p class="text-sm text-gray-400">No courses selected</p>';
        return;
    }
    
    selectedCourseIds.forEach(courseId => {
        const course = getSubjectById(courseId);
        if (!course) return;
        
        const tag = document.createElement('span');
        tag.className = 'inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-700';
        tag.innerHTML = `
            ${course.name} (${course.code})
            <button type="button" onclick="removeSelectedCourse(${courseId})" class="hover:text-green-900">
                <span class="material-symbols-outlined text-sm">close</span>
            </button>
        `;
        container.appendChild(tag);
    });
    
    // Update hidden input with JSON array of IDs
    document.getElementById('assigned-courses-hidden').value = JSON.stringify(selectedCourseIds);
}

// ==========================================
// MODAL & FORM LOGIC
// ==========================================

// Open Add Instructor Modal
function openAddInstructorModal() {
    editMode = false;
    currentInstructor = null;
    expertiseTags = [];
    selectedCourseIds = [];
    document.getElementById('modal-title').textContent = 'Add New Instructor';
    document.getElementById('submit-btn-text').textContent = 'Add Instructor';
    document.getElementById('instructor-form').reset();
    document.getElementById('expertise-tags').innerHTML = '';
    document.getElementById('assigned-courses-tags').innerHTML = '<p class="text-sm text-gray-400">No courses selected</p>';
    document.getElementById('instructor-modal').classList.remove('hidden');
}

// Close Instructor Modal
function closeInstructorModal() {
    document.getElementById('instructor-modal').classList.add('hidden');
    expertiseTags = [];
    selectedCourseIds = [];
}

// Handle Expertise Input (Tag Input)
function handleExpertiseInput(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        const input = event.target;
        const value = input.value.trim();
        
        if (value && !expertiseTags.includes(value)) {
            expertiseTags.push(value);
            renderExpertiseTags();
            input.value = '';
        }
    }
}

function renderExpertiseTags() {
    const container = document.getElementById('expertise-tags');
    container.innerHTML = '';
    
    expertiseTags.forEach((tag, index) => {
        const tagEl = document.createElement('span');
        tagEl.className = 'inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-700';
        tagEl.innerHTML = `
            ${tag}
            <button type="button" onclick="removeExpertiseTag(${index})" class="hover:text-blue-900">
                <span class="material-symbols-outlined text-sm">close</span>
            </button>
        `;
        container.appendChild(tagEl);
    });
    
    // Update hidden input
    document.getElementById('expertise-hidden').value = JSON.stringify(expertiseTags);
}

function removeExpertiseTag(index) {
    expertiseTags.splice(index, 1);
    renderExpertiseTags();
}

// Handle Submit Instructor
async function handleSubmitInstructor(event) {
    event.preventDefault();
    
    // Check if user is logged in
    const token = getAuthToken();
    if (!token) {
        alert('You need to be logged in. Please login first.');
        window.location.href = '/';
        return;
    }

    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());
    
    // Add expertise as JSON string
    data.expertise = JSON.stringify(expertiseTags);
    // Add assigned courses as JSON array of IDs (relational link)
    data.assigned_courses = JSON.stringify(selectedCourseIds);
    
    try {
        const url = editMode ? `${API_BASE}/instructors/${currentInstructor.id}` : `${API_BASE}/instructors`;
        const method = editMode ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: getAuthHeaders(),
            body: JSON.stringify(data)
        });

        if (response.ok) {
            closeInstructorModal();
            fetchInstructors();
            alert(`Instructor ${editMode ? 'updated' : 'added'} successfully!`);
        } else {
            const errorText = await response.text();
            if (response.status === 401) {
                alert('Authentication failed. Please login again.');
                window.location.href = '/';
            } else {
                alert(`Failed to ${editMode ? 'update' : 'add'} instructor: ` + errorText);
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert(`Error ${editMode ? 'updating' : 'adding'} instructor: ` + error.message);
    }
}

// ==========================================
// VIEW PROFILE WITH RELATIONAL DATA
// ==========================================

async function viewProfile(id) {
    const instructor = instructors.find(i => i.id === id);
    if (!instructor) return;

    currentInstructor = instructor;

    // Parse expertise
    let expertise = [];
    try {
        expertise = instructor.expertise ? JSON.parse(instructor.expertise) : [];
    } catch (e) {
        expertise = instructor.expertise ? instructor.expertise.split(',').map(s => s.trim()) : [];
    }

    // Get full subject details using relational link
    const assignedSubjects = await getInstructorSubjects(id);

    // Populate drawer
    const profileImage = instructor.profile_image || `https://ui-avatars.com/api/?name=${encodeURIComponent(instructor.name)}&background=2563eb&color=fff&size=150`;
    document.getElementById('profile-avatar').src = profileImage;
    document.getElementById('profile-name').textContent = instructor.name;
    document.getElementById('profile-designation').textContent = instructor.designation || 'Faculty Member';
    document.getElementById('profile-qualification').textContent = instructor.qualification || 'Not specified';
    document.getElementById('profile-experience').textContent = instructor.experience || 'Not specified';
    document.getElementById('profile-department').textContent = (instructor.department || 'No') + ' Department';
    document.getElementById('profile-email').textContent = instructor.email || 'No email';
    document.getElementById('profile-email').href = `mailto:${instructor.email}`;
    document.getElementById('profile-phone').textContent = instructor.phone || 'No phone';
    document.getElementById('profile-office').textContent = instructor.office_location || 'Not specified';

    // Render expertise tags
    const expertiseContainer = document.getElementById('profile-expertise');
    expertiseContainer.innerHTML = '';
    if (expertise.length > 0) {
        expertise.forEach(tag => {
            const tagEl = document.createElement('span');
            tagEl.className = 'inline-block px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-700';
            tagEl.textContent = tag;
            expertiseContainer.appendChild(tagEl);
        });
    } else {
        expertiseContainer.innerHTML = '<p class="text-sm text-gray-500">No expertise specified</p>';
    }

    // Render courses with relational data (BONUS: clickable to navigate)
    const coursesContainer = document.getElementById('profile-courses');
    coursesContainer.innerHTML = '';
    if (assignedSubjects.length > 0) {
        assignedSubjects.forEach(subject => {
            const courseEl = document.createElement('div');
            courseEl.className = 'flex items-center gap-2 p-2 bg-gray-50 rounded text-sm hover:bg-blue-50 cursor-pointer transition-colors';
            courseEl.innerHTML = `
                <span class="material-symbols-outlined text-blue-600 text-base">book</span>
                <div class="flex-1">
                    <div class="font-medium text-gray-900">${subject.name} (${subject.code})</div>
                    <div class="text-xs text-gray-500">${subject.branchName} - ${subject.branchDegree} - Sem ${subject.semester}</div>
                </div>
            `;
            // BONUS: Navigate to course details on click
            courseEl.onclick = () => navigateToCourse(subject.id);
            coursesContainer.appendChild(courseEl);
        });
    } else {
        coursesContainer.innerHTML = '<p class="text-sm text-gray-500">No courses assigned yet</p>';
    }

    document.getElementById('profile-drawer').classList.remove('hidden');
}

// BONUS: Navigate to course details
function navigateToCourse(courseId) {
    // Navigate to courses page and open the details for this specific course
    window.location.hash = `#courses?courseId=${courseId}`;
    closeProfileDrawer();
}

// Close Profile Drawer
function closeProfileDrawer() {
    document.getElementById('profile-drawer').classList.add('hidden');
}

// Edit Instructor
function editInstructor() {
    if (!currentInstructor) return;

    editMode = true;
    document.getElementById('modal-title').textContent = 'Edit Instructor';
    document.getElementById('submit-btn-text').textContent = 'Update Instructor';
    
    // Populate form
    const form = document.getElementById('instructor-form');
    form.elements['name'].value = currentInstructor.name || '';
    form.elements['email'].value = currentInstructor.email || '';
    form.elements['phone'].value = currentInstructor.phone || '';
    form.elements['department'].value = currentInstructor.department || '';
    form.elements['designation'].value = currentInstructor.designation || '';
    form.elements['qualification'].value = currentInstructor.qualification || '';
    form.elements['experience'].value = currentInstructor.experience || '';
    form.elements['office_location'].value = currentInstructor.office_location || '';
    form.elements['profile_image'].value = currentInstructor.profile_image || '';

    // Parse and set expertise
    try {
        expertiseTags = currentInstructor.expertise ? JSON.parse(currentInstructor.expertise) : [];
    } catch (e) {
        expertiseTags = currentInstructor.expertise ? currentInstructor.expertise.split(',').map(s => s.trim()) : [];
    }
    renderExpertiseTags();

    // Parse and set assigned courses
    try {
        selectedCourseIds = currentInstructor.assigned_courses ? JSON.parse(currentInstructor.assigned_courses) : [];
    } catch (e) {
        selectedCourseIds = [];
    }
    renderSelectedCourses();

    closeProfileDrawer();
    document.getElementById('instructor-modal').classList.remove('hidden');
}

// Delete Instructor
async function deleteInstructor() {
    if (!currentInstructor) return;
    
    if (!confirm(`Are you sure you want to delete ${currentInstructor.name}?`)) return;

    const token = getAuthToken();
    if (!token) {
        alert('You need to be logged in. Please login first.');
        window.location.href = '/';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/instructors/${currentInstructor.id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            closeProfileDrawer();
            fetchInstructors();
            alert('Instructor deleted successfully!');
        } else {
            if (response.status === 401) {
                alert('Authentication failed. Please login again.');
                window.location.href = '/';
            } else {
                alert('Failed to delete instructor');
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting instructor');
    }
}

// Expose functions to global scope for onclick handlers
window.openAddInstructorModal = openAddInstructorModal;
window.closeInstructorModal = closeInstructorModal;
window.handleExpertiseInput = handleExpertiseInput;
window.removeExpertiseTag = removeExpertiseTag;
window.showCourseDropdown = showCourseDropdown;
window.filterCourses = filterCourses;
window.removeSelectedCourse = removeSelectedCourse;
window.handleSubmitInstructor = handleSubmitInstructor;
window.viewProfile = viewProfile;
window.closeProfileDrawer = closeProfileDrawer;
window.editInstructor = editInstructor;
window.deleteInstructor = deleteInstructor;

})(); // End IIFE
