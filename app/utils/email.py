"""
Email notification system for NEARMISS
Handles SMTP configuration, email queue, and sending notifications
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
from ..models.database import NearMissDatabase

logger = logging.getLogger(__name__)

class EmailManager:
    def __init__(self):
        self.db = NearMissDatabase()
        self.config = self.load_email_config()
    
    def load_email_config(self) -> Dict:
        """Load email configuration from database"""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM email_config ORDER BY config_id DESC")
            row = cursor.fetchone()
            
            if row:
                return {
                    'smtp_server': row[1],
                    'smtp_port': row[2],
                    'username': row[3],
                    'password_encrypted': row[4],
                    'auth_type': row[5],
                    'use_auth': row[6],
                    'timeout': row[7],
                    'retries': row[8]
                }
            else:
                # Default configuration
                return {
                    'smtp_server': 'smtp.office365.com',
                    'smtp_port': 587,
                    'username': 'nearmiss@fresco.com',
                    'password_encrypted': None,
                    'auth_type': 'STARTTLS',
                    'use_auth': True,
                    'timeout': 30,
                    'retries': 3
                }
        except Exception as e:
            logger.error(f"Error loading email config: {e}")
            return {}
        finally:
            conn.close()
    
    def save_email_config(self, config: Dict) -> bool:
        """Save email configuration to database"""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO email_config (smtp_server, smtp_port, username, password_encrypted, 
                                        auth_type, use_auth, timeout, retries)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                config.get('smtp_server'),
                config.get('smtp_port', 587),
                config.get('username'),
                config.get('password_encrypted'),
                config.get('auth_type', 'STARTTLS'),
                config.get('use_auth', True),
                config.get('timeout', 30),
                config.get('retries', 3)
            ))
            logger.info("Email configuration saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving email config: {e}")
            return False
        finally:
            conn.close()
    
    def queue_email(self, to_address: str, subject: str, body: str, report_id: int = None) -> bool:
        """Add email to queue for sending"""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO email_queue (to_address, subject, body, report_id, status, created_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (to_address, subject, body, report_id, 'pending', datetime.now()))
            
            logger.info(f"Email queued for {to_address}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Error queuing email: {e}")
            return False
        finally:
            conn.close()
    
    def send_queued_emails(self) -> int:
        """Send all pending emails in queue"""
        conn = self.db.get_connection()
        sent_count = 0
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT queue_id, to_address, subject, body, report_id, retry_count
                FROM email_queue 
                WHERE status = 'pending' AND retry_count < %s
                ORDER BY created_date
            """, (self.config.get('retries', 3),))
            
            pending_emails = cursor.fetchall()
            
            for email in pending_emails:
                queue_id, to_address, subject, body, report_id, retry_count = email
                
                if self.send_email(to_address, subject, body):
                    # Mark as sent
                    cursor.execute("""
                        UPDATE email_queue 
                        SET status = 'sent', sent_date = %s 
                        WHERE queue_id = %s
                    """, (datetime.now(), queue_id))
                    
                    # Add to history
                    cursor.execute("""
                        INSERT INTO email_history (to_address, subject, report_id, sent_date, status)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (to_address, subject, report_id, datetime.now(), 'sent'))
                    
                    sent_count += 1
                    logger.info(f"Email sent successfully to {to_address}")
                    
                else:
                    # Increment retry count
                    new_retry_count = retry_count + 1
                    if new_retry_count >= self.config.get('retries', 3):
                        # Mark as failed after max retries
                        cursor.execute("""
                            UPDATE email_queue 
                            SET status = 'failed', retry_count = %s 
                            WHERE queue_id = %s
                        """, (new_retry_count, queue_id))
                        
                        cursor.execute("""
                            INSERT INTO email_history (to_address, subject, report_id, sent_date, status)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (to_address, subject, report_id, datetime.now(), 'failed'))
                        
                        logger.error(f"Email failed permanently for {to_address} after {new_retry_count} attempts")
                    else:
                        # Update retry count for next attempt
                        cursor.execute("""
                            UPDATE email_queue 
                            SET retry_count = %s 
                            WHERE queue_id = %s
                        """, (new_retry_count, queue_id))
                        
                        logger.warning(f"Email retry {new_retry_count} for {to_address}")
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Error sending queued emails: {e}")
            return 0
        finally:
            conn.close()
    
    def send_email(self, to_address: str, subject: str, body: str, is_html: bool = True) -> bool:
        """Send individual email"""
        if not self.config or not self.config.get('smtp_server'):
            logger.error("Email configuration not available")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config['username']
            msg['To'] = to_address
            msg['Subject'] = subject
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'], timeout=self.config.get('timeout', 30)) as server:
                if self.config.get('auth_type') == 'STARTTLS':
                    server.starttls()
                
                if self.config.get('use_auth') and self.config.get('password_encrypted'):
                    # In production, decrypt the password here
                    password = self.config['password_encrypted']  # Implement decryption
                    server.login(self.config['username'], password)
                
                server.sendmail(self.config['username'], [to_address], msg.as_string())
                return True
                
        except Exception as e:
            logger.error(f"Error sending email to {to_address}: {e}")
            return False
    
    def send_near_miss_notification(self, report_data: Dict, notification_type: str = 'new_report') -> bool:
        """Send near miss report notification"""
        try:
            # Get supervisors and admins for notification
            recipients = self.get_notification_recipients(report_data.get('plant'))
            
            if not recipients:
                logger.warning("No notification recipients found")
                return False
            
            # Generate email content based on notification type
            if notification_type == 'new_report':
                subject = f"New Near Miss Report - {report_data.get('plant')} Plant"
                body = self.generate_new_report_email(report_data)
            elif notification_type == 'high_priority':
                subject = f"HIGH PRIORITY: Near Miss Report - {report_data.get('plant')} Plant"
                body = self.generate_high_priority_email(report_data)
            else:
                subject = f"Near Miss Report Update - {report_data.get('plant')} Plant"
                body = self.generate_update_email(report_data)
            
            # Queue emails for all recipients
            success = True
            for recipient in recipients:
                if not self.queue_email(recipient['email'], subject, body, report_data.get('report_id')):
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending near miss notification: {e}")
            return False
    
    def get_notification_recipients(self, plant: str = None) -> List[Dict]:
        """Get list of users who should receive notifications"""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT first_name, last_name, email, username, plant
                FROM users 
                WHERE (is_supervisor = 1 OR is_admin = 1)
                AND password_hash IS NOT NULL
            """
            params = []
            
            if plant:
                query += " AND plant = %s"
                params.append(plant)
                
            query += " ORDER BY is_admin DESC, last_name"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                {
                    'first_name': row[0],
                    'last_name': row[1],
                    'email': row[2],
                    'username': row[3],
                    'plant': row[4]
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error getting notification recipients: {e}")
            return []
        finally:
            conn.close()
    
    def generate_new_report_email(self, report_data: Dict) -> str:
        """Generate HTML email for new report notification"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #28a745; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ padding: 20px; background-color: #f8f9fa; border-radius: 5px; margin-top: 10px; }}
                .field {{ margin-bottom: 10px; }}
                .label {{ font-weight: bold; color: #495057; }}
                .priority-high {{ background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; }}
                .priority-medium {{ background-color: #ffc107; color: black; padding: 3px 8px; border-radius: 3px; }}
                .priority-low {{ background-color: #17a2b8; color: white; padding: 3px 8px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 New Near Miss Report Submitted</h2>
            </div>
            
            <div class="content">
                <div class="field">
                    <span class="label">Report ID:</span> #{report_data.get('report_id', 'N/A')}
                </div>
                
                <div class="field">
                    <span class="label">Date/Time:</span> 
                    {report_data.get('date_occurred', 'N/A')} at {report_data.get('time_occurred', 'N/A')}
                </div>
                
                <div class="field">
                    <span class="label">Employee:</span> {report_data.get('employee_name', 'N/A')}
                </div>
                
                <div class="field">
                    <span class="label">Location:</span> 
                    {report_data.get('plant', 'N/A')} Plant - {report_data.get('dept_name', 'N/A')}
                    {f" ({report_data.get('equipment_area')})" if report_data.get('equipment_area') else ''}
                </div>
                
                {f'''<div class="field">
                    <span class="label">Priority:</span> 
                    <span class="priority-{report_data.get('hazard_assessment', '').lower().replace('/', '').replace(' ', '')}">{report_data.get('hazard_assessment')}</span>
                </div>''' if report_data.get('hazard_assessment') else ''}
                
                <div class="field">
                    <span class="label">Description:</span>
                    <div style="background: white; padding: 10px; border-left: 4px solid #28a745; margin-top: 5px;">
                        {report_data.get('description', 'No description provided')}
                    </div>
                </div>
                
                {f'''<div class="field">
                    <span class="label">Immediate Action:</span> {report_data.get('immediate_action', 'None specified')}
                </div>''' if report_data.get('immediate_action') else ''}
                
                <div class="field">
                    <span class="label">Submitted by:</span> {report_data.get('created_by', 'N/A')}
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background: white; border-radius: 5px;">
                    <p><strong>Action Required:</strong></p>
                    <ul>
                        <li>Review the incident details</li>
                        <li>Assess if corrective action is needed</li>
                        <li>Update the report status as appropriate</li>
                    </ul>
                </div>
            </div>
            
            <p style="font-size: 12px; color: #6c757d; margin-top: 20px;">
                This is an automated notification from the NEARMISS System.
            </p>
        </body>
        </html>
        """
    
    def generate_high_priority_email(self, report_data: Dict) -> str:
        """Generate HTML email for high priority report"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #dc3545; color: white; padding: 15px; border-radius: 5px; }}
                .urgent {{ background-color: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .content {{ padding: 20px; background-color: #f8f9fa; border-radius: 5px; }}
                .field {{ margin-bottom: 10px; }}
                .label {{ font-weight: bold; color: #495057; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 HIGH PRIORITY: Near Miss Report</h2>
            </div>
            
            <div class="urgent">
                <h3>⚠️ IMMEDIATE ATTENTION REQUIRED ⚠️</h3>
                <p>This near miss has been classified as <strong>HIGH/IMMEDIATE</strong> priority and requires urgent review and action.</p>
            </div>
            
            <div class="content">
                <div class="field">
                    <span class="label">Report ID:</span> #{report_data.get('report_id', 'N/A')}
                </div>
                
                <div class="field">
                    <span class="label">Date/Time:</span> 
                    {report_data.get('date_occurred', 'N/A')} at {report_data.get('time_occurred', 'N/A')}
                </div>
                
                <div class="field">
                    <span class="label">Employee:</span> {report_data.get('employee_name', 'N/A')}
                </div>
                
                <div class="field">
                    <span class="label">Location:</span> 
                    {report_data.get('plant', 'N/A')} Plant - {report_data.get('dept_name', 'N/A')}
                    {f" ({report_data.get('equipment_area')})" if report_data.get('equipment_area') else ''}
                </div>
                
                <div class="field">
                    <span class="label">Description:</span>
                    <div style="background: white; padding: 10px; border-left: 4px solid #dc3545; margin-top: 5px;">
                        {report_data.get('description', 'No description provided')}
                    </div>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background: white; border-radius: 5px; border-left: 4px solid #dc3545;">
                    <p><strong>IMMEDIATE ACTIONS REQUIRED:</strong></p>
                    <ul>
                        <li>Stop work if area poses immediate danger</li>
                        <li>Investigate the incident immediately</li>
                        <li>Implement corrective measures</li>
                        <li>Update report status within 2 hours</li>
                    </ul>
                </div>
            </div>
            
            <p style="font-size: 12px; color: #6c757d; margin-top: 20px;">
                This is an automated HIGH PRIORITY notification from the NEARMISS System.
            </p>
        </body>
        </html>
        """
    
    def generate_update_email(self, report_data: Dict) -> str:
        """Generate HTML email for report updates"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #17a2b8; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ padding: 20px; background-color: #f8f9fa; border-radius: 5px; margin-top: 10px; }}
                .field {{ margin-bottom: 10px; }}
                .label {{ font-weight: bold; color: #495057; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📝 Near Miss Report Updated</h2>
            </div>
            
            <div class="content">
                <div class="field">
                    <span class="label">Report ID:</span> #{report_data.get('report_id', 'N/A')}
                </div>
                
                <div class="field">
                    <span class="label">Updated by:</span> {report_data.get('updated_by', 'N/A')}
                </div>
                
                <div class="field">
                    <span class="label">Update Date:</span> {datetime.now().strftime('%m/%d/%Y %H:%M')}
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background: white; border-radius: 5px;">
                    <p>A near miss report has been updated. Please review the changes and take appropriate action if needed.</p>
                </div>
            </div>
            
            <p style="font-size: 12px; color: #6c757d; margin-top: 20px;">
                This is an automated notification from the NEARMISS System.
            </p>
        </body>
        </html>
        """
    
    def test_email_connection(self) -> bool:
        """Test email server connection"""
        if not self.config or not self.config.get('smtp_server'):
            return False
        
        try:
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'], timeout=10) as server:
                if self.config.get('auth_type') == 'STARTTLS':
                    server.starttls()
                return True
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False
    
    def get_email_queue_status(self) -> Dict:
        """Get email queue statistics"""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Get queue counts
            cursor.execute("SELECT status, COUNT(*) FROM email_queue GROUP BY status")
            queue_stats = dict(cursor.fetchall())
            
            # Get recent emails
            cursor.execute("""
                SELECT to_address, subject, status, created_date, sent_date
                FROM email_queue 
                ORDER BY created_date DESC 
                LIMIT 20
            """)
            recent_emails = cursor.fetchall()
            
            return {
                'pending': queue_stats.get('pending', 0),
                'sent': queue_stats.get('sent', 0),
                'failed': queue_stats.get('failed', 0),
                'recent_emails': recent_emails
            }
        except Exception as e:
            logger.error(f"Error getting email queue status: {e}")
            return {}
        finally:
            conn.close()