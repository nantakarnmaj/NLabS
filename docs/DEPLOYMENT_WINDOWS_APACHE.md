# Windows Server Deployment Guide (Apache / XAMPP → Waitress → Flask)

This guide documents deploying **BreathQuest** on a Windows Server running Apache (or XAMPP) acting as a reverse proxy in front of the Waitress WSGI application server.

> [!IMPORTANT]
> **Manual Deployment Configuration**:
> Do not execute automated scripts to alter production Apache or XAMPP configurations. Review all configuration blocks, verify certificates and loopback ports, and perform backups before applying changes.

---

## 1. Architecture Overview

```text
+-------------------------------------------------------------------+
|                           CLIENT BROWSER                          |
+-------------------------------------------------------------------+
                                  | HTTPS (Port 443)
                                  v
+-------------------------------------------------------------------+
|                     APACHE / XAMPP REVERSE PROXY                  |
|  - Terminates TLS/SSL                                             |
|  - Enforces Security Headers & Content-Security-Policy            |
|  - Forwards X-Forwarded-For and X-Forwarded-Proto                 |
+-------------------------------------------------------------------+
                                  | HTTP (Loopback 127.0.0.1:8080)
                                  v
+-------------------------------------------------------------------+
|                         WAITRESS WSGI SERVER                      |
|  - Multi-threaded pure-Python WSGI server                         |
|  - Managed via Windows Service (NSSM) or Scheduled Task          |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                        FLASK APPLICATION                          |
|  - Instance Directory: C:\apps\breathquest\instance               |
|  - SQLite Database:    breathquest.db (foreign keys ON)           |
|  - Static Assets:      Precompiled local CSS/JS (No CDN)          |
+-------------------------------------------------------------------+
```

---

## 2. Directory Layout & Permissions

Place the application in a dedicated application directory outside of Apache's public document root (`htdocs`):

```text
C:\apps\breathquest\
  ├── .venv\
  ├── app\
  ├── config.py
  ├── run.py
  ├── instance\              <-- SQLite database resides here
  │   └── breathquest.db
  ├── migrations\
  └── requirements.txt
```

> [!CAUTION]
> Ensure the Apache public `htdocs` directory does **not** expose `C:\apps\breathquest\` or the `instance\` folder. File permissions on `instance\` should only permit read/write access to the dedicated application service account and administrators.

---

## 3. Environment & Configuration (.env)

Create a production `.env` file in `C:\apps\breathquest\.env`:

```ini
# Production Environment Configuration
FLASK_ENV=production

# Mandatory: 64-character random hex string (do not use defaults)
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=e83921...your_generated_random_production_secret_32_bytes...

# Instance-relative SQLite database URL
DATABASE_URL=sqlite:///breathquest.db

# Enforce secure cookies across HTTPS
SESSION_COOKIE_SECURE=true

# Loopback binding for Waitress
HOST=127.0.0.1
PORT=8080
```

---

## 4. Apache / XAMPP Virtual Host Configuration

Enable the required Apache modules in `httpd.conf`:
```apache
LoadModule proxy_module modules/mod_proxy.so
LoadModule proxy_http_module modules/mod_proxy_http.so
LoadModule headers_module modules/mod_headers.so
LoadModule ssl_module modules/mod_ssl.so
```

Add the following Virtual Host configuration in `conf/extra/httpd-vhosts.conf` or your site's SSL configuration:

```apache
<VirtualHost *:443>
    ServerName breathquest.your-institution.edu
    ServerAdmin admin@your-institution.edu

    # SSL / TLS Configuration
    SSLEngine on
    SSLCertificateFile "C:/Apache24/conf/ssl/breathquest.crt"
    SSLCertificateKeyFile "C:/Apache24/conf/ssl/breathquest.key"
    SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite HIGH:!aNULL:!MD5:!3DES

    # Reverse Proxy Settings
    ProxyPreserveHost On
    ProxyRequests Off

    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-Port "443"

    # Forward traffic to Waitress WSGI on loopback
    ProxyPass / http://127.0.0.1:8080/ connectiontimeout=10 timeout=60
    ProxyPassReverse / http://127.0.0.1:8080/

    # Security Headers
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "DENY"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"

    # Logging
    ErrorLog "logs/breathquest_error.log"
    CustomLog "logs/breathquest_access.log" combined
</VirtualHost>

# Optional: Redirect HTTP (Port 80) to HTTPS (Port 443)
<VirtualHost *:80>
    ServerName breathquest.your-institution.edu
    Redirect permanent / https://breathquest.your-institution.edu/
</VirtualHost>
```

---

## 5. Running Waitress as a Windows Service

To ensure BreathQuest runs continuously and restarts after server reboots, configure Waitress as a Windows Service using [NSSM (Non-Sucking Service Manager)](https://nssm.cc/).

### Install Service via NSSM:
```cmd
nssm install BreathQuest "C:\apps\breathquest\.venv\Scripts\python.exe" "run.py"
nssm set BreathQuest AppDirectory "C:\apps\breathquest"
nssm set BreathQuest AppStdout "C:\apps\breathquest\instance\waitress_stdout.log"
nssm set BreathQuest AppStderr "C:\apps\breathquest\instance\waitress_stderr.log"
nssm set BreathQuest Start SERVICE_AUTO_START
nssm start BreathQuest
```

### Or using a simple startup batch script (`start_server.bat`):
```bat
@echo off
cd /d C:\apps\breathquest
call .venv\Scripts\activate.bat
set FLASK_ENV=production
python run.py
```

---

## 6. SQLite Database Backup & Safety Procedures

SQLite stores data in `instance/breathquest.db`. During active operations, SQLite may write to write-ahead log files (`breathquest.db-wal` and `breathquest.db-shm`).

> [!WARNING]
> Never perform a simple file copy of `breathquest.db` alone while the server is running, as this risks copying a corrupted or incomplete transaction state.

### Recommended Backup Strategy:
1. **Online Transaction-Safe Backup using sqlite3 CLI**:
   ```cmd
   sqlite3 C:\apps\breathquest\instance\breathquest.db ".backup 'C:\backups\breathquest_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db'"
   ```
   The `.backup` command utilizes SQLite's native backup API to generate an atomic, consistent snapshot without shutting down the service.

2. **Pre-Migration Snapshot**:
   Before executing database migrations (`flask db upgrade`), always create a verified backup:
   ```cmd
   nssm stop BreathQuest
   copy C:\apps\breathquest\instance\breathquest.db* C:\backups\pre_migration\
   nssm start BreathQuest
   ```

---

## 7. Deployment Health Verification

After restarting or deploying:
1. Process Liveness:
   ```cmd
   curl -I http://127.0.0.1:8080/health/live
   # HTTP/1.1 200 OK {"status": "alive"}
   ```
2. Database Schema Readiness:
   ```cmd
   curl -I http://127.0.0.1:8080/health/ready
   # HTTP/1.1 200 OK {"status": "ready"}
   ```
3. External HTTPS Verification:
   ```cmd
   curl -k -I https://breathquest.your-institution.edu/
   # HTTP/1.1 200 OK
   ```
