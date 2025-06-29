# LanJanitor v0.2
When you can't seem to keep your homelab servers up to date, let LanJanitor help!

## Overview
The idea for LanJanitor is to automate the boring job like installing updates...

We have enough of that at work already... Our homelab is supposed to be fun!
## The tech
The pieces that make LanJanitor work are:
* **Docker** - Because why not run it in a container
* **Bootstrap 5** - for page layout
* **AngularJS** - to make api calls and display info
* **Flask 2.x.x** - the brains of the operation
* **Sqlite DB** - the memory for the brain of the operation
* **Ansible** - the mop and bucket

## Features
### 0.1
* CRUD servers from DB
* Check for updates
* Install Updates

### 0.2
* Added login system (default: admin/admin) with session-based authentication
* Password can be changed from the settings page
* Detect if reboot is required using Ansible and update the DB
* Change index.html to display the actual reboot status with icons
* Add a button to reboot server with a confirmation popup
* Ping each server when the server list is loaded and display the ping status in the Bootstrap card with a green check or red X icon

### ToDo...
* (Your next features here)

## Installation
### Manual

### Default Login

* Username: `admin`
* Password: `admin`

1. Pull repo files

2. Build the docker container
```bash
docker build -t lanjanitor:latest .
```

3. Start the docker container. It will make the site available on port 80. You can set the port of your choice.
```bash
docker run --name lanjanitor -d -p 80:5000 --mount type=bind,source="$(pwd)"/app,target=/app lanjanitor
```

4. Browse to port 80

### Docker Compose File

1. Pull repo files

2. Edit the docker-compose.yml file and set the path to your volume.

3. Build and start the docker container
```bash
docker-compose up -d
```

4. Browse to port 80

### Start Script
The benefit of this script is that it can be used to rebuild the image as well.

1. Pull repo files

2. Create a shell script with the following:
```bash
docker stop lanjanitor
docker rm  lanjanitor
docker build -t lanjanitor:latest .
docker run --name lanjanitor -d -p 80:5000 --mount type=bind,source="$(pwd)"/app,target=/app lanjanitor
```
3. Run the script

4. Browse to port 80

## Uninstallation
Ctrl-A + shift + delete
