from typing import List
from twilio.rest import Client
from app.config.settings import settings
from app.utils.helpers import format_phone_number
import logging
import requests

logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.from_number = settings.TWILIO_PHONE_NUMBER
    
    async def send_sms(self, to_number: str, message: str) -> bool:
        """Send SMS to a single number"""
        try:
            # formatted_number = format_phone_number(to_number)
            # message_response = self.client.messages.create(
            #     body=message,
            #     from_=self.from_number,
            #     to=formatted_number
            # )
          
            base_url = f"https://sms.arkesel.com/sms/api?action=send-sms&api_key={settings.Arkesel}&from={settings.Sender_id}"
            sms_url = base_url + f"&to={to_number}&sms={message}"
           
            ## When terminating sms traffic to Nigerian contacts, you are required to specify the use_case to the fields submitted
            ## ie.|   sms_url = base_url + f"&to={phone_number}&sms={message}&use_case=transactional"

            response = requests.get(sms_url)
            response_json = response.json()
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
            return False
    
    async def send_bulk_sms(self, phone_numbers: List[str], message: str) -> dict:
        """Send SMS to multiple numbers"""
        results = {
            "success": [],
            "failed": []
        }
        # print('bulk sms function called')
        for number in phone_numbers:
            success = await self.send_sms(number, message)
           
            if success is True:
                results["success"].append(number)
            else:
                results["failed"].append(number)
     
        return results
    
    async def send_order_notification(self, phone_number: str, order_number: str, status: str) -> bool:
        """Send order status notification"""
        message = f"InnoTrend Order Update: Your order {order_number} is now {status}. Thank you for your business!"
        return await self.send_sms(phone_number, message)
    
    async def notify_admin_new_order(self, order_number: str, customer_name: str) -> bool:
        """Notify admin about new order"""
        message = f"New Order Alert! Order {order_number} from {customer_name} has been placed. Please check the dashboard."
        return await self.send_sms(settings.ADMIN_PHONE_NUMBER, message)
    
    async def notify_admin_contact_form(self, customer_name: str, customer_email: str) -> bool:
        """Notify admin about new contact form submission"""
        message = f"New Contact Form: {customer_name} ({customer_email}) has sent a message. Check your dashboard."
        return await self.send_sms(settings.ADMIN_PHONE_NUMBER, message)

