import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
        "methods": ["POST", "GET"],
        "allow_headers": ["Content-Type"]
    }
})

SENDER_EMAIL = os.getenv("DEL_EMAIL")
SENDER_PASSWORD = os.getenv("PASSWORD")

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "Email service is running!", 
        "service": "GovProcure Email API",
        "smtp_server": "Gmail SMTP",
        "sender_email": SENDER_EMAIL if SENDER_EMAIL else "Not configured"
    }), 200

@app.route("/test-smtp", methods=["GET"])
def test_smtp_connection():
    """Test SMTP connection without sending email"""
    try:
        # Test different SMTP configurations
        configs = [
            {"server": "smtp.gmail.com", "port": 587, "tls": True, "name": "Gmail TLS"},
            {"server": "smtp.gmail.com", "port": 465, "ssl": True, "name": "Gmail SSL"},
            {"server": "smtp.gmail.com", "port": 25, "tls": True, "name": "Gmail Port 25"},
        ]
        
        results = []
        for config in configs:
            try:
                if config.get("ssl"):
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(config["server"], config["port"], context=context, timeout=10) as server:
                        server.login(SENDER_EMAIL, SENDER_PASSWORD)
                        results.append({"config": config["name"], "status": "SUCCESS"})
                else:
                    with smtplib.SMTP(config["server"], config["port"], timeout=10) as server:
                        if config.get("tls"):
                            server.starttls()
                        server.login(SENDER_EMAIL, SENDER_PASSWORD)
                        results.append({"config": config["name"], "status": "SUCCESS"})
                        
            except Exception as e:
                results.append({"config": config["name"], "status": f"FAILED: {str(e)}"})
        
        return jsonify({"test_results": results}), 200
        
    except Exception as e:
        return jsonify({"error": f"Test failed: {str(e)}"}), 500

@app.route("/send-pr-status-email", methods=["POST"])
def send_pr_status_email():
    """
    Send Procurement Request Status Update Email with multiple SMTP fallback
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

        if not SENDER_EMAIL or not SENDER_PASSWORD:
            return jsonify({"error": "Email credentials not configured"}), 500

        # Render HTML template
        html_content = render_template(
            'status_update_email.html',
            pr_number=pr_number,
            status=new_status
        )

        subject = f"Procurement Request #{pr_number} Status Update"
        
        # Create multipart message
        msg = MIMEMultipart('alternative')
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        
        # Create HTML part
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Try multiple SMTP configurations in order of preference
        smtp_configs = [
            {
                "name": "Gmail SSL (Port 465)",
                "method": "ssl",
                "server": "smtp.gmail.com",
                "port": 465
            },
            {
                "name": "Gmail TLS (Port 587)", 
                "method": "tls",
                "server": "smtp.gmail.com",
                "port": 587
            },
            {
                "name": "Gmail Port 25",
                "method": "tls",
                "server": "smtp.gmail.com", 
                "port": 25
            }
        ]

        last_error = None
        
        for config in smtp_configs:
            try:
                print(f"Trying {config['name']}...")
                
                if config["method"] == "ssl":
                    # SSL connection
                    context = ssl.create_default_context()
                    # Relax SSL verification for cloud platforms
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    
                    with smtplib.SMTP_SSL(config["server"], config["port"], context=context, timeout=30) as server:
                        print(f"Connected to {config['name']}")
                        server.login(SENDER_EMAIL, SENDER_PASSWORD)
                        print("Login successful")
                        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
                        print(f"Email sent successfully via {config['name']}")
                        return jsonify({
                            "success": True, 
                            "message": f"Email sent to {recipient_email} via {config['name']}"
                        }), 200
                        
                else:
                    # TLS connection
                    with smtplib.SMTP(config["server"], config["port"], timeout=30) as server:
                        print(f"Connected to {config['name']}")
                        server.set_debuglevel(1)  # Enable debug output
                        
                        if config["method"] == "tls":
                            server.starttls()
                            print("TLS started")
                            
                        server.login(SENDER_EMAIL, SENDER_PASSWORD)
                        print("Login successful")
                        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
                        print(f"Email sent successfully via {config['name']}")
                        return jsonify({
                            "success": True, 
                            "message": f"Email sent to {recipient_email} via {config['name']}"
                        }), 200

            except smtplib.SMTPAuthenticationError as auth_error:
                error_msg = f"{config['name']} - Authentication failed: {str(auth_error)}"
                print(error_msg)
                last_error = error_msg
                continue
                
            except smtplib.SMTPConnectError as conn_error:
                error_msg = f"{config['name']} - Connection failed: {str(conn_error)}"
                print(error_msg)
                last_error = error_msg
                continue
                
            except smtplib.SMTPException as smtp_error:
                error_msg = f"{config['name']} - SMTP error: {str(smtp_error)}"
                print(error_msg)
                last_error = error_msg
                continue
                
            except Exception as e:
                error_msg = f"{config['name']} - General error: {str(e)}"
                print(error_msg)
                last_error = error_msg
                continue

        # If all methods failed
        return jsonify({
            "error": f"All SMTP methods failed. Last error: {last_error}"
        }), 500

    except Exception as e:
        print(f"Error in email function: {str(e)}")
        return jsonify({"error": f"Email service error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)