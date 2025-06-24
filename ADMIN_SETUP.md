# Admin Setup Guide

## Overview
The admin interface allows authorized users to upload new Excel files to replace existing ones without manual deployment. The system uses Vercel Blob Storage for persistent file storage.

## How It Works (Corrected)

### **Vercel Serverless Architecture:**
- **Admin uploads** Excel files to Vercel Blob Storage
- **Search routes** read directly from Vercel Blob (not local files)
- **No startup downloads** - files are read on-demand
- **Persistent storage** - files stay in cloud storage

### **Flow:**
1. Admin uploads Excel → Vercel Blob Storage
2. Search requests → Read from Vercel Blob
3. Data is cached in memory for performance
4. Cache cleared after new uploads

## Setup Instructions

### 1. Vercel Blob Storage Setup

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Create Blob Store**:
   ```bash
   vercel blob create
   ```

4. **Get Blob Token**:
   - Go to your Vercel dashboard
   - Navigate to Storage → Blob
   - Copy the `BLOB_READ_WRITE_TOKEN`

### 2. Environment Variables

Add these environment variables to your Vercel project:

```bash
BLOB_READ_WRITE_TOKEN=your_blob_token_here
ADMIN_PASSWORD=your_secure_admin_password
```

### 3. Deploy

Deploy your application to Vercel:
```bash
vercel --prod
```

## Admin Interface

### Access
- Navigate to `/admin` in your application
- Enter the admin password

### Features
1. **File Status**: View which Excel files are uploaded to cloud storage
2. **File Upload**: Upload new Excel files to replace existing ones
3. **Cache Management**: Clear search cache after updates

### Supported Files
- `attributes.xlsx` - Attributes data
- `category_pdp_plp.xlsx` - Category PDP/PLP data
- `concat_rule.xlsx` - Concat rule data
- `category_tree.xlsx` - Category tree data
- `rejection_reasons.xlsx` - Rejection reasons data
- `ptypes_dump.xlsx` - Product types data

### File Validation
Each uploaded file is validated for:
- Correct file format (.xlsx)
- Required columns
- Non-empty data

### Security
- Admin password required for all operations
- File validation prevents invalid uploads
- Cache clearing after successful uploads

## Technical Implementation

### **Search Routes Updated:**
- Read directly from Vercel Blob Storage
- Fallback to local files if Blob not available
- Async data loading for better performance

### **Admin Routes:**
- Upload files to Vercel Blob
- Validate file structure
- Clear search cache after uploads

### **Configuration:**
- Environment variable validation
- Graceful fallback when Blob not configured
- Secure admin authentication

## Workflow

1. **Admin uploads new Excel file** via `/admin` interface
2. **File is validated** for correct structure
3. **File is uploaded** to Vercel Blob Storage
4. **Search cache is cleared** to ensure fresh data
5. **Search requests read from Blob** storage directly
6. **Search results reflect new data** immediately

## Troubleshooting

### Vercel Blob Not Configured
- Ensure `BLOB_READ_WRITE_TOKEN` is set in environment variables
- Check Vercel dashboard for correct token
- Redeploy after setting environment variables

### Upload Failures
- Check file format (must be .xlsx)
- Verify required columns are present
- Ensure admin password is correct
- Check file size limits

### Search Issues
- Verify files are uploaded via admin interface
- Check Vercel Blob storage in dashboard
- Clear cache if needed
- Check logs for error messages

## Security Notes

- Change default admin password (`admin123`) in production
- Use strong, unique passwords
- Consider implementing additional authentication methods
- Monitor admin access logs

## Cost Considerations

- Vercel Blob Storage has usage-based pricing
- Small Excel files (< 1MB) are very cost-effective
- Monitor usage in Vercel dashboard
- Reading from Blob has minimal cost

## Migration Notes

### **For Existing Routes:**
- Only `pdp_plp.py` has been updated as an example
- Other routes need similar updates to read from Blob
- Local files still work as fallback

### **Next Steps:**
1. Update remaining search routes to read from Blob
2. Test admin interface thoroughly
3. Monitor performance and costs 