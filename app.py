from flask import Flask, request, render_template, redirect, url_for, flash, session, send_file
import sqlite3
import hashlib
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from werkzeug.utils import secure_filename
import csv
import io
from functools import wraps
from email.mime.image import MIMEImage

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'fallback-secret-key-for-development')

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "testmaillle699@gmail.com"
EMAIL_PASSWORD = "inhc wyiy geig iqnl"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_application_id():
    """Generate unique application ID in format ADM20251006001"""
    date_str = datetime.now().strftime('%Y%m%d')
    # Get count of applications today
    conn = sqlite3.connect('admission_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM students WHERE application_id LIKE ?", (f'ADM{date_str}%',))
    count = cursor.fetchone()[0] + 1
    conn.close()
    return f'ADM{date_str}{count:03d}'

def send_email(to_email, application_id, name):
    """Send email with application ID"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = "Admission Application Confirmation"

        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <img src="cid:logo" alt="Institution Logo" width="150" style="margin-bottom: 20px;"/>
            <p>Hello <strong>{name}</strong>,</p>
            <p>Thank you for applying to our institution!</p>
            <p><strong>Your Application ID:</strong> {application_id}</p>
            <p>Use this ID to check your admission status on our website.</p>
            <br>
            <p>Best regards,<br>Admissions Team (Sanskar Sharma)</p>
          </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html'))

        try:
            with open("static/pic1.png", "rb") as img_file:
                img = MIMEImage(img_file.read())
                img.add_header("Content-ID", "<logo>")
                img.add_header("Content-Disposition", "inline", filename="pic1.png")
                msg.attach(img)
        except FileNotFoundError:
            print("Logo file not found. Sending email without logo.")
        except Exception as e:
            print(f"Error attaching logo: {e}")
            
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    """Decorator to require student authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student_logged_in' not in session:
            return redirect(url_for('student_login'))
        return f(*args, **kwargs)
    return decorated_function

def init_db():
    """Initialize database with default admin"""
    from database import init_database
    init_database()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        # Get form data
        name = request.form['name'].strip()
        dob = request.form['dob']
        gender = request.form['gender']
        email = request.form['email'].strip().lower()
        phone = request.form['phone'].strip()
        address = request.form['address'].strip()
        course = request.form['course']
        previous_education = request.form['previous_education'].strip()
        
        # Validation
        if not all([name, dob, gender, email, phone, address, course, previous_education]):
            flash('All fields are required!', 'error')
            return render_template('apply.html')
        
        # Check if email already exists
        conn = sqlite3.connect('admission_system.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM students WHERE email = ?", (email,))
        if cursor.fetchone():
            flash('An application with this email already exists!', 'error')
            conn.close()
            return render_template('apply.html')
        
        # Handle file upload
        documents_path = None
        if 'documents' in request.files:
            file = request.files['documents']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to filename to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                documents_path = filename
        
        # Generate application ID
        application_id = generate_application_id()
        
        # Insert into database
        cursor.execute('''
            INSERT INTO students (name, dob, gender, email, phone, address, course, 
                                previous_education, documents_path, status, application_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, dob, gender, email, phone, address, course, previous_education,
              documents_path, 'Pending', application_id, datetime.now()))
        
        conn.commit()
        conn.close()
        
        # Send email
        email_sent = send_email(email, application_id, name)
        
        if email_sent:
            flash(f'Application submitted successfully! Your Application ID is {application_id}. Check your email for confirmation.', 'success')
        else:
            flash(f'Application submitted successfully! Your Application ID is {application_id}. (Email notification failed)', 'warning')
        
        return redirect(url_for('status'))
    
    return render_template('apply.html')

@app.route('/status', methods=['GET', 'POST'])
def status():
    application_data = None
    if request.method == 'POST':
        application_id = request.form['application_id'].strip().upper()
        
        conn = sqlite3.connect('admission_system.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE application_id = ?", (application_id,))
        application_data = cursor.fetchone()
        conn.close()
        
        if not application_data:
            flash('Application ID not found!', 'error')
    
    return render_template('status.html', application_data=application_data)

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        application_id = request.form['application_id'].strip().upper()
        email = request.form['email'].strip().lower()
        
        conn = sqlite3.connect('admission_system.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE application_id = ? AND email = ?", 
                      (application_id, email))
        student = cursor.fetchone()
        conn.close()
        
        if student:
            session['student_logged_in'] = True
            session['student_application_id'] = application_id
            return redirect(url_for('student_portal'))
        else:
            flash('Invalid Application ID or Email!', 'error')
    
    return render_template('student_login.html')

@app.route('/student/portal')
@student_required
def student_portal():
    application_id = session.get('student_application_id')
    
    conn = sqlite3.connect('admission_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE application_id = ?", (application_id,))
    student_data = cursor.fetchone()
    conn.close()
    
    if not student_data:
        flash('Application not found!', 'error')
        return redirect(url_for('student_login'))
    
    application = {
        'id': student_data[0],
        'name': student_data[1],
        'dob': student_data[2],
        'gender': student_data[3],
        'email': student_data[4],
        'phone': student_data[5],
        'address': student_data[6],
        'course': student_data[7],
        'previous_education': student_data[8],
        'documents_path': student_data[9],
        'status': student_data[10],
        'application_id': student_data[11],
        'created_at': student_data[12],
        'admin_notes': student_data[13],
        'document_status': student_data[14],
        'document_notes': student_data[15]
    }
    
    return render_template('student_portal.html', application=application)

@app.route('/student/update_profile', methods=['POST'])
@student_required
def student_update_profile():
    application_id = session.get('student_application_id')
    email = request.form['email'].strip().lower()
    phone = request.form['phone'].strip()
    address = request.form['address'].strip()
    
    conn = sqlite3.connect('admission_system.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET email = ?, phone = ?, address = ? WHERE application_id = ?", 
                   (email, phone, address, application_id))
    conn.commit()
    conn.close()
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('student_portal'))

@app.route('/student/resubmit_docs', methods=['POST'])
@student_required
def student_resubmit_docs():
    application_id = session.get('student_application_id')
    
    if 'documents' not in request.files:
        flash('No file uploaded!', 'error')
        return redirect(url_for('student_portal'))
    
    file = request.files['documents']
    
    if not file or not file.filename:
        flash('No file selected!', 'error')
        return redirect(url_for('student_portal'))
    
    if not allowed_file(file.filename):
        flash('Invalid file type!', 'error')
        return redirect(url_for('student_portal'))
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
    filename = timestamp + filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    conn = sqlite3.connect('admission_system.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students 
        SET documents_path = ?, document_status = 'Pending', document_notes = NULL 
        WHERE application_id = ?
    """, (filename, application_id))
    conn.commit()
    conn.close()
    
    flash('Documents resubmitted successfully! Verification status has been reset to Pending.', 'success')
    return redirect(url_for('student_portal'))

@app.route('/student/logout')
@student_required
def student_logout():
    session.pop('student_logged_in', None)
    session.pop('student_application_id', None)
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        conn = sqlite3.connect('admission_system.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ? AND password = ?", 
                      (username, hash_password(password)))
        admin = cursor.fetchone()
        conn.close()
        
        if admin:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = sqlite3.connect('admission_system.db')
    cursor = conn.cursor()
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) FROM students")
    total_applications = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM students WHERE status = 'Pending'")
    pending_applications = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM students WHERE status = 'Accepted'")
    accepted_applications = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM students WHERE status = 'Rejected'")
    rejected_applications = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('admin_dashboard.html',
                         total=total_applications,
                         pending=pending_applications,
                         accepted=accepted_applications,
                         rejected=rejected_applications)

@app.route('/admin/applications')
@admin_required
def admin_applications():
    conn = sqlite3.connect('admission_system.db')
    cursor = conn.cursor()
    
    # Get search and filter parameters
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    course_filter = request.args.get('course', '')
    
    # Build query
    query = "SELECT * FROM students WHERE 1=1"
    params = []
    
    if search:
        query += " AND (name LIKE ? OR application_id LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%'])
    
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    
    if course_filter:
        query += " AND course = ?"
        params.append(course_filter)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    applications = cursor.fetchall()
    
    # Get unique courses for filter dropdown
    cursor.execute("SELECT DISTINCT course FROM students ORDER BY course")
    courses = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('admin_applications.html', 
                         applications=applications, 
                         courses=courses,
                         search=search,
                         status_filter=status_filter,
                         course_filter=course_filter)

@app.route('/admin/update_status', methods=['POST'])
@admin_required
def update_status():
    application_id = request.form['application_id']
    new_status = request.form['status']
    admin_notes = request.form.get('admin_notes', '').strip()
    
    conn = sqlite3.connect('admission_system.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET status = ?, admin_notes = ? WHERE application_id = ?", 
                   (new_status, admin_notes, application_id))
    conn.commit()
    conn.close()
    
    flash('Application status updated successfully!', 'success')
    return redirect(url_for('admin_applications'))

@app.route('/admin/bulk_update_status', methods=['POST'])
@admin_required
def bulk_update_status():
    application_ids = request.form.getlist('application_ids')
    bulk_status = request.form['bulk_status']
    bulk_notes = request.form.get('bulk_notes', '').strip()
    
    if not application_ids:
        flash('No applications selected!', 'error')
        return redirect(url_for('admin_applications'))
    
    conn = sqlite3.connect('admission_system.db')
    cursor = conn.cursor()
    
    for app_id in application_ids:
        cursor.execute("UPDATE students SET status = ?, admin_notes = ? WHERE application_id = ?", 
                       (bulk_status, bulk_notes, app_id))
    
    conn.commit()
    conn.close()
    
    flash(f'Successfully updated {len(application_ids)} application(s) to {bulk_status}!', 'success')
    return redirect(url_for('admin_applications'))

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    conn = sqlite3.connect('admission_system.db')
    cursor = conn.cursor()
    
    # Basic statistics
    cursor.execute("SELECT COUNT(*) FROM students")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM students WHERE status = 'Pending'")
    pending = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM students WHERE status = 'Accepted'")
    accepted = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM students WHERE status = 'Rejected'")
    rejected = cursor.fetchone()[0]
    
    # Calculate acceptance rate
    acceptance_rate = round((accepted / total * 100) if total > 0 else 0, 1)
    
    # Today's applications
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM students WHERE DATE(created_at) = ?", (today,))
    today_applications = cursor.fetchone()[0]
    
    # Course-wise statistics
    cursor.execute("""
        SELECT course, COUNT(*) as total,
               SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) as accepted
        FROM students
        GROUP BY course
        ORDER BY total DESC
    """)
    course_results = cursor.fetchall()
    
    course_stats = []
    course_labels = []
    course_data = []
    
    for course, total_count, accepted_count in course_results:
        rate = round((accepted_count / total_count * 100) if total_count > 0 else 0, 1)
        course_stats.append({
            'name': course,
            'total': total_count,
            'accepted': accepted_count,
            'rate': rate
        })
        course_labels.append(course)
        course_data.append(total_count)
    
    # Daily statistics for last 7 days
    cursor.execute("""
        SELECT DATE(created_at) as date, COUNT(*) as total,
               SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) as accepted,
               SUM(CASE WHEN status = 'Rejected' THEN 1 ELSE 0 END) as rejected
        FROM students
        WHERE DATE(created_at) >= DATE('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at) DESC
    """)
    daily_results = cursor.fetchall()
    
    daily_stats = []
    for date, total_count, accepted_count, rejected_count in daily_results:
        daily_stats.append({
            'date': date,
            'total': total_count,
            'accepted': accepted_count or 0,
            'rejected': rejected_count or 0
        })
    
    # Trend data for last 30 days
    cursor.execute("""
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM students
        WHERE DATE(created_at) >= DATE('now', '-30 days')
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at) ASC
    """)
    trend_results = cursor.fetchall()
    
    trend_labels = [row[0] for row in trend_results]
    trend_data = [row[1] for row in trend_results]
    
    conn.close()
    
    stats = {
        'total': total,
        'pending': pending,
        'accepted': accepted,
        'rejected': rejected,
        'acceptance_rate': acceptance_rate,
        'today_applications': today_applications,
        'course_stats': course_stats,
        'course_labels': course_labels,
        'course_data': course_data,
        'daily_stats': daily_stats,
        'trend_labels': trend_labels,
        'trend_data': trend_data
    }
    
    return render_template('admin_analytics.html', stats=stats)

@app.route('/admin/verify_document', methods=['POST'])
@admin_required
def verify_document():
    application_id = request.form['application_id']
    document_status = request.form['document_status']
    document_notes = request.form.get('document_notes', '').strip()
    
    # Validate document status
    valid_statuses = ['Pending', 'Verified', 'Rejected']
    if document_status not in valid_statuses:
        flash('Invalid document status!', 'error')
        return redirect(url_for('admin_applications'))
    
    conn = sqlite3.connect('admission_system.db')
    cursor = conn.cursor()
    
    # Check if application exists and has documents uploaded
    cursor.execute("SELECT id, documents_path FROM students WHERE application_id = ?", (application_id,))
    result = cursor.fetchone()
    
    if not result:
        flash('Application not found!', 'error')
        conn.close()
        return redirect(url_for('admin_applications'))
    
    if not result[1]:
        flash('No documents uploaded for this application!', 'error')
        conn.close()
        return redirect(url_for('admin_applications'))
    
    cursor.execute("UPDATE students SET document_status = ?, document_notes = ? WHERE application_id = ?", 
                   (document_status, document_notes, application_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    if rows_affected > 0:
        flash(f'Document status updated to {document_status}!', 'success')
    else:
        flash('Failed to update document status!', 'error')
    
    return redirect(url_for('admin_applications'))

@app.route('/admin/export_csv')
@admin_required
def export_csv():
    conn = sqlite3.connect('admission_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students ORDER BY created_at DESC")
    applications = cursor.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Name', 'Date of Birth', 'Gender', 'Email', 'Phone', 'Address', 
                     'Course', 'Previous Education', 'Status', 'Application ID', 'Created At', 'Admin Notes'])
    
    # Write data
    for app in applications:
        writer.writerow(app)
    
    # Create file-like object
    output.seek(0)
    
    # Create response
    output_bytes = io.BytesIO()
    output_bytes.write(output.getvalue().encode('utf-8'))
    output_bytes.seek(0)
    
    return send_file(output_bytes,
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name=f'applications_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
