#!/usr/bin/env python3
"""
Clean up and properly format dropdown data with professional capitalization
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models.database import NearMissDatabase
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def title_case_with_exceptions(text):
    """Convert text to title case with common exceptions"""
    # Words that should remain lowercase (articles, prepositions, conjunctions)
    lowercase_words = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'if', 'in', 'of', 'on', 'or', 'the', 'to', 'via', 'with'}
    
    # Words that should be uppercase
    uppercase_words = {'HVAC', 'PPE', 'LOTO', 'SDS', 'MSDS', 'OSHA', 'EPA', 'DOT', 'UV', 'IR', 'AC', 'DC'}
    
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        # Remove special characters and check if it's a number
        clean_word = re.sub(r'[^\w]', '', word)
        
        if clean_word.upper() in uppercase_words:
            # Keep uppercase abbreviations
            formatted = word.upper()
        elif i == 0 or clean_word.lower() not in lowercase_words:
            # Capitalize first word and words not in lowercase exceptions
            formatted = word.capitalize()
        else:
            # Keep lowercase for articles, prepositions, etc.
            formatted = word.lower()
        
        result.append(formatted)
    
    return ' '.join(result)

def clean_dropdown_data():
    """Clean and format all dropdown data"""
    try:
        db = NearMissDatabase()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Clean hazard types
        logger.info("Cleaning hazard types...")
        cursor.execute("SELECT hazard_type_id, hazard_type FROM hazard_types")
        hazard_types = cursor.fetchall()
        
        for hazard_id, hazard_type in hazard_types:
            cleaned = title_case_with_exceptions(hazard_type.strip())
            if cleaned != hazard_type:
                cursor.execute("UPDATE hazard_types SET hazard_type = %s WHERE hazard_type_id = %s", 
                             (cleaned, hazard_id))
                logger.info(f"Updated hazard type: '{hazard_type}' -> '{cleaned}'")
        
        # Clean immediate actions
        logger.info("Cleaning immediate actions...")
        cursor.execute("SELECT action_id, action_description FROM immediate_actions")
        actions = cursor.fetchall()
        
        for action_id, action_desc in actions:
            cleaned = title_case_with_exceptions(action_desc.strip())
            if cleaned != action_desc:
                cursor.execute("UPDATE immediate_actions SET action_description = %s WHERE action_id = %s", 
                             (cleaned, action_id))
                logger.info(f"Updated action: '{action_desc}' -> '{cleaned}'")
        
        # Clean equipment names
        logger.info("Cleaning equipment names...")
        cursor.execute("SELECT equip_id, equip_name FROM equipment")
        equipment = cursor.fetchall()
        
        for equip_id, equip_name in equipment:
            cleaned = title_case_with_exceptions(equip_name.strip())
            if cleaned != equip_name:
                cursor.execute("UPDATE equipment SET equip_name = %s WHERE equip_id = %s", 
                             (cleaned, equip_id))
                logger.info(f"Updated equipment: '{equip_name}' -> '{cleaned}'")
        
        # Clean department names
        logger.info("Cleaning department names...")
        cursor.execute("SELECT dept_id, dept_name FROM departments")
        departments = cursor.fetchall()
        
        for dept_id, dept_name in departments:
            cleaned = title_case_with_exceptions(dept_name.strip())
            if cleaned != dept_name:
                cursor.execute("UPDATE departments SET dept_name = %s WHERE dept_id = %s", 
                             (cleaned, dept_id))
                logger.info(f"Updated department: '{dept_name}' -> '{cleaned}'")
        
        conn.close()
        logger.info("Data cleanup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning data: {e}")
        return False

if __name__ == "__main__":
    success = clean_dropdown_data()
    if not success:
        sys.exit(1)