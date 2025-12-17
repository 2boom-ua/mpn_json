from flask import Flask, request, jsonify, render_template, send_from_directory, render_template, Response, make_response
import json
import requests
import re
import traceback


check_emoji = "\u2705"

app = Flask(__name__)
app.logger.disabled = True

# ------------------------
# CORS
# ------------------------
@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

# ------------------------
# Routes
# ------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

@app.route("/test-notification", methods=["POST", "OPTIONS"])
def test_notification():
    if request.method == "OPTIONS":
        return "", 204

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data received"}), 400

        service_name = data.get("service")
        config_json = data.get("config")

        if not service_name or not config_json:
            return jsonify({
                "success": False,
                "message": "Missing service name or configuration"
            }), 400

        print(f"\n=== Test request for {service_name} from {request.remote_addr} ===")

        # Parse JSON safely
        try:
            config_json = clean_json_string(config_json)
            config = json.loads(config_json)
        except json.JSONDecodeError as e:
            return jsonify({
                "success": False,
                "message": f"Invalid JSON: {str(e)}"
            }), 400

        # Find service key
        service_key = service_name.upper()
        found_key = next(
            (k for k in config if k.upper() == service_key or service_name.lower() in k.lower()),
            None
        )

        if not found_key:
            return jsonify({
                "success": False,
                "message": f"Service '{service_name}' not found. Available: {list(config.keys())}"
            }), 400

        service_config = config[found_key]

        if not service_config.get("ENABLED", True):
            return jsonify({
                "success": False,
                "message": f"Service {found_key} is disabled"
            })

        webhook_urls = service_config.get("WEBHOOK_URL", [])
        if not webhook_urls:
            return jsonify({
                "success": False,
                "message": "No webhook URL found"
            }), 400

        webhook_url = clean_url(webhook_urls[0])

        payload = (service_config.get("PAYLOAD") or [{}])[0].copy()
        headers = (service_config.get("HEADER") or [{}])[0]

        test_message = f"{check_emoji} Test notification from MPN JSON Creator"
        test_payload = prepare_test_payload(found_key, payload, test_message)

        ssl_verify = service_config.get("SSL_VERIFY", True)

        response = requests.post(
            webhook_url,
            json=test_payload,
            headers=headers,
            timeout=15,
            verify=ssl_verify
        )

        if response.status_code in (200, 201, 202, 204):
            return jsonify({
                "success": True,
                "message": f"Test notification sent to {found_key}",
                "status_code": response.status_code
            })

        return jsonify({
            "success": False,
            "message": f"Failed with status {response.status_code}",
            "response": response.text[:300],
            "status_code": response.status_code
        })

    except requests.exceptions.Timeout:
        return jsonify({"success": False, "message": "Request timeout (15s)"})
    except requests.exceptions.SSLError:
        return jsonify({"success": False, "message": "SSL certificate error"})
    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "message": "Connection error"})
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)[:100]}"
        }), 500

# ------------------------
# Helpers
# ------------------------
def clean_json_string(json_str):
    """Minimal JSON cleanup (safe)"""
    if not json_str:
        return "{}"
    json_str = json_str.strip()
    json_str = re.sub(r"<[^>]+>", "", json_str)  # remove HTML only
    return json_str

def clean_url(url):
    if not url:
        return ""
    return url.strip().strip('"').strip("'").replace("\\", "")

def prepare_test_payload(service_key, payload, message):
    payload = payload.copy()
    key = service_key.upper()

    handlers = {
        "TELEGRAM": lambda p: {**p, "text": message, "parse_mode": "Markdown"},
        "DISCORD": lambda p: {**p, "content": message},
        "SLACK": lambda p: {**p, "text": message},
        "MATTERMOST": lambda p: {**p, "text": message},
        "ROCKET.CHAT": lambda p: {**p, "text": message},
        "PUMBLE": lambda p: {**p, "text": message},
        "FLOCK": lambda p: {**p, "text": message},
        "ZULIP": lambda p: {
            **p,
            "content": message,
            "type": p.get("type", "stream")
        },
        "MATRIX": lambda p: {
            **p,
            "msgtype": "m.text",
            "body": message,
            "formatted_body": message
        },
        "GOTIFY": lambda p: {**p, "message": message, "title": "Test Notification"},
        "PUSHOVER": lambda p: {**p, "message": message, "title": "Test Notification"},
        "PUSHBULLET": lambda p: {**p, "body": message, "title": "Test Notification"},
        "NTFY": lambda p: {**p, "message": message, "title": "Test"},
        "WEBNTFY": lambda p: {**p, "message": message},
        "APPRISE": lambda p: {**p, "body": message, "type": "info"},
    }

    if key in handlers:
        return handlers[key](payload)

    for field in ("message", "text", "content", "body"):
        if field in payload:
            payload[field] = message
            return payload

    payload["message"] = message
    return payload

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

# ------------------------
# Errors
# ------------------------
@app.errorhandler(404)
def not_found(_):
    return jsonify({"success": False, "message": f"Route not found: {request.path}"}), 404

@app.errorhandler(500)
def internal_error(_):
    return jsonify({"success": False, "message": "Internal server error"}), 500

# ------------------------
# Run
# ------------------------
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5299, debug=False, use_reloader=False)