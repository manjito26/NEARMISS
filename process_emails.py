#!/usr/bin/env python3
"""
NEARMISS Email Queue Processor
Background script to process queued emails
Run this periodically via cron or as a service
"""
import sys
import os
import time
import logging
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.utils.email import EmailManager
except ImportError as e:
    print(f"Error importing EmailManager: {e}")
    print("Make sure you're running from the NEARMISS directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/email_processor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main email processing function"""
    logger.info("=" * 50)
    logger.info("NEARMISS Email Queue Processor Starting")
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    try:
        # Initialize email manager
        email_manager = EmailManager()
        
        # Check email configuration
        if not email_manager.config or not email_manager.config.get('smtp_server'):
            logger.warning("No email configuration found. Emails cannot be sent.")
            return
        
        logger.info(f"Email configuration loaded: {email_manager.config.get('smtp_server')}:{email_manager.config.get('smtp_port')}")
        
        # Test connection (optional)
        if email_manager.test_email_connection():
            logger.info("Email server connection test successful")
        else:
            logger.warning("Email server connection test failed - continuing with queue processing")
        
        # Process email queue
        logger.info("Processing email queue...")
        sent_count = email_manager.send_queued_emails()
        
        if sent_count > 0:
            logger.info(f"Successfully sent {sent_count} emails")
        else:
            logger.info("No emails were sent (queue empty or all failed)")
        
        # Get queue status
        status = email_manager.get_email_queue_status()
        logger.info(f"Queue Status - Pending: {status.get('pending', 0)}, "
                   f"Sent: {status.get('sent', 0)}, "
                   f"Failed: {status.get('failed', 0)}")
        
        logger.info("Email processing completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Email processor stopped by user")
    except Exception as e:
        logger.error(f"Error in email processor: {e}")
        sys.exit(1)

def run_daemon(interval=300):
    """Run as daemon process with specified interval (default 5 minutes)"""
    logger.info(f"Starting email processor daemon (checking every {interval} seconds)")
    
    try:
        while True:
            main()
            logger.info(f"Sleeping for {interval} seconds...")
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Email processor daemon stopped by user")
    except Exception as e:
        logger.error(f"Email processor daemon error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='NEARMISS Email Queue Processor')
    parser.add_argument('--daemon', '-d', action='store_true', 
                       help='Run as daemon process')
    parser.add_argument('--interval', '-i', type=int, default=300,
                       help='Interval in seconds for daemon mode (default: 300)')
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    if args.daemon:
        run_daemon(args.interval)
    else:
        main()