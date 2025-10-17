#!/usr/bin/env python3
"""
Database initialization script for NEARMISS system
Creates database, tables, and initial data
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models.database import NearMissDatabase
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Initialize the database"""
    try:
        logger.info("Starting NEARMISS database initialization...")
        
        db = NearMissDatabase()
        
        # Create database
        logger.info("Creating database...")
        db.create_database()
        
        # Create tables
        logger.info("Creating tables...")
        db.create_tables()
        
        # Insert initial data
        logger.info("Inserting initial data...")
        db.insert_initial_data()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()