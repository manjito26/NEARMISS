"""
Database model for NEARMISS System
Handles SQL Server connection and database operations
"""
import pytds
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class NearMissDatabase:
    def __init__(self):
        self.connection_params = {
            'dsn': '192.168.10.70',
            'port': 1433,
            'database': 'NEARMISS',
            'user': 'SA',
            'password': 'GreenCandyOneBang',
            'autocommit': True,
            'timeout': 10
        }
    
    def get_connection(self):
        """Get database connection"""
        try:
            conn = pytds.connect(**self.connection_params)
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def create_database(self):
        """Create NEARMISS database if it doesn't exist"""
        conn_params = self.connection_params.copy()
        conn_params['database'] = 'master'  # Connect to master to create database
        
        try:
            conn = pytds.connect(**conn_params)
            cursor = conn.cursor()
            cursor.execute("IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'NEARMISS') CREATE DATABASE NEARMISS")
            logger.info("NEARMISS database created successfully")
            conn.close()
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    def create_tables(self):
        """Create all necessary tables"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
                CREATE TABLE users (
                    user_id INT IDENTITY(1,1) PRIMARY KEY,
                    first_name NVARCHAR(50) NOT NULL,
                    last_name NVARCHAR(50) NOT NULL,
                    username NVARCHAR(50) UNIQUE NOT NULL,
                    email NVARCHAR(100) NOT NULL,
                    plant NVARCHAR(20) NOT NULL,
                    is_admin BIT DEFAULT 0,
                    is_supervisor BIT DEFAULT 0,
                    password_hash NVARCHAR(255) NULL,
                    created_date DATETIME DEFAULT GETDATE()
                )
            """)
            
            # Create departments table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='departments' AND xtype='U')
                CREATE TABLE departments (
                    dept_id INT IDENTITY(1,1) PRIMARY KEY,
                    plant NVARCHAR(20) NOT NULL,
                    dept_name NVARCHAR(100) NOT NULL
                )
            """)
            
            # Create equipment table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='equipment' AND xtype='U')
                CREATE TABLE equipment (
                    equip_id INT IDENTITY(1,1) PRIMARY KEY,
                    plant NVARCHAR(20) NOT NULL,
                    dept_id INT NOT NULL,
                    equip_name NVARCHAR(100) NOT NULL,
                    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
                )
            """)
            
            # Create hazard_types table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='hazard_types' AND xtype='U')
                CREATE TABLE hazard_types (
                    hazard_type_id INT IDENTITY(1,1) PRIMARY KEY,
                    hazard_type NVARCHAR(100) NOT NULL
                )
            """)
            
            # Create immediate_actions table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='immediate_actions' AND xtype='U')
                CREATE TABLE immediate_actions (
                    action_id INT IDENTITY(1,1) PRIMARY KEY,
                    action_description NVARCHAR(200) NOT NULL
                )
            """)
            
            # Create near_miss_reports table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='near_miss_reports' AND xtype='U')
                CREATE TABLE near_miss_reports (
                    report_id INT IDENTITY(1,1) PRIMARY KEY,
                    date_occurred DATE NOT NULL,
                    time_occurred TIME NOT NULL,
                    employee_id INT NOT NULL,
                    plant NVARCHAR(20) NOT NULL,
                    dept_id INT NULL,
                    equipment_area NVARCHAR(100) NULL,
                    hazard_assessment NVARCHAR(20) NULL,
                    hazard_type_id INT NULL,
                    custom_hazard_type NVARCHAR(100) NULL,
                    description NVARCHAR(400) NOT NULL,
                    immediate_action_id INT NULL,
                    corrective_action TEXT NULL,
                    responsible_party_id INT NULL,
                    corrective_action_completed BIT DEFAULT 0,
                    completion_date DATE NULL,
                    completed_by_id INT NULL,
                    created_by_id INT NOT NULL,
                    created_date DATETIME DEFAULT GETDATE(),
                    FOREIGN KEY (employee_id) REFERENCES users(user_id),
                    FOREIGN KEY (dept_id) REFERENCES departments(dept_id),
                    FOREIGN KEY (hazard_type_id) REFERENCES hazard_types(hazard_type_id),
                    FOREIGN KEY (immediate_action_id) REFERENCES immediate_actions(action_id),
                    FOREIGN KEY (responsible_party_id) REFERENCES users(user_id),
                    FOREIGN KEY (completed_by_id) REFERENCES users(user_id),
                    FOREIGN KEY (created_by_id) REFERENCES users(user_id)
                )
            """)
            
            # Create attachments table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='attachments' AND xtype='U')
                CREATE TABLE attachments (
                    attachment_id INT IDENTITY(1,1) PRIMARY KEY,
                    report_id INT NOT NULL,
                    filename NVARCHAR(255) NOT NULL,
                    file_path NVARCHAR(500) NOT NULL,
                    uploaded_date DATETIME DEFAULT GETDATE(),
                    FOREIGN KEY (report_id) REFERENCES near_miss_reports(report_id)
                )
            """)
            
            # Create edit_history table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='edit_history' AND xtype='U')
                CREATE TABLE edit_history (
                    history_id INT IDENTITY(1,1) PRIMARY KEY,
                    report_id INT NOT NULL,
                    user_id INT NOT NULL,
                    field_changed NVARCHAR(50) NOT NULL,
                    old_value NVARCHAR(500) NULL,
                    new_value NVARCHAR(500) NULL,
                    changed_date DATETIME DEFAULT GETDATE(),
                    FOREIGN KEY (report_id) REFERENCES near_miss_reports(report_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Create email_config table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='email_config' AND xtype='U')
                CREATE TABLE email_config (
                    config_id INT IDENTITY(1,1) PRIMARY KEY,
                    smtp_server NVARCHAR(100) NULL,
                    smtp_port INT NULL,
                    username NVARCHAR(100) NULL,
                    password_encrypted NVARCHAR(255) NULL,
                    auth_type NVARCHAR(20) NULL,
                    use_auth BIT DEFAULT 1,
                    timeout INT DEFAULT 30,
                    retries INT DEFAULT 3
                )
            """)
            
            # Create email_queue table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='email_queue' AND xtype='U')
                CREATE TABLE email_queue (
                    queue_id INT IDENTITY(1,1) PRIMARY KEY,
                    to_address NVARCHAR(100) NOT NULL,
                    subject NVARCHAR(200) NOT NULL,
                    body TEXT NOT NULL,
                    report_id INT NULL,
                    status NVARCHAR(20) DEFAULT 'pending',
                    created_date DATETIME DEFAULT GETDATE(),
                    sent_date DATETIME NULL,
                    retry_count INT DEFAULT 0,
                    FOREIGN KEY (report_id) REFERENCES near_miss_reports(report_id)
                )
            """)
            
            # Create email_history table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='email_history' AND xtype='U')
                CREATE TABLE email_history (
                    history_id INT IDENTITY(1,1) PRIMARY KEY,
                    to_address NVARCHAR(100) NOT NULL,
                    subject NVARCHAR(200) NOT NULL,
                    report_id INT NULL,
                    sent_date DATETIME DEFAULT GETDATE(),
                    status NVARCHAR(20) NOT NULL,
                    FOREIGN KEY (report_id) REFERENCES near_miss_reports(report_id)
                )
            """)
            
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
        finally:
            conn.close()
    
    def insert_initial_data(self):
        """Insert initial data including default admin user and dropdown data"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Insert default admin user (Caleb Kull)
            password_hash = hashlib.sha256("mera7".encode()).hexdigest()
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'ckull')
                INSERT INTO users (first_name, last_name, username, email, plant, is_admin, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ("Caleb", "Kull", "ckull", "ckull@fresco.com", "Red Oak", 1, password_hash))
            
            # Insert departments for both plants
            departments = [
                ("Red Oak", "Press"),
                ("Red Oak", "Make Ready"),
                ("Red Oak", "Ink Room"),
                ("Red Oak", "Slit/Pack"),
                ("Red Oak", "Warehouse"),
                ("Red Oak", "Maintenance"),
                ("Telford", "Press"),
                ("Telford", "Make Ready"),
                ("Telford", "Ink Room"),
                ("Telford", "Slit/Pack"),
                ("Telford", "Warehouse"),
                ("Telford", "Maintenance")
            ]
            
            for plant, dept_name in departments:
                cursor.execute("""
                    IF NOT EXISTS (SELECT 1 FROM departments WHERE plant = %s AND dept_name = %s)
                    INSERT INTO departments (plant, dept_name) VALUES (%s, %s)
                """, (plant, dept_name, plant, dept_name))
            
            # Insert hazard types
            hazard_types = [
                "Slip / trip / fall",
                "Fall from height",
                "Struck by (object, vehicle, equipment, load)",
                "Struck against (stationary object, equipment, etc.)",
                "Caught in / between",
                "Pinch point",
                "Cuts / lacerations",
                "Chemical exposure",
                "Heat / burn",
                "Electrical",
                "Fire / explosion",
                "Machinery / equipment malfunction",
                "Lifting / ergonomic",
                "Respiratory / inhalation",
                "Eye injury",
                "Noise exposure",
                "Environmental"
            ]
            
            for hazard_type in hazard_types:
                cursor.execute("""
                    IF NOT EXISTS (SELECT 1 FROM hazard_types WHERE hazard_type = %s)
                    INSERT INTO hazard_types (hazard_type) VALUES (%s)
                """, (hazard_type, hazard_type))
            
            # Insert immediate actions
            immediate_actions = [
                "Hazard corrected / removed immediately",
                "Area cleaned or debris removed",
                "Area isolated / barricaded / tagged off",
                "Equipment shut down / locked out",
                "Reported to supervisor or line owner",
                "Reported to safety",
                "PPE provided",
                "Training provided",
                "Procedure reviewed / updated",
                "Warning signs posted",
                "Temporary repairs made",
                "Work order submitted",
                "Incident documented",
                "Other personnel notified",
                "No immediate action taken"
            ]
            
            for action in immediate_actions:
                cursor.execute("""
                    IF NOT EXISTS (SELECT 1 FROM immediate_actions WHERE action_description = %s)
                    INSERT INTO immediate_actions (action_description) VALUES (%s)
                """, (action, action))
            
            logger.info("Initial data inserted successfully")
            
        except Exception as e:
            logger.error(f"Error inserting initial data: {e}")
            raise
        finally:
            conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash a password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        return self.hash_password(password) == password_hash
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, first_name, last_name, username, email, plant, is_admin, is_supervisor, password_hash
                FROM users WHERE username = %s
            """, (username,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'user_id': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'username': row[3],
                    'email': row[4],
                    'plant': row[5],
                    'is_admin': row[6],
                    'is_supervisor': row[7],
                    'password_hash': row[8]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
        finally:
            conn.close()
    
    def get_all_users(self, plant: str = None) -> List[Dict]:
        """Get all users, optionally filtered by plant"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT user_id, first_name, last_name, username, email, plant, is_admin, is_supervisor
                FROM users
            """
            params = []
            
            if plant:
                query += " WHERE plant = %s"
                params.append(plant)
            
            query += " ORDER BY last_name, first_name"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            users = []
            for row in rows:
                users.append({
                    'user_id': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'username': row[3],
                    'email': row[4],
                    'plant': row[5],
                    'is_admin': row[6],
                    'is_supervisor': row[7]
                })
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
        finally:
            conn.close()
    
    def get_departments(self, plant: str = None) -> List[Dict]:
        """Get departments, optionally filtered by plant"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            query = "SELECT dept_id, plant, dept_name FROM departments"
            params = []
            
            if plant:
                query += " WHERE plant = %s"
                params.append(plant)
                
            query += " ORDER BY dept_name"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [{'dept_id': row[0], 'plant': row[1], 'dept_name': row[2]} for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting departments: {e}")
            return []
        finally:
            conn.close()
    
    def get_equipment(self, plant: str = None, dept_id: int = None) -> List[Dict]:
        """Get equipment, optionally filtered by plant and department"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT e.equip_id, e.plant, e.dept_id, e.equip_name, d.dept_name
                FROM equipment e
                JOIN departments d ON e.dept_id = d.dept_id
                WHERE 1=1
            """
            params = []
            
            if plant:
                query += " AND e.plant = %s"
                params.append(plant)
                
            if dept_id:
                query += " AND e.dept_id = %s"
                params.append(dept_id)
                
            query += " ORDER BY e.equip_name"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [{
                'equip_id': row[0], 
                'plant': row[1], 
                'dept_id': row[2], 
                'equip_name': row[3],
                'dept_name': row[4]
            } for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting equipment: {e}")
            return []
        finally:
            conn.close()
    
    def get_hazard_types(self) -> List[Dict]:
        """Get all hazard types"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT hazard_type_id, hazard_type FROM hazard_types ORDER BY hazard_type")
            rows = cursor.fetchall()
            return [{'hazard_type_id': row[0], 'hazard_type': row[1]} for row in rows]
        except Exception as e:
            logger.error(f"Error getting hazard types: {e}")
            return []
        finally:
            conn.close()
    
    def get_immediate_actions(self) -> List[Dict]:
        """Get all immediate actions"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT action_id, action_description FROM immediate_actions ORDER BY action_description")
            rows = cursor.fetchall()
            return [{'action_id': row[0], 'action_description': row[1]} for row in rows]
        except Exception as e:
            logger.error(f"Error getting immediate actions: {e}")
            return []
        finally:
            conn.close()
    
    def create_near_miss_report(self, data: Dict, created_by_id: int) -> bool:
        """Create a new near miss report"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Convert checkbox value to boolean
            corrective_completed = 1 if data.get('corrective_action_completed') == 'on' else 0
            
            cursor.execute("""
                INSERT INTO near_miss_reports (
                    date_occurred, time_occurred, employee_id, plant, dept_id, 
                    equipment_area, hazard_assessment, hazard_type_id, 
                    custom_hazard_type, description, immediate_action_id, 
                    corrective_action, responsible_party_id, corrective_action_completed,
                    completion_date, completed_by_id, created_by_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data.get('date_occurred'),
                data.get('time_occurred'),
                data.get('employee_id'),
                data.get('plant'),
                data.get('dept_id') if data.get('dept_id') else None,
                data.get('equipment_area'),
                data.get('hazard_assessment'),
                data.get('hazard_type_id') if data.get('hazard_type_id') else None,
                data.get('custom_hazard_type'),
                data.get('description'),
                data.get('immediate_action_id') if data.get('immediate_action_id') else None,
                data.get('corrective_action'),
                data.get('responsible_party_id') if data.get('responsible_party_id') else None,
                corrective_completed,
                data.get('completion_date') if data.get('completion_date') else None,
                data.get('completed_by_id') if data.get('completed_by_id') else None,
                created_by_id
            ))
            
            logger.info(f"Near miss report created successfully by user {created_by_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating near miss report: {e}")
            return False
        finally:
            conn.close()
    
    def get_near_miss_reports(self, search_query: str = "", plant_filter: str = "", 
                             user_filter: str = "", date_from: str = "", date_to: str = "") -> List[Dict]:
        """Get near miss reports with filtering"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    r.report_id, r.date_occurred, r.time_occurred, r.plant,
                    u.first_name + ' ' + u.last_name as employee_name,
                    d.dept_name, r.equipment_area, r.hazard_assessment,
                    ht.hazard_type, r.custom_hazard_type, r.description,
                    ia.action_description, r.corrective_action,
                    rp.first_name + ' ' + rp.last_name as responsible_party,
                    r.corrective_action_completed, r.completion_date,
                    cb.first_name + ' ' + cb.last_name as completed_by,
                    cr.first_name + ' ' + cr.last_name as created_by,
                    r.created_date
                FROM near_miss_reports r
                LEFT JOIN users u ON r.employee_id = u.user_id
                LEFT JOIN departments d ON r.dept_id = d.dept_id
                LEFT JOIN hazard_types ht ON r.hazard_type_id = ht.hazard_type_id
                LEFT JOIN immediate_actions ia ON r.immediate_action_id = ia.action_id
                LEFT JOIN users rp ON r.responsible_party_id = rp.user_id
                LEFT JOIN users cb ON r.completed_by_id = cb.user_id
                LEFT JOIN users cr ON r.created_by_id = cr.user_id
                WHERE 1=1
            """
            
            params = []
            
            if search_query:
                query += " AND (r.description LIKE %s OR u.first_name LIKE %s OR u.last_name LIKE %s)"
                search_param = f"%{search_query}%"
                params.extend([search_param, search_param, search_param])
            
            if plant_filter:
                query += " AND r.plant = %s"
                params.append(plant_filter)
            
            if user_filter:
                query += " AND u.username = %s"
                params.append(user_filter)
            
            if date_from:
                query += " AND r.date_occurred >= %s"
                params.append(date_from)
                
            if date_to:
                query += " AND r.date_occurred <= %s"
                params.append(date_to)
            
            query += " ORDER BY r.created_date DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            reports = []
            for row in rows:
                reports.append({
                    'report_id': row[0],
                    'date_occurred': row[1],
                    'time_occurred': row[2],
                    'plant': row[3],
                    'employee_name': row[4],
                    'dept_name': row[5],
                    'equipment_area': row[6],
                    'hazard_assessment': row[7],
                    'hazard_type': row[8],
                    'custom_hazard_type': row[9],
                    'description': row[10],
                    'action_description': row[11],
                    'corrective_action': row[12],
                    'responsible_party': row[13],
                    'corrective_action_completed': row[14],
                    'completion_date': row[15],
                    'completed_by': row[16],
                    'created_by': row[17],
                    'created_date': row[18]
                })
            
            return reports
            
        except Exception as e:
            logger.error(f"Error getting near miss reports: {e}")
            return []
        finally:
            conn.close()
    
    def add_user(self, first_name: str, last_name: str, username: str, plant: str, email: str = None) -> Optional[int]:
        """Add a new user and return user_id"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            if not email:
                email = f"{username}@fresco.com"
            
            cursor.execute("""
                INSERT INTO users (first_name, last_name, username, email, plant)
                OUTPUT INSERTED.user_id
                VALUES (%s, %s, %s, %s, %s)
            """, (first_name, last_name, username, email, plant))
            
            result = cursor.fetchone()
            if result:
                user_id = result[0]
                logger.info(f"User added successfully: {username} (ID: {user_id})")
                return user_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return None
        finally:
            conn.close()
