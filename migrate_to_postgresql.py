#!/usr/bin/env python3
"""
Migration script to transfer data from SQLite to PostgreSQL for Render deployment.
This script should be run locally before deployment to backup data.
"""

import sqlite3
import json
import os
from datetime import datetime
from database_manager import PracticeDatabase

def export_sqlite_data(sqlite_path="practice.db"):
    """Export all data from SQLite database to JSON files"""
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found at {sqlite_path}")
        return None
    
    print(f"📊 Exporting data from {sqlite_path}...")
    
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    export_data = {
        'export_timestamp': datetime.now().isoformat(),
        'source_database': sqlite_path,
        'tables': {}
    }
    
    for table in tables:
        print(f"  📋 Exporting table: {table}")
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        export_data['tables'][table] = [dict(row) for row in rows]
        print(f"    ✅ Exported {len(rows)} records from {table}")
    
    conn.close()
    
    # Save to JSON file
    export_filename = f"sqlite_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(export_filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"✅ Data exported to {export_filename}")
    return export_filename

def create_postgresql_backup_script(export_file):
    """Create a script to restore data to PostgreSQL"""
    if not os.path.exists(export_file):
        print(f"❌ Export file not found: {export_file}")
        return
    
    with open(export_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    script_content = f'''#!/usr/bin/env python3
"""
PostgreSQL restore script generated from SQLite export.
Run this script after deploying to Render to restore your data.
"""

import json
import os
import sys
from database_manager import PracticeDatabase

def restore_data_to_postgresql():
    """Restore data to PostgreSQL database"""
    
    # Check if we're in production with PostgreSQL
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL not found. This script should run in production.")
        return False
    
    print("🔄 Restoring data to PostgreSQL...")
    
    # Initialize database (this will create tables)
    db = PracticeDatabase()
    
    # Data to restore
    export_data = {json.dumps(data, indent=2)}
    
    # Restore each table
    for table_name, records in export_data['tables'].items():
        if not records:
            continue
            
        print(f"  📋 Restoring table: {{table_name}} ({{len(records)}} records)")
        
        try:
            # Get column names from first record
            if records:
                columns = list(records[0].keys())
                placeholders = ', '.join(['%s'] * len(columns))
                column_names = ', '.join(columns)
                
                # Create INSERT query
                query = f"INSERT INTO {{table_name}} ({{column_names}}) VALUES ({{placeholders}}) ON CONFLICT DO NOTHING"
                
                # Insert records
                for record in records:
                    values = [record.get(col) for col in columns]
                    db._execute_query(query, tuple(values))
                
                print(f"    ✅ Restored {{len(records)}} records to {{table_name}}")
        
        except Exception as e:
            print(f"    ❌ Error restoring {{table_name}}: {{e}}")
    
    print("✅ Data restoration completed")
    return True

if __name__ == "__main__":
    restore_data_to_postgresql()
'''
    
    restore_script = f"restore_postgresql_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    with open(restore_script, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✅ PostgreSQL restore script created: {restore_script}")
    return restore_script

def main():
    """Main migration function"""
    print("🚀 Starting SQLite to PostgreSQL migration preparation...")
    
    # Step 1: Export SQLite data
    export_file = export_sqlite_data()
    if not export_file:
        return
    
    # Step 2: Create PostgreSQL restore script
    restore_script = create_postgresql_backup_script(export_file)
    
    print("\n📋 Migration preparation complete!")
    print(f"📁 Backup file: {export_file}")
    print(f"📁 Restore script: {restore_script}")
    
    print("\n🔄 Next steps:")
    print("1. Keep the backup file safe")
    print("2. Deploy to Render")
    print("3. Run the restore script in production")
    print("4. Verify data integrity")

if __name__ == "__main__":
    main() 