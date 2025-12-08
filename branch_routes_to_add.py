# Backend routes for Branch and Subject Management
# Add these to app_with_navigation.py

'''
# ============================================================================
# BRANCH MANAGEMENT ROUTES
# ============================================================================

@app.route('/branches', methods=['GET'])
@login_required
def get_branches():
    """Get all branches"""
    branches = Branch.query.all()
    return jsonify({
        'success': True,
        'branches': [b.to_dict() for b in branches]
    })


@app.route('/branches/add', methods=['POST'])
@admin_required
def add_branch():
    """Create a new branch/specialization"""
    try:
        data = request.json
        
        # Check if branch code already exists
        existing = Branch.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({
                'success': False,
                'error': f"Branch with code '{data['code']}' already exists"
            }), 400
        
        branch = Branch(
            program=data['program'],
            name=data['name'],
            code=data['code'],
            hod_name=data.get('hod_name', ''),
            duration_years=int(data.get('duration_years', 4)),
            total_semesters=int(data.get('total_semesters', 8))
        )
        
        db.session.add(branch)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Branch created successfully',
            'branch': branch.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/branches/<branch_code>', methods=['GET'])
@login_required
def get_branch(branch_code):
    """Get a specific branch with all its subjects organized by semester"""
    branch = Branch.query.filter_by(code=branch_code).first()
    if not branch:
        return jsonify({'success': False, 'error': 'Branch not found'}), 404
    
    # Get all subjects for this branch
    subjects = Course.query.filter_by(branch=branch.name, program=branch.program).all()
    
    # Organize by semester
    subjects_by_semester = {}
    for semester in range(1, branch.total_semesters + 1):
        semester_subjects = [s for s in subjects if getattr(s, 'semester', None) == semester]
        subjects_by_semester[semester] = [
            {
                'id': s.id,
                'code': s.code,
                'name': s.name,
                'credits': getattr(s, 'credits', 0),
                'course_type': getattr(s, 'course_type', 'theory'),
                'hours_per_week': getattr(s, 'hours_per_week', 0)
            }
            for s in semester_subjects
        ]
    
    return jsonify({
        'success': True,
        'branch': branch.to_dict(),
        'subjects_by_semester': subjects_by_semester
    })


@app.route('/branches/<branch_code>/delete', methods=['POST'])
@admin_required
def delete_branch(branch_code):
    """Delete a branch and all its subjects"""
    try:
        branch = Branch.query.filter_by(code=branch_code).first()
        if not branch:
            return jsonify({'success': False, 'error': 'Branch not found'}), 404
        
        # Delete all subjects in this branch
        Course.query.filter_by(branch=branch.name, program=branch.program).delete()
        
        # Delete the branch
        Branch.query.filter_by(code=branch_code).delete()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Branch and all subjects deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# SUBJECT MANAGEMENT ROUTES (within branches)
# ============================================================================

@app.route('/branches/<branch_code>/subjects/add', methods=['POST'])
@admin_required
def add_subject_to_branch(branch_code):
    """Add a subject to a specific semester of a branch"""
    try:
        # Get the branch
        branch = Branch.query.filter_by(code=branch_code).first()
        if not branch:
            return jsonify({'success': False, 'error': 'Branch not found'}), 404
        
        data = request.json
        semester = int(data['semester'])
        
        # Validate semester is within range
        if semester < 1 or semester > branch.total_semesters:
            return jsonify({
                'success': False,
                'error': f'Semester must be between 1 and {branch.total_semesters}'
            }), 400
        
        # Check if subject code already exists in this branch
        existing = Course.query.filter_by(
            code=data['code'],
            branch=branch.name,
            program=branch.program
        ).first()
        if existing:
            return jsonify({
                'success': False,
                'error': f"Subject with code '{data['code']}' already exists in this branch"
            }), 400
        
        # Create the subject (Course)
        subject = Course(
            code=data['code'],
            name=data['name'],
            program=branch.program,
            branch=branch.name,
            semester=semester,
            credits=int(data.get('credits', 3)),
            course_type=data.get('type', 'theory').lower(),
            hours_per_week=int(data.get('hours_per_week', 3)),
            required_room_tags=data.get('required_room_tags', '')
        )
        
        db.session.add(subject)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Subject added successfully',
            'subject': {
                'id': subject.id,
                'code': subject.code,
                'name': subject.name,
                'semester': subject.semester,
                'credits': subject.credits,
                'course_type': subject.course_type
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/branches/<branch_code>/subjects/<int:subject_id>/delete', methods=['POST'])
@admin_required
def delete_subject_from_branch(branch_code, subject_id):
    """Delete a subject from a branch"""
    try:
        branch = Branch.query.filter_by(code=branch_code).first()
        if not branch:
            return jsonify({'success': False, 'error': 'Branch not found'}), 404
        
        subject = Course.query.get(subject_id)
        if not subject:
            return jsonify({'success': False, 'error': 'Subject not found'}), 404
        
        # Verify subject belongs to this branch
        if subject.branch != branch.name or subject.program != branch.program:
            return jsonify({'success': False, 'error': 'Subject does not belong to this branch'}), 400
        
        Course.query.filter_by(id=subject_id).delete()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Subject deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# UPDATED COURSES VIEW (Now shows branches)
# ============================================================================

@app.route('/courses')
@login_required  
def courses():
    """Main courses page - now shows branches"""
    user = User.query.get(session['user_id'])
    
    # Get all branches
    branches = Branch.query.all()
    
    # Build structure: branch -> semesters -> subjects
    branch_structure = {}
    for branch in branches:
        # Get all subjects for this branch
        subjects = Course.query.filter_by(
            program=branch.program,
            branch=branch.name
        ).all()
        
        # Organize by semester
        subjects_by_semester = {}
        for semester in range(1, branch.total_semesters + 1):
            semester_subjects = [
                s for s in subjects 
                if getattr(s, 'semester', None) == semester
            ]
            subjects_by_semester[semester] = [s.to_dict() for s in semester_subjects]
        
        branch_structure[branch.code] = {
            'branch': branch.to_dict(),
            'subjects_by_semester': subjects_by_semester
        }
    
    return render_template(
        'courses_v2.html',
        branches=branches,
        branch_structure=branch_structure,
        user=user
    )
'''
