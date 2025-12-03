from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, session, flash, abort, g, make_response
from celery import Celery
from cache import cache_response, invalidate_cache
from auth_jwt import create_tokens, decode_token, revoke_token, is_token_revoked
from models import db, Course, Faculty, Room, Student, TimeSlot, TimetableEntry, User, PeriodConfig, BreakConfig, StudentGroup, get_next_id
from scheduler import TimetableGenerator
from functools import wraps
import time
from pyinstrument import Profiler
import csv
import io
from datetime import datetime
import json
import secrets
import math
import os

from csv_processor import process_upload_stream, get_missing_columns
from pymongo.errors import DuplicateKeyError as IntegrityError
import warnings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Suppress MongoDB schema migration warnings
warnings.filterwarnings('ignore', message='ensure_column skipped for MongoDB')

def time_to_minutes(time_str):
    """Convert time string (HH:MM) to minutes since midnight"""
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

def minutes_to_time(minutes):
    """Convert minutes since midnight to time string (HH:MM)"""
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def ensure_column(table_name, column_name, ddl):
    # Schema migrations / ALTER TABLE are not applicable for MongoDB.
    # This is a no-op when running with Mongo backend.
    warnings.warn(f"ensure_column skipped for MongoDB: {table_name}.{column_name}")

def hydrate_default_faculty_values():
    updated = False
    for faculty in Faculty.query.all():
        if faculty.min_hours_per_week is None:
            faculty.min_hours_per_week = 4
            updated = True
        if faculty.max_hours_per_week is None:
            faculty.max_hours_per_week = 16
            updated = True
        if not faculty.availability:
            faculty.availability = "{}"
            updated = True
    if updated:
        db.session.commit()

def validate_faculty_availability(availability_data):
    """
    Validates that faculty is available for at least 70% of total periods.
    Returns (is_valid, error_message, availability_percentage)
    """
    # Get period configuration
    period_config = PeriodConfig.query.first()
    if not period_config:
        # Use default values if no config exists
        periods_per_day = 8
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    else:
        periods_per_day = period_config.periods_per_day
        days_of_week = [d.strip() for d in period_config.days_of_week.split(',')]
    
    total_periods = periods_per_day * len(days_of_week)
    min_required_periods = math.ceil(total_periods * 0.70)  # 70% threshold
    
    # Parse availability data
    if isinstance(availability_data, str):
        try:
            availability_data = json.loads(availability_data)
        except:
            availability_data = {}
    
    # Count available periods
    available_periods = 0
    for day in days_of_week:
        if day in availability_data:
            available_periods += len(availability_data[day])
    
    availability_percentage = (available_periods / total_periods * 100) if total_periods > 0 else 0
    
    if available_periods < min_required_periods:
        error_msg = f"Faculty must be available for at least 70% of periods. Currently available for {available_periods}/{total_periods} periods ({availability_percentage:.1f}%). Minimum required: {min_required_periods} periods."
        return False, error_msg, availability_percentage
    
    return True, None, availability_percentage

def create_faculty_profile(payload):
    username = payload.get('username', '').strip() or None
    raw_password = payload.get('password', '').strip()
    generated_password = None

    user = None
    if username:
        existing_faculty = Faculty.query.filter_by(username=username).first()
        if existing_faculty:
            raise ValueError('Username already assigned to another faculty profile.')
        user = User.query.filter_by(username=username).first()
        if user:
            user.role = 'teacher'
            user.name = payload['name']
            if raw_password:
                user.set_password(raw_password)
        else:
            password_to_use = raw_password or secrets.token_urlsafe(8)
            generated_password = None if raw_password else password_to_use
            email = payload.get('email') or f'{username}@faculty.local'
            email = email.strip()
            existing_email_user = User.query.filter_by(email=email).first()
            if existing_email_user:
                email = f'{username}+{secrets.token_hex(3)}@faculty.local'
            user = User(username=username, email=email, role='teacher', name=payload['name'])
            user.set_password(password_to_use)
            db.session.add(user)
            db.session.flush()

    availability_payload = payload.get('availability', '{}')
    # Sanitize availability: allow dict/list -> JSON; else ensure string JSON object
    if isinstance(availability_payload, (dict, list)):
        availability_payload = json.dumps(availability_payload)
    elif not isinstance(availability_payload, str):
        availability_payload = '{}'

    expertise_payload = normalize_comma_list(payload.get('expertise', []))

    faculty = Faculty(
        name=payload['name'],
        email=payload.get('email', ''),
        expertise=','.join(expertise_payload),
        availability=availability_payload,
        username=username,
        min_hours_per_week=int(payload.get('min_hours_per_week', 4)),
        max_hours_per_week=int(payload.get('max_hours_per_week', 16)),
        user_id=user.id if user else None
    )
    db.session.add(faculty)
    return faculty, generated_password

def parse_int(value, default=0):
    try:
        return int(value) if value not in (None, '', 'nan') else default
    except (TypeError, ValueError):
        return default

def normalize_comma_list(value):
    if not value or value == 'nan':
        return []
    if isinstance(value, list):
        return value
    return [item.strip() for item in str(value).split(',') if item.strip()]


# Navigation flow for guided setup
def get_next_page(current_page):
    """Get the next page URL in the navigation flow for admin guided setup"""
    navigation_map = {
        'courses': '/faculty',
        'faculty': '/rooms',
        'rooms': '/students',
        'students': '/student-groups',
        'student-groups': '/settings',
        'settings': '/timetable',
        'timetable': None  # Last step
    }
    return navigation_map.get(current_page)

def get_progress_steps(current_page):
    """Get list of all steps with current step marked"""
    steps = [
        {'name': 'courses', 'title': 'Courses', 'icon': 'book'},
        {'name': 'faculty', 'title': 'Faculty', 'icon': 'person-badge'},
        {'name': 'rooms', 'title': 'Rooms', 'icon': 'building'},
        {'name': 'students', 'title': 'Students', 'icon': 'people'},
        {'name': 'student-groups', 'title': 'Groups', 'icon': 'people-fill'},
        {'name': 'settings', 'title': 'Settings', 'icon': 'gear'},
        {'name': 'timetable', 'title': 'Timetable', 'icon': 'calendar-week'}
    ]
    
    current_index = next((i for i, s in enumerate(steps) if s['name'] == current_page), -1)
    
    for i, step in enumerate(steps):
        if i < current_index:
            step['status'] = 'completed'
        elif i == current_index:
            step['status'] = 'active'
        else:
            step['status'] = 'pending'
    
    return steps





def generate_time_slots():
    """Generate time slots based on PeriodConfig and BreakConfig"""
    # Clear existing time slots efficiently
    TimeSlot.query.delete()
    
    # Get period configuration
    period_config = PeriodConfig.query.first()
    if not period_config:
        # Use defaults if no config exists
        period_config = PeriodConfig(
            periods_per_day=8,
            period_duration_minutes=60,
            day_start_time='09:00',
            days_of_week='Monday,Tuesday,Wednesday,Thursday,Friday'
        )
        db.session.add(period_config)
        db.session.commit()
    
    # Get break configurations, ordered by after_period
    breaks = BreakConfig.query.order_by(BreakConfig.after_period).all()
    break_map = {br.after_period: br for br in breaks}
    
    days = [d.strip() for d in period_config.days_of_week.split(',')]
    start_minutes = time_to_minutes(period_config.day_start_time)
    period_duration = period_config.period_duration_minutes
    
    # Prepare list for bulk insert
    slots_data = []
    
    for day in days:
        current_time = start_minutes
        for period_num in range(1, period_config.periods_per_day + 1):
            # Calculate period start and end
            period_start = current_time
            period_end = period_start + period_duration
            
            # Create time slot dict
            slots_data.append({
                'day': day,
                'period': period_num,
                'start_time': minutes_to_time(period_start),
                'end_time': minutes_to_time(period_end)
            })
            
            # Move to next period start (after this period ends)
            current_time = period_end
            
            # Check if there's a break after this period
            if period_num in break_map:
                break_config = break_map[period_num]
                current_time += break_config.duration_minutes
    
    if slots_data:
        # Bulk allocate IDs
        count = len(slots_data)
        counters = db._db['__counters__']
        res = counters.find_one_and_update(
            {'_id': 'timeslot'}, 
            {'$inc': {'seq': count}}, 
            upsert=True, 
            return_document=True
        )
        end_seq = int(res['seq'])
        start_seq = end_seq - count + 1
        
        # Assign IDs
        for i, slot in enumerate(slots_data):
            slot['id'] = start_seq + i
            
        # Bulk insert
        db._db['timeslot'].insert_many(slots_data)
        print(f"[Performance] Bulk inserted {count} time slots.")


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        broker=app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timetable.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Load configuration from environment variables
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.config['MONGO_DBNAME'] = os.getenv('MONGO_DBNAME', 'timetable')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')

# Profiling Middleware
@app.before_request
def before_request():
    request._start_time = time.time()
    
    if 'profile' in request.args:
        g.profiler = Profiler()
        g.profiler.start()

@app.after_request
def after_request(response):
    # Timing Log
    if hasattr(request, '_start_time'):
        elapsed = time.time() - request._start_time
        # Log to console/file
        app.logger.info(f"[{request.remote_addr}] {request.method} {request.path} {elapsed:.3f}s")
        
        # Add header
        response.headers["X-Response-Time"] = f"{elapsed:.3f}s"

    # Profiler Report
    if hasattr(g, 'profiler'):
        g.profiler.stop()
        output_html = g.profiler.output_html()
        return make_response(output_html)
        
    return response

# Celery Configuration
app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery = make_celery(app)

@celery.task(bind=True)
def generate_timetable_task(self):
    """Background task to generate timetable"""
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Initializing generation...'})
        
        # Clear existing timetable
        TimetableEntry.query.delete()
        db.session.commit()
        
        self.update_state(state='PROGRESS', meta={'status': 'Running algorithm...'})
        
        # Generate new timetable
        generator = TimetableGenerator(db)
        result = generator.generate()
        
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}
# Initialize our MongoDB-backed db compatibility layer
db.init_app(app)

# Inject `next_page` into all templates based on a fixed navigation order.
@app.context_processor
def inject_next_page():
    try:
        path = request.path or '/'
    except RuntimeError:
        # No request context; return nothing
        return {'next_page': None}

    # Define the linear navigation order for the Next button
    navigation_order = ['/', '/courses', '/faculty', '/rooms', '/students', '/student-groups', '/settings', '/timetable']

    # Exact match
    if path in navigation_order:
        idx = navigation_order.index(path)
        if idx < len(navigation_order) - 1:
            return {'next_page': navigation_order[idx + 1]}
        return {'next_page': None}

    # Handle subpaths like /courses/add or /faculty/123 by matching prefix
    for i, p in enumerate(navigation_order):
        if p != '/' and path.startswith(p + '/'):
            if i < len(navigation_order) - 1:
                return {'next_page': navigation_order[i + 1]}
            return {'next_page': None}

    return {'next_page': None}

# Initialize database
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        # If there's a schema mismatch, drop and recreate
        print(f"Database schema mismatch detected: {e}")
        print("Dropping and recreating database...")
        db.drop_all()
        db.create_all()
    
    # Create default period config if it doesn't exist (singleton enforced)
    if PeriodConfig.query.count() == 0:
        period_config = PeriodConfig(
            id=1,
            periods_per_day=8,
            period_duration_minutes=60,
            day_start_time='09:00',
            days_of_week='Monday,Tuesday,Wednesday,Thursday,Friday'
        )
        db.session.add(period_config)
        db.session.commit()
    
    # Create default break configs if they don't exist
    if BreakConfig.query.count() == 0:
        breaks = [
            BreakConfig(break_name='Short Break', after_period=2, duration_minutes=15, order=1),
            BreakConfig(break_name='Lunch Break', after_period=4, duration_minutes=60, order=2),
            BreakConfig(break_name='Short Break', after_period=6, duration_minutes=15, order=3)
        ]
        for br in breaks:
            db.session.add(br)
        db.session.commit()
    
    # Generate time slots based on config if they don't exist
    if TimeSlot.query.count() == 0:
        generate_time_slots()
    
    # Create default admin user if it doesn't exist
    if User.query.filter_by(username='admin').first() is None:
        admin = User(username='admin', email='admin@college.edu', role='admin', name='Administrator')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

    # Ensure new schema columns exist
    ensure_column('course', 'branch', 'VARCHAR(100)')
    ensure_column('course', 'required_room_tags', 'VARCHAR(255)')
    ensure_column('faculty', 'username', 'VARCHAR(80)')
    ensure_column('faculty', 'min_hours_per_week', 'INTEGER')
    ensure_column('faculty', 'max_hours_per_week', 'INTEGER')
    ensure_column('faculty', 'user_id', 'INTEGER')
    ensure_column('room', 'tags', 'VARCHAR(255)')
    ensure_column('student', 'username', 'VARCHAR(80)')
    ensure_column('student', 'user_id', 'INTEGER')
    ensure_column('student_group', 'total_students', 'INTEGER')
    ensure_column('student_group', 'batches', 'TEXT')

    hydrate_default_faculty_values()

def get_current_user():
    """Get the current user from session or JWT"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    if hasattr(g, 'user_id'):
        return User.query.get(g.user_id)
    return None

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check Session
        if 'user_id' in session:
            return f(*args, **kwargs)
            
        # Check JWT
        token = request.cookies.get('access_token')
        if token:
            payload = decode_token(token)
            if payload and payload['type'] == 'access':
                g.user_id = int(payload['sub'])
                g.user_role = payload['role']
                return f(*args, **kwargs)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return redirect(url_for('login'))
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check Session
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if not user or user.role != 'admin':
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                    return jsonify({'success': False, 'error': 'Access denied. Admin privileges required.'}), 403
                flash('Access denied. Admin privileges required.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)

        # Check JWT
        token = request.cookies.get('access_token')
        if token:
            payload = decode_token(token)
            if payload and payload['type'] == 'access':
                if payload['role'] == 'admin':
                    g.user_id = int(payload['sub'])
                    g.user_role = payload['role']
                    return f(*args, **kwargs)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'Access denied. Admin privileges required.'}), 403
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('login'))
    return decorated_function

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Save user in case password was migrated from Werkzeug to bcrypt
            user.save()
            
            # Create JWTs
            access_token, refresh_token = create_tokens(user.id, user.role)
            
            # Set Session (Legacy support)
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['name'] = user.name
            
            flash(f'Welcome back, {user.name}!', 'success')
            
            resp = make_response(redirect(url_for('index')))
            
            # Set Cookies (HttpOnly, Secure if HTTPS)
            is_secure = request.scheme == 'https'
            resp.set_cookie('access_token', access_token, httponly=True, secure=is_secure, samesite='Lax', max_age=15*60)
            resp.set_cookie('refresh_token', refresh_token, httponly=True, secure=is_secure, samesite='Lax', max_age=7*24*60*60)
            
            return resp
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        name = request.form.get('name')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('register.html')
        
        user = User(username=username, email=email, role=role, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/refresh', methods=['POST'])
def refresh():
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return jsonify({'message': 'Missing refresh token'}), 401
        
    payload = decode_token(refresh_token)
    if not payload or payload['type'] != 'refresh':
        return jsonify({'message': 'Invalid refresh token'}), 401
        
    # Rotate tokens: Revoke old refresh token
    revoke_token(payload['jti'], 7*24*60*60)
    
    new_access, new_refresh = create_tokens(payload['sub'], payload['role'])
    
    resp = make_response(jsonify({'message': 'Token refreshed'}))
    is_secure = request.scheme == 'https'
    resp.set_cookie('access_token', new_access, httponly=True, secure=is_secure, samesite='Lax', max_age=15*60)
    resp.set_cookie('refresh_token', new_refresh, httponly=True, secure=is_secure, samesite='Lax', max_age=7*24*60*60)
    
    return resp

@app.route('/logout')
def logout():
    try:
        # Revoke tokens if present
        access_token = request.cookies.get('access_token')
        refresh_token = request.cookies.get('refresh_token')
        
        if access_token:
            try:
                payload = decode_token(access_token)
                if payload:
                    revoke_token(payload['jti'], 15*60)
            except Exception:
                pass
                
        if refresh_token:
            try:
                payload = decode_token(refresh_token)
                if payload:
                    revoke_token(payload['jti'], 7*24*60*60)
            except Exception:
                pass

        session.clear()
        flash('You have been logged out', 'info')
        resp = make_response(redirect(url_for('login')))
        resp.delete_cookie('access_token')
        resp.delete_cookie('refresh_token')
        return resp
    except Exception as e:
        print(f"Logout error: {e}")
        session.clear()
        return redirect(url_for('login'))


@app.route('/download-template/<entity>')
@admin_required
def download_template(entity):
    """Generate a CSV or Excel template for courses, faculty, rooms, students, or student-groups and send as attachment.
    Usage: /download-template/courses?format=csv or ?format=xlsx
    """
    fmt = (request.args.get('format') or 'csv').lower()
    if entity not in ('courses', 'faculty', 'rooms', 'students', 'student-groups'):
        abort(404)

    if entity == 'courses':
        columns = ['code', 'name', 'credits', 'hours_per_week', 'course_type', 'branch', 'required_room_tags']
        filename_base = 'courses_template'
    elif entity == 'faculty':
        columns = ['name', 'username', 'email', 'expertise', 'password', 'min_hours_per_week', 'max_hours_per_week', 'availability']
        filename_base = 'faculty_template'
    elif entity == 'rooms':
        columns = ['name', 'capacity', 'room_type', 'equipment', 'tags']
        filename_base = 'rooms_template'
    elif entity == 'students':
        columns = ['student_id', 'name', 'username', 'password', 'enrolled_courses']
        filename_base = 'students_template'
    elif entity == 'student-groups':
        columns = ['name', 'description', 'total_students', 'batches', 'batches_students']
        filename_base = 'student_groups_template'

    if fmt == 'csv':
        # Create CSV in-memory
        output = io.StringIO()
        import csv as _csv
        writer = _csv.writer(output)
        writer.writerow(columns)
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8'))
        mem.seek(0)
        return send_file(mem, mimetype='text/csv', as_attachment=True, download_name=f"{filename_base}.csv")

    elif fmt in ('xls', 'xlsx'):
        # Use pandas to create an Excel file in-memory. Try available engines.
        df = pd.DataFrame(columns=columns)
        mem = io.BytesIO()
        engines_to_try = ['xlsxwriter', 'openpyxl']
        writer_used = None
        for eng in engines_to_try:
            try:
                with pd.ExcelWriter(mem, engine=eng) as writer:
                    df.to_excel(writer, index=False, sheet_name='Template')
                writer_used = eng
                break
            except ModuleNotFoundError:
                # try next engine
                mem.seek(0)
                mem.truncate(0)
                continue

        if not writer_used:
            # Fallback: return CSV if no excel engine is available
            output = io.StringIO()
            import csv as _csv
            writer = _csv.writer(output)
            writer.writerow(columns)
            mem2 = io.BytesIO()
            mem2.write(output.getvalue().encode('utf-8'))
            mem2.seek(0)
            return send_file(mem2, mimetype='text/csv', as_attachment=True, download_name=f"{filename_base}.csv")

        mem.seek(0)
        return send_file(mem, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f"{filename_base}.xlsx")

    else:
        # Unsupported format
        return jsonify({'success': False, 'error': 'Unsupported format'}), 400

# Health Check Endpoint (for load balancers, Docker, monitoring)
@app.route('/health')
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns 200 OK if application is healthy.
    """
    try:
        # Check database connectivity
        db._db.command('ping')
        
        return jsonify({
            'status': 'healthy',
            'service': 'AI Timetable Generator',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'AI Timetable Generator',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/')
@login_required
def index():
    user = User.query.get(session['user_id'])
    stats = {
        'courses': Course.query.count(),
        'faculty': Faculty.query.count(),
        'rooms': Room.query.count(),
        'students': Student.query.count(),
        'timetable_entries': TimetableEntry.query.count()
    }
    return render_template('index.html', stats=stats, user=user)

# Course Management
@app.route('/courses')
@login_required
def courses():
    user = User.query.get(session['user_id'])
    courses_list = Course.query.all()
    return render_template('courses.html', courses=courses_list, user=user)

@app.route('/courses/add', methods=['POST'])
@admin_required
def add_course():
    data = request.json
    course = Course(
        code=data['code'],
        name=data['name'],
        credits=int(data['credits']),
        course_type=data['type'],
        hours_per_week=int(data['hours_per_week']),
        branch=data.get('branch', '').strip() or None,
        required_room_tags=','.join(tag.strip() for tag in data.get('required_room_tags', '').split(',') if tag.strip())
    )
    db.session.add(course)
    db.session.commit()
    invalidate_cache('timetable_view')
    return jsonify({'success': True, 'id': course.id})

@app.route('/courses/<int:course_id>/delete', methods=['POST'])
@admin_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    # Remove timetable entries referencing this course first to avoid
    # NOT NULL / FK constraint failures when the course is deleted.
    TimetableEntry.query.filter_by(course_id=course.id).delete(synchronize_session=False)
    db.session.delete(course)
    db.session.commit()
    invalidate_cache('timetable_view')
    return jsonify({'success': True})

@app.route('/courses/import', methods=['POST'])
@admin_required
def import_courses():
    upload = request.files.get('file')
    if not upload:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    try:
        # Validate file type and get streaming processor
        chunks_generator = process_upload_stream(upload, chunk_size=1000)
        
        # Validate required columns from first chunk
        first_chunk = None
        required_columns = {'code', 'name', 'credits', 'hours_per_week'}
        
        # Pre-fetch existing courses to avoid N+1 queries
        existing_courses = {c.code: c for c in Course.query.all()}
        
        created, updated = 0, 0
        
        for chunk_idx, chunk in enumerate(chunks_generator):
            # Validate columns on first chunk
            if chunk_idx == 0 and chunk:
                available_columns = set(chunk[0].keys())
                missing = get_missing_columns(available_columns, required_columns)
                if missing:
                    return jsonify({
                        'success': False,
                        'error': f'Missing columns: {", ".join(sorted(missing))}'
                    }), 400
            
            # Process chunk
            for row in chunk:
                code = str(row.get('code', '')).strip()
                if not code:
                    continue
                
                course = existing_courses.get(code)
                course_type = str(row.get('course_type', row.get('type', 'theory'))).lower()
                course_type = 'practical' if 'prac' in course_type else 'theory'
                branch = str(row.get('branch', '')).strip() or None
                tags_raw = row.get('required_room_tags') or row.get('room_tags') or ''
                tags = ','.join(tag.strip() for tag in str(tags_raw).split(',') if tag.strip())

                payload = {
                    'code': code,
                    'name': str(row.get('name', code)).strip(),
                    'credits': parse_int(row.get('credits'), 0),
                    'course_type': course_type,
                    'hours_per_week': parse_int(row.get('hours_per_week'), 1),
                    'branch': branch,
                    'required_room_tags': tags
                }

                if course:
                    course.name = payload['name']
                    course.credits = payload['credits']
                    course.course_type = payload['course_type']
                    course.hours_per_week = payload['hours_per_week']
                    course.branch = payload['branch']
                    course.required_room_tags = payload['required_room_tags']
                    updated += 1
                    db.session.add(course)
                else:
                    course = Course(
                        code=payload['code'],
                        name=payload['name'],
                        credits=payload['credits'],
                        course_type=payload['course_type'],
                        hours_per_week=payload['hours_per_week'],
                        branch=payload['branch'],
                        required_room_tags=payload['required_room_tags']
                    )
                    existing_courses[code] = course
                    db.session.add(course)
                    created += 1
            
            # Commit after each chunk for better memory management
            db.session.commit()
        
        return jsonify({'success': True, 'created': created, 'updated': updated})
    
    except ValueError as exc:
        return jsonify({'success': False, 'error': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Import failed: {str(exc)}'}), 500


@app.route('/courses/delete-all', methods=['POST'])
@admin_required
def delete_all_courses():
    """Delete all courses"""
    try:
        # Bulk delete timetable entries first
        TimetableEntry.query.delete(synchronize_session=False)
        
        # Count courses before deletion
        deleted_count = Course.query.count()
        
        # Bulk delete all courses
        Course.query.delete(synchronize_session=False)
        
        db.session.commit()
        return jsonify({'success': True, 'deleted': deleted_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

# Faculty Management
@app.route('/faculty')
@login_required
def faculty():
    user = User.query.get(session['user_id'])
    faculty_list = Faculty.query.all()
    courses_list = Course.query.all()
    return render_template('faculty.html', faculty=faculty_list, courses=courses_list, user=user)

@app.route('/faculty/add', methods=['POST'])
@admin_required
def add_faculty():
    data = request.json
    try:
        # Admin adds faculty: do not enforce 70% availability validation here.
        # Admin-provided availability (if any) will be stored as-is; missing
        # availability defaults to an empty JSON object '{}' which scheduler
        # treats as 100% available.
        faculty, generated_password = create_faculty_profile(data)
    except ValueError as exc:
        return jsonify({'success': False, 'error': str(exc)}), 400
    db.session.commit()
    response = {'success': True, 'id': faculty.id}
    if generated_password:
        response['generated_password'] = generated_password
    return jsonify(response)

@app.route('/faculty/<int:faculty_id>/delete', methods=['POST'])
@admin_required
def delete_faculty(faculty_id):
    faculty = Faculty.query.get_or_404(faculty_id)
    linked_user = User.query.get(faculty.user_id) if faculty.user_id else None
    # Remove timetable entries referencing this faculty to avoid FK issues
    TimetableEntry.query.filter_by(faculty_id=faculty.id).delete(synchronize_session=False)
    db.session.delete(faculty)
    if linked_user and linked_user.role == 'teacher':
        db.session.delete(linked_user)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/faculty/availability', methods=['POST'])
@login_required
def update_own_availability():
    user = User.query.get(session['user_id'])
    if user.role != 'teacher':
        abort(403)
    faculty = Faculty.query.filter_by(user_id=user.id).first()
    if not faculty:
        return jsonify({'success': False, 'error': 'Profile not linked to faculty record'}), 404
    data = request.json or {}
    availability_payload = data.get('availability', {})
    
    # Validate availability meets 70% threshold
    is_valid, error_msg, percentage = validate_faculty_availability(availability_payload)
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400
    
    if isinstance(availability_payload, (dict, list)):
        availability_payload = json.dumps(availability_payload)
    elif not isinstance(availability_payload, str):
        availability_payload = '{}'
    faculty.availability = availability_payload
    db.session.commit()
    return jsonify({'success': True, 'message': f'Availability saved successfully ({percentage:.1f}% available)'})

@app.route('/faculty/import', methods=['POST'])
@admin_required
def import_faculty():
    upload = request.files.get('file')
    if not upload:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    try:
        chunks_generator = process_upload_stream(upload, chunk_size=1000)
        required = {'name', 'username'}
        
        # Pre-fetch existing faculty to avoid N+1 queries
        existing_faculty = {f.username: f for f in Faculty.query.all()}
        
        created = 0
        updated = 0
        
        for chunk_idx, chunk in enumerate(chunks_generator):
            # Validate columns on first chunk
            if chunk_idx == 0 and chunk:
                available_columns = set(chunk[0].keys())
                missing = get_missing_columns(available_columns, required)
                if missing:
                    return jsonify({
                        'success': False,
                        'error': f'Missing columns: {", ".join(sorted(missing))}'
                    }), 400
            
            for row in chunk:
                name = str(row.get('name', '')).strip()
                if not name:
                    continue
                username = str(row.get('username', '')).strip()
                email = str(row.get('email', '')).strip()
                expertise = normalize_comma_list(row.get('expertise', ''))
                min_hours = parse_int(row.get('min_hours_per_week'), 4)
                max_hours = parse_int(row.get('max_hours_per_week'), 16)

                raw_availability = row.get('availability', '{}')
                if isinstance(raw_availability, (dict, list)):
                    raw_availability = json.dumps(raw_availability)
                elif not isinstance(raw_availability, str):
                    raw_availability = '{}'
                payload = {
                    'name': name,
                    'email': email,
                    'expertise': expertise,
                    'username': username,
                    'password': str(row.get('password', '')).strip(),
                    'min_hours_per_week': min_hours,
                    'max_hours_per_week': max_hours,
                    'availability': raw_availability
                }
                
                faculty = existing_faculty.get(username)
                if faculty:
                    faculty.name = name
                    faculty.email = email
                    faculty.expertise = ','.join(expertise)
                    faculty.min_hours_per_week = min_hours
                    faculty.max_hours_per_week = max_hours
                    faculty.availability = payload.get('availability', '{}')
                    updated += 1
                    db.session.add(faculty)
                    continue

                new_fac, _ = create_faculty_profile(payload)
                existing_faculty[username] = new_fac
                created += 1
            
            # Commit after each chunk
            db.session.commit()
        
        return jsonify({'success': True, 'created': created, 'updated': updated})
    
    except ValueError as exc:
        return jsonify({'success': False, 'error': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Import failed: {str(exc)}'}), 500


@app.route('/faculty/delete-all', methods=['POST'])
@admin_required
def delete_all_faculty():
    """Delete all faculty members and their linked user accounts"""
    try:
        # Count faculty before deletion
        deleted_count = Faculty.query.count()
        
        # Get all faculty user IDs for bulk user deletion
        faculty_user_ids = [f.user_id for f in Faculty.query.all() if f.user_id]
        
        # Delete linked teacher users one by one (MongoDB doesn't support filter().in_())
        if faculty_user_ids:
            for user_id in faculty_user_ids:
                user = User.query.filter_by(id=user_id, role='teacher').first()
                if user:
                    db.session.delete(user)
        
        # Bulk delete timetable entries
        TimetableEntry.query.delete(synchronize_session=False)
        
        # Bulk delete all faculty
        Faculty.query.delete(synchronize_session=False)
        
        db.session.commit()
        return jsonify({'success': True, 'deleted': deleted_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

# Room Management
@app.route('/rooms')
@login_required
def rooms():
    user = User.query.get(session['user_id'])
    rooms_list = Room.query.all()
    return render_template('rooms.html', rooms=rooms_list, user=user)

@app.route('/rooms/add', methods=['POST'])
@admin_required
def add_room():
    data = request.json or {}

    # Validate name
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Room name is required.'}), 400

    # Prevent duplicate room names with a friendly error
    existing = Room.query.filter_by(name=name).first()
    if existing:
        return jsonify({'success': False, 'error': f'A room named "{name}" already exists.'}), 400

    # Parse capacity safely
    try:
        capacity = int(data.get('capacity')) if data.get('capacity') not in (None, '') else 0
    except (TypeError, ValueError):
        capacity = 0

    room = Room(
        name=name,
        capacity=capacity,
        room_type=data.get('type', ''),
        equipment=data.get('equipment', ''),
        tags=','.join(tag.strip() for tag in data.get('tags', '').split(',') if tag.strip())
    )
    db.session.add(room)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'A room named "{name}" already exists.'}), 400

    return jsonify({'success': True, 'id': room.id})

@app.route('/rooms/<int:room_id>/delete', methods=['POST'])
@admin_required
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/rooms/import', methods=['POST'])
@admin_required
def import_rooms():
    upload = request.files.get('file')
    if not upload:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    try:
        chunks_generator = process_upload_stream(upload, chunk_size=1000)
        required_columns = {'name', 'capacity'}
        
        # Pre-fetch existing rooms to avoid N+1 queries
        existing_rooms = {r.name: r for r in Room.query.all()}
        
        created, updated = 0, 0
        
        for chunk_idx, chunk in enumerate(chunks_generator):
            if chunk_idx == 0 and chunk:
                available_columns = set(chunk[0].keys())
                missing = get_missing_columns(available_columns, required_columns)
                if missing:
                    return jsonify({
                        'success': False,
                        'error': f'Missing columns: {", ".join(sorted(missing))}'
                    }), 400
            
            for row in chunk:
                name = str(row.get('name', '')).strip()
                if not name:
                    continue
                
                room = existing_rooms.get(name)
                capacity = parse_int(row.get('capacity'), 0)
                room_type = str(row.get('room_type', 'classroom')).strip()
                equipment = str(row.get('equipment', '')).strip()
                tags = ','.join(tag.strip() for tag in str(row.get('tags', '')).split(',') if tag.strip())

                payload = {
                    'name': name,
                    'capacity': capacity,
                    'room_type': room_type,
                    'equipment': equipment,
                    'tags': tags
                }

                if room:
                    room.name = payload['name']
                    room.capacity = payload['capacity']
                    room.room_type = payload['room_type']
                    room.equipment = payload['equipment']
                    room.tags = payload['tags']
                    updated += 1
                    db.session.add(room)
                else:
                    room = Room(
                        name=payload['name'],
                        capacity=payload['capacity'],
                        room_type=payload['room_type'],
                        equipment=payload['equipment'],
                        tags=payload['tags']
                    )
                    existing_rooms[name] = room
                    db.session.add(room)
                    created += 1
            
            db.session.commit()
        
        return jsonify({'success': True, 'created': created, 'updated': updated})
    
    except ValueError as exc:
        return jsonify({'success': False, 'error': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Import failed: {str(exc)}'}), 500

@app.route('/rooms/delete-all', methods=['POST'])
@admin_required
def delete_all_rooms():
    """Delete all rooms"""
    try:
        # Count rooms before deletion
        deleted_count = Room.query.count()
        
        # Bulk delete timetable entries
        TimetableEntry.query.delete(synchronize_session=False)
        
        # Bulk delete all rooms
        Room.query.delete(synchronize_session=False)
        
        db.session.commit()
        return jsonify({'success': True, 'deleted': deleted_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

# Student Management
@app.route('/students')
@login_required
def students():
    user = User.query.get(session['user_id'])
    students_list = Student.query.all()
    courses_list = Course.query.all()
    return render_template('students.html', students=students_list, courses=courses_list, user=user)

@app.route('/students/add', methods=['POST'])
@admin_required
def add_student():
    data = request.json or {}
    # Basic fields
    name = (data.get('name') or '').strip()
    student_id = (data.get('student_id') or '').strip()
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    courses = data.get('courses', []) or []

    if not name or not student_id:
        return jsonify({'success': False, 'error': 'name and student_id are required'}), 400

    # Create/Link student user account if username provided
    user = None
    if username:
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            if existing_user.role not in ('student', 'teacher', 'admin'):
                # Unknown role, but still allow setting to student
                existing_user.role = 'student'
            elif existing_user.role != 'student':
                return jsonify({'success': False, 'error': 'Username already used by another account'}), 400
            existing_user.name = name
            if password:
                existing_user.set_password(password)
            user = existing_user
        else:
            # Create new student user
            email = f"{username}@student.local"
            # Ensure email uniqueness
            if User.query.filter_by(email=email).first():
                email = f"{username}+{secrets.token_hex(3)}@student.local"
            user = User(username=username, email=email, role='student', name=name)
            if password:
                user.set_password(password)
            else:
                user.set_password(secrets.token_urlsafe(8))
            db.session.add(user)
            db.session.flush()

    student = Student(
        name=name,
        student_id=student_id,
        enrolled_courses=','.join(courses),
        username=username or None,
        user_id=(user.id if user else None)
    )
    db.session.add(student)
    db.session.commit()
    response = {'success': True, 'id': student.id}
    return jsonify(response)

@app.route('/students/<int:student_id>/delete', methods=['POST'])
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    # Remove linked user account if it exists and is a student
    if getattr(student, 'user_id', None):
        u = User.query.get(student.user_id)
        if u and u.role == 'student':
            db.session.delete(u)
    db.session.delete(student)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/students/import', methods=['POST'])
@admin_required
def import_students():
    upload = request.files.get('file')
    if not upload:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    try:
        chunks_generator = process_upload_stream(upload, chunk_size=1000)
        required = {'student_id', 'name'}
        
        # Pre-fetch
        existing_students = {s.student_id: s for s in Student.query.all()}
        existing_users = {u.username: u for u in User.query.all()}
        
        created, updated = 0, 0
        
        for chunk_idx, chunk in enumerate(chunks_generator):
            if chunk_idx == 0 and chunk:
                available_columns = set(chunk[0].keys())
                missing = get_missing_columns(available_columns, required)
                if missing:
                    return jsonify({
                        'success': False,
                        'error': f'Missing columns: {", ".join(sorted(missing))}'
                    }), 400
            
            for row in chunk:
                student_id = str(row.get('student_id', '')).strip()
                if not student_id: continue
                
                name = str(row.get('name', '')).strip()
                enrolled_courses = str(row.get('enrolled_courses', '')).strip()
                username = str(row.get('username', '')).strip()
                password = str(row.get('password', '')).strip()
                
                student = existing_students.get(student_id)
                
                # User logic
                user_id = None
                if username:
                    u = existing_users.get(username)
                    if u:
                        if u.role != 'student':
                            u.role = 'student'
                        u.name = name
                        if password:
                            u.set_password(password)
                        db.session.add(u)
                        user_id = u.id
                    else:
                        email = f"{username}@student.local"
                        u = User(username=username, email=email, role='student', name=name)
                        if password:
                            u.set_password(password)
                        else:
                            u.set_password(secrets.token_urlsafe(8))
                        
                        # Generate ID manually for linking
                        u.id = get_next_id(db._db, 'user')
                        
                        existing_users[username] = u
                        db.session.add(u)
                        user_id = u.id
                
                if student:
                    student.name = name
                    student.enrolled_courses = enrolled_courses
                    if username:
                        student.username = username
                        student.user_id = user_id
                    updated += 1
                    db.session.add(student)
                else:
                    student = Student(
                        student_id=student_id,
                        name=name,
                        enrolled_courses=enrolled_courses,
                        username=username or None,
                        user_id=user_id
                    )
                    existing_students[student_id] = student
                    db.session.add(student)
                    created += 1
            
            db.session.commit()
            
        return jsonify({'success': True, 'created': created, 'updated': updated})

    except ValueError as exc:
        return jsonify({'success': False, 'error': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Import failed: {str(exc)}'}), 500

@app.route('/students/delete-all', methods=['POST'])
@admin_required
def delete_all_students():
    """Delete all students"""
    try:
        # Count students before deletion
        deleted_count = Student.query.count()
        
        # Get all student user IDs for bulk user deletion
        student_user_ids = [s.user_id for s in Student.query.all() if getattr(s, 'user_id', None)]
        
        # Bulk delete linked student users
        if student_user_ids:
            User.query.filter(User.id.in_(student_user_ids), User.role == 'student').delete(synchronize_session=False)
        
        # Bulk delete all students
        Student.query.delete(synchronize_session=False)
        
        db.session.commit()
        return jsonify({'success': True, 'deleted': deleted_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

# Student Group Management
@app.route('/student-groups')
@admin_required
def student_groups():
    user = User.query.get(session['user_id'])
    raw_groups = StudentGroup.query.all()
    groups = []
    for g in raw_groups:
        # Safely obtain batches list; some legacy records may have a mis-typed 'batche' field
        batches_raw = getattr(g, 'batches', None)
        if batches_raw is None:
            batches_raw = getattr(g, 'batche', None)
        batches = []
        if batches_raw:
            try:
                parsed = json.loads(batches_raw) if isinstance(batches_raw, str) else batches_raw
                if isinstance(parsed, list):
                    batches = parsed
            except Exception:
                batches = []
        groups.append({
            'id': getattr(g, 'id', None),
            'name': getattr(g, 'name', ''),
            'description': getattr(g, 'description', ''),
            'total_students': getattr(g, 'total_students', 0),
            'batches': batches
        })
    return render_template('student_groups.html', groups=groups, user=user)

@app.route('/student-groups/add', methods=['POST'])
@admin_required
def add_student_group():
    data = request.json
    # Validate name
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Class name is required.'}), 400

    # Prevent duplicate names (return friendly error instead of raising DB exception)
    existing = StudentGroup.query.filter_by(name=name).first()
    if existing:
        return jsonify({'success': False, 'error': f'A class named "{name}" already exists.'}), 400
    batches = data.get('batches')
    # Ensure batches is stored as JSON string if provided as list/dict
    if isinstance(batches, (list, dict)):
        batches_json = json.dumps(batches)
    else:
        batches_json = batches or None

    total_students = None
    try:
        total_students = int(data.get('total_students')) if data.get('total_students') not in (None, '') else None
    except (TypeError, ValueError):
        total_students = None

    group = StudentGroup(
        name=name,
        description=data.get('description', ''),
        total_students=total_students,
        batches=batches_json
    )
    db.session.add(group)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'A class named "{name}" already exists.'}), 400
    return jsonify({'success': True, 'id': group.id})

@app.route('/student-groups/<int:group_id>/delete', methods=['POST'])
@admin_required
def delete_student_group(group_id):
    group = StudentGroup.query.get_or_404(group_id)
    db.session.delete(group)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/student-groups/import', methods=['POST'])
@admin_required
def import_student_groups():
    upload = request.files.get('file')
    if not upload:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    try:
        chunks_generator = process_upload_stream(upload, chunk_size=1000)
        required = {'name'}
        
        existing_groups = {g.name: g for g in StudentGroup.query.all()}
        
        created, updated = 0, 0
        
        for chunk_idx, chunk in enumerate(chunks_generator):
            if chunk_idx == 0 and chunk:
                available_columns = set(chunk[0].keys())
                missing = get_missing_columns(available_columns, required)
                if missing:
                    return jsonify({
                        'success': False,
                        'error': f'Missing columns: {", ".join(sorted(missing))}'
                    }), 400
            
            for row in chunk:
                name = str(row.get('name', '')).strip()
                if not name: continue
                
                description = str(row.get('description', '')).strip()
                total_students = parse_int(row.get('total_students'), None)
                
                # Parse batches
                batches = []
                batches_col = row.get('batches', '')
                batches_students_col = row.get('batches_students', '')
                if batches_col or batches_students_col:
                    batch_names = [b.strip() for b in str(batches_col).split(',') if b.strip()]
                    batch_students = [s.strip() for s in str(batches_students_col).split(',') if s.strip()]
                    for i, batch_name in enumerate(batch_names):
                        students = batch_students[i] if i < len(batch_students) else ''
                        batches.append({'batch_name': batch_name, 'students': students})
                batches_json = json.dumps(batches) if batches else None
                
                group = existing_groups.get(name)
                if group:
                    group.name = name
                    group.description = description
                    group.total_students = total_students
                    if batches_json:
                        group.batches = batches_json
                    updated += 1
                    db.session.add(group)
                else:
                    group = StudentGroup(
                        name=name,
                        description=description,
                        total_students=total_students,
                        batches=batches_json
                    )
                    existing_groups[name] = group
                    db.session.add(group)
                    created += 1
            
            db.session.commit()
            
        return jsonify({'success': True, 'created': created, 'updated': updated})

    except ValueError as exc:
        return jsonify({'success': False, 'error': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Import failed: {str(exc)}'}), 500

@app.route('/student-groups/delete-all', methods=['POST'])
@admin_required
def delete_all_student_groups():
    """Delete all student groups"""
    try:
        # Count student groups before deletion
        deleted_count = StudentGroup.query.count()
        
        # Bulk delete all student groups
        StudentGroup.query.delete(synchronize_session=False)
        
        db.session.commit()
        return jsonify({'success': True, 'deleted': deleted_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

# Timetable Generation
@app.route('/timetable')
@login_required
@cache_response(ttl=300, prefix='timetable_view')
def timetable():
    user = User.query.get(session['user_id'])
    entries_query = TimetableEntry.query
    faculty_profile = None
    if user.role == 'teacher':
        faculty_profile = Faculty.query.filter_by(user_id=user.id).first()
        if faculty_profile:
            entries_query = entries_query.filter_by(faculty_id=faculty_profile.id)
        else:
            entries_query = entries_query.filter_by(faculty_id=-1)
    slots = TimeSlot.query.all()
    slots_dict = {s.id: s for s in slots}
    valid_slot_ids = set(slots_dict.keys())

    # Filter entries to only include those with valid time_slot_id
    entries = [e for e in entries_query.all() if e.time_slot_id in valid_slot_ids]
    
    print(f"[TIMETABLE VIEW] Loading timetable for user: {user.username} (role: {user.role})")
    print(f"[TIMETABLE VIEW] Found {len(entries)} timetable entries")
    print(f"[TIMETABLE VIEW] Found {len(slots)} time slots")

    courses_dict = {c.id: c for c in Course.query.all()}
    faculty_dict = {f.id: f for f in Faculty.query.all()}
    rooms_dict = {r.id: r for r in Room.query.all()}
    
    # Get break configurations
    breaks = BreakConfig.query.order_by(BreakConfig.after_period).all()
    break_map = {br.after_period: br for br in breaks}
    
    # Organize by day and period (one lecture per period per class is enforced by unique constraint)
    timetable_data = {}
    for entry in entries:
        slot = slots_dict[entry.time_slot_id]
        key = (slot.day, slot.period)
        if key not in timetable_data:
            timetable_data[key] = []
        timetable_data[key].append({
            'course': courses_dict[entry.course_id],
            'faculty': faculty_dict[entry.faculty_id],
            'room': rooms_dict[entry.room_id],
            'slot': slot,
            'student_group': entry.student_group
        })
    
    # Get days from period config or default
    period_config = PeriodConfig.query.first()
    if period_config:
        days = [d.strip() for d in period_config.days_of_week.split(',')]
    else:
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    periods = sorted(set(s.period for s in TimeSlot.query.all()))
    
    teacher_availability = {}
    if faculty_profile and faculty_profile.availability:
        try:
            # Ensure availability is a string before parsing
            avail_data = faculty_profile.availability
            if isinstance(avail_data, str):
                teacher_availability = json.loads(avail_data)
            elif isinstance(avail_data, dict):
                teacher_availability = avail_data
            else:
                # If it's something else (float, int, etc.), reset to empty
                teacher_availability = {}
        except (json.JSONDecodeError, TypeError, ValueError):
            teacher_availability = {}

    # Provide data needed for manual assignments UI (serialize to plain dicts)
    raw_student_groups = StudentGroup.query.all()
    student_groups_list = []
    for g in raw_student_groups:
        batches_raw = getattr(g, 'batches', None)
        if batches_raw is None:
            batches_raw = getattr(g, 'batche', None)
        batches = []
        if batches_raw:
            try:
                parsed = json.loads(batches_raw) if isinstance(batches_raw, str) else batches_raw
                if isinstance(parsed, list):
                    batches = parsed
            except Exception:
                batches = []
        student_groups_list.append({
            'id': getattr(g, 'id', None),
            'name': getattr(g, 'name', ''),
            'description': getattr(g, 'description', ''),
            'total_students': getattr(g, 'total_students', 0),
            'batches': batches
        })

    courses_list = []
    for c in Course.query.all():
        courses_list.append({
            'id': getattr(c, 'id', None),
            'code': getattr(c, 'code', ''),
            'name': getattr(c, 'name', ''),
            'credits': getattr(c, 'credits', 0),
            'hours_per_week': getattr(c, 'hours_per_week', 0),
            'course_type': getattr(c, 'course_type', 'lecture')
        })

    faculty_list = []
    for f in Faculty.query.all():
        faculty_list.append({
            'id': getattr(f, 'id', None),
            'name': getattr(f, 'name', ''),
            'email': getattr(f, 'email', ''),
            'expertise': getattr(f, 'expertise', '')
        })

    rooms_list = []
    for r in Room.query.all():
        rooms_list.append({
            'id': getattr(r, 'id', None),
            'name': getattr(r, 'name', ''),
            'capacity': getattr(r, 'capacity', 0),
            'room_type': getattr(r, 'room_type', 'classroom'),
            'tags': getattr(r, 'tags', '')
        })
    
    # Build time_ranges dictionary from TimeSlot data
    # This will show the actual start-end time for each period based on admin settings
    time_ranges = {}
    for slot in slots:
        if slot.period not in time_ranges:
            # Format: "09:00 - 10:00"
            time_ranges[slot.period] = f"{slot.start_time} - {slot.end_time}"

    return render_template('timetable.html', 
                         timetable_data=timetable_data,
                         days=days,
                         periods=periods,
                         break_map=break_map,
                         time_ranges=time_ranges,
                         user=user,
                         teacher_availability=teacher_availability,
                         student_groups=student_groups_list,
                         courses=courses_list,
                         faculty=faculty_list,
                         rooms=rooms_list)


@app.route('/timetable/entries')
@login_required
@cache_response(ttl=300, prefix='timetable_entries')
def timetable_entries():
    # Return entries for a given day to prefill manual assignment UI
    day = request.args.get('day')
    if not day:
        return jsonify({'entries': []})

    slots = TimeSlot.query.filter_by(day=day).all()
    slot_map = {s.id: s for s in slots}
    # Mongo-backed Query object does not support SQLAlchemy-style .filter or in_ operations.
    # Fetch all timetable entries and manually filter by matching time_slot_id.
    entries = [e for e in TimetableEntry.query.all() if e.time_slot_id in slot_map]
    result = []
    for e in entries:
        s = slot_map.get(e.time_slot_id)
        if not s:
            continue
        result.append({
            'period': s.period,
            'student_group': e.student_group,
            'course_id': e.course_id,
            'faculty_id': e.faculty_id,
            'room_id': e.room_id
        })
    return jsonify({'entries': result})

@app.route('/timetable/generate', methods=['POST'])
@admin_required
def generate_timetable():
    try:
        invalidate_cache('timetable_view')
        invalidate_cache('timetable_entries')
        
        # Try async generation with Celery (for local development with Redis)
        try:
            task = generate_timetable_task.delay()
            return jsonify({
                'success': True,
                'message': 'Timetable generation started in background.',
                'task_id': task.id
            }), 202
        except Exception as celery_error:
            # Celery not available (e.g., on Vercel) - run synchronously
            print(f"Celery unavailable ({celery_error}), running synchronously...")
            
            # Clear existing timetable
            TimetableEntry.query.delete()
            db.session.commit()
            
            # Generate new timetable synchronously
            generator = TimetableGenerator(db)
            result = generator.generate()
            
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'message': 'Timetable generated successfully!',
                    'result': result
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Generation failed')
                }), 400
                
    except Exception as e:
        db.session.rollback()
        print(f"Error generating timetable: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Failed to generate timetable: {str(e)}'
        }), 500

@app.route('/tasks/<task_id>')
@login_required
def get_task_status(task_id):
    task = generate_timetable_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        # task.info is the result or status dict
        response = {
            'state': task.state,
            'status': task.info.get('status', '') if isinstance(task.info, dict) else str(task.info)
        }
        if task.state == 'SUCCESS':
            result = task.result
            if isinstance(result, dict):
                response.update(result)
    else:
        response = {
            'state': task.state,
            'status': str(task.info),  # Exception info
        }
    return jsonify(response)


@app.route('/timetable/manual-save', methods=['POST'])
@admin_required
def manual_save_timetable():
    """Save manual assignments posted from the admin UI.
    Expected JSON payload:
    { "day": "Monday", "assignments": [ {"period":1, "group":"CSE-A", "course_id":1, "faculty_id":2, "room_id":3}, ... ] }
    """
    payload = request.get_json() or {}
    day = payload.get('day')
    assignments = payload.get('assignments', [])

    if not day:
        return jsonify({'success': False, 'error': 'Day is required.'}), 400

    errors = []
    processed = 0

    # Validate per-group per-day maximums before applying changes
    period_config = PeriodConfig.query.first()
    if period_config:
        max_per_day = getattr(period_config, 'max_periods_per_day_per_group', period_config.periods_per_day)
    else:
        max_per_day = None

    # Gather slots for this day and existing entries in those slots
    day_slots = TimeSlot.query.filter_by(day=day).all()
    day_slot_ids = {s.id for s in day_slots}
    existing_entries = [e for e in TimetableEntry.query.all() if e.time_slot_id in day_slot_ids]

    # Count existing assigned periods per group for the day (only count entries with a course)
    from collections import defaultdict as _dd
    existing_count = _dd(int)
    existing_by_slot_group = {}
    for e in existing_entries:
        if getattr(e, 'course_id', None) not in (None, '', 0):
            existing_count[e.student_group] += 1
        existing_by_slot_group[(e.time_slot_id, e.student_group)] = e

    # Simulate final counts after applying incoming assignments
    final_count = existing_count.copy()
    for a in assignments:
        try:
            period = int(a.get('period'))
        except Exception:
            continue
        group_name = a.get('group')
        if not group_name:
            continue
        slot = TimeSlot.query.filter_by(day=day, period=period).first()
        if not slot:
            continue
        course_id = a.get('course_id')
        incoming_has_course = course_id not in (None, '', 0)
        currently = existing_by_slot_group.get((slot.id, group_name))
        currently_has_course = getattr(currently, 'course_id', None) not in (None, '', 0) if currently else False

        if incoming_has_course and not currently_has_course:
            final_count[group_name] += 1
        if not incoming_has_course and currently_has_course:
            final_count[group_name] -= 1

    # If any group would exceed the per-day maximum, abort early with error
    if max_per_day is not None:
        exceeded = [g for g, cnt in final_count.items() if cnt > max_per_day]
        if exceeded:
            return jsonify({'success': False, 'error': f'Per-day limit exceeded for groups: {", ".join(exceeded)}. Max per day: {max_per_day}'}), 400

    for a in assignments:
        try:
            period = int(a.get('period'))
        except Exception:
            continue

        group_name = a.get('group')
        if not group_name:
            continue

        # Find timeslot
        slot = TimeSlot.query.filter_by(day=day, period=period).first()
        if not slot:
            errors.append(f'No timeslot for {day} P{period}')
            continue

        course_id = a.get('course_id')
        faculty_id = a.get('faculty_id')
        room_id = a.get('room_id')

        # Basic conflict checks: faculty or room already assigned at this timeslot to another group
        if faculty_id:
            # Mongo Query does not support SQLAlchemy-style filter conditions; perform manual conflict check
            existing_entries = TimetableEntry.query.all()
            conflict = next((te for te in existing_entries
                             if te.time_slot_id == slot.id and te.faculty_id == faculty_id and te.student_group != group_name), None)
            if conflict:
                errors.append(f'Faculty id {faculty_id} is already assigned at {day} P{period} to {conflict.student_group}')
                continue

        if room_id:
            existing_entries = 'existing_entries' in locals() and existing_entries or TimetableEntry.query.all()
            conflict = next((te for te in existing_entries
                             if te.time_slot_id == slot.id and te.room_id == room_id and te.student_group != group_name), None)
            if conflict:
                errors.append(f'Room id {room_id} is already used at {day} P{period} by {conflict.student_group}')
                continue

        # Upsert TimetableEntry for this slot + group
        entry = TimetableEntry.query.filter_by(time_slot_id=slot.id, student_group=group_name).first()
        if course_id in (None, '', 0):
            # Delete existing entry if any
            if entry:
                db.session.delete(entry)
            processed += 1
            continue

        if not entry:
            entry = TimetableEntry(time_slot_id=slot.id, student_group=group_name)
            db.session.add(entry)

        entry.course_id = int(course_id) if course_id not in (None, '') else None
        entry.faculty_id = int(faculty_id) if faculty_id not in (None, '') else None
        entry.room_id = int(room_id) if room_id not in (None, '') else None
        processed += 1

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database integrity error: ' + str(e)}), 500

    result = {'success': True, 'processed': processed}
    if errors:
        result['warnings'] = errors
    return jsonify(result)

@app.route('/timetable/clear', methods=['POST'])
@admin_required
def clear_timetable():
    TimetableEntry.query.delete()
    db.session.commit()
    return jsonify({'success': True})

# Export
# Settings Management
@app.route('/settings')
@admin_required
def settings():
    user = User.query.get(session['user_id'])
    period_config = PeriodConfig.query.first()
    
    print(f"[DEBUG SETTINGS] Loading settings page")
    if period_config:
        print(f"[DEBUG SETTINGS] Config found: periods_per_day={period_config.periods_per_day}, period_duration_minutes={period_config.period_duration_minutes}, day_start_time={period_config.day_start_time}, days_of_week={period_config.days_of_week}")
    else:
        print(f"[DEBUG SETTINGS] No config found in database!")
    
    breaks = BreakConfig.query.order_by(BreakConfig.after_period).all()
    days_list = [d.strip() for d in period_config.days_of_week.split(',')] if period_config else []
    return render_template('settings.html', period_config=period_config, breaks=breaks, days_list=days_list, user=user)

@app.route('/settings/period', methods=['POST'])
@admin_required
def update_period_config():
    try:
        data = request.json
        print(f"[DEBUG] Received data: {data}")
        
        period_config = PeriodConfig.query.first()
        
        if not period_config:
            print("[DEBUG] No existing config found, creating new one")
            period_config = PeriodConfig(id=1)
        else:
            print(f"[DEBUG] Existing config found: periods_per_day={period_config.periods_per_day}, days_of_week={period_config.days_of_week}")
        
        # Update the config fields
        period_config.periods_per_day = int(data['periods_per_day'])
        period_config.period_duration_minutes = int(data['period_duration_minutes'])
        period_config.day_start_time = data['day_start_time']
        period_config.days_of_week = ','.join(data.get('days_of_week', []))
        
        print(f"[DEBUG] Updated config: periods_per_day={period_config.periods_per_day}, days_of_week={period_config.days_of_week}")
        
        # CRITICAL FIX: Always add to session, even for existing configs
        db.session.add(period_config)
        
        # Enforce singleton: remove any stray extra PeriodConfig documents
        try:
            existing = PeriodConfig.query.all()
            for cfg in existing:
                if getattr(cfg, 'id', None) != 1:
                    db.session.delete(cfg)
            # Flush deletions before commit
            db.session.flush()
        except Exception as _:
            pass
        db.session.commit()
        
        print("[DEBUG] Committed to database")
        
        # Verify the save by querying again
        verify_config = PeriodConfig.query.first()
        if verify_config:
            print(f"[DEBUG] Verification query: periods_per_day={verify_config.periods_per_day}, days_of_week={verify_config.days_of_week}")
        
        # Regenerate time slots
        generate_time_slots()
        
        return jsonify({'success': True, 'message': 'Period configuration updated and time slots regenerated.'})
    except Exception as e:
        db.session.rollback()
        print(f"Error updating period config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/settings/break/add', methods=['POST'])
@admin_required
def add_break():
    try:
        data = request.json
        break_config = BreakConfig(
            break_name=data['break_name'],
            after_period=int(data['after_period']),
            duration_minutes=int(data['duration_minutes']),
            order=int(data.get('order', 1))
        )
        db.session.add(break_config)
        db.session.commit()
        
        # Regenerate time slots
        generate_time_slots()
        
        return jsonify({'success': True, 'id': break_config.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/settings/break/<int:break_id>/update', methods=['POST'])
@admin_required
def update_break(break_id):
    try:
        data = request.json
        break_config = BreakConfig.query.get_or_404(break_id)
        
        break_config.break_name = data['break_name']
        break_config.after_period = int(data['after_period'])
        break_config.duration_minutes = int(data['duration_minutes'])
        break_config.order = int(data.get('order', break_config.order))
        
        db.session.commit()
        
        # Regenerate time slots
        generate_time_slots()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/settings/break/<int:break_id>/delete', methods=['POST'])
@admin_required
def delete_break(break_id):
    try:
        break_config = BreakConfig.query.get_or_404(break_id)
        db.session.delete(break_config)
        db.session.commit()
        
        # Regenerate time slots
        generate_time_slots()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/timetable/export')
@login_required
def export_timetable():
    slots = TimeSlot.query.all()
    slots_dict = {s.id: s for s in slots}
    valid_slot_ids = set(slots_dict.keys())

    # Filter entries to only include those with valid time_slot_id
    entries = [e for e in TimetableEntry.query.all() if e.time_slot_id in valid_slot_ids]

    courses_dict = {c.id: c for c in Course.query.all()}
    faculty_dict = {f.id: f for f in Faculty.query.all()}
    rooms_dict = {r.id: r for r in Room.query.all()}
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Day', 'Period', 'Start Time', 'End Time', 'Course Code', 'Course Name', 'Faculty', 'Room'])
    
    for entry in entries:
        slot = slots_dict[entry.time_slot_id]
        course = courses_dict[entry.course_id]
        faculty = faculty_dict[entry.faculty_id]
        room = rooms_dict[entry.room_id]
        writer.writerow([
            slot.day,
            slot.period,
            slot.start_time,
            slot.end_time,
            course.code,
            course.name,
            faculty.name,
            room.name
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'timetable_{datetime.now().strftime("%Y%m%d")}.csv'
    )

if __name__ == '__main__':
    # Run with reloader disabled to avoid Windows socket errors
    # Add one-time cleanup: normalize faculty availability types
    try:
        fixed = 0
        for f in Faculty.query.all():
            raw = getattr(f, 'availability', None)
            if raw and not isinstance(raw, str):
                if isinstance(raw, (dict, list)):
                    f.availability = json.dumps(raw)
                else:
                    f.availability = '{}'
                fixed += 1
            elif raw is None:
                f.availability = '{}'
                fixed += 1
        if fixed:
            db.session.commit()
            print(f"Normalized availability for {fixed} faculty records.")
    except Exception as e:
        print(f"Availability normalization skipped due to error: {e}")
    app.run(debug=True, port=5000, use_reloader=False, threaded=True)

# Vercel serverless function handler
# This is required for Vercel deployment
if __name__ != '__main__':
    # When running on Vercel, expose the app object
    application = app
