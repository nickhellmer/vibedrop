import os
from twilio.rest import Client

def send_sms(to_number, message_body):
    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )
    from_number = os.getenv("TWILIO_PHONE_NUMBER")

    message = client.messages.create(
        body=message_body,
        from_=from_number,
        to=to_number
    )
    return message.sid