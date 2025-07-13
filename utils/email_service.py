"""
Email Service

This module handles email notifications for property alerts.
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from datetime import datetime

from database.database_manager import DatabaseManager
from scraper.base_scraper import PropertyListing

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending email notifications
    
    This class handles:
    - Sending property alert emails
    - Email template management
    - SMTP configuration
    """
    
    def __init__(self):
        """Initialize the email service"""
        self.smtp_server = os.environ.get('SMTP_SERVER')
        self.smtp_port = int(os.environ.get('SMTP_PORT', 587))
        self.smtp_username = os.environ.get('SMTP_USERNAME')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.from_email = os.environ.get('ALERT_EMAIL_FROM', 'alerts@realestate-scraper.com')
        
        # Initialize database manager
        self.db_manager = DatabaseManager()
        
        # Check if email is configured
        self.is_configured = all([
            self.smtp_server,
            self.smtp_username,
            self.smtp_password
        ])
        
        if not self.is_configured:
            logger.warning("Email service not fully configured. Alerts will not be sent.")
    
    def send_alert_email(
        self,
        user_email: str,
        user_name: str,
        alert_name: str,
        matching_listings: List[PropertyListing]
    ) -> bool:
        """
        Send an alert email to a user
        
        Args:
            user_email: User's email address
            user_name: User's name
            alert_name: Name of the alert
            matching_listings: List of matching property listings
            
        Returns:
            bool: True if email sent successfully
        """
        if not self.is_configured:
            logger.warning("Email service not configured, skipping alert email")
            return False
        
        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🏠 New Property Alert: {alert_name}"
            msg['From'] = self.from_email
            msg['To'] = user_email
            
            # Create email content
            html_content = self._create_alert_email_html(
                user_name, alert_name, matching_listings
            )
            text_content = self._create_alert_email_text(
                user_name, alert_name, matching_listings
            )
            
            # Attach content
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Alert email sent to {user_email} for {len(matching_listings)} listings")
            return True
            
        except Exception as e:
            logger.error(f"Error sending alert email to {user_email}: {e}")
            return False
    
    def _create_alert_email_html(
        self,
        user_name: str,
        alert_name: str,
        listings: List[PropertyListing]
    ) -> str:
        """
        Create HTML content for alert email
        
        Args:
            user_name: User's name
            alert_name: Alert name
            listings: Matching listings
            
        Returns:
            str: HTML email content
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .listing {{ border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 5px; }}
                .listing-title {{ font-size: 18px; font-weight: bold; color: #2c3e50; }}
                .listing-details {{ margin: 10px 0; }}
                .price {{ font-size: 16px; color: #e74c3c; font-weight: bold; }}
                .location {{ color: #7f8c8d; }}
                .footer {{ background: #ecf0f1; padding: 15px; text-align: center; font-size: 12px; }}
                .btn {{ display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏠 Real Estate Alert</h1>
                    <p>New properties matching your criteria</p>
                </div>
                
                <div class="content">
                    <p>Hello {user_name},</p>
                    
                    <p>We found <strong>{len(listings)} new properties</strong> matching your alert "<strong>{alert_name}</strong>":</p>
                    
                    {self._create_listings_html(listings)}
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:5000" class="btn">View All Properties</a>
                    </p>
                    
                    <p>Best regards,<br>
                    Real Estate Scraper Team</p>
                </div>
                
                <div class="footer">
                    <p>You received this email because you have an active property alert.</p>
                    <p>To manage your alerts, visit your dashboard.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_listings_html(self, listings: List[PropertyListing]) -> str:
        """
        Create HTML for listings section
        
        Args:
            listings: List of property listings
            
        Returns:
            str: HTML for listings
        """
        html = ""
        
        for listing in listings:
            # Format price
            if listing.price >= 1000000000:  # Billion
                price_str = f"{listing.price / 1000000000:.1f} tỷ VND"
            elif listing.price >= 1000000:  # Million
                price_str = f"{listing.price / 1000000:.0f} triệu VND"
            else:
                price_str = f"{listing.price:,.0f} VND"
            
            # Format price per m²
            if listing.price_per_m2 >= 1000000:
                price_per_m2_str = f"{listing.price_per_m2 / 1000000:.1f}M VND/m²"
            else:
                price_per_m2_str = f"{listing.price_per_m2:,.0f} VND/m²"
            
            html += f"""
            <div class="listing">
                <div class="listing-title">{listing.title}</div>
                <div class="listing-details">
                    <div class="price">{price_str}</div>
                    <div class="location">📍 {listing.location}</div>
                    <div>🏠 {listing.property_type} • {listing.area}m² • {price_per_m2_str}</div>
                    {f'<div>🛏️ {listing.bedrooms} phòng ngủ' if listing.bedrooms else ''}
                    {f' • 🚿 {listing.bathrooms} phòng tắm' if listing.bathrooms else ''}
                    <div>📅 {listing.timestamp.strftime('%d/%m/%Y %H:%M')} • 📊 {listing.source}</div>
                </div>
                <div style="margin-top: 10px;">
                    <a href="{listing.link}" target="_blank" class="btn">View Details</a>
                </div>
            </div>
            """
        
        return html
    
    def _create_alert_email_text(
        self,
        user_name: str,
        alert_name: str,
        listings: List[PropertyListing]
    ) -> str:
        """
        Create plain text content for alert email
        
        Args:
            user_name: User's name
            alert_name: Alert name
            listings: Matching listings
            
        Returns:
            str: Plain text email content
        """
        text = f"""
Real Estate Alert

Hello {user_name},

We found {len(listings)} new properties matching your alert "{alert_name}":

"""
        
        for i, listing in enumerate(listings, 1):
            # Format price
            if listing.price >= 1000000000:  # Billion
                price_str = f"{listing.price / 1000000000:.1f} tỷ VND"
            elif listing.price >= 1000000:  # Million
                price_str = f"{listing.price / 1000000:.0f} triệu VND"
            else:
                price_str = f"{listing.price:,.0f} VND"
            
            text += f"""
{i}. {listing.title}
   Price: {price_str}
   Location: {listing.location}
   Type: {listing.property_type}
   Area: {listing.area}m²
   Price/m²: {listing.price_per_m2:,.0f} VND/m²
   Source: {listing.source}
   Link: {listing.link}

"""
        
        text += """
Best regards,
Real Estate Scraper Team

---
You received this email because you have an active property alert.
To manage your alerts, visit your dashboard.
"""
        
        return text
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """
        Send welcome email to new users
        
        Args:
            user_email: User's email address
            user_name: User's name
            
        Returns:
            bool: True if email sent successfully
        """
        if not self.is_configured:
            logger.warning("Email service not configured, skipping welcome email")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "🏠 Welcome to Real Estate Scraper!"
            msg['From'] = self.from_email
            msg['To'] = user_email
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #2c3e50; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .btn {{ display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🏠 Welcome to Real Estate Scraper!</h1>
                    </div>
                    
                    <div class="content">
                        <p>Hello {user_name},</p>
                        
                        <p>Welcome to Real Estate Scraper! We're excited to help you find your perfect property in Vietnam.</p>
                        
                        <h3>What you can do:</h3>
                        <ul>
                            <li>🔍 Search properties with advanced filters</li>
                            <li>📊 Compare prices and market trends</li>
                            <li>🔔 Set up alerts for new listings</li>
                            <li>📈 Track price changes over time</li>
                            <li>📱 Get notifications via email</li>
                        </ul>
                        
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="http://localhost:5000" class="btn">Get Started</a>
                        </p>
                        
                        <p>If you have any questions, feel free to reach out to our support team.</p>
                        
                        <p>Best regards,<br>
                        Real Estate Scraper Team</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
Welcome to Real Estate Scraper!

Hello {user_name},

Welcome to Real Estate Scraper! We're excited to help you find your perfect property in Vietnam.

What you can do:
- Search properties with advanced filters
- Compare prices and market trends
- Set up alerts for new listings
- Track price changes over time
- Get notifications via email

Get started: http://localhost:5000

Best regards,
Real Estate Scraper Team
"""
            
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Welcome email sent to {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {user_email}: {e}")
            return False
    
    def test_email_configuration(self) -> bool:
        """
        Test email configuration
        
        Returns:
            bool: True if configuration is working
        """
        if not self.is_configured:
            logger.error("Email service not configured")
            return False
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                logger.info("Email configuration test successful")
                return True
                
        except Exception as e:
            logger.error(f"Email configuration test failed: {e}")
            return False 