from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    send_from_directory,
    make_response,
)
import json
import requests
import re
import logging
import random
import time

check_emoji = "\u2705"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.logger.disabled = True

check_emoji = "\u2705"
platform_webhook_url = []
platform_header = []
platform_payload = []
platform_format_message = []

def cors_response(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    resp.headers["Access-Control-Max-Age"] = "86400"
    return resp

def clean_json_string(json_str):
    """Safely clean JSON string from frontend by removing <span> and </span> tags"""
    if not json_str:
        return "{}"
    json_str = json_str.strip()
    json_str = re.sub(r"</?span[^>]*>", "", json_str)  # Remove both <span> and </span>
    return json_str

def clean_url(url):
    """Clean and validate webhook URL"""
    if not url:
        return ""
    url = url.strip().strip('"').strip("'").replace("\\", "")
    if not url.startswith(("http://", "https://")):
        return ""
    return url

def send_message(message: str):
    """Send HTTP POST requests with retry logic."""
    def send_request(url, json_data=None, data=None, headers=None):
        """
        Send a POST request with retry logic and exponential backoff.
        
        Args:
            url: Target URL
            json_data: JSON data to send (optional)
            data: Form data to send (optional)
            headers: Request headers (optional)
        
        Returns:
            tuple: (success, response_data) where success is boolean and
                response_data is either the response or error info
        """
        max_attempts = 5
        
        for attempt in range(max_attempts):
            try:
                response = requests.post(
                    url, 
                    json=json_data, 
                    data=data, 
                    headers=headers, 
                    timeout=(5, 20)
                )
                response.raise_for_status()

                return True
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"error_send_request_failed {attempt + 1}/{max_attempts} - {url}: {e}")
                
                if attempt == max_attempts - 1:
                    logger.error(f"error_send_request_max_attempts {url}")
                    return False
                else:
                    backoff_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"log_retrying {backoff_time:.2f} seconds...")
                    time.sleep(backoff_time)
        
        return False


    def to_html_format(message: str) -> str:
        message = ''.join(f"<b>{part}</b>" if i % 2 else part for i, part in enumerate(message.split('*')))
        return message.replace("\n", "<br>")

    def to_markdown_format(message: str, markdown_type: str) -> str:
        formatters = {
            "html": lambda msg: to_html_format(msg),
            "markdown": lambda msg: msg.replace("*", "**"),
            "text": lambda msg: msg.replace("*", ""),
            "simplified": lambda msg: msg,
        }
        formatter = formatters.get(markdown_type)
        if formatter:
            return formatter(message)
        logger.error("error_unknown_format" + f" '{markdown_type}'")
        return message

    for url, header, payload, format_message in zip(platform_webhook_url, platform_header, platform_payload, platform_format_message):
        data, ntfy = None, False
        formatted_message = to_markdown_format(message, format_message)
        header_json = header if header else None

        if isinstance(payload, dict):
            for key in list(payload.keys()):
                if key == "title":
                    delimiter = "<br>" if format_message == "html" else "\n"
                    if delimiter in formatted_message:                          # ← FIX added
                        header, formatted_message = formatted_message.split(delimiter, 1)
                        payload[key] = header.replace("*", "")
                elif key == "extras":
                    formatted_message = formatted_message.replace("\n", "\n\n")
                    payload["message"] = formatted_message
                elif key == "data":
                    ntfy = True
                payload[key] = formatted_message if key in ["text", "content", "message", "body", "formatted_body", "data"] else payload[key]

        payload_json = None if ntfy else payload
        data = formatted_message.encode("utf-8") if ntfy else None
        send_request(url, payload_json, data, header_json)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/test-notification", methods=["POST", "OPTIONS"])
def test_notification():
    global platform_webhook_url, platform_header, platform_payload, platform_format_message
    
    if request.method == "OPTIONS":
        return cors_response(make_response("", 204))

    try:
        data = request.get_json()
        if not data:
            return cors_response(jsonify({"success": False, "message": "Missing request body"}), 400)
        
        config = data.get('config')
        if not config:
            return cors_response(jsonify({"success": False, "message": "Missing configuration"}), 400)
        
        # Parse JSON config
        try:
            config_json = json.loads(config)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return cors_response(jsonify({"success": False, "message": "Invalid JSON format"}), 400)
        
        # Initialize platform-specific lists
        platform_webhook_url = []
        platform_header = []
        platform_payload = []
        platform_format_message = []
        
        # Track enabled platforms for response
        enabled_platforms = []
        
        # Process each platform configuration
        for platform, settings in config_json.items():
            if not isinstance(settings, dict):
                logger.warning(f"Invalid settings format for platform {platform}")
                continue
                
            if settings.get("ENABLED", False):
                enabled_platforms.append(platform)
                
                # Store configuration in appropriate lists
                for key, value in settings.items():
                    # Skip the ENABLED flag for data storage
                    if key == "ENABLED":
                        continue
                        
                    # Store based on key type
                    if key.lower() == "webhook_url":
                        if isinstance(value, list):
                            platform_webhook_url.extend(value)
                        else:
                            platform_webhook_url.append(value)
                    elif key.lower() == "header":
                        if isinstance(value, list):
                            platform_header.extend(value)
                        else:
                            platform_header.append(value)
                    elif key.lower() == "payload":
                        if isinstance(value, list):
                            platform_payload.extend(value)
                        else:
                            platform_payload.append(value)
                    elif key.lower() == "format_message":
                        if isinstance(value, list):
                            platform_format_message.extend(value)
                        else:
                            platform_format_message.append(value)
                    
                    logger.info(f"{platform} - {key}: {value}")
        
        # Check if we have valid configurations
        if not enabled_platforms:
            return cors_response(jsonify({
                "success": False, 
                "message": "No enabled platforms found in configuration"
            }), 400)
        
        # Verify all required lists have data
        required_data = all([
            platform_webhook_url,
            platform_header,
            platform_payload,
            platform_format_message
        ])
        
        if not required_data:
            missing = []
            if not platform_webhook_url: missing.append("webhook_url")
            if not platform_header: missing.append("header")
            if not platform_payload: missing.append("payload")
            if not platform_format_message: missing.append("format_message")
            
            logger.error(f"Missing configuration: {', '.join(missing)}")
            return cors_response(jsonify({
                "success": False,
                "message": f"Missing required configuration: {', '.join(missing)}"
            }), 400)
        
        # Send test notification
        logger.info("Configuration OK! Sending test notification...")
        test_message = f"{check_emoji} Test notification from *MPN JSON Creator*"
        
        # Store configuration temporarily (consider using app.config or session instead of globals)
        app.config['TEST_NOTIFICATION_CONFIG'] = {
            'webhook_url': platform_webhook_url,
            'header': platform_header,
            'payload': platform_payload,
            'format_message': platform_format_message
        }
        
        # Call your send_message function
        #send_result = send_message(test_message)
        success = send_message(test_message)
        
        if not success:
            return jsonify({"status": "error"}), 500
        
        platform_list = ", ".join(enabled_platforms)
        return cors_response(jsonify({
            "success": True,
            "message": f"Test notification sent to {platform_list}",
            "platforms": enabled_platforms,
            "status_code": 200
        }))
        
    except Exception as e:
        logger.error(f"Unexpected error in test_notification: {str(e)}", exc_info=True)
        return cors_response(jsonify({
            "success": False,
            "message": "Internal server error",
            "error": str(e) if app.debug else None
        }), 500)

@app.route("/health")
def health():
    return cors_response(jsonify({"status": "ok"}))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5299, debug=False, use_reloader=False)