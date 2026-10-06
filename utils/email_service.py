import os
from dotenv import load_dotenv
from azure.communication.email import EmailClient
from azure.core.credentials import AzureKeyCredential
 
load_dotenv()  
 
endpoint = os.getenv("AZURE_COMMUNICATION_ENDPOINT")
 
key = os.getenv("AZURE_COMMUNICATION_KEY")
 
sender_email = os.getenv(
    "ACS_SENDER_EMAIL"
)
 
if not endpoint:
    raise ValueError(
        "AZURE_COMMUNICATION_ENDPOINT is missing"
    )
 
if not key:
    raise ValueError(
        "AZURE_COMMUNICATION_KEY is missing"
    )
if not sender_email:
    raise ValueError(
        "ACS_SENDER_EMAIL is missing"
    )
 
 
cc_recipients = [
    {"address": email.strip()}
    for email in os.getenv("MAIL_CC", "").split(",")
    if email.strip()
]
 
email_client = EmailClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(
        key
    )
)
 

def send_interview_email(
    candidate_email: str,
    candidate_name: str,
    interview_link: str,
    interview_id: str,
    role: str
):
   
    email_content = f"""
    Dear {candidate_name},
 
    You have been invited to join the interview.
 
    Please click the link below to get started:

    {interview_link}

    Below are the Interview Details:
    Interview ID: {interview_id}
    Applied Role : {role}

    Please have your Aadhar Card or any Government ID ready for the interview.

    Best Regards,
    Human Resources,
    ValueMomentum Services Pvt Ltd
    """.strip()
 
    message = {
        "senderAddress": sender_email,
        "recipients": {
            "to": [{"address": candidate_email}],
            "cc": cc_recipients
        },
        "content":{
        "subject": "On Boarding Invitation",
        "plainText": email_content
    }
    }
    try:
        poller = email_client.begin_send(message)
       
        poller.result()
 
       
        return True
   
 
    except Exception as ex:
 
        raise RuntimeError(
            f"Failed to send email: {str(ex)}")