#!/usr/bin/env python3
"""
NEARMISS System - Startup Script
Near Miss reporting Flask web application

To run the application:
    python run.py

Or for development with debug mode:
    python run.py --debug
"""
import os
import sys
import logging
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app import create_app
except ImportError as e:
    print(f"Error importing app: {e}")
    print("Make sure you're in the NEARMISS directory and all dependencies are installed")
    sys.exit(1)

# Configure logging
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to start the Flask application"""
    
    # Check if debug mode is requested
    debug_mode = '--debug' in sys.argv or '-d' in sys.argv
    
    logger.info("="*60)
    logger.info("NEARMISS System Starting...")
    logger.info(f"Debug Mode: {debug_mode}")
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    try:
        # Create Flask application
        app = create_app()
        
        # Application configuration
        host = '0.0.0.0'  # Allow external connections
        port = 5000
        
        logger.info(f"Starting server on http://{host}:{port}")
        logger.info("Available endpoints:")
        logger.info("  - http://localhost:5000/login (Login page)")
        logger.info("  - http://localhost:5000/ (Dashboard)")
        logger.info("  - http://localhost:5000/entry (Near Miss Entry)")
        logger.info("  - http://localhost:5000/reports (View Reports)")
        logger.info("  - http://localhost:5000/debug (Debug information)")
        logger.info("="*60)
        
        # Start the Flask development server
        app.run(
            host=host,
            port=port,
            debug=debug_mode,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()