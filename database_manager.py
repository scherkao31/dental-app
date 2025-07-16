import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import uuid
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

class PracticeDatabase:
    def __init__(self, db_path: str = "practice.db"):
        self.db_path = db_path
        self.db_type = self._determine_db_type()
        self.init_database()
    
    def _determine_db_type(self):
        """Determine database type based on environment"""
        database_url = os.getenv('DATABASE_URL')
        if database_url and database_url.startswith('postgresql'):
            return 'postgresql'
        return 'sqlite'
    
    def _get_connection(self):
        """Get database connection based on type"""
        if self.db_type == 'postgresql':
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL environment variable is required for PostgreSQL")
            
            # Parse the database URL
            parsed = urlparse(database_url)
            
            return psycopg2.connect(
                host=parsed.hostname,
                database=parsed.path[1:],  # Remove leading slash
                user=parsed.username,
                password=parsed.password,
                port=parsed.port or 5432,
                cursor_factory=RealDictCursor
            )
        else:
            return sqlite3.connect(self.db_path)
    
    def _execute_query(self, query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
        """Execute query with proper connection handling"""
        conn = self._get_connection()
        
        try:
            if self.db_type == 'postgresql':
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                
                if fetch_one:
                    result = cursor.fetchone()
                    return dict(result) if result else None
                elif fetch_all:
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                else:
                    conn.commit()
                    return cursor.rowcount
            else:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                
                if fetch_one:
                    result = cursor.fetchone()
                    if result:
                        columns = [desc[0] for desc in cursor.description]
                        return dict(zip(columns, result))
                    return None
                elif fetch_all:
                    results = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in results]
                else:
                    conn.commit()
                    return cursor.rowcount
        finally:
            conn.close()

    def init_database(self):
        """Initialize the database with required tables"""
        # PostgreSQL and SQLite have slightly different syntax
        if self.db_type == 'postgresql':
            self._init_postgresql()
        else:
            self._init_sqlite()
        
        # Initialize pricing data
        self.initialize_swiss_pricing()
        
        print(f"✅ Database initialized successfully ({self.db_type})")
    
    def _init_sqlite(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                birth_date DATE,
                address TEXT,
                medical_history TEXT,
                allergies TEXT,
                emergency_contact TEXT,
                insurance_info TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id TEXT PRIMARY KEY,
                patient_id TEXT,
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                duration_minutes INTEGER DEFAULT 60,
                treatment_type TEXT,
                status TEXT DEFAULT 'scheduled',
                doctor TEXT DEFAULT 'Dr.',
                room TEXT,
                notes TEXT,
                treatment_plan_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')
        
        # Treatment plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS treatment_plans (
                id TEXT PRIMARY KEY,
                patient_id TEXT,
                plan_data TEXT NOT NULL,
                consultation_text TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')
        
        # Schedule blocks table (for blocking time slots)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule_blocks (
                id TEXT PRIMARY KEY,
                block_date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                block_type TEXT DEFAULT 'unavailable',
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Swiss dental pricing table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dental_pricing (
                id TEXT PRIMARY KEY,
                tarmed_code TEXT UNIQUE,
                treatment_name TEXT NOT NULL,
                treatment_category TEXT,
                base_price_chf REAL NOT NULL,
                lamal_covered BOOLEAN DEFAULT FALSE,
                lamal_percentage REAL DEFAULT 0.0,
                description TEXT,
                duration_minutes INTEGER DEFAULT 60,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Continue with other tables...
        self._create_remaining_tables_sqlite(cursor)
        
        conn.commit()
        conn.close()
    
    def _init_postgresql(self):
        """Initialize PostgreSQL database"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                birth_date DATE,
                address TEXT,
                medical_history TEXT,
                allergies TEXT,
                emergency_contact TEXT,
                insurance_info TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id TEXT PRIMARY KEY,
                patient_id TEXT,
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                duration_minutes INTEGER DEFAULT 60,
                treatment_type TEXT,
                status TEXT DEFAULT 'scheduled',
                doctor TEXT DEFAULT 'Dr.',
                room TEXT,
                notes TEXT,
                treatment_plan_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')
        
        # Treatment plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS treatment_plans (
                id TEXT PRIMARY KEY,
                patient_id TEXT,
                plan_data TEXT NOT NULL,
                consultation_text TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')
        
        # Schedule blocks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule_blocks (
                id TEXT PRIMARY KEY,
                block_date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                block_type TEXT DEFAULT 'unavailable',
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Swiss dental pricing table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dental_pricing (
                id TEXT PRIMARY KEY,
                tarmed_code TEXT UNIQUE,
                treatment_name TEXT NOT NULL,
                treatment_category TEXT,
                base_price_chf REAL NOT NULL,
                lamal_covered BOOLEAN DEFAULT FALSE,
                lamal_percentage REAL DEFAULT 0.0,
                description TEXT,
                duration_minutes INTEGER DEFAULT 60,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Continue with other tables...
        self._create_remaining_tables_postgresql(cursor)
        
        conn.commit()
        conn.close()
    
    def _create_remaining_tables_sqlite(self, cursor):
        """Create remaining tables for SQLite"""
        # Invoices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                treatment_plan_id TEXT,
                invoice_number TEXT UNIQUE NOT NULL,
                invoice_date TEXT NOT NULL,
                due_date TEXT,
                total_amount_chf REAL NOT NULL,
                lamal_amount_chf REAL DEFAULT 0.0,
                insurance_amount_chf REAL DEFAULT 0.0,
                patient_amount_chf REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')
        
        # Invoice items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_items (
                id TEXT PRIMARY KEY,
                invoice_id TEXT NOT NULL,
                tarmed_code TEXT,
                treatment_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                unit_price_chf REAL NOT NULL,
                total_price_chf REAL NOT NULL,
                lamal_covered BOOLEAN DEFAULT FALSE,
                lamal_amount_chf REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id)
            )
        ''')
        
        # Continue with other tables...
        self._create_additional_tables_sqlite(cursor)
    
    def _create_remaining_tables_postgresql(self, cursor):
        """Create remaining tables for PostgreSQL"""
        # Invoices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                treatment_plan_id TEXT,
                invoice_number TEXT UNIQUE NOT NULL,
                invoice_date TEXT NOT NULL,
                due_date TEXT,
                total_amount_chf REAL NOT NULL,
                lamal_amount_chf REAL DEFAULT 0.0,
                insurance_amount_chf REAL DEFAULT 0.0,
                patient_amount_chf REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')
        
        # Invoice items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_items (
                id TEXT PRIMARY KEY,
                invoice_id TEXT NOT NULL,
                tarmed_code TEXT,
                treatment_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                unit_price_chf REAL NOT NULL,
                total_price_chf REAL NOT NULL,
                lamal_covered BOOLEAN DEFAULT FALSE,
                lamal_amount_chf REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id)
            )
        ''')
        
        # Continue with other tables...
        self._create_additional_tables_postgresql(cursor)
    
    def _create_additional_tables_sqlite(self, cursor):
        """Create additional tables for SQLite"""
        # Payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                invoice_id TEXT NOT NULL,
                payment_date TEXT NOT NULL,
                amount_chf REAL NOT NULL,
                payment_method TEXT,
                reference_number TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id)
            )
        ''')
        
        # Devis (estimates) table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devis (
                id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                treatment_plan_id TEXT,
                devis_number TEXT UNIQUE NOT NULL,
                devis_date TEXT NOT NULL,
                valid_until TEXT,
                total_amount_chf REAL NOT NULL,
                lamal_amount_chf REAL DEFAULT 0.0,
                insurance_amount_chf REAL DEFAULT 0.0,
                patient_amount_chf REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                approved_date TEXT,
                rejected_date TEXT,
                rejection_reason TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (treatment_plan_id) REFERENCES treatment_plans (id)
            )
        ''')
        
        # Continue with remaining tables...
        self._create_final_tables_sqlite(cursor)
    
    def _create_additional_tables_postgresql(self, cursor):
        """Create additional tables for PostgreSQL"""
        # Payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                invoice_id TEXT NOT NULL,
                payment_date TEXT NOT NULL,
                amount_chf REAL NOT NULL,
                payment_method TEXT,
                reference_number TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id)
            )
        ''')
        
        # Devis (estimates) table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devis (
                id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                treatment_plan_id TEXT,
                devis_number TEXT UNIQUE NOT NULL,
                devis_date TEXT NOT NULL,
                valid_until TEXT,
                total_amount_chf REAL NOT NULL,
                lamal_amount_chf REAL DEFAULT 0.0,
                insurance_amount_chf REAL DEFAULT 0.0,
                patient_amount_chf REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                approved_date TEXT,
                rejected_date TEXT,
                rejection_reason TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (treatment_plan_id) REFERENCES treatment_plans (id)
            )
        ''')
        
        # Continue with remaining tables...
        self._create_final_tables_postgresql(cursor)
    
    def _create_final_tables_sqlite(self, cursor):
        """Create final tables for SQLite"""
        # Devis items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devis_items (
                id TEXT PRIMARY KEY,
                devis_id TEXT NOT NULL,
                tarmed_code TEXT,
                treatment_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                unit_price_chf REAL NOT NULL,
                total_price_chf REAL NOT NULL,
                lamal_covered BOOLEAN DEFAULT FALSE,
                lamal_amount_chf REAL DEFAULT 0.0,
                discount_percentage REAL DEFAULT 0.0,
                discount_amount_chf REAL DEFAULT 0.0,
                final_price_chf REAL NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (devis_id) REFERENCES devis (id)
            )
        ''')
        
        # Payment plans table for flexible payment options
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_plans (
                id TEXT PRIMARY KEY,
                invoice_id TEXT NOT NULL,
                plan_name TEXT NOT NULL,
                total_amount_chf REAL NOT NULL,
                number_of_payments INTEGER NOT NULL,
                payment_frequency TEXT DEFAULT 'monthly',
                first_payment_date TEXT NOT NULL,
                payment_amount_chf REAL NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id)
            )
        ''')
        
        # Scheduled payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_payments (
                id TEXT PRIMARY KEY,
                payment_plan_id TEXT NOT NULL,
                payment_number INTEGER NOT NULL,
                scheduled_date TEXT NOT NULL,
                amount_chf REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                actual_payment_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (payment_plan_id) REFERENCES payment_plans (id),
                FOREIGN KEY (actual_payment_id) REFERENCES payments (id)
            )
        ''')
        
        # Expected revenue table for financial forecasting
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expected_revenue (
                id TEXT PRIMARY KEY,
                invoice_id TEXT NOT NULL,
                devis_id TEXT,
                expected_date TEXT NOT NULL,
                expected_amount_chf REAL NOT NULL,
                actual_amount_chf REAL DEFAULT 0.0,
                status TEXT DEFAULT 'pending',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id),
                FOREIGN KEY (devis_id) REFERENCES devis (id)
            )
        ''')
        
        # Patient education documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_education (
                id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                treatment_plan_id TEXT,
                education_content TEXT NOT NULL,
                education_title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (treatment_plan_id) REFERENCES treatment_plans (id)
            )
        ''')
    
    def _create_final_tables_postgresql(self, cursor):
        """Create final tables for PostgreSQL"""
        # Devis items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devis_items (
                id TEXT PRIMARY KEY,
                devis_id TEXT NOT NULL,
                tarmed_code TEXT,
                treatment_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                unit_price_chf REAL NOT NULL,
                total_price_chf REAL NOT NULL,
                lamal_covered BOOLEAN DEFAULT FALSE,
                lamal_amount_chf REAL DEFAULT 0.0,
                discount_percentage REAL DEFAULT 0.0,
                discount_amount_chf REAL DEFAULT 0.0,
                final_price_chf REAL NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (devis_id) REFERENCES devis (id)
            )
        ''')
        
        # Payment plans table for flexible payment options
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_plans (
                id TEXT PRIMARY KEY,
                invoice_id TEXT NOT NULL,
                plan_name TEXT NOT NULL,
                total_amount_chf REAL NOT NULL,
                number_of_payments INTEGER NOT NULL,
                payment_frequency TEXT DEFAULT 'monthly',
                first_payment_date TEXT NOT NULL,
                payment_amount_chf REAL NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id)
            )
        ''')
        
        # Scheduled payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_payments (
                id TEXT PRIMARY KEY,
                payment_plan_id TEXT NOT NULL,
                payment_number INTEGER NOT NULL,
                scheduled_date TEXT NOT NULL,
                amount_chf REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                actual_payment_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (payment_plan_id) REFERENCES payment_plans (id),
                FOREIGN KEY (actual_payment_id) REFERENCES payments (id)
            )
        ''')
        
        # Expected revenue table for financial forecasting
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expected_revenue (
                id TEXT PRIMARY KEY,
                invoice_id TEXT NOT NULL,
                devis_id TEXT,
                expected_date TEXT NOT NULL,
                expected_amount_chf REAL NOT NULL,
                actual_amount_chf REAL DEFAULT 0.0,
                status TEXT DEFAULT 'pending',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id),
                FOREIGN KEY (devis_id) REFERENCES devis (id)
            )
        ''')
        
        # Patient education documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_education (
                id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                treatment_plan_id TEXT,
                education_content TEXT NOT NULL,
                education_title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (treatment_plan_id) REFERENCES treatment_plans (id)
            )
        ''')

    def add_patient(self, patient_data: Dict[str, Any]) -> str:
        """Add a new patient"""
        patient_id = str(uuid.uuid4())
        
        query = '''
            INSERT INTO patients (
                id, first_name, last_name, email, phone, birth_date,
                address, medical_history, allergies, emergency_contact,
                insurance_info, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        params = (
            patient_id,
            patient_data.get('first_name', ''),
            patient_data.get('last_name', ''),
            patient_data.get('email', ''),
            patient_data.get('phone', ''),
            patient_data.get('birth_date', ''),
            patient_data.get('address', ''),
            patient_data.get('medical_history', ''),
            patient_data.get('allergies', ''),
            patient_data.get('emergency_contact', ''),
            patient_data.get('insurance_info', ''),
            patient_data.get('notes', '')
        )
        
        self._execute_query(query, params)
        return patient_id
    
    def get_patients(self, search_term: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all patients or search by name/email"""
        if search_term:
            query = '''
                SELECT * FROM patients 
                WHERE first_name LIKE ? OR last_name LIKE ? OR email LIKE ?
                ORDER BY last_name, first_name
            '''
            params = (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%')
        else:
            query = 'SELECT * FROM patients ORDER BY last_name, first_name'
            params = None
        
        return self._execute_query(query, params, fetch_all=True)

    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific patient by ID"""
        query = 'SELECT * FROM patients WHERE id = ?'
        params = (patient_id,)
        
        return self._execute_query(query, params, fetch_one=True)

    def create_patient(self, **patient_data) -> str:
        """Create a new patient"""
        patient_id = str(uuid.uuid4())
        
        query = '''
            INSERT INTO patients (
                id, first_name, last_name, email, phone, birth_date,
                address, medical_history, allergies, emergency_contact,
                insurance_info, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        params = (
            patient_id,
            patient_data.get('first_name'),
            patient_data.get('last_name'),
            patient_data.get('email'),
            patient_data.get('phone'),
            patient_data.get('birth_date'),
            patient_data.get('address'),
            patient_data.get('medical_history'),
            patient_data.get('allergies'),
            patient_data.get('emergency_contact'),
            patient_data.get('insurance_info'),
            patient_data.get('notes'),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        )
        
        self._execute_query(query, params)
        return patient_id

    def update_patient(self, patient_id: str, **patient_data) -> bool:
        """Update an existing patient"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE patients SET
                first_name = ?, last_name = ?, email = ?, phone = ?, birth_date = ?,
                address = ?, medical_history = ?, allergies = ?, emergency_contact = ?,
                insurance_info = ?, notes = ?, updated_at = ?
            WHERE id = ?
        ''', (
            patient_data.get('first_name'),
            patient_data.get('last_name'),
            patient_data.get('email'),
            patient_data.get('phone'),
            patient_data.get('birth_date'),
            patient_data.get('address'),
            patient_data.get('medical_history'),
            patient_data.get('allergies'),
            patient_data.get('emergency_contact'),
            patient_data.get('insurance_info'),
            patient_data.get('notes'),
            datetime.now().isoformat(),
            patient_id
        ))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def add_appointment(self, appointment_data: Dict[str, Any]) -> str:
        """Add a new appointment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        appointment_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO appointments (
                id, patient_id, appointment_date, appointment_time,
                duration_minutes, treatment_type, status, doctor,
                room, notes, treatment_plan_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            appointment_id,
            appointment_data.get('patient_id'),
            appointment_data.get('appointment_date'),
            appointment_data.get('appointment_time'),
            appointment_data.get('duration_minutes', 60),
            appointment_data.get('treatment_type', ''),
            appointment_data.get('status', 'scheduled'),
            appointment_data.get('doctor', 'Dr.'),
            appointment_data.get('room', ''),
            appointment_data.get('notes', ''),
            appointment_data.get('treatment_plan_id', '')
        ))
        
        conn.commit()
        conn.close()
        return appointment_id

    def get_appointments(self, date: str = None, patient_id: str = None) -> List[Dict]:
        """Get appointments by date or patient"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT a.*, p.first_name, p.last_name, p.phone
            FROM appointments a
            LEFT JOIN patients p ON a.patient_id = p.id
        '''
        params = []
        
        if date and patient_id:
            query += ' WHERE a.appointment_date = ? AND a.patient_id = ?'
            params = [date, patient_id]
        elif date:
            query += ' WHERE a.appointment_date = ?'
            params = [date]
        elif patient_id:
            query += ' WHERE a.patient_id = ?'
            params = [patient_id]
        
        query += ' ORDER BY a.appointment_date, a.appointment_time'
        
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        appointments = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return appointments

    def get_schedule_for_week(self, start_date: str) -> List[Dict]:
        """Get appointments for a week starting from start_date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate end date (7 days later)
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = start_dt + timedelta(days=7)
        end_date = end_dt.strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT a.*, p.first_name, p.last_name, p.phone
            FROM appointments a
            LEFT JOIN patients p ON a.patient_id = p.id
            WHERE a.appointment_date >= ? AND a.appointment_date < ?
            ORDER BY a.appointment_date, a.appointment_time
        ''', (start_date, end_date))
        
        columns = [desc[0] for desc in cursor.description]
        appointments = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return appointments

    def save_treatment_plan(self, patient_id: str, plan_data: Dict, consultation_text: str = '') -> str:
        """Save a treatment plan for a patient"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        plan_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO treatment_plans (id, patient_id, plan_data, consultation_text)
            VALUES (?, ?, ?, ?)
        ''', (plan_id, patient_id, json.dumps(plan_data), consultation_text))
        
        conn.commit()
        conn.close()
        return plan_id

    def get_treatment_plans(self, patient_id: str) -> List[Dict]:
        """Get treatment plans for a patient"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM treatment_plans 
            WHERE patient_id = ? 
            ORDER BY created_at DESC
        ''', (patient_id,))
        
        columns = [desc[0] for desc in cursor.description]
        plans = []
        
        for row in cursor.fetchall():
            plan = dict(zip(columns, row))
            plan['plan_data'] = json.loads(plan['plan_data'])
            plans.append(plan)
        
        conn.close()
        return plans

    def create_treatment_plan(self, patient_id: str = None, consultation_text: str = '', 
                             treatment_data: Dict[str, Any] = None, treatment_sequence: List = None,
                             created_at: str = None, status: str = 'draft', **kwargs) -> str:
        """Create a new treatment plan"""
        plan_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Handle both old and new calling patterns
        if treatment_data is None and treatment_sequence is not None:
            treatment_data = {
                'treatment_sequence': treatment_sequence,
                'consultation_text': consultation_text,
                'status': status
            }
        elif treatment_data is None:
            treatment_data = {}
        
        if created_at is None:
            created_at = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO treatment_plans (
                id, patient_id, consultation_text, plan_data, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            plan_id,
            patient_id,
            consultation_text,
            json.dumps(treatment_data),
            status,
            created_at,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        return plan_id

    def schedule_treatment_sequence(self, patient_id: str, treatment_plan_id: str, 
                                  treatment_sequence: List[Dict], start_date: str) -> List[str]:
        """Schedule appointments for a treatment sequence"""
        appointment_ids = []
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        
        for i, treatment in enumerate(treatment_sequence):
            # Parse duration
            duration_str = treatment.get('duree', '60 min')
            duration_minutes = 60  # default
            
            if 'min' in duration_str:
                try:
                    duration_minutes = int(duration_str.split('min')[0].strip())
                except:
                    duration_minutes = 60
            elif 'h' in duration_str:
                try:
                    hours = float(duration_str.split('h')[0].strip())
                    duration_minutes = int(hours * 60)
                except:
                    duration_minutes = 60
            
            # Create appointment
            appointment_data = {
                'patient_id': patient_id,
                'appointment_date': current_date.strftime('%Y-%m-%d'),
                'appointment_time': '09:00',  # Default time, can be customized
                'duration_minutes': duration_minutes,
                'treatment_type': treatment.get('traitement', 'Traitement dentaire'),
                'status': 'scheduled',
                'doctor': treatment.get('dr', 'Dr.'),
                'notes': treatment.get('remarque', ''),
                'treatment_plan_id': treatment_plan_id
            }
            
            appointment_id = self.add_appointment(appointment_data)
            appointment_ids.append(appointment_id)
            
            # Calculate next appointment date based on delay
            delay_str = treatment.get('delai', '1 semaine')
            if 'jour' in delay_str:
                try:
                    days = int(delay_str.split('jour')[0].strip())
                    current_date += timedelta(days=days)
                except:
                    current_date += timedelta(days=7)
            elif 'semaine' in delay_str:
                try:
                    weeks = int(delay_str.split('semaine')[0].strip())
                    current_date += timedelta(weeks=weeks)
                except:
                    current_date += timedelta(weeks=1)
            else:
                current_date += timedelta(weeks=1)  # Default 1 week
        
        return appointment_ids

    def get_appointments_for_date(self, date: str) -> List[Dict[str, Any]]:
        """Get all appointments for a specific date"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, p.first_name, p.last_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE a.appointment_date = ? AND a.status != 'cancelled'
            ORDER BY a.appointment_time
        ''', (date,))
        
        appointments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return appointments

    def get_appointments_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get all appointments within a date range"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, patient_id, appointment_date as date, appointment_time as time,
                   duration_minutes, treatment_type as treatment, status, doctor, notes
            FROM appointments 
            WHERE appointment_date BETWEEN ? AND ?
            ORDER BY appointment_date, appointment_time
        ''', (start_date, end_date))
        
        appointments = []
        for row in cursor.fetchall():
            appointments.append({
                'id': row[0],
                'patient_id': row[1],
                'date': row[2],
                'time': row[3],
                'duration_minutes': row[4],
                'treatment': row[5],
                'status': row[6],
                'doctor': row[7],
                'notes': row[8],
                'duration': f"{row[4]} min"
            })
        
        conn.close()
        return appointments

    def get_available_slots(self, date: str, duration_minutes: int = 60) -> List[str]:
        """Get available time slots for a given date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get existing appointments for the date
        cursor.execute('''
            SELECT appointment_time, duration_minutes 
            FROM appointments 
            WHERE appointment_date = ? AND status != 'cancelled'
            ORDER BY appointment_time
        ''', (date,))
        
        booked_slots = cursor.fetchall()
        conn.close()
        
        # Define working hours (9 AM to 6 PM)
        working_start = 9 * 60  # 9:00 AM in minutes
        working_end = 18 * 60   # 6:00 PM in minutes
        
        # Generate all possible slots
        available_slots = []
        current_time = working_start
        
        while current_time + duration_minutes <= working_end:
            slot_time = f"{current_time // 60:02d}:{current_time % 60:02d}"
            
            # Check if this slot conflicts with existing appointments
            conflicts = False
            for booked_time, booked_duration in booked_slots:
                booked_minutes = int(booked_time.split(':')[0]) * 60 + int(booked_time.split(':')[1])
                
                # Check for overlap
                if (current_time < booked_minutes + booked_duration and 
                    current_time + duration_minutes > booked_minutes):
                    conflicts = True
                    break
            
            if not conflicts:
                available_slots.append(slot_time)
            
            current_time += 30  # 30-minute intervals
        
        return available_slots

    def delete_appointment(self, appointment_id: str) -> bool:
        """Delete an appointment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return success

    def update_appointment_status(self, appointment_id: str, status: str) -> bool:
        """Update appointment status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE appointments 
            SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (status, appointment_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success 

    def get_appointments(self, week_start: Optional[str] = None, patient_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get appointments for a specific week or patient"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if week_start:
            # Get appointments for the week starting from week_start
            week_end = (datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT a.*, p.first_name, p.last_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                WHERE a.appointment_date BETWEEN ? AND ?
                ORDER BY a.appointment_date, a.appointment_time
            ''', (week_start, week_end))
        elif patient_id:
            cursor.execute('''
                SELECT a.*, p.first_name, p.last_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                WHERE a.patient_id = ?
                ORDER BY a.appointment_date, a.appointment_time
            ''', (patient_id,))
        else:
            cursor.execute('''
                SELECT a.*, p.first_name, p.last_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                ORDER BY a.appointment_date, a.appointment_time
            ''')
        
        appointments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return appointments

    def create_appointment(self, **appointment_data) -> str:
        """Create a new appointment"""
        appointment_id = str(uuid.uuid4())
        
        query = '''
            INSERT INTO appointments (
                id, patient_id, treatment_plan_id, appointment_date, appointment_time,
                duration_minutes, treatment_type, doctor, notes, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        params = (
            appointment_id,
            appointment_data.get('patient_id'),
            appointment_data.get('treatment_plan_id'),
            appointment_data.get('appointment_date'),
            appointment_data.get('appointment_time'),
            appointment_data.get('duration_minutes', 60),
            appointment_data.get('treatment_type'),
            appointment_data.get('doctor'),
            appointment_data.get('notes'),
            appointment_data.get('status', 'scheduled'),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        )
        
        self._execute_query(query, params)
        return appointment_id

    def get_patient_details(self, patient_id: str) -> Dict[str, Any]:
        """Get patient with their treatment plans and appointments"""
        patient = self.get_patient(patient_id)
        if not patient:
            return None
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get treatment plans
        cursor.execute('''
            SELECT * FROM treatment_plans 
            WHERE patient_id = ?
            ORDER BY created_at DESC
        ''', (patient_id,))
        treatment_plans = [dict(row) for row in cursor.fetchall()]
        
        # Get appointments
        cursor.execute('''
            SELECT * FROM appointments 
            WHERE patient_id = ?
            ORDER BY appointment_date DESC, appointment_time DESC
        ''', (patient_id,))
        appointments = [dict(row) for row in cursor.fetchall()]
        
        # Get patient education documents
        cursor.execute('''
            SELECT * FROM patient_education 
            WHERE patient_id = ?
            ORDER BY created_at DESC
        ''', (patient_id,))
        education_documents = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'patient': patient,
            'treatment_plans': treatment_plans,
            'appointments': appointments,
            'education_documents': education_documents
        }

    def close(self):
        """Close database connection (if needed)"""
        pass 

    def initialize_swiss_pricing(self):
        """Initialize Swiss dental pricing based on TARMED and typical Swiss dental fees"""
        try:
            # Check if pricing data already exists
            count_result = self._execute_query("SELECT COUNT(*) FROM dental_pricing", fetch_one=True)
            if count_result and list(count_result.values())[0] > 0:
                print("✅ Swiss dental pricing already initialized")
                return
                
                # Swiss dental pricing data (based on TARMED and typical Swiss fees)
                pricing_data = [
                    # Basic treatments
                    ("00.0010", "Consultation initiale", "Consultation", 180.0, True, 90.0, "Première consultation avec examen clinique", 60),
                    ("00.0020", "Consultation de contrôle", "Consultation", 120.0, True, 90.0, "Consultation de suivi", 30),
                    ("00.0030", "Consultation d'urgence", "Consultation", 250.0, True, 90.0, "Consultation d'urgence", 45),
                    
                    # Diagnostics
                    ("39.0010", "Radiographie rétro-alvéolaire", "Radiologie", 35.0, True, 90.0, "Radiographie dentaire simple", 15),
                    ("39.0020", "Radiographie panoramique", "Radiologie", 85.0, True, 90.0, "Radiographie panoramique", 20),
                    ("39.0030", "Radiographie 3D CBCT", "Radiologie", 280.0, False, 0.0, "Tomographie 3D", 30),
                    
                    # Prophylaxie
                    ("01.0010", "Détartrage simple", "Prophylaxie", 120.0, True, 90.0, "Détartrage et polissage", 45),
                    ("01.0020", "Détartrage complexe", "Prophylaxie", 180.0, True, 90.0, "Détartrage approfondi", 60),
                    ("01.0030", "Scellement de fissures", "Prophylaxie", 65.0, True, 90.0, "Scellement préventif", 30),
                    
                    # Soins conservateurs
                    ("04.0010", "Composite 1 face", "Composite", 180.0, True, 90.0, "Obturation composite simple", 45),
                    ("04.0020", "Composite 2 faces", "Composite", 220.0, True, 90.0, "Obturation composite moyenne", 60),
                    ("04.0030", "Composite 3 faces", "Composite", 280.0, True, 90.0, "Obturation composite complexe", 75),
                    ("04.0040", "Composite esthétique", "Composite", 350.0, False, 0.0, "Composite esthétique premium", 90),
                    
                    # Endodontie
                    ("05.0010", "Traitement de canal 1 canal", "Endodontie", 450.0, True, 90.0, "Traitement endodontique simple", 90),
                    ("05.0020", "Traitement de canal 2 canaux", "Endodontie", 650.0, True, 90.0, "Traitement endodontique bicanalaire", 120),
                    ("05.0030", "Traitement de canal 3+ canaux", "Endodontie", 850.0, True, 90.0, "Traitement endodontique complexe", 150),
                    ("05.0040", "Retraitement endodontique", "Endodontie", 950.0, True, 90.0, "Retraitement de canal", 180),
                    
                    # Chirurgie
                    ("06.0010", "Extraction simple", "Chirurgie", 180.0, True, 90.0, "Extraction dentaire simple", 30),
                    ("06.0020", "Extraction complexe", "Chirurgie", 280.0, True, 90.0, "Extraction chirurgicale", 60),
                    ("06.0030", "Extraction dent de sagesse", "Chirurgie", 350.0, True, 90.0, "Extraction dent de sagesse", 75),
                    ("06.0040", "Apicectomie", "Chirurgie", 650.0, True, 90.0, "Résection apicale", 90),
                    
                    # Prothèses
                    ("07.0010", "Couronne métallique", "Prothèse", 950.0, True, 90.0, "Couronne métallo-céramique", 120),
                    ("07.0020", "Couronne céramique", "Prothèse", 1200.0, False, 0.0, "Couronne tout céramique", 120),
                    ("07.0030", "Couronne zircone", "Prothèse", 1450.0, False, 0.0, "Couronne zircone premium", 120),
                    ("07.0040", "Bridge 3 éléments", "Prothèse", 2850.0, True, 90.0, "Bridge fixe 3 unités", 180),
                    ("07.0050", "Prothèse partielle", "Prothèse", 1800.0, True, 90.0, "Prothèse partielle amovible", 150),
                    ("07.0060", "Prothèse complète", "Prothèse", 2200.0, True, 90.0, "Prothèse totale", 180),
                    
                    # Implantologie
                    ("08.0010", "Implant dentaire", "Implantologie", 1800.0, False, 0.0, "Pose d'implant titanium", 90),
                    ("08.0020", "Couronne sur implant", "Implantologie", 1450.0, False, 0.0, "Couronne vissée sur implant", 90),
                    ("08.0030", "Greffe osseuse", "Implantologie", 850.0, False, 0.0, "Augmentation osseuse", 120),
                    ("08.0040", "Sinus lift", "Implantologie", 1200.0, False, 0.0, "Élévation sinusienne", 150),
                    
                    # Parodontologie
                    ("09.0010", "Surfaçage radiculaire", "Parodontologie", 280.0, True, 90.0, "Surfaçage par quadrant", 60),
                    ("09.0020", "Chirurgie parodontale", "Parodontologie", 650.0, True, 90.0, "Chirurgie parodontale", 120),
                    ("09.0030", "Greffe gingivale", "Parodontologie", 850.0, True, 90.0, "Greffe de gencive", 90),
                    
                    # Orthodontie
                    ("10.0010", "Consultation orthodontique", "Orthodontie", 180.0, False, 0.0, "Consultation orthodontique", 60),
                    ("10.0020", "Appareil orthodontique", "Orthodontie", 4500.0, False, 0.0, "Traitement orthodontique fixe", 0),
                    ("10.0030", "Invisalign", "Orthodontie", 6500.0, False, 0.0, "Traitement Invisalign", 0),
                    ("10.0040", "Contention orthodontique", "Orthodontie", 350.0, False, 0.0, "Fil de contention", 45),
                    
                    # Esthétique
                    ("11.0010", "Blanchiment dentaire", "Esthétique", 650.0, False, 0.0, "Blanchiment professionnel", 90),
                    ("11.0020", "Facette céramique", "Esthétique", 1200.0, False, 0.0, "Facette en céramique", 120),
                    ("11.0030", "Facette composite", "Esthétique", 450.0, False, 0.0, "Facette en composite", 90),
                ]
                
                # Insert pricing data
                for item in pricing_data:
                    pricing_id = str(uuid.uuid4())
                    query = '''
                        INSERT INTO dental_pricing 
                        (id, tarmed_code, treatment_name, treatment_category, base_price_chf, 
                         lamal_covered, lamal_percentage, description, duration_minutes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''
                    params = (pricing_id, *item)
                    self._execute_query(query, params)
                
                print(f"✅ Swiss dental pricing initialized with {len(pricing_data)} treatments")
                
        except Exception as e:
            print(f"❌ Error initializing Swiss pricing: {e}")
    
    # Financial Management Methods
    
    def create_invoice(self, patient_id, treatment_items, invoice_date=None, due_date=None, treatment_plan_id=None):
        """Create a new invoice for a patient"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Generate invoice number
                cursor.execute("SELECT COUNT(*) FROM invoices WHERE strftime('%Y', invoice_date) = strftime('%Y', 'now')")
                year_count = cursor.fetchone()[0] + 1
                invoice_number = f"INV-{datetime.now().year}-{year_count:04d}"
                
                # Calculate totals
                total_amount = 0.0
                lamal_amount = 0.0
                insurance_amount = 0.0
                
                for item in treatment_items:
                    item_total = item['quantity'] * item['unit_price']
                    total_amount += item_total
                    
                    if item.get('lamal_covered', False):
                        lamal_item_amount = item_total * (item.get('lamal_percentage', 0) / 100)
                        lamal_amount += lamal_item_amount
                
                patient_amount = total_amount - lamal_amount - insurance_amount
                
                # Create invoice
                invoice_id = str(uuid.uuid4())
                if not invoice_date:
                    invoice_date = datetime.now().strftime('%Y-%m-%d')
                if not due_date:
                    due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                
                cursor.execute('''
                    INSERT INTO invoices 
                    (id, patient_id, treatment_plan_id, invoice_number, invoice_date, due_date, 
                     total_amount_chf, lamal_amount_chf, insurance_amount_chf, patient_amount_chf, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                ''', (invoice_id, patient_id, treatment_plan_id, invoice_number, invoice_date, due_date,
                      total_amount, lamal_amount, insurance_amount, patient_amount))
                
                # Create invoice items
                for item in treatment_items:
                    item_id = str(uuid.uuid4())
                    item_total = item['quantity'] * item['unit_price']
                    item_lamal = item_total * (item.get('lamal_percentage', 0) / 100) if item.get('lamal_covered', False) else 0
                    
                    cursor.execute('''
                        INSERT INTO invoice_items 
                        (id, invoice_id, tarmed_code, treatment_name, quantity, unit_price_chf, 
                         total_price_chf, lamal_covered, lamal_amount_chf)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (item_id, invoice_id, item.get('tarmed_code', ''), item['treatment_name'],
                          item['quantity'], item['unit_price'], item_total, 
                          item.get('lamal_covered', False), item_lamal))
                
                conn.commit()
                return invoice_id
                
        except Exception as e:
            print(f"❌ Error creating invoice: {e}")
            return None
    
    def get_pricing_data(self, search_term=None):
        """Get dental pricing data with optional search"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if search_term:
                    cursor.execute('''
                        SELECT * FROM dental_pricing 
                        WHERE treatment_name LIKE ? OR tarmed_code LIKE ? OR treatment_category LIKE ?
                        ORDER BY treatment_category, treatment_name
                    ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
                else:
                    cursor.execute('''
                        SELECT * FROM dental_pricing 
                        ORDER BY treatment_category, treatment_name
                    ''')
                
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in results]
                
        except Exception as e:
            print(f"❌ Error fetching pricing data: {e}")
            return []
    
    def get_financial_dashboard_data(self):
        """Get financial dashboard data for analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Monthly revenue
                cursor.execute('''
                    SELECT strftime('%Y-%m', invoice_date) as month,
                           SUM(total_amount_chf) as revenue,
                           COUNT(*) as invoice_count
                    FROM invoices 
                    WHERE invoice_date >= date('now', '-12 months')
                    GROUP BY strftime('%Y-%m', invoice_date)
                    ORDER BY month
                ''')
                monthly_revenue = [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]
                
                # Payment status
                cursor.execute('''
                    SELECT status, COUNT(*) as count, SUM(total_amount_chf) as amount
                    FROM invoices
                    GROUP BY status
                ''')
                payment_status = [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]
                
                # Top treatments
                cursor.execute('''
                    SELECT ii.treatment_name, 
                           SUM(ii.quantity) as total_quantity,
                           SUM(ii.total_price_chf) as total_revenue
                    FROM invoice_items ii
                    JOIN invoices i ON ii.invoice_id = i.id
                    WHERE i.invoice_date >= date('now', '-12 months')
                    GROUP BY ii.treatment_name
                    ORDER BY total_revenue DESC
                    LIMIT 10
                ''')
                top_treatments = [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]
                
                # Top patients
                cursor.execute('''
                    SELECT p.first_name || ' ' || p.last_name as patient_name,
                           COUNT(i.id) as invoice_count,
                           SUM(i.total_amount_chf) as total_spent
                    FROM patients p
                    JOIN invoices i ON p.id = i.patient_id
                    WHERE i.invoice_date >= date('now', '-12 months')
                    GROUP BY p.id
                    ORDER BY total_spent DESC
                    LIMIT 10
                ''')
                top_patients = [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]
                
                return {
                    'monthly_revenue': monthly_revenue,
                    'payment_status': payment_status,
                    'top_treatments': top_treatments,
                    'top_patients': top_patients
                }
                
        except Exception as e:
            print(f"❌ Error fetching dashboard data: {e}")
            return {}
    
    def get_invoices(self, patient_id=None, status=None, invoice_id=None):
        """Get invoices with optional filters"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT i.*, p.first_name || ' ' || p.last_name as patient_name
                    FROM invoices i
                    JOIN patients p ON i.patient_id = p.id
                    WHERE 1=1
                '''
                params = []
                
                if invoice_id:
                    query += ' AND i.id = ?'
                    params.append(invoice_id)
                elif patient_id:
                    query += ' AND i.patient_id = ?'
                    params.append(patient_id)
                
                if status:
                    query += ' AND i.status = ?'
                    params.append(status)
                
                query += ' ORDER BY i.invoice_date DESC'
                
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in results]
                
        except Exception as e:
            print(f"❌ Error fetching invoices: {e}")
            return []
    
    def get_invoice_items(self, invoice_id):
        """Get items for a specific invoice"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM invoice_items 
                    WHERE invoice_id = ?
                    ORDER BY treatment_name
                ''', (invoice_id,))
                
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in results]
                
        except Exception as e:
            print(f"❌ Error fetching invoice items: {e}")
            return []
    
    def add_payment(self, invoice_id, amount, payment_date=None, payment_method='cash', reference_number=None):
        """Add a payment to an invoice"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create payment record
                payment_id = str(uuid.uuid4())
                if not payment_date:
                    payment_date = datetime.now().strftime('%Y-%m-%d')
                
                cursor.execute('''
                    INSERT INTO payments 
                    (id, invoice_id, payment_date, amount_chf, payment_method, reference_number)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (payment_id, invoice_id, payment_date, amount, payment_method, reference_number))
                
                # Check if invoice is fully paid
                cursor.execute('''
                    SELECT i.patient_amount_chf, COALESCE(SUM(p.amount_chf), 0) as total_paid
                    FROM invoices i
                    LEFT JOIN payments p ON i.id = p.invoice_id
                    WHERE i.id = ?
                    GROUP BY i.id
                ''', (invoice_id,))
                
                result = cursor.fetchone()
                if result:
                    patient_amount, total_paid = result
                    if total_paid >= patient_amount:
                        cursor.execute('UPDATE invoices SET status = ? WHERE id = ?', ('paid', invoice_id))
                    elif total_paid > 0:
                        cursor.execute('UPDATE invoices SET status = ? WHERE id = ?', ('partial', invoice_id))
                
                # Update expected revenue
                self.update_expected_revenue(invoice_id, amount)
                
                conn.commit()
                return payment_id
                
        except Exception as e:
            print(f"❌ Error adding payment: {e}")
            return None
    
    # Devis (Estimates) Management Methods
    
    def create_devis(self, patient_id, treatment_plan_id, devis_items, valid_days=30):
        """Create a new devis (estimate) for a patient"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Generate devis number
                cursor.execute("SELECT COUNT(*) FROM devis WHERE strftime('%Y', devis_date) = strftime('%Y', 'now')")
                year_count = cursor.fetchone()[0] + 1
                devis_number = f"DEV-{datetime.now().year}-{year_count:04d}"
                
                # Calculate totals
                total_amount = 0.0
                lamal_amount = 0.0
                insurance_amount = 0.0
                
                for item in devis_items:
                    item_total = item['quantity'] * item['unit_price']
                    discount_amount = item.get('discount_amount_chf', 0)
                    final_price = item_total - discount_amount
                    
                    total_amount += final_price
                    
                    if item.get('lamal_covered', False):
                        lamal_item_amount = final_price * (item.get('lamal_percentage', 0) / 100)
                        lamal_amount += lamal_item_amount
                
                patient_amount = total_amount - lamal_amount - insurance_amount
                
                # Create devis
                devis_id = str(uuid.uuid4())
                devis_date = datetime.now().strftime('%Y-%m-%d')
                valid_until = (datetime.now() + timedelta(days=valid_days)).strftime('%Y-%m-%d')
                
                cursor.execute('''
                    INSERT INTO devis 
                    (id, patient_id, treatment_plan_id, devis_number, devis_date, valid_until,
                     total_amount_chf, lamal_amount_chf, insurance_amount_chf, patient_amount_chf, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                ''', (devis_id, patient_id, treatment_plan_id, devis_number, devis_date, valid_until,
                      total_amount, lamal_amount, insurance_amount, patient_amount))
                
                # Create devis items
                for item in devis_items:
                    item_id = str(uuid.uuid4())
                    item_total = item['quantity'] * item['unit_price']
                    discount_amount = item.get('discount_amount_chf', 0)
                    final_price = item_total - discount_amount
                    item_lamal = final_price * (item.get('lamal_percentage', 0) / 100) if item.get('lamal_covered', False) else 0
                    
                    cursor.execute('''
                        INSERT INTO devis_items 
                        (id, devis_id, tarmed_code, treatment_name, quantity, unit_price_chf, 
                         total_price_chf, lamal_covered, lamal_amount_chf, discount_percentage,
                         discount_amount_chf, final_price_chf, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (item_id, devis_id, item.get('tarmed_code', ''), item['treatment_name'],
                          item['quantity'], item['unit_price'], item_total, 
                          item.get('lamal_covered', False), item_lamal, 
                          item.get('discount_percentage', 0), discount_amount, final_price,
                          item.get('notes', '')))
                
                conn.commit()
                return devis_id
                
        except Exception as e:
            print(f"❌ Error creating devis: {e}")
            return None
    
    def get_devis(self, patient_id=None, status=None, devis_id=None):
        """Get devis with optional filters"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT d.*, p.first_name || ' ' || p.last_name as patient_name,
                           tp.consultation_text
                    FROM devis d
                    JOIN patients p ON d.patient_id = p.id
                    LEFT JOIN treatment_plans tp ON d.treatment_plan_id = tp.id
                    WHERE 1=1
                '''
                params = []
                
                if devis_id:
                    query += ' AND d.id = ?'
                    params.append(devis_id)
                elif patient_id:
                    query += ' AND d.patient_id = ?'
                    params.append(patient_id)
                
                if status:
                    query += ' AND d.status = ?'
                    params.append(status)
                
                query += ' ORDER BY d.devis_date DESC'
                
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
                
                devis_list = []
                for row in results:
                    devis = dict(zip(columns, row))
                    
                    # Get devis items
                    cursor.execute('''
                        SELECT * FROM devis_items WHERE devis_id = ?
                        ORDER BY treatment_name
                    ''', (devis['id'],))
                    item_columns = [desc[0] for desc in cursor.description]
                    devis['items'] = [dict(zip(item_columns, item_row)) for item_row in cursor.fetchall()]
                    
                    devis_list.append(devis)
                
                return devis_list
                
        except Exception as e:
            print(f"❌ Error fetching devis: {e}")
            return []
    
    def approve_devis(self, devis_id):
        """Approve a devis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE devis 
                    SET status = 'approved', approved_date = ?
                    WHERE id = ?
                ''', (datetime.now().strftime('%Y-%m-%d'), devis_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"❌ Error approving devis: {e}")
            return False
    
    def reject_devis(self, devis_id, reason=""):
        """Reject a devis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE devis 
                    SET status = 'rejected', rejected_date = ?, rejection_reason = ?
                    WHERE id = ?
                ''', (datetime.now().strftime('%Y-%m-%d'), reason, devis_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"❌ Error rejecting devis: {e}")
            return False
    
    def create_invoice_from_devis(self, devis_id, selected_items=None):
        """Create an invoice from an approved devis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get devis details
                devis_list = self.get_devis(devis_id=devis_id)
                if not devis_list or devis_list[0]['status'] != 'approved':
                    return None
                
                devis = devis_list[0]
                
                # Filter items if specified
                items_to_invoice = devis['items']
                if selected_items:
                    items_to_invoice = [item for item in devis['items'] if item['id'] in selected_items]
                
                # Create invoice
                invoice_items = []
                for item in items_to_invoice:
                    invoice_items.append({
                        'tarmed_code': item['tarmed_code'],
                        'treatment_name': item['treatment_name'],
                        'quantity': item['quantity'],
                        'unit_price': item['unit_price_chf'],
                        'lamal_covered': item['lamal_covered'],
                        'lamal_percentage': (item['lamal_amount_chf'] / item['final_price_chf']) * 100 if item['final_price_chf'] > 0 else 0
                    })
                
                invoice_id = self.create_invoice(
                    patient_id=devis['patient_id'],
                    treatment_items=invoice_items,
                    treatment_plan_id=devis['treatment_plan_id']
                )
                
                if invoice_id:
                    # Update devis status
                    cursor.execute('''
                        UPDATE devis SET status = 'invoiced' WHERE id = ?
                    ''', (devis_id,))
                    
                    # Create expected revenue entry
                    expected_revenue_id = str(uuid.uuid4())
                    cursor.execute('''
                        INSERT INTO expected_revenue 
                        (id, invoice_id, devis_id, expected_date, expected_amount_chf, status)
                        VALUES (?, ?, ?, ?, ?, 'pending')
                    ''', (expected_revenue_id, invoice_id, devis_id, 
                          (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                          sum(item['final_price_chf'] for item in items_to_invoice)))
                    
                    conn.commit()
                
                return invoice_id
                
        except Exception as e:
            print(f"❌ Error creating invoice from devis: {e}")
            return None
    
    def create_payment_plan(self, invoice_id, plan_name, number_of_payments, frequency='monthly', first_payment_date=None):
        """Create a payment plan for an invoice"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get invoice details
                cursor.execute('SELECT patient_amount_chf FROM invoices WHERE id = ?', (invoice_id,))
                result = cursor.fetchone()
                if not result:
                    return None
                
                total_amount = result[0]
                payment_amount = total_amount / number_of_payments
                
                if not first_payment_date:
                    first_payment_date = datetime.now().strftime('%Y-%m-%d')
                
                # Create payment plan
                plan_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO payment_plans 
                    (id, invoice_id, plan_name, total_amount_chf, number_of_payments,
                     payment_frequency, first_payment_date, payment_amount_chf)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (plan_id, invoice_id, plan_name, total_amount, number_of_payments,
                      frequency, first_payment_date, payment_amount))
                
                # Create scheduled payments
                current_date = datetime.strptime(first_payment_date, '%Y-%m-%d')
                for i in range(number_of_payments):
                    scheduled_payment_id = str(uuid.uuid4())
                    cursor.execute('''
                        INSERT INTO scheduled_payments 
                        (id, payment_plan_id, payment_number, scheduled_date, amount_chf)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (scheduled_payment_id, plan_id, i + 1, 
                          current_date.strftime('%Y-%m-%d'), payment_amount))
                    
                    # Calculate next payment date
                    if frequency == 'monthly':
                        current_date = current_date.replace(month=current_date.month + 1)
                    elif frequency == 'weekly':
                        current_date += timedelta(weeks=1)
                    elif frequency == 'biweekly':
                        current_date += timedelta(weeks=2)
                
                conn.commit()
                return plan_id
                
        except Exception as e:
            print(f"❌ Error creating payment plan: {e}")
            return None
    
    # Patient Education Management Methods
    
    def create_patient_education(self, patient_id, education_content, education_title=None, treatment_plan_id=None):
        """Create a new patient education document"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                education_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO patient_education 
                    (id, patient_id, treatment_plan_id, education_content, education_title, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (education_id, patient_id, treatment_plan_id, education_content, education_title, 
                      datetime.now().isoformat(), datetime.now().isoformat()))
                
                conn.commit()
                return education_id
                
        except Exception as e:
            print(f"❌ Error creating patient education: {e}")
            return None
    
    def get_patient_education(self, patient_id=None, education_id=None):
        """Get patient education documents"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if education_id:
                    cursor.execute('''
                        SELECT pe.*, p.first_name || ' ' || p.last_name as patient_name
                        FROM patient_education pe
                        JOIN patients p ON pe.patient_id = p.id
                        WHERE pe.id = ?
                    ''', (education_id,))
                    
                    result = cursor.fetchone()
                    if result:
                        columns = [desc[0] for desc in cursor.description]
                        return dict(zip(columns, result))
                    return None
                
                elif patient_id:
                    cursor.execute('''
                        SELECT pe.*, p.first_name || ' ' || p.last_name as patient_name
                        FROM patient_education pe
                        JOIN patients p ON pe.patient_id = p.id
                        WHERE pe.patient_id = ?
                        ORDER BY pe.created_at DESC
                    ''', (patient_id,))
                    
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                else:
                    cursor.execute('''
                        SELECT pe.*, p.first_name || ' ' || p.last_name as patient_name
                        FROM patient_education pe
                        JOIN patients p ON pe.patient_id = p.id
                        ORDER BY pe.created_at DESC
                    ''')
                    
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ Error getting patient education: {e}")
            return [] if patient_id or not education_id else None
    
    def update_patient_education(self, education_id, education_content, education_title=None):
        """Update an existing patient education document"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE patient_education 
                    SET education_content = ?, education_title = ?, updated_at = ?
                    WHERE id = ?
                ''', (education_content, education_title, datetime.now().isoformat(), education_id))
                
                success = cursor.rowcount > 0
                conn.commit()
                return success
                
        except Exception as e:
            print(f"❌ Error updating patient education: {e}")
            return False
    
    def get_payment_plans(self, invoice_id=None):
        """Get payment plans"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT pp.*, i.invoice_number, p.first_name || ' ' || p.last_name as patient_name
                    FROM payment_plans pp
                    JOIN invoices i ON pp.invoice_id = i.id
                    JOIN patients p ON i.patient_id = p.id
                    WHERE 1=1
                '''
                params = []
                
                if invoice_id:
                    query += ' AND pp.invoice_id = ?'
                    params.append(invoice_id)
                
                query += ' ORDER BY pp.created_at DESC'
                
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
                
                payment_plans = []
                for row in results:
                    plan = dict(zip(columns, row))
                    
                    # Get scheduled payments
                    cursor.execute('''
                        SELECT * FROM scheduled_payments 
                        WHERE payment_plan_id = ?
                        ORDER BY payment_number
                    ''', (plan['id'],))
                    payment_columns = [desc[0] for desc in cursor.description]
                    plan['scheduled_payments'] = [dict(zip(payment_columns, payment_row)) for payment_row in cursor.fetchall()]
                    
                    payment_plans.append(plan)
                
                return payment_plans
                
        except Exception as e:
            print(f"❌ Error fetching payment plans: {e}")
            return []
    
    def update_expected_revenue(self, invoice_id, actual_amount):
        """Update expected revenue when payment is received"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE expected_revenue 
                    SET actual_amount_chf = actual_amount_chf + ?, 
                        status = CASE 
                            WHEN actual_amount_chf + ? >= expected_amount_chf THEN 'completed'
                            WHEN actual_amount_chf + ? > 0 THEN 'partial'
                            ELSE 'pending'
                        END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE invoice_id = ?
                ''', (actual_amount, actual_amount, actual_amount, invoice_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"❌ Error updating expected revenue: {e}")
            return False
    
    def get_revenue_forecast(self, months_ahead=12):
        """Get revenue forecast based on expected payments"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get expected revenue
                cursor.execute('''
                    SELECT strftime('%Y-%m', expected_date) as month,
                           SUM(expected_amount_chf - actual_amount_chf) as expected_revenue
                    FROM expected_revenue
                    WHERE expected_date >= date('now') 
                    AND expected_date <= date('now', '+{} months')
                    AND status != 'completed'
                    GROUP BY strftime('%Y-%m', expected_date)
                    ORDER BY month
                '''.format(months_ahead))
                
                columns = [desc[0] for desc in cursor.description]
                forecast = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return forecast
                
        except Exception as e:
            print(f"❌ Error getting revenue forecast: {e}")
            return [] 

    def delete_devis(self, devis_id):
        """Delete a devis and its items"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete devis items first (due to foreign key constraints)
                cursor.execute('DELETE FROM devis_items WHERE devis_id = ?', (devis_id,))
                
                # Delete the devis
                cursor.execute('DELETE FROM devis WHERE id = ?', (devis_id,))
                
                success = cursor.rowcount > 0
                conn.commit()
                return success
                
        except Exception as e:
            print(f"❌ Error deleting devis: {e}")
            return False
    
    def delete_invoice(self, invoice_id):
        """Delete an invoice and its related data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete payments first (due to foreign key constraints)
                cursor.execute('DELETE FROM payments WHERE invoice_id = ?', (invoice_id,))
                
                # Delete invoice items
                cursor.execute('DELETE FROM invoice_items WHERE invoice_id = ?', (invoice_id,))
                
                # Delete expected revenue entries
                cursor.execute('DELETE FROM expected_revenue WHERE invoice_id = ?', (invoice_id,))
                
                # Delete the invoice
                cursor.execute('DELETE FROM invoices WHERE id = ?', (invoice_id,))
                
                success = cursor.rowcount > 0
                conn.commit()
                return success
                
        except Exception as e:
            print(f"❌ Error deleting invoice: {e}")
            return False 