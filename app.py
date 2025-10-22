import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
import time
import socket

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

# Multiple SMTP configurations for different environments
SMTP_CONFIGS = [
    {
        "name": "Gmail TLS",
        "server": "smtp.gmail.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False
    },
    {
        "name": "Gmail SSL", 
        "server": "smtp.gmail.com",
        "port": 465,
        "use_tls": False,
        "use_ssl": True
    },
    {
        "name": "Gmail Alternative Port",
        "server": "smtp.gmail.com", 
        "port": 25,
        "use_tls": True,
        "use_ssl": False
    }
]

SENDER_EMAIL = os.getenv("DEL_EMAIL")
SENDER_PASSWORD = os.getenv("PASSWORD")

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "Email service is running!", 
        "service": "GovProcure Email API",
        "sender_configured": bool(SENDER_EMAIL and SENDER_PASSWORD),
        "sender_email": SENDER_EMAIL if SENDER_EMAIL else "Not configured"
    }), 200

def check_network_connectivity(server="smtp.gmail.com", port=587, timeout=10):
    """Check if we can reach the SMTP server"""
    try:
        # Try to create a socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((server, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Network connectivity OK - can reach {server}:{port}")
            return True
        else:
            print(f"❌ Network connectivity FAILED - cannot reach {server}:{port} (error code: {result})")
            return False
    except Exception as e:
        print(f"❌ Network connectivity check failed for {server}:{port}: {e}")
        return False

def test_all_smtp_configs():
    """Test all SMTP configurations to see which ones work"""
    working_configs = []
    
    for config in SMTP_CONFIGS:
        print(f"\n🔍 Testing {config['name']} ({config['server']}:{config['port']})")
        
        if check_network_connectivity(config['server'], config['port'], timeout=5):
            working_configs.append(config)
            print(f"✅ {config['name']} - Network reachable")
        else:
            print(f"❌ {config['name']} - Network unreachable")
    
    return working_configs

def send_email_with_multiple_configs(recipient_email, subject, html_content, max_retries=2):
    """Try multiple SMTP configurations"""
    
    # Test which configs work first
    working_configs = test_all_smtp_configs()
    
    if not working_configs:
        raise Exception("No SMTP servers are reachable from this environment")
    
    print(f"📊 Found {len(working_configs)} working SMTP configurations")
    
    for config in working_configs:
        for attempt in range(max_retries):
            try:
                print(f"\n📧 Attempt {attempt + 1}/{max_retries} with {config['name']}")
                print(f"   Server: {config['server']}:{config['port']}")
                print(f"   To: {recipient_email}")
                print(f"   Subject: {subject}")
                
                # Create message
                msg = MIMEText(html_content, 'html', 'utf-8')
                msg["Subject"] = subject
                msg["From"] = SENDER_EMAIL
                msg["To"] = recipient_email

                # Configure SMTP based on config
                if config['use_ssl']:
                    # Use SSL (port 465)
                    import ssl
                    context = ssl.create_default_context()
                    server = smtplib.SMTP_SSL(config['server'], config['port'], context=context, timeout=30)
                    print("🔒 Connected via SSL")
                else:
                    # Use regular SMTP (port 587 or 25)
                    server = smtplib.SMTP(config['server'], config['port'], timeout=30)
                    print("🔗 Connected via SMTP")
                    
                    if config['use_tls']:
                        print("🔒 Starting TLS...")
                        server.starttls()
                
                print("🔑 Authenticating...")
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                
                print("📤 Sending email...")
                server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
                server.quit()
                
                print(f"✅ Email sent successfully via {config['name']}!")
                return True
                
            except smtplib.SMTPAuthenticationError as auth_error:
                print(f"❌ Authentication failed with {config['name']}: {auth_error}")
                try:
                    server.quit()
                except:
                    pass
                break  # Don't retry auth errors for this config
                
            except smtplib.SMTPRecipientsRefused as recip_error:
                print(f"❌ Recipient refused by {config['name']}: {recip_error}")
                try:
                    server.quit()
                except:
                    pass
                break  # Don't retry recipient errors for this config
                
            except (smtplib.SMTPException, socket.error, OSError) as e:
                print(f"❌ SMTP/Network error with {config['name']} attempt {attempt + 1}: {e}")
                try:
                    server.quit()
                except:
                    pass
                    
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"⏳ Retrying {config['name']} in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Failed all attempts with {config['name']}")
                    
            except Exception as e:
                print(f"❌ Unexpected error with {config['name']}: {e}")
                try:
                    server.quit()
                except:
                    pass
                break  # Don't retry unexpected errors for this config
    
    # If we get here, all configs failed
    raise Exception(f"Failed to send email with all {len(working_configs)} available SMTP configurations")

@app.route("/send-pr-status-email", methods=["POST"])
def send_pr_status_email():
    """Send Procurement Request Status Update Email"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        recipient_email = data.get("email")
        pr_number = data.get("prNumber") or data.get("prId")
        new_status = data.get("newStatus")

        print(f"\n📧 EMAIL REQUEST RECEIVED:")
        print(f"   Recipient: {recipient_email}")
        print(f"   PR Number: {pr_number}")
        print(f"   New Status: {new_status}")
        print(f"   Sender configured: {SENDER_EMAIL}")
        print(f"   Request received at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Environment: {'Render' if os.getenv('RENDER') else 'Local'}")

        # Validate required fields
        if not all([recipient_email, pr_number, new_status]):
            missing_fields = []
            if not recipient_email: missing_fields.append("email")
            if not pr_number: missing_fields.append("prNumber/prId")
            if not new_status: missing_fields.append("newStatus")
            
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            print(f"❌ Validation error: {error_msg}")
            return jsonify({"error": error_msg}), 400

        # Validate email format
        if "@" not in recipient_email or "." not in recipient_email:
            error_msg = f"Invalid email format: {recipient_email}"
            print(f"❌ Email format error: {error_msg}")
            return jsonify({"error": error_msg}), 400

        # Validate sender credentials
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            error_msg = "Email service not properly configured - missing credentials"
            print(f"❌ Configuration error: {error_msg}")
            return jsonify({"error": error_msg}), 500

        # Create email content (fallback HTML)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Purchase Request Status Update</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background-color: #0f2942; color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .status-box {{ background-color: #e8f5e8; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>GovProcure System</h1>
                    <h2>Purchase Request Status Update</h2>
                </div>
                <div class="content">
                    <p>Dear User,</p>
                    <p>Your purchase request has been updated:</p>
                    <div class="status-box">
                        <p><strong>Request ID:</strong> #{pr_number}</p>
                        <p><strong>New Status:</strong> {new_status}</p>
                        <p><strong>Updated At:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    <p>Please log in to your GovProcure account to view full details.</p>
                    <p>Thank you for using GovProcure!</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from GovProcure System.</p>
                    <p>If you have any questions, please contact your procurement administrator.</p>
                </div>
            </div>
        </body>
        </html>
        """

        subject = f"GovProcure - Purchase Request #{pr_number} Status: {new_status}"
        
        # Send email with multiple config retry logic
        print(f"🚀 Starting email send process...")
        start_time = time.time()
        
        try:
            send_email_with_multiple_configs(recipient_email, subject, html_content)
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            success_msg = f"Email sent successfully to {recipient_email} (took {duration}s)"
            print(f"✅ {success_msg}")
            return jsonify({
                "success": True, 
                "message": success_msg,
                "duration_seconds": duration,
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }), 200
            
        except Exception as email_error:
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            error_msg = str(email_error)
            print(f"❌ Email sending failed after {duration}s: {error_msg}")
            
            # Return appropriate error response
            if "No SMTP servers are reachable" in error_msg:
                return jsonify({
                    "error": "Email service unavailable - no SMTP servers reachable from this environment.",
                    "technical_details": error_msg,
                    "type": "network_error",
                    "duration_seconds": duration,
                    "suggestion": "This may be due to hosting platform network restrictions."
                }), 503
            else:
                return jsonify({
                    "error": "Failed to send email notification. Status was updated successfully.",
                    "technical_details": error_msg,
                    "type": "general_error",
                    "duration_seconds": duration
                }), 500

    except Exception as e:
        error_msg = f"Unexpected error in email service: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({
            "error": "Internal server error in email service",
            "technical_details": str(e),
            "type": "server_error"
        }), 500

@app.route("/test-email", methods=["POST"])
def test_email():
    """Test endpoint for email functionality"""
    try:
        data = request.get_json() or {}
        test_email_addr = data.get("email", SENDER_EMAIL)
        
        print(f"\n🧪 TESTING EMAIL FUNCTIONALITY")
        print(f"   Test email address: {test_email_addr}")
        print(f"   Sender email: {SENDER_EMAIL}")
        print(f"   Sender password configured: {'Yes' if SENDER_PASSWORD else 'No'}")
        
        # Check network connectivity
        if not check_network_connectivity():
            return jsonify({
                "success": False,
                "error": "Cannot reach Gmail SMTP server",
                "details": "Network connectivity test failed"
            }), 503
            
        # Test basic email sending
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1 style="color: #0f2942;">GovProcure Email Test</h1>
            <p>This is a test email from the GovProcure email service.</p>
            <p><strong>Timestamp:</strong> """ + str(time.time()) + """</p>
            <p>If you received this email, the service is working correctly!</p>
        </body>
        </html>
        """
        
        send_email_with_retry(test_email_addr, "GovProcure Email Service Test", html_content)
        
        return jsonify({
            "success": True, 
            "message": f"Test email sent successfully to {test_email_addr}",
            "timestamp": time.time()
        }), 200
        
    except Exception as e:
        print(f"❌ Email test failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Email test failed: {str(e)}",
            "details": "Check server logs for more details"
        }), 500

@app.route("/debug", methods=["GET"])
def debug_info():
    """Debug endpoint to check service configuration"""
    return jsonify({
        "service": "GovProcure Email API",
        "status": "running",
        "smtp_server": SMTP_SERVER,
        "smtp_port": SMTP_PORT,
        "sender_email": SENDER_EMAIL,
        "sender_configured": bool(SENDER_EMAIL and SENDER_PASSWORD),
        "password_configured": bool(SENDER_PASSWORD),
        "network_test": check_network_connectivity()
    }), 200

@app.route("/network-test", methods=["GET"])
def network_test():
    """Test network connectivity to various SMTP servers"""
    results = []
    
    for config in SMTP_CONFIGS:
        test_result = {
            "name": config['name'],
            "server": config['server'],
            "port": config['port'],
            "reachable": False,
            "error": None
        }
        
        try:
            if check_network_connectivity(config['server'], config['port'], timeout=10):
                test_result["reachable"] = True
            else:
                test_result["error"] = "Connection failed"
        except Exception as e:
            test_result["error"] = str(e)
        
        results.append(test_result)
    
    return jsonify({
        "service": "GovProcure Email API - Network Test",
        "environment": "Render" if os.getenv('RENDER') else "Local",
        "smtp_tests": results,
        "working_configs": len([r for r in results if r["reachable"]]),
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🚀 STARTING GOVPROCURE EMAIL SERVICE")
    print(f"   Port: {port}")
    print(f"   Sender email: {SENDER_EMAIL}")
    print(f"   Password configured: {'Yes' if SENDER_PASSWORD else 'No'}")
    print(f"   Environment: {'Render' if os.getenv('RENDER') else 'Local'}")
    
    # Test all SMTP configurations on startup
    print(f"\n🔍 Testing all SMTP configurations...")
    working_configs = test_all_smtp_configs()
    print(f"\n📊 Summary: {len(working_configs)}/{len(SMTP_CONFIGS)} SMTP configurations working")
    
    if not working_configs:
        print("⚠️  WARNING: No SMTP servers are reachable! Email functionality will not work.")
    else:
        for config in working_configs:
            print(f"   ✅ {config['name']} ({config['server']}:{config['port']}) - Working")
    
    print(f"\n🌐 Flask application starting...")
    app.run(debug=True, host="0.0.0.0", port=port)