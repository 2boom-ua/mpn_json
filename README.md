# Multi-Platform Notification JSON Creator

![Python](https://img.shields.io/badge/python-3.8+-blue)
![Flask](https://img.shields.io/badge/flask-2.3+-lightgrey)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License](https://img.shields.io/badge/license-MIT-orange)


<div align="center">  
    <img src="https://github.com/2boom-ua/mpn_json/blob/main/screenshot.png?raw=true" alt="" width="800" height="285">
</div>


A user-friendly web application for generating and testing notification configurations in JSON format. Designed specifically to simplify setup for monitoring tools created by [@2boom-ua](https://github.com/2boom-ua), such as **Dockcheck**, **WatchDigest**, **Check Services**, **Web Check** and ect..

This tool provides an interactive interface to configure notifications for over a dozen popular platforms, with real-time JSON preview and one-click testing.

---

## Features

* **Interactive Form Builder**: Fill in platform-specific fields with guidance and validation.
* **Real-Time JSON Preview**: See the generated `notifications` section instantly as you type.
* **Test Notifications**: Send a test message directly from the app to verify your configuration works.
* **Export Options**: Copy to clipboard or download the JSON snippet/file.
* **Reset & Clear**: Easily reset forms or clear individual fields.
* **Toast Notifications**: Friendly feedback for actions like success or errors.
* **Responsive Design**: Clean, mobile-friendly interface.
* **Generic Panel**: For custom or unsupported platforms.

### Supported Notification Platforms (15+)

| Category | Platforms |
| :--- | :--- |
| **Messaging Apps** | Telegram, Discord, Slack, Matrix |
| **Team Collaboration** | Mattermost, Rocket.Chat, Zulip, Pumble |
| **Self-Hosted** | Ntfy, Gotify, Apprise |
| **Push Services** | Pushover, Pushbullet, Webntfy |
| **Others** | Custom webhook/API |

---
### Compatible Tools

| Tool | Description | Link |
| :--- | :--- | :--- |
| **Dockcheck** | Monitors Docker resources and notifies on changes | [GitHub](https://github.com/2boom-ua/dockcheck) |
| **WatchDigest** | Checks for outdated Docker image digests | [GitHub](https://github.com/2boom-ua/watchdigest) |
| **Check Services**| Monitors systemd service status | [GitHub](https://github.com/2boom-ua/check_services) |
| **Web Check** | Website availability monitoring | [GitHub](https://github.com/2boom-ua/web_check) |

---

## Installation & Running

The application is distributed as a Docker image for easy deployment.

### Access the App

Open your browser and go to: http://localhost:5299 (or your server's IP).

### 1. Using Docker CLI
```bash
docker run --name mpn_json \
  -p 5299:5299 \
  -e TZ=Etc/UTC \
  --restart unless-stopped \
  ghcr.io/2boom-ua/mpn_json:latest
```
### Using Docker Compose
```bash
services:
  mpn_json_creator:
    image: ghcr.io/2boom-ua/mpn_json:latest
    container_name: mpn_json
    ports:
      - "5299:5299"
    environment:
      - TZ=Etc/UTC
    restart: unless-stopped
```

### Start

```
docker compose up -d
```

## Running as a Linux Service

You can set this app to run as a Linux service for continuous monitoring.

### Clone the repository:

```
git clone https://github.com/2boom-ua/mnp_json.git
cd mnp_json
```


### Install required Python packages:

```
pip install -r requirements.txt
```
### Create a systemd service file:

```
nano /etc/systemd/system/mpn_json.service
```
### Add the following content:

```
[Unit]
Description=Multi-Platform Notification JSON Creator
After=multi-user.target

[Service]
Type=simple
Restart=always
ExecStart=/usr/bin/python3 /opt/mpn_json/mpn_json_creator.py

[Install]
WantedBy=multi-user.target
```

### Start

```
systemctl daemon-reload
```
```
systemctl enable mpn_json.service
```
```
systemctl restart mpn_json.service
```

### Contributing

Contributions are welcome! Feel free to:

### Report bugs

Suggest new platforms
Submit pull requests

Please open an issue first for major changes.

### License

This project is licensed under the MIT License - see the LICENSE file for details.
