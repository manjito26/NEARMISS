"""
NEARMISS System - Main Flask Application
Near Miss reporting system with plant-specific functionality
"""
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import logging
import os
from datetime import datetime
from .utils.auth import AuthManager
from .models.database import NearMissDatabase

# Configure logging
logging.basicConfig(
    filename='logs/app.log', 
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.secret_key = 'nearmiss_system_secret_key_2025'
    
    # Initialize components
    auth_manager = AuthManager()
    db = NearMissDatabase()
    
    try:
        # Test database connection
        test_conn = db.get_connection()
        test_conn.close()
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    
    @app.route('/')
    def index():
        """Main dashboard - redirect to login if not authenticated"""
        if 'username' not in session:
            return redirect(url_for('login'))
        
        logger.info(f"User {session['username']} accessed dashboard")
        return render_template('dashboard.html', username=session['username'])
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login page with plant user quick entry"""
        if request.method == 'POST':
            login_type = request.form.get('login_type', 'regular')
            
            if login_type == 'plant':
                # Plant user quick entry
                selected_user = request.form.get('plant_user')
                if selected_user:
                    user = db.get_user_by_username(selected_user)
                    if user:
                        session['user_id'] = user['user_id']
                        session['username'] = user['username']
                        session['full_name'] = f"{user['first_name']} {user['last_name']}"
                        session['plant'] = user['plant']
                        session['is_admin'] = user['is_admin']
                        session['is_supervisor'] = user['is_supervisor']
                        session['login_type'] = 'plant'
                        logger.info(f"Plant user {selected_user} logged in via quick entry")
                        return redirect(url_for('entry_form'))
                    else:
                        flash('Selected user not found')
            else:
                # Regular login with password
                username = request.form['username']
                password = request.form['password']
                
                user = auth_manager.authenticate(username, password)
                if user:
                    session['user_id'] = user['user_id']
                    session['username'] = user['username']
                    session['full_name'] = f"{user['first_name']} {user['last_name']}"
                    session['plant'] = user['plant']
                    session['is_admin'] = user['is_admin']
                    session['is_supervisor'] = user['is_supervisor']
                    session['login_type'] = 'regular'
                    logger.info(f"User {username} logged in successfully")
                    return redirect(url_for('index'))
                else:
                    flash('Invalid username or password')
                    logger.warning(f"Failed login attempt for {username}")
        
        # Get all users for plant dropdown
        users = db.get_all_users()
        return render_template('login.html', users=users)
    
    @app.route('/logout')
    def logout():
        """Logout user"""
        username = session.get('username', 'Unknown')
        session.clear()
        logger.info(f"User {username} logged out")
        flash('You have been logged out')
        return redirect(url_for('login'))
    
    @app.route('/entry', methods=['GET', 'POST'])
    def entry_form():
        """Near miss entry form"""
        if 'username' not in session:
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            # Handle form submission
            try:
                # Extract form data
                data = {
                    'date_occurred': request.form['date_occurred'],
                    'time_occurred': request.form['time_occurred'],
                    'employee_id': request.form['employee_id'],
                    'plant': request.form['plant'],
                    'dept_id': request.form.get('dept_id'),
                    'equipment_area': request.form.get('equipment_area'),
                    'hazard_assessment': request.form.get('hazard_assessment'),
                    'hazard_type_id': request.form.get('hazard_type_id'),
                    'custom_hazard_type': request.form.get('custom_hazard_type'),
                    'description': request.form['description'],
                    'immediate_action_id': request.form.get('immediate_action_id'),
                    'corrective_action': request.form.get('corrective_action'),
                    'responsible_party_id': request.form.get('responsible_party_id')
                }
                
                # Submit the report (implement in database model)
                success = db.create_near_miss_report(data, session['user_id'])
                
                if success:
                    flash('Near miss report submitted successfully')
                    logger.info(f"Near miss report created by {session['username']}")
                    return redirect(url_for('reports'))
                else:
                    flash('Error submitting report. Please try again.')
                    
            except Exception as e:
                logger.error(f"Error submitting near miss report: {e}")
                flash('Error submitting report. Please try again.')
        
        # Get dropdown data
        users = db.get_all_users(session.get('plant'))
        departments = db.get_departments(session.get('plant'))
        hazard_types = db.get_hazard_types()
        immediate_actions = db.get_immediate_actions()
        
        return render_template('entry_form.html', 
                             users=users, 
                             departments=departments,
                             hazard_types=hazard_types,
                             immediate_actions=immediate_actions,
                             username=session['username'])
    
    @app.route('/reports')
    def reports():
        """View near miss reports"""
        if 'username' not in session:
            return redirect(url_for('login'))
        
        # Get filter parameters
        search_query = request.args.get('search', '')
        plant_filter = request.args.get('plant', '')
        user_filter = request.args.get('user', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Get reports with filters
        reports = db.get_near_miss_reports(search_query, plant_filter, user_filter, date_from, date_to)
        users = db.get_all_users()
        
        return render_template('reports.html', 
                             reports=reports,
                             users=users,
                             search_query=search_query,
                             plant_filter=plant_filter,
                             user_filter=user_filter,
                             username=session['username'])
    
    @app.route('/admin/users')
    def admin_users():
        """Admin page for user management"""
        if 'username' not in session or not session.get('is_admin'):
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('index'))
        
        users = db.get_all_users()
        return render_template('admin_users.html', users=users, username=session['username'])
    
    @app.route('/admin/dropdowns')
    def admin_dropdowns():
        """Admin page for managing dropdown options"""
        if 'username' not in session or not session.get('is_admin'):
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('index'))
        
        departments = db.get_departments()
        equipment = db.get_equipment()
        hazard_types = db.get_hazard_types()
        immediate_actions = db.get_immediate_actions()
        
        return render_template('admin_dropdowns.html',
                             departments=departments,
                             equipment=equipment,
                             hazard_types=hazard_types,
                             immediate_actions=immediate_actions,
                             username=session['username'])
    
    @app.route('/api/departments/<plant>')
    def api_departments(plant):
        """API endpoint to get departments for a plant"""
        if 'username' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        departments = db.get_departments(plant)
        return jsonify(departments)
    
    @app.route('/api/equipment/<plant>/<int:dept_id>')
    def api_equipment(plant, dept_id):
        """API endpoint to get equipment for a plant and department"""
        if 'username' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        equipment = db.get_equipment(plant, dept_id)
        return jsonify(equipment)
    
    @app.route('/api/users/<plant>')
    def api_users(plant):
        """API endpoint to get users for a plant"""
        if 'username' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        users = db.get_all_users(plant)
        return jsonify(users)
    
    @app.route('/api/add-employee', methods=['POST'])
    def api_add_employee():
        """API endpoint to add a new employee"""
        if 'username' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            data = request.get_json()
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            username = data.get('username')
            plant = data.get('plant')
            
            if not all([first_name, last_name, username, plant]):
                return jsonify({'success': False, 'message': 'Missing required fields'})
            
            # Check if username already exists
            existing_user = db.get_user_by_username(username)
            if existing_user:
                return jsonify({'success': False, 'message': 'Username already exists'})
            
            user_id = db.add_user(first_name, last_name, username, plant)
            
            if user_id:
                return jsonify({'success': True, 'user_id': user_id, 'message': 'Employee added successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to add employee'})
                
        except Exception as e:
            logger.error(f"Error adding employee: {e}")
            return jsonify({'success': False, 'message': 'Server error'}), 500
    
    @app.route('/debug')
    def debug():
        """Debug endpoint showing all available routes"""
        if 'username' not in session:
            return redirect(url_for('login'))
        
        logger.info(f"User {session['username']} accessed debug endpoint")
        endpoints = []
        
        for rule in app.url_map.iter_rules():
            methods = ', '.join(rule.methods - {'HEAD', 'OPTIONS'})
            endpoints.append({
                'endpoint': rule.rule,
                'methods': methods,
                'function': rule.endpoint
            })
        
        return render_template('debug.html', endpoints=endpoints, username=session['username'])
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return render_template('500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)