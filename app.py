import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:8080", 
            "https://gov-procure.vercel.app"
        ],
        "methods": ["POST", "GET"],  # Added GET
        "allow_headers": ["Content-Type"]
    }
})

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("DEL_EMAIL")
SENDER_PASSWORD = os.getenv("PASSWORD")

# ADD THIS ROUTE for health checks
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "Email service is running!", "service": "GovProcure Email API"}), 200

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

        print(f"Attempting to send email to: {recipient_email}")
        print(f"Using sender email: {SENDER_EMAIL}")

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

        # Updated SMTP with timeout handling
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
                print("Connecting to SMTP server...")
                server.starttls()
                print("Attempting login...")
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                print("Login successful, sending email...")
                server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
                print("Email sent successfully")
        except smtplib.SMTPException as smtp_error:
            print(f"SMTP Error: {str(smtp_error)}")
            return jsonify({"error": f"SMTP Error: {str(smtp_error)}"}), 500
        except Exception as conn_error:
            print(f"Connection Error: {str(conn_error)}")
            return jsonify({"error": f"Connection Error: {str(conn_error)}"}), 500

        return jsonify({"success": True, "message": f"Email sent to {recipient_email}"}), 200

    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)