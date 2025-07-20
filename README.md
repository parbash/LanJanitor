# LanJanitor v0.3
When you can't seem to keep your homelab servers up to date, let LanJanitor help!

## Overview
LanJanitor automates server update management, reboot detection, and status monitoring for your homelab. Designed for simplicity, modern UI, and easy deployment in Docker.

## Tech Stack
- **Docker** – Containerized deployment
- **Bootstrap 5.3** – Responsive layout and UI
- **Vue.js 3** – Reactive frontend and API calls
- **Flask 2.x.x** – Backend logic and API
- **Sqlite DB** – Persistent storage
- **Ansible** – Server automation (updates, reboots)

## Code Organization & Best Practices
- **Modular Blueprints:** API routes are split into `auth_api.py`, `servers_api.py`, and `updates_api.py` for maintainability and scalability.
- **Configuration:** Docker Compose uses relative paths and environment variables for secrets. See `docker-compose.yml` for details.
- **Requirements:** All Python dependencies are listed in `requirements.txt` with comments for clarity.
- **Ansible Playbooks:** Located in `app/ansible/`, organized by function and tags.
- **Static & Templates:** Frontend assets in `static/`, HTML templates in `templates/`.
- **Logging & Docs:** API endpoints include logging and docstrings for traceability and self-documentation.

## Current Features
- Add, edit, and delete servers (CRUD)
- Set server OS type (Windows, Ubuntu, Other Linux) with icons
- Check for updates and install updates on servers
- Detect and display reboot-required status
- Ping servers and show online/offline status
- Login system (default: admin/admin) with session-based authentication
- Change password from settings page
- Modular frontend JS (api.js, utils.js, main.js, Vue components)
- Modern UI with Bootstrap 5.3 and Bootstrap Icons
- Dark mode toggle (persistent via localStorage)
- Toast notifications for feedback
- "Check for Updates on All Servers" button
- Jinja base template for DRYness
- CSS variables for easy theming
- Mobile-friendly and accessible design

## Changelog
### 0.1
- CRUD servers from DB
- Check for updates
- Install Updates

### 0.2
- Added login system (default: admin/admin) with session-based authentication
- Password can be changed from the settings page
- Detect if reboot is required using Ansible and update the DB
- Change index.html to display the actual reboot status with icons
- Add a button to reboot server with a confirmation popup
- Ping each server when the server list is loaded and display the ping status in the Bootstrap card with a green check or red X icon

### 0.3
- Migrated from AngularJS to Vue.js for all frontend logic
- Modularized frontend JS (split into api.js, utils.js, main.js, and Vue components)
- Upgraded UI to Bootstrap 5.3 and Bootstrap Icons
- Added dark mode toggle (with persistent setting)
- Added OS type (Windows, Ubuntu, Other Linux) for each server, with icons
- Added consolidated theme CSS with CSS variables and improved theming
- Refactored all templates to use a Jinja base template for DRYness
- Added toast notifications for user feedback
- Added "Check for Updates on All Servers" button and backend support
- Improved error/reboot alerts and badges on server cards
- Improved accessibility and mobile responsiveness
- Cleaned up and modernized all UI/UX

## Installation
### Prerequisites
- Docker (recommended)
- (Optional) Python 3.9+, Flask, Ansible if running outside Docker

### Quick Start (Docker)
1. Pull repo files
2. Build the docker container
   ```bash
   docker build -t lanjanitor:latest .
   ```
3. Start the docker container (default Flask port is 5000, mapped to 80)
   ```bash
   docker run --name lanjanitor -d -p 80:5000 --mount type=bind,source="$(pwd)"/app,target=/app lanjanitor
   ```
4. Browse to port 80

### Docker Compose
1. Pull repo files
2. Edit the docker-compose.yml file and set the path to your volume.
3. Build and start the docker container
   ```bash
   docker-compose up -d
   ```
4. Browse to port 80

### Start Script
1. Pull repo files
2. Create a shell script with the following:
   ```bash
   docker stop lanjanitor
   docker rm lanjanitor
   docker build -t lanjanitor:latest .
   docker run --name lanjanitor -d -p 80:5000 --mount type=bind,source="$(pwd)"/app,target=/app lanjanitor
   ```
3. Run the script
4. Browse to port 80

### Default Login
- Username: `admin`
- Password: `admin`

## Usage
- Log in with the default credentials
- Add servers with their OS type
- Use the dark mode toggle in settings
- Check for updates, install updates, and reboot servers
- View server status, update count, and reboot alerts

## Troubleshooting
- If you have issues with Docker volumes, check permissions
- If login fails, ensure the DB is initialized and the container has write access
- For Ansible errors, verify SSH keys and server connectivity

## Contributing
Pull requests and suggestions are welcome! Please open an issue for bugs or feature requests.

## License
MIT License

## Screenshots
*Add screenshots or GIFs here to showcase the UI and features (optional)*
