import os
from dotenv import load_dotenv
from azure.communication.email import EmailClient
from azure.core.credentials import AzureKeyCredential
from models.models import InterviewMetadata
from starlette.concurrency import run_in_threadpool
from services.db_connection import insert_metadata
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
    
#     email_content_html = f"""
#     <html>
#     <body>
#     Dear {candidate_name},

#    <p>You have been invited to join the interview.</p>

#     <p>Please click the link below to get started:</p>

#     <p>{interview_link}</p>

#     <p>Below are the Interview Details:</p>
#     <p>Interview ID: {interview_id}</p>
#     <p>Applied Role: {role}</p>
#     <b><p>You can attempt only once </p></b>

#     <p>We look forward to your participation and wish you the best of luck!</p>
#     <p>Points to be noted while interview:</p>
#     <p>1. Please ensure you are in a quiet environment with good lighting.</p>
#     <p>2. Please keep your camera ON throughout the interview.</p>
#     <p>3. Please have your Aadhar Card or any Government ID ready for the interview.</p>
#     <p>4. You can attempt only once.</p>
#     <p>5. The interview will be recorded for quality purposes.</p>
#     <br />
#     <p>Best Regards,</p>
#     <p>Human Resources,</p>
#     <p>ValueMomentum Services Pvt Ltd</p>
#     </body>
#     </html>
#     """

    email_content_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interview Invitation</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f6f9;
             font-family: Arial, Helvetica, sans-serif; color: #333333;">

    <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
           border="0" style="background-color: #f4f6f9; padding: 30px 10px;">
        <tr>
            <td align="center">

                <table role="presentation" width="600" cellspacing="0"
                       cellpadding="0" border="0"
                       style="width: 100%; max-width: 600px;
                              background-color: #ffffff;
                              border-radius: 8px; overflow: hidden;">

                    <!-- Header -->
                    <tr>
                        <td align="center"
                            style="background-color: #123b63; padding: 28px 20px;">
                            <h1 style="margin: 0; color: #ffffff;
                                       font-size: 24px; font-weight: bold;">
                                Interview Invitation
                            </h1>
                            <p style="margin: 10px 0 0; color: #e2eaf3;
                                      font-size: 14px;">
                                ValueMomentum Services Pvt Ltd
                            </p>
                        </td>
                    </tr>

                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 30px 28px;">

                            <p style="margin: 0 0 18px; font-size: 16px;
                                      line-height: 1.6;">
                                Dear <strong>{candidate_name}</strong>,
                            </p>

                            <p style="margin: 0 0 16px; font-size: 14px;
                                      line-height: 1.8;">
                                Congratulations! You have been invited to
                                participate in a technical interview for the
                                role mentioned below.
                            </p>

                            <p style="margin: 0 0 24px; font-size: 14px;
                                      line-height: 1.8;">
                                Please use the button below to access your
                                interview when you are ready to begin.
                            </p>

                            <!-- Interview Button -->
                            <table role="presentation" cellspacing="0"
                                   cellpadding="0" border="0" align="center"
                                   style="margin: 0 auto 28px;">
                                <tr>
                                    <td align="center"
                                        bgcolor="#1769aa"
                                        style="border-radius: 5px;">
                                        <a href="{interview_link}"
                                           target="_blank"
                                           style="display: inline-block;
                                                  padding: 14px 30px;
                                                  font-size: 15px;
                                                  font-weight: bold;
                                                  color: #ffffff;
                                                  text-decoration: none;
                                                  border-radius: 5px;">
                                            Start Interview
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <!-- Interview Details -->
                            <h2 style="margin: 0 0 14px; font-size: 17px;
                                       color: #123b63;">
                                Interview Details
                            </h2>

                            <table role="presentation" width="100%"
                                   cellspacing="0" cellpadding="0" border="0"
                                   style="border: 1px solid #dfe5ec;
                                          border-radius: 5px;">
                                <tr>
                                    <td style="padding: 13px 15px;
                                               background-color: #f7f9fc;
                                               border-bottom: 1px solid #dfe5ec;
                                               font-size: 14px; width: 38%;">
                                        <strong>Interview ID</strong>
                                    </td>
                                    <td style="padding: 13px 15px;
                                               border-bottom: 1px solid #dfe5ec;
                                               font-size: 14px;
                                               overflow-wrap: anywhere;">
                                        {interview_id}
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 13px 15px;
                                               background-color: #f7f9fc;
                                               font-size: 14px;">
                                        <strong>Applied Role</strong>
                                    </td>
                                    <td style="padding: 13px 15px;
                                               font-size: 14px;">
                                        {role}
                                    </td>
                                </tr>
                            </table>

                            <!-- Important Notice -->
                            <table role="presentation" width="100%"
                                   cellspacing="0" cellpadding="0" border="0"
                                   style="margin-top: 24px;
                                          background-color: #fff8e6;
                                          border-left: 4px solid #e5a000;">
                                <tr>
                                    <td style="padding: 15px 16px;">
                                        <p style="margin: 0; color: #664d03;
                                                  font-size: 14px;
                                                  line-height: 1.7;">
                                            <strong>Important:</strong>
                                            You are allowed only one attempt.
                                            Please ensure you are ready before
                                            starting the interview.
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            <!-- Instructions -->
                            <h2 style="margin: 28px 0 14px; font-size: 17px;
                                       color: #123b63;">
                                Before You Begin
                            </h2>

                            <p style="margin: 0 0 12px; font-size: 14px;
                                      line-height: 1.7;">
                                Please review the following instructions
                                carefully:
                            </p>

                            <ol style="margin: 0; padding-left: 22px;
                                       font-size: 14px; line-height: 1.9;">
                                <li style="padding-left: 4px; margin-bottom: 8px;">
                                    Choose a quiet environment with adequate
                                    lighting and a stable internet connection.
                                </li>
                                <li style="padding-left: 4px; margin-bottom: 8px;">
                                    Keep your camera turned on throughout
                                    the interview.
                                </li>
                                <li style="padding-left: 4px; margin-bottom: 8px;">
                                    Keep a valid Aadhaar card or other
                                    government-issued ID ready for identity
                                    verification, if required.
                                </li>
                                <li style="padding-left: 4px; margin-bottom: 8px;">
                                    Only one interview attempt is permitted.
                                </li>
                                <li style="padding-left: 4px; margin-bottom: 8px;">
                                    The interview session will be recorded
                                    for assessment and quality purposes.
                                </li>
                            </ol>

                            <p style="margin: 26px 0 0; font-size: 14px;
                                      line-height: 1.8;">
                                We look forward to your participation.
                                We wish you the very best for your interview!
                            </p>

                            <p style="margin: 24px 0 0; font-size: 14px;
                                      line-height: 1.7;">
                                Best regards,<br>
                                <strong>Human Resources Team</strong><br>
                                ValueMomentum Services Pvt Ltd
                            </p>

                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td align="center"
                            style="background-color: #f7f9fc;
                                   border-top: 1px solid #e5eaf0;
                                   padding: 18px 20px;">
                            <p style="margin: 0; color: #6b7280;
                                      font-size: 12px; line-height: 1.6;">
                                This email contains information about your
                                interview invitation. Please keep your
                                Interview ID confidential.
                            </p>
                        </td>
                    </tr>

                </table>

            </td>
        </tr>
    </table>

</body>
</html>
"""


    message = {
        "senderAddress": sender_email,
        "recipients": {
            "to": [{"address": candidate_email}],
            "cc": cc_recipients
        },
        "content":{
        "subject": "On Boarding Invitation",
        # "plainText": email_content,
        "html": email_content_html
    }
    }
    try:
        poller = email_client.begin_send(message)
       
        poller.result()

        interview_metadata = InterviewMetadata(
            interview_id=interview_id,
            key="email_sent",
            value="true"
        )
        insert_metadata(interview_metadata)
        return True
   
 
    except Exception as ex:
        interview_metadata = InterviewMetadata(
            interview_id=interview_id,
            key="email_sent",
            value="false"
        )

        insert_metadata(interview_metadata)
        raise RuntimeError(
            f"Failed to send email: {str(ex)}")