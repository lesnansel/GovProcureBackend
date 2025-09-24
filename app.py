# import smtplib
# from email.mime.text import MIMEText
# from flask import Flask, request, jsonify, render_template
# from flask_cors import CORS
# import os
# from dotenv import load_dotenv

# load_dotenv()

# app = Flask(__name__)
# CORS(app, resources={
#     r"/*": {
#         "origins": ["http://localhost:8080"],
#         "methods": ["POST"],
#         "allow_headers": ["Content-Type"]
#     }
# })

# SMTP_SERVER = "smtp.gmail.com"
# SMTP_PORT = 587
# SENDER_EMAIL = os.getenv("DEL_EMAIL")
# SENDER_PASSWORD = os.getenv("PASSWORD")

# @app.route("/send-pr-status-email", methods=["POST"])
# def send_pr_status_email():
#     """
#     Send Procurement Request Status Update Email
#     """
#     try:
#         data = request.get_json()
#         recipient_email = data.get("email")
#         pr_number = data.get("prNumber")
#         new_status = data.get("newStatus")

#         print(f"Attempting to send email to: {recipient_email}")  # Debug log
#         print(f"Using sender email: {SENDER_EMAIL}")  # Debug log

#         if not all([recipient_email, pr_number, new_status]):
#             return jsonify({"error": "Missing required fields"}), 400

#         # Render HTML template
#         html_content = render_template(
#             'status_update_email.html',
#             pr_number=pr_number,
#             status=new_status
#         )

#         subject = f"Procurement Request #{pr_number} Status Update"
#         msg = MIMEText(html_content, 'html')
#         msg["Subject"] = subject
#         msg["From"] = SENDER_EMAIL
#         msg["To"] = recipient_email

#         with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
#             print("Connecting to SMTP server...")  # Debug log
#             server.starttls()
#             print("Attempting login...")  # Debug log
#             server.login(SENDER_EMAIL, SENDER_PASSWORD)
#             print("Login successful, sending email...")  # Debug log
#             server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
#             print("Email sent successfully")  # Debug log

#         return jsonify({"success": True, "message": f"Email sent to {recipient_email}"}), 200

#     except Exception as e:
#         print(f"Error sending email: {str(e)}")  # Debug log
#         return jsonify({"error": str(e)}), 500

# if __name__ == "__main__":
#     app.run(debug=True, port=5000)
# import smtplib
# from email.mime.text import MIMEText
# from flask import Flask, request, jsonify, render_template
# from flask_cors import CORS
# import os
# from dotenv import load_dotenv

# load_dotenv()

# app = Flask(__name__)

# # ONLY updated CORS origins - everything else stays the same
# CORS(app, resources={
#     r"/*": {
#         "origins": [
#             "http://localhost:8080", 
#             "https://gov-procure.vercel.app"
#         ],
#         "methods": ["POST"],
#         "allow_headers": ["Content-Type"]
#     }
# })

# SMTP_SERVER = "smtp.gmail.com"
# SMTP_PORT = 587
# SENDER_EMAIL = os.getenv("DEL_EMAIL")
# SENDER_PASSWORD = os.getenv("PASSWORD")

# @app.route("/send-pr-status-email", methods=["POST"])
# def send_pr_status_email():
#     """
#     Send Procurement Request Status Update Email
#     """
#     try:
#         data = request.get_json()
#         recipient_email = data.get("email")
#         pr_number = data.get("prNumber")
#         new_status = data.get("newStatus")

#         print(f"Attempting to send email to: {recipient_email}")  # Debug log
#         print(f"Using sender email: {SENDER_EMAIL}")  # Debug log

#         if not all([recipient_email, pr_number, new_status]):
#             return jsonify({"error": "Missing required fields"}), 400

#         # Render HTML template
#         html_content = render_template(
#             'status_update_email.html',
#             pr_number=pr_number,
#             status=new_status
#         )

#         subject = f"Procurement Request #{pr_number} Status Update"
#         msg = MIMEText(html_content, 'html')
#         msg["Subject"] = subject
#         msg["From"] = SENDER_EMAIL
#         msg["To"] = recipient_email

#         with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
#             print("Connecting to SMTP server...")  # Debug log
#             server.starttls()
#             print("Attempting login...")  # Debug log
#             server.login(SENDER_EMAIL, SENDER_PASSWORD)
#             print("Login successful, sending email...")  # Debug log
#             server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
#             print("Email sent successfully")  # Debug log

#         return jsonify({"success": True, "message": f"Email sent to {recipient_email}"}), 200

#     except Exception as e:
#         print(f"Error sending email: {str(e)}")  # Debug log
#         return jsonify({"error": str(e)}), 500

# if __name__ == "__main__":
#     # ONLY updated for deployment - keeps your exact functionality
#     port = int(os.environ.get("PORT", 5000))
#     app.run(debug=True, host="0.0.0.0", port=port)

import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ONLY updated CORS origins - everything else stays the same
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:8080", 
            "https://gov-procure.vercel.app"
        ],
        "methods": ["POST"],
        "allow_headers": ["Content-Type"]
    }
})

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("DEL_EMAIL")
SENDER_PASSWORD = os.getenv("PASSWORD")

@app.route("/send-pr-status-email", methods=["POST"])
def send_pr_status_email():
    """
    Send Procurement Request Status Update Email
    """
    try:
        data = request.get_json()
        recipient_email = data.get("email")
        pr_number = data.get("prNumber")
        new_status = data.get("newStatus")

        print(f"Attempting to send email to: {recipient_email}")  # Debug log
        print(f"Using sender email: {SENDER_EMAIL}")  # Debug log

        if not all([recipient_email, pr_number, new_status]):
            return jsonify({"error": "Missing required fields"}), 400

        # Render HTML template
        html_content = render_template(
            'status_update_email.html',
            pr_number=pr_number,
            status=new_status
        )

        subject = f"Procurement Request #{pr_number} Status Update"
        msg = MIMEText(html_content, 'html')
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            print("Connecting to SMTP server...")  # Debug log
            server.starttls()
            print("Attempting login...")  # Debug log
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print("Login successful, sending email...")  # Debug log
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
            print("Email sent successfully")  # Debug log

        return jsonify({"success": True, "message": f"Email sent to {recipient_email}"}), 200

    except Exception as e:
        print(f"Error sending email: {str(e)}")  # Debug log
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # ONLY updated for deployment - keeps your exact functionality
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)