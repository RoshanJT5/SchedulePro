# 🔄 COURSE STRUCTURE MIGRATION SPECIFICATION
# Version: 2.0
# Purpose: Complete restructuring of Course management system
# Auto-apply: This file serves as a blueprint for AI agents to understand and implement changes

---

## 📋 MIGRATION OVERVIEW

**Objective:** Restructure the Course model to include comprehensive academic hierarchy

**Current Structure:**
```
Course
├── id (int)
├── code (string)
├── name (string)
├── credits (int)
├── hours_per_week (int)
├── course_type (string: 'lecture' | 'practical')
├── program (string, optional)
├── branch (string, optional)
├── semester (int, optional)
└── required_room_tags (string, optional)
```

**New Enhanced Structure:**
```
Course
├── id (int)
├── code (string) - Unique course code (e.g., "CS101")
├── name (string) - Full course name
├── credits (int) - Credit hours
├── hours_per_week (int) - Weekly contact hours
├── course_type (string) - 'lecture' | 'practical' | 'tutorial'
├── program (string, REQUIRED) - e.g., "B.Tech", "M.Tech", "BCA"
├── branch (string, REQUIRED) - e.g., "Computer Science", "Electronics"
├── semester (int, REQUIRED) - 1-8 for most programs
├── subject_category (string, NEW) - 'core' | 'elective' | 'lab' | 'project'
├── prerequisites (list, NEW) - List of course codes required before this
├── faculty_preference (list, NEW) - Preferred faculty IDs
├── required_room_tags (string) - Tags for room requirements
├── description (string, NEW) - Course description
├── syllabus_url (string, NEW) - Link to syllabus document
└── is_active (boolean, NEW) - Whether course is currently offered
```

---

## 🎯 IMPLEMENTATION ROADMAP

### PHASE 1: DATABASE MODEL UPDATES

**File:** `models.py`

**Action:** Update the `Course` class

```python
class Course(BaseModel):
    """
    Enhanced Course model with complete academic hierarchy.
    
    Attributes:
        id (int): Unique identifier
        code (str): Course code (e.g., "CS101")
        name (str): Full course name
        credits (int): Credit hours
        hours_per_week (int): Weekly contact hours
        course_type (str): Type - 'lecture', 'practical', 'tutorial'
        program (str): Academic program (e.g., "B.Tech", "M.Tech")
        branch (str): Branch/specialization (e.g., "Computer Science")
        semester (int): Semester number (1-8)
        subject_category (str): Category - 'core', 'elective', 'lab', 'project'
        prerequisites (list): List of prerequisite course codes
        faculty_preference (list): Preferred faculty IDs
        required_room_tags (str): Comma-separated room requirement tags
        description (str): Course description
        syllabus_url (str): URL to syllabus document
        is_active (bool): Whether course is currently offered
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # REQUIRED FIELDS (enforce defaults)
        if not hasattr(self, 'program') or not self.program:
            self.program = None  # Will be validated in routes
        if not hasattr(self, 'branch') or not self.branch:
            self.branch = None  # Will be validated in routes
        if not hasattr(self, 'semester'):
            self.semester = None  # Will be validated in routes
        
        # NEW FIELDS (with defaults)
        if not hasattr(self, 'subject_category'):
            self.subject_category = 'core'
        if not hasattr(self, 'prerequisites'):
            self.prerequisites = []
        if not hasattr(self, 'faculty_preference'):
            self.faculty_preference = []
        if not hasattr(self, 'description'):
            self.description = ''
        if not hasattr(self, 'syllabus_url'):
            self.syllabus_url = ''
        if not hasattr(self, 'is_active'):
            self.is_active = True
        
        # EXISTING FIELDS (preserve)
        if not hasattr(self, 'course_type'):
            self.course_type = 'lecture'
        if not hasattr(self, 'required_room_tags'):
            self.required_room_tags = ''

    def to_dict(self):
        """Convert to dictionary for MongoDB storage"""
        d = super().to_dict()
        
        # Ensure all fields are included
        d['program'] = getattr(self, 'program', None)
        d['branch'] = getattr(self, 'branch', None)
        d['semester'] = getattr(self, 'semester', None)
        d['subject_category'] = getattr(self, 'subject_category', 'core')
        d['prerequisites'] = getattr(self, 'prerequisites', [])
        d['faculty_preference'] = getattr(self, 'faculty_preference', [])
        d['description'] = getattr(self, 'description', '')
        d['syllabus_url'] = getattr(self, 'syllabus_url', '')
        d['is_active'] = getattr(self, 'is_active', True)
        
        return d

    def __repr__(self):
        return f'<Course {getattr(self, "code", None)} {getattr(self, "program", "")}-{getattr(self, "branch", "")} Sem-{getattr(self, "semester", "")}>'
    
    def validate(self):
        """Validate required fields"""
        errors = []
        
        if not getattr(self, 'code', None):
            errors.append('Course code is required')
        if not getattr(self, 'name', None):
            errors.append('Course name is required')
        if not getattr(self, 'program', None):
            errors.append('Program is required')
        if not getattr(self, 'branch', None):
            errors.append('Branch is required')
        if not getattr(self, 'semester', None):
            errors.append('Semester is required')
        
        return errors
```

---

### PHASE 2: BACKEND API ROUTES

**File:** `app_with_navigation.py`

**Section:** Course Management Routes

**Updates Required:**

#### 1. GET /courses (List Courses)
```python
@app.route('/courses')
@login_required
def courses():
    """
    Display courses page with enhanced filtering.
    
    Query Parameters:
        - program: Filter by program
        - branch: Filter by branch
        - semester: Filter by semester
        - category: Filter by subject category
        - active_only: Show only active courses
    """
    # Build query with filters
    query = Course.query
    
    # Apply filters from query parameters
    program = request.args.get('program')
    branch = request.args.get('branch')
    semester = request.args.get('semester')
    category = request.args.get('category')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    
    if program:
        query = query.filter_by(program=program)
    if branch:
        query = query.filter_by(branch=branch)
    if semester:
        query = query.filter_by(semester=int(semester))
    if category:
        query = query.filter_by(subject_category=category)
    if active_only:
        query = query.filter_by(is_active=True)
    
    courses = query.all()
    
    # Get unique values for filter dropdowns
    all_courses = Course.query.all()
    programs = sorted(set(c.program for c in all_courses if c.program))
    branches = sorted(set(c.branch for c in all_courses if c.branch))
    semesters = sorted(set(c.semester for c in all_courses if c.semester))
    categories = ['core', 'elective', 'lab', 'project']
    
    # Get all faculty for preference dropdown
    faculty_list = Faculty.query.all()
    
    return render_template('courses.html',
                         courses=courses,
                         programs=programs,
                         branches=branches,
                         semesters=semesters,
                         categories=categories,
                         faculty_list=faculty_list,
                         current_filters={
                             'program': program,
                             'branch': branch,
                             'semester': semester,
                             'category': category,
                             'active_only': active_only
                         })
```

#### 2. POST /courses/add (Add Course)
```python
@app.route('/courses/add', methods=['POST'])
@admin_required
def add_course():
    """
    Add a new course with validation.
    
    Required Fields:
        - code, name, program, branch, semester
    
    Optional Fields:
        - credits, hours_per_week, course_type, subject_category,
          prerequisites, faculty_preference, description, syllabus_url
    """
    try:
        data = request.get_json() or request.form.to_dict()
        
        # Create course instance
        course = Course(
            code=data.get('code'),
            name=data.get('name'),
            credits=int(data.get('credits', 3)),
            hours_per_week=int(data.get('hours_per_week', 3)),
            course_type=data.get('course_type', 'lecture'),
            program=data.get('program'),
            branch=data.get('branch'),
            semester=int(data.get('semester')) if data.get('semester') else None,
            subject_category=data.get('subject_category', 'core'),
            prerequisites=data.get('prerequisites', []),  # Expect list
            faculty_preference=data.get('faculty_preference', []),  # Expect list
            required_room_tags=data.get('required_room_tags', ''),
            description=data.get('description', ''),
            syllabus_url=data.get('syllabus_url', ''),
            is_active=data.get('is_active', True)
        )
        
        # Validate
        errors = course.validate()
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        
        # Check for duplicate code
        existing = Course.query.filter_by(code=course.code).first()
        if existing:
            return jsonify({'success': False, 'error': 'Course code already exists'}), 400
        
        # Save
        db.session.add(course)
        db.session.commit()
        
        invalidate_cache('courses_list')
        
        return jsonify({
            'success': True,
            'id': course.id,
            'message': f'Course {course.code} added successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
```

#### 3. PUT /courses/<id>/update (Update Course)
```python
@app.route('/courses/<int:course_id>/update', methods=['POST', 'PUT'])
@admin_required
def update_course(course_id):
    """Update existing course"""
    try:
        course = Course.query.get_or_404(course_id)
        data = request.get_json() or request.form.to_dict()
        
        # Update fields
        if 'code' in data: course.code = data['code']
        if 'name' in data: course.name = data['name']
        if 'credits' in data: course.credits = int(data['credits'])
        if 'hours_per_week' in data: course.hours_per_week = int(data['hours_per_week'])
        if 'course_type' in data: course.course_type = data['course_type']
        if 'program' in data: course.program = data['program']
        if 'branch' in data: course.branch = data['branch']
        if 'semester' in data: course.semester = int(data['semester'])
        if 'subject_category' in data: course.subject_category = data['subject_category']
        if 'prerequisites' in data: course.prerequisites = data['prerequisites']
        if 'faculty_preference' in data: course.faculty_preference = data['faculty_preference']
        if 'required_room_tags' in data: course.required_room_tags = data['required_room_tags']
        if 'description' in data: course.description = data['description']
        if 'syllabus_url' in data: course.syllabus_url = data['syllabus_url']
        if 'is_active' in data: course.is_active = bool(data['is_active'])
        
        # Validate
        errors = course.validate()
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        
        db.session.add(course)
        db.session.commit()
        
        invalidate_cache('courses_list')
        
        return jsonify({'success': True, 'message': 'Course updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

### PHASE 3: FRONTEND TEMPLATES

**File:** `templates/courses.html`

**Structure:** Complete redesign with enhanced features

```html
{% extends "base.html" %}

{% block title %}Courses - Enhanced Management{% endblock %}

{% block content %}
<div class="container-fluid">
    <!-- Header with Actions -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="bi bi-book"></i> Course Management</h2>
        <div>
            <button class="btn btn-primary" onclick="showAddCourseModal()">
                <i class="bi bi-plus-circle"></i> Add Course
            </button>
            <button class="btn btn-success" onclick="bulkImport()">
                <i class="bi bi-upload"></i> Import CSV
            </button>
            <button class="btn btn-info" onclick="exportCourses()">
                <i class="bi bi-download"></i> Export
            </button>
        </div>
    </div>

    <!-- Enhanced Filters -->
    <div class="card mb-4">
        <div class="card-header">
            <h5><i class="bi bi-funnel"></i> Filters</h5>
        </div>
        <div class="card-body">
            <div class="row g-3">
                <div class="col-md-3">
                    <label class="form-label">Program</label>
                    <select class="form-select" id="filterProgram" onchange="applyFilters()">
                        <option value="">All Programs</option>
                        {% for program in programs %}
                        <option value="{{ program }}" {% if current_filters.program == program %}selected{% endif %}>
                            {{ program }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Branch</label>
                    <select class="form-select" id="filterBranch" onchange="applyFilters()">
                        <option value="">All Branches</option>
                        {% for branch in branches %}
                        <option value="{{ branch }}" {% if current_filters.branch == branch %}selected{% endif %}>
                            {{ branch }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-2">
                    <label class="form-label">Semester</label>
                    <select class="form-select" id="filterSemester" onchange="applyFilters()">
                        <option value="">All Semesters</option>
                        {% for sem in semesters %}
                        <option value="{{ sem }}" {% if current_filters.semester == sem|string %}selected{% endif %}>
                            Semester {{ sem }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-2">
                    <label class="form-label">Category</label>
                    <select class="form-select" id="filterCategory" onchange="applyFilters()">
                        <option value="">All Categories</option>
                        {% for cat in categories %}
                        <option value="{{ cat }}" {% if current_filters.category == cat %}selected{% endif %}>
                            {{ cat|title }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-2">
                    <label class="form-label">Status</label>
                    <div class="form-check form-switch mt-2">
                        <input class="form-check-input" type="checkbox" id="filterActive" 
                               {% if current_filters.active_only %}checked{% endif %}
                               onchange="applyFilters()">
                        <label class="form-check-label" for="filterActive">
                            Active Only
                        </label>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Courses Table -->
    <div class="card">
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Code</th>
                            <th>Name</th>
                            <th>Program</th>
                            <th>Branch</th>
                            <th>Semester</th>
                            <th>Category</th>
                            <th>Type</th>
                            <th>Credits</th>
                            <th>Hours/Week</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for course in courses %}
                        <tr>
                            <td><strong>{{ course.code }}</strong></td>
                            <td>{{ course.name }}</td>
                            <td><span class="badge bg-primary">{{ course.program }}</span></td>
                            <td><span class="badge bg-info">{{ course.branch }}</span></td>
                            <td><span class="badge bg-secondary">Sem {{ course.semester }}</span></td>
                            <td><span class="badge bg-{{ 'success' if course.subject_category == 'core' else 'warning' }}">
                                {{ course.subject_category|title }}
                            </span></td>
                            <td>{{ course.course_type|title }}</td>
                            <td>{{ course.credits }}</td>
                            <td>{{ course.hours_per_week }}</td>
                            <td>
                                {% if course.is_active %}
                                <span class="badge bg-success">Active</span>
                                {% else %}
                                <span class="badge bg-danger">Inactive</span>
                                {% endif %}
                            </td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="editCourse({{ course.id }})">
                                    <i class="bi bi-pencil"></i>
                                </button>
                                <button class="btn btn-sm btn-danger" onclick="deleteCourse({{ course.id }})">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<!-- Add/Edit Course Modal -->
<div class="modal fade" id="courseModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="courseModalTitle">Add Course</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="courseForm">
                    <input type="hidden" id="courseId">
                    
                    <!-- Basic Information -->
                    <h6 class="mb-3">Basic Information</h6>
                    <div class="row g-3 mb-4">
                        <div class="col-md-6">
                            <label class="form-label">Course Code *</label>
                            <input type="text" class="form-control" id="courseCode" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Course Name *</label>
                            <input type="text" class="form-control" id="courseName" required>
                        </div>
                    </div>

                    <!-- Academic Details -->
                    <h6 class="mb-3">Academic Details</h6>
                    <div class="row g-3 mb-4">
                        <div class="col-md-4">
                            <label class="form-label">Program *</label>
                            <select class="form-select" id="courseProgram" required>
                                <option value="">Select Program</option>
                                {% for program in programs %}
                                <option value="{{ program }}">{{ program }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Branch *</label>
                            <select class="form-select" id="courseBranch" required>
                                <option value="">Select Branch</option>
                                {% for branch in branches %}
                                <option value="{{ branch }}">{{ branch }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Semester *</label>
                            <select class="form-select" id="courseSemester" required>
                                <option value="">Select Semester</option>
                                {% for i in range(1, 9) %}
                                <option value="{{ i }}">Semester {{ i }}</option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>

                    <!-- Course Details -->
                    <h6 class="mb-3">Course Details</h6>
                    <div class="row g-3 mb-4">
                        <div class="col-md-3">
                            <label class="form-label">Category</label>
                            <select class="form-select" id="courseCategory">
                                <option value="core">Core</option>
                                <option value="elective">Elective</option>
                                <option value="lab">Lab</option>
                                <option value="project">Project</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Type</label>
                            <select class="form-select" id="courseType">
                                <option value="lecture">Lecture</option>
                                <option value="practical">Practical</option>
                                <option value="tutorial">Tutorial</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Credits</label>
                            <input type="number" class="form-control" id="courseCredits" value="3" min="1">
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Hours/Week</label>
                            <input type="number" class="form-control" id="courseHours" value="3" min="1">
                        </div>
                    </div>

                    <!-- Additional Information -->
                    <h6 class="mb-3">Additional Information</h6>
                    <div class="row g-3 mb-4">
                        <div class="col-md-12">
                            <label class="form-label">Description</label>
                            <textarea class="form-control" id="courseDescription" rows="3"></textarea>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Syllabus URL</label>
                            <input type="url" class="form-control" id="courseSyllabusUrl">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Room Requirements</label>
                            <input type="text" class="form-control" id="courseRoomTags" 
                                   placeholder="e.g., lab, projector">
                        </div>
                    </div>

                    <!-- Status -->
                    <div class="form-check form-switch">
                        <input class="form-check-input" type="checkbox" id="courseActive" checked>
                        <label class="form-check-label" for="courseActive">
                            Course is Active
                        </label>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" onclick="saveCourse()">Save Course</button>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
// Filter application
function applyFilters() {
    const program = document.getElementById('filterProgram').value;
    const branch = document.getElementById('filterBranch').value;
    const semester = document.getElementById('filterSemester').value;
    const category = document.getElementById('filterCategory').value;
    const activeOnly = document.getElementById('filterActive').checked;
    
    const params = new URLSearchParams();
    if (program) params.append('program', program);
    if (branch) params.append('branch', branch);
    if (semester) params.append('semester', semester);
    if (category) params.append('category', category);
    params.append('active_only', activeOnly);
    
    window.location.href = '/courses?' + params.toString();
}

// Show add course modal
function showAddCourseModal() {
    document.getElementById('courseModalTitle').textContent = 'Add Course';
    document.getElementById('courseForm').reset();
    document.getElementById('courseId').value = '';
    new bootstrap.Modal(document.getElementById('courseModal')).show();
}

// Save course
function saveCourse() {
    const courseId = document.getElementById('courseId').value;
    const url = courseId ? `/courses/${courseId}/update` : '/courses/add';
    
    const data = {
        code: document.getElementById('courseCode').value,
        name: document.getElementById('courseName').value,
        program: document.getElementById('courseProgram').value,
        branch: document.getElementById('courseBranch').value,
        semester: parseInt(document.getElementById('courseSemester').value),
        subject_category: document.getElementById('courseCategory').value,
        course_type: document.getElementById('courseType').value,
        credits: parseInt(document.getElementById('courseCredits').value),
        hours_per_week: parseInt(document.getElementById('courseHours').value),
        description: document.getElementById('courseDescription').value,
        syllabus_url: document.getElementById('courseSyllabusUrl').value,
        required_room_tags: document.getElementById('courseRoomTags').value,
        is_active: document.getElementById('courseActive').checked
    };
    
    fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(result => {
        if (result.success) {
            alert('Course saved successfully!');
            location.reload();
        } else {
            alert('Error: ' + (result.error || result.errors.join(', ')));
        }
    })
    .catch(err => alert('Error: ' + err.message));
}

// Edit course
function editCourse(id) {
    fetch(`/courses/${id}`)
        .then(r => r.json())
        .then(course => {
            document.getElementById('courseModalTitle').textContent = 'Edit Course';
            document.getElementById('courseId').value = course.id;
            document.getElementById('courseCode').value = course.code;
            document.getElementById('courseName').value = course.name;
            document.getElementById('courseProgram').value = course.program;
            document.getElementById('courseBranch').value = course.branch;
            document.getElementById('courseSemester').value = course.semester;
            document.getElementById('courseCategory').value = course.subject_category;
            document.getElementById('courseType').value = course.course_type;
            document.getElementById('courseCredits').value = course.credits;
            document.getElementById('courseHours').value = course.hours_per_week;
            document.getElementById('courseDescription').value = course.description || '';
            document.getElementById('courseSyllabusUrl').value = course.syllabus_url || '';
            document.getElementById('courseRoomTags').value = course.required_room_tags || '';
            document.getElementById('courseActive').checked = course.is_active;
            
            new bootstrap.Modal(document.getElementById('courseModal')).show();
        });
}

// Delete course
function deleteCourse(id) {
    if (!confirm('Are you sure you want to delete this course?')) return;
    
    fetch(`/courses/${id}/delete`, {method: 'POST'})
        .then(r => r.json())
        .then(result => {
            if (result.success) {
                alert('Course deleted successfully!');
                location.reload();
            } else {
                alert('Error: ' + result.error);
            }
        });
}
</script>
{% endblock %}
```

---

### PHASE 4: SCHEDULER ALGORITHM UPDATES

**File:** `scheduler.py`

**Updates:** Enhance course matching logic to use new fields

```python
def _eligible_groups_for_course(self, course: Course, groups: List[StudentGroup]):
    """
    Enhanced matching with new course structure.
    
    Matching Rules:
    1. Program must match exactly
    2. Branch must match exactly
    3. Semester must match exactly
    4. Subject category affects priority (core > elective)
    """
    eligible = []
    
    # Get course attributes (now REQUIRED)
    c_prog = getattr(course, 'program', None)
    c_branch = getattr(course, 'branch', None)
    c_sem = getattr(course, 'semester', None)
    c_category = getattr(course, 'subject_category', 'core')
    
    # Validate course has required fields
    if not c_prog or not c_branch or c_sem is None:
        if self.verbose:
            print(f"[MATCH] Course {course.code} missing required fields (P:{c_prog}, B:{c_branch}, S:{c_sem})")
        return []
    
    # Normalize
    c_prog = str(c_prog).strip().lower()
    c_branch = str(c_branch).strip().lower()
    c_sem = int(c_sem)
    
    # Match groups
    for group in groups:
        g_prog = getattr(group, 'program', None)
        g_branch = getattr(group, 'branch', None)
        g_sem = getattr(group, 'semester', None)
        
        if not g_prog or not g_branch or g_sem is None:
            continue
        
        # Normalize
        g_prog = str(g_prog).strip().lower()
        g_branch = str(g_branch).strip().lower()
        g_sem = int(g_sem)
        
        # Exact match required for all three
        if c_prog == g_prog and c_branch == g_branch and c_sem == g_sem:
            eligible.append(group)
    
    if self.verbose and not eligible:
        print(f"[MATCH] Course {course.code} (P:{c_prog}, B:{c_branch}, S:{c_sem}) matched 0 groups")
    
    return eligible
```

---

### PHASE 5: CSV IMPORT/EXPORT TEMPLATES

**New CSV Template Structure:**

```csv
code,name,credits,hours_per_week,course_type,program,branch,semester,subject_category,description,required_room_tags,is_active
CS101,Introduction to Programming,4,4,lecture,B.Tech,Computer Science,1,core,"Basics of programming using Python",projector,true
CS102,Programming Lab,2,4,practical,B.Tech,Computer Science,1,lab,"Hands-on programming practice",lab,true
CS201,Data Structures,4,4,lecture,B.Tech,Computer Science,3,core,"Advanced data structures and algorithms",projector,true
CS301,Machine Learning,3,3,lecture,B.Tech,Computer Science,5,elective,"Introduction to ML concepts",projector,true
```

---

## 📊 MIGRATION CHECKLIST

### Database Layer
- [ ] Update `Course` model in `models.py`
- [ ] Add new fields with defaults
- [ ] Add validation method
- [ ] Update `to_dict()` method
- [ ] Test model creation and retrieval

### Backend API
- [ ] Update GET /courses route with filters
- [ ] Update POST /courses/add with validation
- [ ] Update PUT /courses/<id>/update
- [ ] Add GET /courses/<id> for single course
- [ ] Update DELETE /courses/<id>/delete
- [ ] Update CSV import/export handlers

### Frontend
- [ ] Redesign courses.html template
- [ ] Add enhanced filter UI
- [ ] Create comprehensive add/edit modal
- [ ] Add category badges and status indicators
- [ ] Implement JavaScript for CRUD operations
- [ ] Add bulk import/export buttons

### Scheduler
- [ ] Update `_eligible_groups_for_course()` method
- [ ] Add category-based prioritization
- [ ] Update session building logic
- [ ] Test with new course structure

### Testing
- [ ] Test course creation with all fields
- [ ] Test filtering by program/branch/semester
- [ ] Test timetable generation with new structure
- [ ] Test CSV import/export
- [ ] Verify backward compatibility

---

## 🚀 DEPLOYMENT STEPS

1. **Backup Database**
   ```bash
   mongodump --uri="your_mongodb_uri" --out=backup_$(date +%Y%m%d)
   ```

2. **Update Code**
   - Apply all changes from this specification
   - Run tests

3. **Migrate Existing Data**
   ```python
   # Migration script
   from models import Course, db
   
   courses = Course.query.all()
   for course in courses:
       # Set defaults for new fields
       if not hasattr(course, 'subject_category'):
           course.subject_category = 'core'
       if not hasattr(course, 'is_active'):
           course.is_active = True
       if not hasattr(course, 'prerequisites'):
           course.prerequisites = []
       if not hasattr(course, 'faculty_preference'):
           course.faculty_preference = []
       
       db.session.add(course)
   
   db.session.commit()
   ```

4. **Verify**
   - Check all courses display correctly
   - Test timetable generation
   - Verify filters work

---

## 📝 NOTES FOR AI AGENTS

**When processing this file:**

1. **Read the entire specification** before making changes
2. **Follow the phase order** - Database → Backend → Frontend → Scheduler
3. **Preserve existing functionality** - Don't break current features
4. **Test after each phase** - Ensure changes work before proceeding
5. **Update documentation** - Keep README and comments current

**Key Principles:**
- **Backward Compatibility:** Existing courses should still work
- **Validation:** Always validate required fields
- **User Experience:** Make UI intuitive and responsive
- **Performance:** Maintain fast query performance with proper indexing

---

**END OF SPECIFICATION**
**Version:** 2.0
**Last Updated:** December 9, 2025
