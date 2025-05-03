from twilio.rest import Client
from dotenv import load_dotenv
import os
from urllib.parse import quote

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

# initialize twilio client
client = Client(account_sid, auth_token)

# define the list of moving companies and their phone numbers
companies = [
    {"name": "Best Movers", "phone": "+17023039282"},
    {"name": "Talia's Moving", "phone": "+16178178993"}
]

# companies_real = [
#     {"name": "U-Pack", "phone": "+18009683285"},
#     {"name": "Allied Van Lines", "phone": "+18006898684"},
#     {"name": "North American Van Lines", "phone": "+18002283092"},
#     {"name": "PODS", "phone": "+18777707637"},
#     {"name": "Mayflower", "phone": "+18777204066"},
#     {"name": "Two Men and a Truck", "phone": "+18003451070"}
# ]

webhook_base = os.getenv("VOICE_WEBHOOK_URL")

def dispatch_call(from_city, to_city):
    """
    Iterate through the list of companies and, dial the phone number in order and trigger the voice webhook with the city parameter entered by the user
    """
    for company in companies:
        number = company["phone"]
        name = company["name"]
        try:
            webhook_url = f"{webhook_base}/voice?from={quote(from_city)}&to={quote(to_city)}"
            call = client.calls.create(
                to=number,
                from_=twilio_number,
                url=webhook_url
            )
            print(f"Dialing {name} at {number}")
            print(f"Call SID: {call.sid}")
        except Exception as e:
            print(f"Error dialing {name}: {e}")

# test the function
if __name__ == "__main__":
    from_city = input("Enter the city of origin: ").strip()
    to_city = input("Enter the city of destination: ").strip()
    dispatch_call(from_city, to_city)
            
