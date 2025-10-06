import sqlite3
import hashlib

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_database():
    """Initialize the database with required tables and default admin"""
    conn = sqlite3.connect('admission_system.db')
    cursor = conn.cursor()
    
    # Create students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dob DATE NOT NULL,
            gender TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            course TEXT NOT NULL,
            previous_education TEXT NOT NULL,
            documents_path TEXT,
            status TEXT DEFAULT 'Pending',
            application_id TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            admin_notes TEXT,
            document_status TEXT DEFAULT 'Pending',
            document_notes TEXT
        )
    ''')
    
    # Create admins table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default admin if not exists
    cursor.execute("SELECT COUNT(*) FROM admins WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        default_password = hash_password('admin123')
        cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)", 
                      ('admin', default_password))
    
    # Add document_status and document_notes columns if they don't exist
    cursor.execute("PRAGMA table_info(students)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'document_status' not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN document_status TEXT DEFAULT 'Pending'")
        print("Added document_status column")
    
    if 'document_notes' not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN document_notes TEXT")
        print("Added document_notes column")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()
