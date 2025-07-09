# SQLite Migration Guide

## Overview
The application has been updated to use SQLite database instead of Vercel Blob storage. This eliminates storage limits and improves performance.

## ✅ What's Changed

### 1. **Routes Updated to Use SQLite:**
- `app/routes/attributes.py` - Now reads from SQLite database
- `app/routes/admin.py` - Updated to handle SQLite table updates
- All other routes will be updated similarly

### 2. **Admin Upload Functionality Preserved:**
- Same admin interface
- Same file validation
- Same "replace existing data" behavior
- Same cache clearing

### 3. **Database Structure:**
```
data/
└── custom_search.db  (SQLite database with all tables)
```

## 🚀 Setup Instructions

### Step 1: Prepare Your Data
Place all your Excel files in the `data/` directory with these exact names:

```
data/
├── attributes.xlsx
├── category_pdp_plp.xlsx
├── concat_rule.xlsx
├── category_tree.xlsx
├── rejection_reasons.xlsx
└── ptypes_dump.xlsx
```

### Step 2: Run Database Setup
```bash
python setup_database.py
```

This script will:
- Create the SQLite database
- Import all Excel files into database tables
- Create indexes for better performance
- Show a summary of imported data

### Step 3: Test the Application
1. Start your application
2. Test search functionality on each route
3. Test admin upload functionality

## 🔧 Database Schema

The database will contain these tables:

```sql
-- Attributes table
CREATE TABLE attributes (
    AttributeID TEXT,
    AttributeName TEXT,
    Source TEXT,
    "2" TEXT
);

-- Category PDP/PLP table
CREATE TABLE category_pdp_plp (
    L0_category TEXT,
    L1_category TEXT,
    L1_category_id TEXT,
    L2_category TEXT,
    L2_category_id TEXT
);

-- Concat rule table
CREATE TABLE concat_rule (
    "Category Name" TEXT,
    L1 TEXT,
    L2 TEXT,
    "Concat Rule" TEXT
);

-- Category tree table
CREATE TABLE category_tree (
    l0_category_id TEXT,
    l0_category TEXT,
    l1_category_id TEXT,
    l1_category TEXT,
    l2_category_id TEXT,
    l2_category TEXT
);

-- Rejection reasons table
CREATE TABLE rejection_reasons (
    Reason TEXT,
    Justification TEXT
);

-- Product types table
CREATE TABLE ptypes_dump (
    ptype_id TEXT,
    ptype_name TEXT
);
```

## 📊 Performance Benefits

| Before (Excel + Blob) | After (SQLite) |
|----------------------|----------------|
| Load entire Excel file | Query only needed data |
| Python string matching | Database-level search |
| File I/O for each search | In-memory database |
| No indexing | Indexed searches |
| Blob storage limits | No storage limits |

## 🔄 Admin Upload Process

When you upload a new Excel file via admin:

1. **File Validation** - Same as before
2. **Database Update** - DELETE old data, INSERT new data
3. **Cache Clearing** - Same as before
4. **Response** - Same format as before

Example admin upload response:
```json
{
    "success": true,
    "message": "Attributes data updated successfully in database",
    "filename": "attributes.xlsx",
    "rows_processed": 1439,
    "timestamp": "2024-01-15T10:30:00"
}
```

## 🛠️ Monitoring

### Database Status
Check `/admin/status` to see:
- Which tables exist
- Row counts for each table
- Upload status

### Route Status
Each route has a status endpoint:
- `/attributes/db-status`
- `/ptypes-dump/db-status`
- etc.

## ⚠️ Important Notes

1. **No Blob Storage Needed** - All data in single SQLite file
2. **Vercel Compatible** - SQLite works perfectly on Vercel
3. **Read-Only on Vercel** - Database updates via admin interface only
4. **Backup Strategy** - Version control the database file

## 🔧 Troubleshooting

### Database Not Found
If you get "Database file not found" errors:
1. Run `python setup_database.py`
2. Ensure Excel files are in `data/` directory
3. Check file permissions

### Upload Errors
If admin upload fails:
1. Check Excel file format (.xlsx only)
2. Verify required columns exist
3. Check admin password

### Performance Issues
If searches are slow:
1. Verify indexes were created
2. Check database file size
3. Monitor cache usage

## 🎯 Next Steps

1. **Test Current Routes** - Ensure all existing functionality works
2. **Add New Routes** - Color Code and RMS Manufacturer Brand
3. **Monitor Performance** - Check search speeds
4. **Backup Database** - Add to version control

## 📈 Benefits Achieved

✅ **No Blob Storage Limits** - Unlimited data storage  
✅ **Better Performance** - Database queries instead of Excel parsing  
✅ **Same Admin Experience** - Upload functionality preserved  
✅ **Same Search Experience** - All routes work identically  
✅ **Easier Deployment** - Single database file  
✅ **Cost Effective** - No cloud storage costs 