# NEARMISS System - Near Miss Reporting System

## Project Overview
Near Miss reporting system similar to ESTOP system. Flask-based web application for recording and managing workplace near miss incidents with plant-specific functionality.

## Project Goals

### Core Functionality
1. **Login System**
   - Standard user login with username/password
   - "Near Miss Entry" button for "plant" user quick access
   - Auto-login when plant user selected from dropdown
   
2. **Plant Selection**
   - Two plants: "Red Oak" (default), "Telford"
   - Plant selection filters all subsequent dropdowns (departments, equipment, personnel)
   
3. **Near Miss Entry Form**
   - Date picker (default: today)
   - Time selector (15-minute increments, default: now)
   - Employee dropdown with auto-complete and new entry capability
   - Department dropdown with custom entry
   - Equipment/Area dropdown with custom entry (filtered by plant/department)
   - Hazard assessment (High/Immediate, Medium, Low, Resolved/No Hazard) - supervisors/admins only
   - Hazard types selection with custom entry
   - Description field (400 characters with countdown)
   - Immediate action taken dropdown
   - Corrective action field (supervisors/admins only)
   - Responsible party selection (supervisors/admins)
   - Corrective action completion status (supervisors/admins only)
   - Optional file attachments

### Database Schema
**Database**: NEARMISS on 192.168.10.70, SA:GreenCandyOneBang

#### Tables:
1. **users**
   - user_id (INT, PK)
   - first_name (VARCHAR(50))
   - last_name (VARCHAR(50))
   - username (VARCHAR(50)) - {firstname_initial}{full_lastname}
   - email (VARCHAR(100)) - default: {username}@fresco.com
   - plant (VARCHAR(20)) - Red Oak/Telford
   - is_admin (BIT)
   - is_supervisor (BIT)
   - created_date (DATETIME)
   - password_hash (VARCHAR(255)) - for supervisors/admins only

2. **departments**
   - dept_id (INT, PK)
   - plant (VARCHAR(20))
   - dept_name (VARCHAR(100))

3. **equipment**
   - equip_id (INT, PK)
   - plant (VARCHAR(20))
   - dept_id (INT, FK)
   - equip_name (VARCHAR(100))

4. **hazard_types**
   - hazard_type_id (INT, PK)
   - hazard_type (VARCHAR(100))

5. **immediate_actions**
   - action_id (INT, PK)
   - action_description (VARCHAR(200))

6. **near_miss_reports**
   - report_id (INT, PK)
   - date_occurred (DATE)
   - time_occurred (TIME)
   - employee_id (INT, FK to users)
   - plant (VARCHAR(20))
   - dept_id (INT, FK)
   - equipment_area (VARCHAR(100))
   - hazard_assessment (VARCHAR(20))
   - hazard_type_id (INT, FK)
   - custom_hazard_type (VARCHAR(100))
   - description (VARCHAR(400))
   - immediate_action_id (INT, FK)
   - corrective_action (TEXT)
   - responsible_party_id (INT, FK to users)
   - corrective_action_completed (BIT)
   - completion_date (DATE)
   - completed_by_id (INT, FK to users)
   - created_by_id (INT, FK to users)
   - created_date (DATETIME)

7. **attachments**
   - attachment_id (INT, PK)
   - report_id (INT, FK)
   - filename (VARCHAR(255))
   - file_path (VARCHAR(500))
   - uploaded_date (DATETIME)

8. **edit_history**
   - history_id (INT, PK)
   - report_id (INT, FK)
   - user_id (INT, FK)
   - field_changed (VARCHAR(50))
   - old_value (VARCHAR(500))
   - new_value (VARCHAR(500))
   - changed_date (DATETIME)

9. **email_config**
   - config_id (INT, PK)
   - smtp_server (VARCHAR(100))
   - smtp_port (INT)
   - username (VARCHAR(100))
   - password_encrypted (VARCHAR(255))
   - auth_type (VARCHAR(20))
   - use_auth (BIT)
   - timeout (INT)
   - retries (INT)

10. **email_queue**
    - queue_id (INT, PK)
    - to_address (VARCHAR(100))
    - subject (VARCHAR(200))
    - body (TEXT)
    - report_id (INT, FK)
    - status (VARCHAR(20)) - pending/sent/failed
    - created_date (DATETIME)
    - sent_date (DATETIME)
    - retry_count (INT)

11. **email_history**
    - history_id (INT, PK)
    - to_address (VARCHAR(100))
    - subject (VARCHAR(200))
    - report_id (INT, FK)
    - sent_date (DATETIME)
    - status (VARCHAR(20))

### Dropdown Data (from Excel):
1. **Departments**: Press, Make Ready, Ink Room, Slit/Pack, Warehouse, Maintenance
2. **Equipment/Areas**: Plant-specific equipment lists
3. **Hazard Assessment**: High/Immediate, Medium, Low, Resolved/No Hazard
4. **Hazard Types**: 40+ types including Slip/trip/fall, Fall from height, Struck by, etc.
5. **Immediate Actions**: 15+ actions like "Hazard corrected immediately", "Area isolated", etc.

## Technical Implementation

### Directory Structure
```
NEARMISS/
├── app/
│   ├── static/
│   │   ├── css/          # Bootstrap 5 + custom styles
│   │   ├── js/           # Bootstrap 5 + custom JS
│   │   ├── icons/        # Logo and icons
│   │   └── images/       # Uploaded images
│   ├── templates/        # Flask templates
│   ├── routes/           # Route definitions
│   ├── models/           # Database models
│   └── utils/            # Utilities (auth, email, etc.)
├── tests/                # Test scripts
├── backups/              # Timestamped backups
├── aux/                  # Unused files
├── logs/                 # Application logs
└── requirements.txt      # Dependencies
```

### Key Features
1. **Authentication**: Multi-level (plant user, regular user, supervisor, admin)
2. **Plant-based filtering**: All data filtered by selected plant
3. **Dynamic dropdowns**: Auto-complete with custom entry capability
4. **Permission-based fields**: Certain fields restricted to supervisors/admins
5. **Email notifications**: Configurable SMTP with queue and logging
6. **Audit trail**: Complete edit history tracking
7. **File attachments**: Image upload capability
8. **Advanced reporting**: Filtered list views with date ranges

### User Roles
1. **Plant User**: Quick entry access, can only create near miss reports
2. **Regular User**: Can create and edit own reports
3. **Supervisor**: Can edit all reports, approve corrective actions, access restricted fields
4. **Admin**: Full system access, user management, SMTP configuration

## Default User
- Username: ckull
- Password: mera7
- Role: Admin

## Development Standards
- Follow Warp.dev best practices
- Green CSS theme (consistent with RACE/ESTOP systems)
- Bootstrap 5 for UI
- Local CDN storage
- Comprehensive logging
- Mobile-friendly design
- Debug endpoint for development

## GitHub Repository
**Repository URL**: https://github.com/manjito26/NEARMISS.git
**Status**: Public repository with complete codebase
**Initial Commit**: 2025-10-17 - Complete near miss reporting system with database, templates, and admin interface

## Change Log
### 2025-10-17 02:30:15
- Created GitHub repository: https://github.com/manjito26/NEARMISS.git
- Successfully pushed complete codebase to public repository
- Added comprehensive README.md with setup and usage instructions
- Initialized Git repository with proper .gitignore for Python projects
- Created .gitkeep files for empty directories to maintain structure

### 2025-10-17 02:03:37
- Downloaded Bootstrap 5 CSS and JS for local CDN storage
- Created green-themed CSS following Warp.dev standards
- Built Flask application structure with routes and authentication
- Created base template with navigation and green theme
- Implemented login page with plant user quick entry dropdown
- Created main startup script (run.py) following ESTOP pattern
- Added admin dropdown edit page requirement

### 2025-10-17 01:56:41
- Created NEARMISS project directory structure
- Analyzed ESTOP system for reference architecture
- Created WARP.md documentation
- Identified Excel dropdown data structure
- Defined comprehensive database schema with 11 tables
- Established user roles and permission system
- Planned email notification system with queue and history
- Set up project goals and technical requirements
- Successfully initialized NEARMISS database with all tables
- Imported and cleaned Excel dropdown data with professional formatting
- Created data cleanup script for proper capitalization
