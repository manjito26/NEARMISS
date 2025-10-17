# NEARMISS System

Near Miss Reporting System - A Flask-based web application for recording and managing workplace near miss incidents with plant-specific functionality.

## Features

- **Multi-level Authentication**: Plant user quick entry, regular users, supervisors, and admins
- **Plant-based Filtering**: Red Oak and Telford plants with plant-specific data
- **Dynamic Forms**: Auto-complete dropdowns with custom entry capabilities
- **Permission-based Access**: Supervisor/admin-only fields for hazard assessment and corrective actions
- **Professional UI**: Green-themed Bootstrap 5 interface following Warp.dev standards
- **Database Integration**: SQL Server backend with comprehensive audit trail
- **Admin Controls**: Complete dropdown management for departments, equipment, hazard types, and actions

## Quick Start

1. **Prerequisites**
   - Python 3.8+
   - Access to SQL Server database (192.168.10.70)
   - Flask and dependencies (see requirements.txt)

2. **Installation**
   ```bash
   git clone https://github.com/yourusername/NEARMISS.git
   cd NEARMISS
   pip install -r requirements.txt
   ```

3. **Database Setup**
   ```bash
   python3 init_database.py
   python3 import_excel_data.py
   python3 cleanup_data.py
   ```

4. **Run Application**
   ```bash
   python3 run.py
   ```

5. **Access**
   - Login: http://localhost:5000/login
   - Default Admin: username `ckull`, password `mera7`

## Project Structure

```
NEARMISS/
├── app/
│   ├── static/           # CSS, JS, images, icons
│   ├── templates/        # HTML templates
│   ├── models/          # Database models
│   └── utils/           # Authentication and utilities
├── tests/               # Test scripts
├── logs/                # Application logs
├── backups/             # Database backups
└── requirements.txt     # Python dependencies
```

## User Roles

- **Plant User**: Quick entry access for reporting near misses
- **Regular User**: Create and edit own reports
- **Supervisor**: Edit all reports, access restricted fields, approve corrective actions
- **Admin**: Full system access, user management, dropdown configuration

## Key Components

- **Near Miss Entry Form**: Comprehensive form with all OSHA-compliant fields
- **Plant Selection**: Filters all data by selected plant (Red Oak/Telford)
- **Dynamic Dropdowns**: Auto-complete with custom entry for departments, equipment, hazard types
- **Admin Interface**: Complete CRUD operations for all dropdown data
- **Audit Trail**: Complete edit history tracking for all changes

## Database

- **Server**: 192.168.10.70 (SQL Server)
- **Database**: NEARMISS
- **Tables**: 11 tables including users, reports, dropdowns, email system, and audit history

## Development

Built following Warp.dev best practices:
- Green CSS theme consistent with RACE/ESTOP systems
- Bootstrap 5 for responsive UI
- Local CDN storage for all assets
- Comprehensive logging throughout
- Mobile-friendly design
- Professional data formatting and validation

## Version

Current Version: 1.0.0
Last Updated: October 2025

## Support

For technical support or questions about the Near Miss reporting system, contact your system administrator.