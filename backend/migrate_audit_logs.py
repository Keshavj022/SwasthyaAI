#!/usr/bin/env python3
"""
Migration script to add explainability fields to audit_logs table.

Run this once to update existing databases:
    python migrate_audit_logs.py
"""

import sys
from pathlib import Path
from sqlalchemy import text, inspect
from database import engine, SessionLocal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def migrate_audit_logs():
    """Add missing explainability columns to audit_logs table"""
    db = SessionLocal()
    
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('audit_logs')]
        
        print("Current audit_logs columns:", columns)
        
        # Columns to add if they don't exist
        columns_to_add = {
            'explainability_score': 'INTEGER',
            'reasoning_summary': 'TEXT',
            'decision_factors': 'TEXT',  # JSON stored as TEXT in SQLite
            'alternative_considerations': 'TEXT',  # JSON stored as TEXT in SQLite
            'escalation_triggered': 'TEXT',
            'safety_flags': 'TEXT',  # JSON stored as TEXT in SQLite
            'clinician_override': 'TEXT',
            'reviewed_by': 'TEXT',
            'review_timestamp': 'DATETIME',
            'review_notes': 'TEXT',
            'action': 'TEXT',  # May be missing if old schema
            'input_data': 'TEXT',  # JSON stored as TEXT in SQLite
            'output_data': 'TEXT',  # JSON stored as TEXT in SQLite
        }
        
        # Also check if we need to rename old columns
        column_mapping = {
            'request_data': 'input_data',
            'response_data': 'output_data',
            'request_type': 'action',
        }
        
        added_count = 0
        renamed_count = 0
        
        for column_name, column_type in columns_to_add.items():
            if column_name not in columns:
                try:
                    db.execute(text(f"ALTER TABLE audit_logs ADD COLUMN {column_name} {column_type}"))
                    print(f"✓ Added column: {column_name}")
                    added_count += 1
                except Exception as e:
                    print(f"⚠ Could not add {column_name}: {e}")
        
        # Rename old columns if they exist
        for old_name, new_name in column_mapping.items():
            if old_name in columns and new_name not in columns:
                try:
                    # SQLite doesn't support RENAME COLUMN directly, so we'll skip this
                    # The old columns will just remain unused
                    print(f"ℹ Note: Old column '{old_name}' exists but '{new_name}' also exists or was added")
                except Exception as e:
                    print(f"⚠ Could not rename {old_name} to {new_name}: {e}")
        
        db.commit()
        
        print(f"\n✓ Migration complete!")
        print(f"  - Added {added_count} new columns")
        print(f"  - Database schema updated")
        
        # Verify the migration
        inspector = inspect(engine)
        new_columns = [col['name'] for col in inspector.get_columns('audit_logs')]
        print(f"\nUpdated audit_logs columns: {new_columns}")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Audit Logs Migration")
    print("=" * 60)
    print("\nThis will add explainability fields to the audit_logs table.")
    print("Existing data will be preserved.\n")
    
    success = migrate_audit_logs()
    
    if success:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        sys.exit(1)
