# Image Server

A learning project built with Python, Nginx, Docker, and Docker Compose.

The application allows users to upload images, store them, view uploaded images in a gallery, and access image files through Nginx.

## Technologies

- Python 3.12+
- Nginx
- Docker
- Docker Compose
- Python standard library

## Features

- Welcome page
- Image upload
- Support for `.jpg`, `.png`, and `.gif` formats
- Maximum file size of 5 MB
- Unique filename generation for every uploaded image
- Image gallery
- Direct image serving through Nginx
- Application action logging
- Persistent storage for images and logs
- Automatic container restart

## Architecture

The application consists of two Docker containers:

```text
Browser
   │
   │ HTTP :8080
   ▼
Nginx
   │
   ├── /images/<filename>
   │       └── serves image directly
   │
   └── other requests
           │
           │ HTTP :8000
           ▼
       Python application
```

The Python application is **not exposed directly to the host**.

The Python server listens on port `8000` inside the Docker network and can be accessed by Nginx through:

```text
http://app:8000
```

Nginx is the only service exposed to the host:

```text
http://localhost:8080/
```

## Project Structure

```text
img-loader/
├── app.py
├── requirements.txt
├── Dockerfile
├── compose.yaml
├── nginx.conf
├── images/
├── logs/
└── static/
    ├── index.html
    ├── upload.html
    └── images.html
```

## Application Routes

### Main page

```text
GET /
```

Displays the main page with links to the upload page and image gallery.

### Upload page

```text
GET /upload
```

Displays the image upload form.

### Upload image

```text
POST /upload
```

Accepts image files with the following extensions:

```text
.jpg
.png
.gif
```

The maximum allowed file size is 5 MB.

Each uploaded image receives a unique filename.

### Image gallery

```text
GET /images/
```

Displays all uploaded images.

### Image file

```text
GET /images/<filename>
```

Images are served directly by Nginx.

## Logging

Application actions are written to:

```text
/logs/app.log
```

Log entries use the following format:

```text
[2026-10-08 15:30:00] Дія: Відкрито головну сторінку
```

The log file is stored in a Docker volume, so logs remain available after container restarts.

## Docker Volumes

The application uses two persistent Docker volumes:

```text
images
logs
```

The `images` volume stores uploaded images.

The `logs` volume stores the application log.

Removing or recreating the containers does not remove these volumes unless they are explicitly deleted.

## Docker Configuration

The project uses a multi-stage Dockerfile.

The application container contains the Python server and application files.

The Nginx container:

- receives external HTTP requests;
- serves uploaded images;
- forwards application requests to the Python container.

## Running the Project

Make sure Docker and Docker Compose are installed.

From the project directory, run:

```bash
docker compose up --build
```

After the containers start, open:

```text
http://localhost:8080/
```

### Upload page

```text
http://localhost:8080/upload
```

### Image gallery

```text
http://localhost:8080/images/
```

The Python server is not directly available from the host on port `8000`.

## Stopping the Project

To stop the containers:

```bash
docker compose down
```

To stop the containers and remove the project Docker volumes:

```bash
docker compose down --volumes
```

The second command also removes uploaded images and application logs stored in the Docker volumes.

## Project Status

This project was created as a Python learning project focused on:

- Python HTTP servers
- file handling
- HTTP requests
- Docker
- Docker Compose
- Nginx
- container networking
- persistent Docker volumes
- application logging
- basic web application architecture

## Backup and Restore

### Creating a Backup

A database backup can be created by sending a GET request to:

```text
http://localhost:8080/backup
```

The application creates an SQL dump of the PostgreSQL database using `pg_dump`.

Each backup file is named using the following format:

```text
backup_YYYY-MM-DD_HHMMSS.sql
```

Backup files are stored in the local `backups/` directory, which is mounted into the application container at `/backups`.

If the backup is created successfully, the application returns the backup filename. If an error occurs, the application returns an HTTP 500 response and logs the error.

### Restoring a Backup

To restore a backup, first ensure that the project containers are running:

```bash
docker compose up -d
```

Create an empty database for the restore operation:

```bash
docker compose exec postgres psql -U postgres -d postgres -c "CREATE DATABASE images_restore_test;"
```

Replace `backup_YYYY-MM-DD_HHMMSS.sql` with the actual backup filename and run the following command in PowerShell from the project directory:

```powershell
Get-Content .\backups\backup_YYYY-MM-DD_HHMMSS.sql -Raw | docker compose exec -T postgres psql -U postgres -d images_restore_test
```

Verify that the restored database contains the expected data:

```powershell
docker compose exec postgres psql -U postgres -d images_restore_test -c "SELECT COUNT(*) FROM images;"
```

After testing the restored database, remove it:

```powershell
docker compose exec postgres psql -U postgres -d postgres -c "DROP DATABASE images_restore_test;"
```

**Important:** These commands restore the database into a separate test database and do not overwrite the production database. Do not restore a backup into an existing database containing data you need to preserve.

Database backups contain image metadata, not the image files themselves. The uploaded images are stored separately in the Docker `images` volume. To preserve the complete application data, back up both the database and the image files.
