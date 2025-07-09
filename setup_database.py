#!/usr/bin/env python3
"""
Database Setup Script for Custom Search App
Converts Excel files to SQLite database
"""

import sqlite3
import pandas as pd
from pathlib import Path
import sys

def create_database():
    """Create SQLite database with all required tables"""
    
    # Database file path
    data_dir = Path("data")
    db_file = data_dir / "custom_search.db"
    
    # Ensure data directory exists
    data_dir.mkdir(exist_ok=True)
    
    # Excel file configurations (same as in admin.py)
    EXCEL_FILES = {
        "attributes": {
            "filename": "attributes.xlsx",
            "required_columns": ["AttributeID", "AttributeName", "Source", "2"],
            "description": "Attributes data"
        },
        "category_pdp_plp": {
            "filename": "category_pdp_plp.xlsx",
            "required_columns": ["L0_category", "L1_category", "L1_category_id", "L2_category", "L2_category_id"],
            "description": "Category PDP/PLP data"
        },
        "concat_rule": {
            "filename": "concat_rule.xlsx",
            "required_columns": ["Category Name", "L1", "L2", "Concat Rule"],
            "description": "Concat rule data"
        },
        "category_tree": {
            "filename": "category_tree.xlsx",
            "required_columns": ["l0_category_id", "l0_category", "l1_category_id", "l1_category", "l2_category_id", "l2_category"],
            "description": "Category tree data"
        },
        "rejection_reasons": {
            "filename": "rejection_reasons.xlsx",
            "required_columns": ["Reason", "Justification"],
            "description": "Rejection reasons data"
        },
        "ptypes_dump": {
            "filename": "ptypes_dump.xlsx",
            "required_columns": ["ptype_id", "ptype_name"],
            "description": "Product types data"
        },
        "color_code": {
            "filename": "colour_code.xlsx",
            "required_columns": ["Color Name", "Hex Code"],
            "description": "Color code data"
        },
        "rms_manufacturer_brand": {
            "filename": "rms_manufacturer_brand.xlsx",
            "required_columns": ["ManufacturerID", "ManufacturerName", "BrandID", "BrandName", "Description"],
            "description": "RMS Manufacturer Brand data"
        }
    }
    
    # Table mapping
    table_mapping = {
        "attributes": "attributes",
        "category_pdp_plp": "category_pdp_plp", 
        "concat_rule": "concat_rule",
        "category_tree": "category_tree",
        "rejection_reasons": "rejection_reasons",
        "ptypes_dump": "ptypes_dump",
        "color_code": "color_codes",
        "rms_manufacturer_brand": "rms_manufacturer_brands"
    }
    
    print("🔧 Setting up SQLite database...")
    
    # Create database connection
    with sqlite3.connect(db_file) as conn:
        print(f"✓ Connected to database: {db_file}")
        
        # Process each Excel file
        for file_type, config in EXCEL_FILES.items():
            excel_file = data_dir / config["filename"]
            table_name = table_mapping[file_type]
            
            if excel_file.exists():
                try:
                    print(f"\n📊 Processing {config['filename']}...")
                    
                    # Read Excel file
                    df = pd.read_excel(excel_file)
                    print(f"  ✓ Loaded {len(df)} rows from {config['filename']}")
                    
                    # Create table and insert data
                    df.to_sql(table_name, conn, if_exists='replace', index=False)
                    print(f"  ✓ Created table '{table_name}' with {len(df)} rows")
                    
                except Exception as e:
                    print(f"  ❌ Error processing {config['filename']}: {e}")
            else:
                print(f"\n⚠️  File not found: {config['filename']}")
                print(f"  Creating empty table '{table_name}'...")
                
                # Create empty table with expected columns
                columns = config["required_columns"]
                create_sql = f"CREATE TABLE {table_name} ("
                create_sql += ", ".join([f"{col} TEXT" for col in columns])
                create_sql += ")"
                
                conn.execute(create_sql)
                print(f"  ✓ Created empty table '{table_name}'")
        
        # Create indexes for better performance
        print("\n🔍 Creating indexes...")
        indexes = [
            ("attributes", "AttributeName"),
            ("attributes", "AttributeID"),
            ("category_pdp_plp", "L1_category"),
            ("category_pdp_plp", "L2_category"),
            ("concat_rule", "Category Name"),
            ("category_tree", "l1_category"),
            ("category_tree", "l2_category"),
            ("rejection_reasons", "Reason"),
            ("ptypes_dump", "ptype_name"),
            ("color_codes", "Color Name"),
            ("color_codes", "Hex Code"),
            ("rms_manufacturer_brands", "MfgID"),
            ("rms_manufacturer_brands", "MfgName"),
            ("rms_manufacturer_brands", "BrandID"),
            ("rms_manufacturer_brands", "BrandName")
        ]
        
        for table, column in indexes:
            try:
                # Quote column names with spaces for SQLite
                if ' ' in column:
                    quoted_column = f'"{column}"'
                else:
                    quoted_column = column
                conn.execute(f"CREATE INDEX idx_{table}_{column.replace(' ', '_').lower()} ON {table}({quoted_column})")
                print(f"  ✓ Created index on {table}.{column}")
            except Exception as e:
                print(f"  ⚠️  Could not create index on {table}.{column}: {e}")
        
        print(f"\n✅ Database setup complete!")
        print(f"📁 Database file: {db_file}")
        
        # Show table summary
        print("\n📋 Database Summary:")
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  • {table_name}: {count} rows")

if __name__ == "__main__":
    try:
        create_database()
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Start your application")
        print("2. Test the search functionality")
        print("3. Use admin interface to upload new Excel files")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1) 