#!/usr/bin/env python3
"""
Import detailed dropdown data from Excel file to database
"""
import sys
import os
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models.database import NearMissDatabase
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def import_equipment_data():
    """Import equipment data from Excel file"""
    excel_file = '/home/eraser/Downloads/near_miss_data.xlsx'
    
    if not os.path.exists(excel_file):
        logger.error(f"Excel file not found: {excel_file}")
        return False
    
    try:
        db = NearMissDatabase()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Read the "Specifc Area" sheet which has equipment by department
        df = pd.read_excel(excel_file, sheet_name='Specifc Area')
        logger.info(f"Read Excel sheet with columns: {df.columns.tolist()}")
        
        # Get department IDs for mapping
        departments = {}
        cursor.execute("SELECT dept_id, dept_name, plant FROM departments")
        for row in cursor.fetchall():
            key = f"{row[2]}_{row[1]}"  # plant_deptname
            departments[key] = row[0]
        
        # Map department names to match Excel columns
        dept_mapping = {
            'Press': 'Press',
            'Ink Room': 'Ink Room', 
            'Make Ready': 'Make Ready',
            'Slit/Pack': 'Slit/Pack',
            'Maintenace': 'Maintenance',  # Note: typo in Excel
            'Warehouse': 'Warehouse'
        }
        
        # Process each department column
        for excel_col, db_dept in dept_mapping.items():
            if excel_col in df.columns:
                # Get equipment for this department
                equipment_list = df[excel_col].dropna().tolist()
                
                for plant in ['Red Oak', 'Telford']:
                    dept_key = f"{plant}_{db_dept}"
                    if dept_key in departments:
                        dept_id = departments[dept_key]
                        
                        for equip_name in equipment_list:
                            equip_name = str(equip_name).strip()
                            if equip_name and equip_name != 'General':
                                # Insert equipment if it doesn't exist
                                cursor.execute("""
                                    IF NOT EXISTS (SELECT 1 FROM equipment WHERE plant = %s AND dept_id = %s AND equip_name = %s)
                                    INSERT INTO equipment (plant, dept_id, equip_name) VALUES (%s, %s, %s)
                                """, (plant, dept_id, equip_name, plant, dept_id, equip_name))
                                
                                logger.info(f"Added equipment: {equip_name} to {plant} - {db_dept}")
        
        # Also read and update hazard types from Excel
        hazard_df = pd.read_excel(excel_file, sheet_name='Hazard Types')
        if not hazard_df.empty and len(hazard_df.columns) > 0:
            hazard_col = hazard_df.columns[0]
            hazard_types = hazard_df[hazard_col].dropna().tolist()
            
            for hazard_type in hazard_types:
                hazard_type = str(hazard_type).strip()
                if hazard_type:
                    cursor.execute("""
                        IF NOT EXISTS (SELECT 1 FROM hazard_types WHERE hazard_type = %s)
                        INSERT INTO hazard_types (hazard_type) VALUES (%s)
                    """, (hazard_type, hazard_type))
        
        # Update immediate actions from Excel
        actions_df = pd.read_excel(excel_file, sheet_name='Immediate Action Taken')
        if not actions_df.empty and len(actions_df.columns) > 0:
            actions_col = actions_df.columns[0]
            actions = actions_df[actions_col].dropna().tolist()
            
            for action in actions:
                action = str(action).strip()
                if action:
                    cursor.execute("""
                        IF NOT EXISTS (SELECT 1 FROM immediate_actions WHERE action_description = %s)
                        INSERT INTO immediate_actions (action_description) VALUES (%s)
                    """, (action, action))
        
        conn.close()
        logger.info("Excel data import completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error importing Excel data: {e}")
        return False

if __name__ == "__main__":
    success = import_equipment_data()
    if not success:
        sys.exit(1)