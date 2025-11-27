from typing import List
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, Content
from app.config.settings import settings
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        self.from_email = settings.SENDGRID_FROM_EMAIL
    
     
    async def send_email(self, to_email: str, subject: str, content: str, html_content: str = None) -> bool:
        """Send email to a single recipient"""
     
        # Set up SMTP server connection

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
       
    # Login to the Gmail SMTP server
        user_email = "innotrend23@gmail.com"  # Replace with your email
        app_password = "zikj epah lvuf qwhx"  # Replace with your Gmail App Password
        server.login(user_email, app_password)

    # Create message container (MIME)
        msg = MIMEMultipart()
        msg['From'] = f'innoTrend <{user_email}>'
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Reply-To'] = user_email
        msg['X-Priority'] = '3'
        msg['X-MSMail-Priority'] = 'Normal'
        msg['Importance'] = 'Normal'
      
    # Attach the HTML content of the email
        msg.attach(MIMEText(content, 'plain'))
        if html_content:
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

        try:
        # Send email
         server.sendmail(user_email, to_email, msg.as_string())
        
         return True
        except Exception as e:
          print(f"Failed to send email to {to_email}: {e}")
    
          return False
        finally:
        # Close the connection
          server.quit()
          return False

    
    async def send_bulk_email(self, recipients: List[str], subject: str, content: str, html_content: str = None) -> dict:
        """Send email to multiple recipients"""
        
        results = {
            "success": [],
            "failed": []
        }
        for email in recipients:
           
            success = await self.send_email(email, subject, content, html_content)
            if success:
                results["success"].append(email)
            else:
                results["failed"].append(email)
        
        return results
    
    async def send_order_confirmation(self, to_email: str, order_number: str, customer_name: str, product_service: str, amount: float) -> bool:
        """Send order confirmation email"""
        subject = f"Order Confirmation - {order_number}"
        content = f"""
Dear {customer_name},

Thank you for your order with InnoTrend!

Order Details:
- Order Number: {order_number}
- Product/Service: {product_service}
- Amount: ${amount:.2f}

We will process your order shortly and keep you updated on its progress.

Best regards,
InnoTrend Team
        """
        
        html_content = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Order Confirmation</h2>
        <p>Dear {customer_name},</p>
        <p>Thank you for your order with InnoTrend!</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0;">Order Details:</h3>
            <p><strong>Order Number:</strong> {order_number}</p>
            <p><strong>Product/Service:</strong> {product_service}</p>
            <p><strong>Amount:</strong> Cedis{amount:.2f}</p>
        </div>
        
        <p>We will process your order shortly and keep you updated on its progress.</p>
        
        <p>Best regards,<br>InnoTrend Team</p>
    </div>
</body>
</html>
        """
        
        return await self.send_email(to_email, subject, content, html_content)
    
    async def send_order_update(self, to_email: str, order_number: str, customer_name: str, status: str, progress_notes: str = None) -> bool:
        """Send order status update email"""
        subject = f"Order Update - {order_number}"
        content = f"""
Dear {customer_name},

Your order {order_number} has been updated.

Current Status: {status}
{f"Progress Notes: {progress_notes}" if progress_notes else ""}

Thank you for choosing innoTrend!

Best regards,
InnoTrend Team
        """
        
        return await self.send_email(to_email, subject, content)
    
    async def send_contact_form_response(self, to_email: str, name: str, original_message: str, response: str) -> bool:
        """Send response to contact form submission"""
        subject = "Response to Your Inquiry - InnoTrend"
        content = f"""
Dear {name},

Thank you for contacting InnoTrend. We have received your message:

"{original_message}"

Our response:
{response}

If you have any further questions, please don't hesitate to reach out.

Best regards,
InnoTrend Team
        """
        
        return await self.send_email(to_email, subject, content)
    
    async def notify_admin_new_order(self, order_number: str, customer_name: str, customer_email: str, product_service: str, amount: float, phone:str) -> bool:
        """Notify admin about new order"""
        subject = f"New Order Received - {order_number}"
        content = f"""
New order has been placed!

Order Number: {order_number}
Customer: {customer_name} ({customer_email})
Product/Service: ${product_service}
Amount: ${amount:.2f}

Please check the admin dashboard for more details.
        """
        
        return await self.send_email(settings.ADMIN_EMAIL, subject, content)
    
    async def notify_admin_contact_form(self, name: str, email: str, message: str, phone: str = None) -> bool:
        """Notify admin about new contact form submission"""
        subject = f"New Contact Form Submission from {name}"
        content = f"""
New contact form submission received:

Name: {name}
Email: {email}
{f"Phone: {phone}" if phone else ""}

Message:
{message}

Please respond to this inquiry through the admin dashboard.
        """
        
        return await self.send_email(settings.ADMIN_EMAIL, subject, content)

