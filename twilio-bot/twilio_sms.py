import os
from dotenv import load_dotenv
from twilio.rest import Client
from typing import Optional, List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(override=True)

class TwilioSMS:
    def __init__(self, alpha_sender_id=None):
        """Initialize the Twilio client with alpha sender ID."""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.alpha_sender_id = alpha_sender_id
        
        # Validate required credentials
        if not all([self.account_sid, self.auth_token]):
            missing = []
            if not self.account_sid: missing.append("TWILIO_ACCOUNT_SID")
            if not self.auth_token: missing.append("TWILIO_AUTH_TOKEN")
            
            error_msg = f"Missing required Twilio credentials: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not self.alpha_sender_id:
            error_msg = "Alpha sender ID is required"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        self.from_identity = self.alpha_sender_id
        self.client = Client(self.account_sid, self.auth_token)
        logger.info(f"Twilio SMS service initialized with sender identity: {self.from_identity}")
    
    def send_sms(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send an SMS message using Twilio."""
        
        if to_number is None:
            to_number = "+48605555835"
        try:
            if not to_number.startswith('+'):
                logger.warning(f"Phone number {to_number} may not be in E.164 format")
            
            sms = self.client.messages.create(
                body=message,
                from_=self.from_identity,
                to=to_number
            )
            
            logger.info(f"SMS sent successfully to {to_number}. SID: {sms.sid}")
            
            return {
                'sid': sms.sid,
                'status': sms.status,
                'to': sms.to,
                'from': sms.from_,
                'body': sms.body,
                'date_created': str(sms.date_created),
                'date_sent': str(sms.date_sent) if sms.date_sent else None,
            }
            
        except Exception as e:
            error_message = f"Failed to send SMS to {to_number}: {str(e)}"
            logger.error(error_message)
            raise Exception(error_message)
    
    def send_bulk_sms(self, to_numbers: List[str], message: str) -> List[Dict[str, Any]]:
        """Send the same SMS message to multiple recipients."""
        results = []
        errors = []
        
        for number in to_numbers:
            try:
                result = self.send_sms(number, message)
                results.append(result)
            except Exception as e:
                errors.append(f"{number}: {str(e)}")
        
        if errors:
            logger.warning(f"Some messages failed to send: {', '.join(errors)}")
        
        return results


if __name__ == "__main__":
    try:
        sms_sender = TwilioSMS(alpha_sender_id="AsystentNFZ")
        recipient = ""  # Replace with a real phone number
        message = "This is a test message from your NFZ appointment system!"
        
        result = sms_sender.send_sms(recipient, message)
        print(f"Message sent successfully! SID: {result['sid']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")