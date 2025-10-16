# Ubuntu Package Manager with Admin Dashboard

A full-stack package management system with a beautiful dark-themed admin dashboard, CLI tool, and intelligent dependency resolution. Built with React, Node.js, Express, MySQL, and Python.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Ubuntu%2024.04-orange.svg)

---


### Frontend (React)
- **Modern Dark Theme** with gradient accents
- **Real-time Package Search** with pagination
- **Three Main Views:**
  -  Packages - Browse 100k+ Ubuntu packages
  -  Dependencies - View package dependency relationships
  -  Downloads - Monitor installation logs with timestamps
- **One-Click Package Updates** from Ubuntu Noble repositories
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Loading States** - Smooth transitions between views
- **Admin Authentication** - Secure JWT-based login

### 🖥️ CLI Tool (Python)
- **Auto-login** - Stores credentials securely in `.env`
- **Smart Dependency Resolution** - Recursively installs all dependencies
- **Version Compatibility** - Checks version constraints automatically
- **Progress Bars** - Visual feedback during downloads
- **t64 Conflict Protection** - Prevents system-breaking installations
- **Ubuntu Version Detection** - Warns about repository mismatches
- **Backend Logging** - All installations tracked in database
- **Commands:**
  - `register` - Create new user account (register username password)
  - `login` - Authenticate user
  - `search` - Find packages
  - `info` - View package details and dependencies
  - `install` - Install package with dependencies
  - `logout` - Clear credentials

###  Backend (Node.js + Express)
- **RESTful API** with JWT authentication
- **MySQL Integration** with connection pooling
- **Real-time Package Updates** from Ubuntu repositories
- **Progress Logging** - Detailed download and parse metrics
- **Two Login Endpoints:**
  - `/login` - Admin-only (frontend)
  - `/login-cli` - All users (CLI tool)
- **Rate-Limited APIs** with proper error handling
- **CORS Enabled** for cross-origin requests

###  Database (MySQL)
- **Optimized Schema** with indexes on search columns
- **4 Main Tables:**
  - `users` - Authentication and roles
  - `packages` - ~100k Ubuntu packages
  - `dependencies` - Package relationships
  - `packagedownloads` - Installation logs with metrics
- **Backup & Restore** - Python scripts with compression

---

##  Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

---

##  Prerequisites

### System Requirements
- **OS:** Ubuntu 24.04 LTS (Noble Numbat) or compatible
- **RAM:** 4GB minimum (8GB recommended for package updates)
- **Disk:** 2GB free space minimum
- **Internet:** Required for package downloads

### Software Requirements

#### Windows (for backend/frontend):
Node.js 18+ and npm
node --version # Should be v18.0.0 or higher
npm --version

MySQL 8.0+
mysql --version

Python 3.8+ (for scripts)
python --version

text

#### Ubuntu/WSL (for CLI tool):
Python 3.8+
python3 --version

pip
pip3 --version

MySQL client tools
mysql --version

dpkg (pre-installed)
dpkg --version

text

---

## Installation

### 1. Clone Repository
git clone https://github.com/yourusername/package-manager.git
cd package-manager

text

### 2. Database Setup

Create MySQL database and user:
CREATE DATABASE adminpy;
CREATE USER 'admin'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON adminpy.* TO 'admin'@'localhost';
FLUSH PRIVILEGES;

text

Create tables:
USE adminpy;

CREATE TABLE users (
id INT AUTO_INCREMENT PRIMARY KEY,
username VARCHAR(255) UNIQUE NOT NULL,
password_hash VARCHAR(255) NOT NULL,
role VARCHAR(50) DEFAULT 'user'
);

CREATE TABLE packages (
id INT AUTO_INCREMENT PRIMARY KEY,
name VARCHAR(255) NOT NULL,
version VARCHAR(255),
architecture VARCHAR(50),
filename VARCHAR(1000),
INDEX idx_name (name)
);

CREATE TABLE dependencies (
id INT AUTO_INCREMENT PRIMARY KEY,
package_id INT NOT NULL,
dependency_name VARCHAR(255) NOT NULL,
version_constraint VARCHAR(1000),
FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
INDEX idx_package_id (package_id),
INDEX idx_dependency_name (dependency_name)
);

CREATE TABLE packagedownloads (
id INT AUTO_INCREMENT PRIMARY KEY,
user_id VARCHAR(255) NOT NULL,
package_name VARCHAR(255) NOT NULL,
version VARCHAR(255),
download_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
download_duration_seconds DECIMAL(10, 2),
install_duration_seconds DECIMAL(10, 2),
client_ip VARCHAR(45),
download_status VARCHAR(50),
install_status VARCHAR(50),
INDEX idx_user_id (user_id),
INDEX idx_package_name (package_name),
INDEX idx_timestamp (download_timestamp)
);

text

### 3. Backend Setup

cd backend

Install dependencies
npm install

Create .env file
cat > .env << EOF
MYSQL_HOST=localhost
MYSQL_USER=admin
MYSQL_PASSWORD=your_secure_password
MYSQL_DB=adminpy
JWT_SECRET=your_random_secret_key_here
PORT=8000
EOF

Start backend
npm start

text

### 4. Frontend Setup

cd frontend

Install dependencies
npm install

Start frontend
npm start

text

### 5. CLI Tool Setup

cd .. # Back to root directory

Install Python dependencies
pip3 install -r requirements.txt

Test CLI
python3 test.py --help

text

---

## Configuration

### Environment Variables

#### Backend (.env)
MYSQL_HOST=localhost # MySQL server host
MYSQL_USER=admin # Database username
MYSQL_PASSWORD=your_password # Database password
MYSQL_DB=adminpy # Database name
JWT_SECRET=random_secret_key # JWT signing key (generate secure random)
PORT=8000 # Backend port

text

#### CLI Tool (.env) - Auto-generated
PKG_MANAGER_USER=username # CLI user credentials
PKG_MANAGER_PASS=password # Auto-saved on login

text

### Ubuntu Repository Configuration

By default, the system uses Ubuntu 24.04 (Noble) repositories. To change:

Edit `backend/index.js`:
const repos = [
'http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz',
'http://archive.ubuntu.com/ubuntu/dists/noble/universe/binary-amd64/Packages.gz'
];

text

Supported Ubuntu versions:
- `noble` - 24.04 LTS
- `jammy` - 22.04 LTS
- `focal` - 20.04 LTS

---

## Usage

### Starting Services

#### Windows (Quick Start)
Start everything
start.bat

text

#### Linux/WSL
Make executable
chmod +x start.sh

Start all services
./start.sh

text

#### Manual Start
Terminal 1: Backend
cd backend
npm start

Terminal 2: Frontend
cd frontend
npm start

Terminal 3: CLI (WSL/Ubuntu)
python3 test.py search gcc

text

### Admin Dashboard

1. **Access:** Open browser to `http://localhost:3000`

2. **First Login:** Create admin user via backend:
curl -X POST http://localhost:8000/register
-H "Content-Type: application/json"
-d '{"username":"admin","password":"yourpassword","role":"admin"}'

text

3. **Features:**
   - **Packages Tab:** Search and browse all packages
   - **Dependencies Tab:** View dependency relationships
   - **Downloads Tab:** Monitor user installations
   - **Update Packages:** Sync with Ubuntu repositories (takes 3-5 minutes)

### CLI Tool

#### First Time Setup
Register user
python3 test.py register johndoe mypassword

Credentials auto-saved to .env
text

#### Search Packages
python3 test.py search gcc
python3 test.py search python3

text

#### View Package Info
python3 test.py info nmap

Shows: version, architecture, dependencies
text

#### Install Package
python3 test.py install nmap

Automatically:
1. Analyzes dependencies
2. Shows install plan
3. Downloads missing dependencies
4. Installs in correct order
5. Logs to database
text

#### Logout
python3 test.py logout

text

### Database Management

#### Backup Database
Simple backup (compressed)
python3 save_db.py

Backup without compression
python3 save_db.py --no-compress

List backups
python3 save_db.py --list

text

#### Restore Database
Interactive restore
python3 restore_db.py

Restore latest backup
python3 restore_db.py --latest

Restore specific backup
python3 restore_db.py backups/adminpy_backup_20251016_180000.sql.gz

text

---

## Project Structure

package-manager/
├── backend/ # Node.js Express backend
│ ├── index.js # Main server file
│ ├── package.json # Dependencies
│ ├── .env # Configuration (create this)
│ └── node_modules/ # npm packages
│
├── frontend/ # React admin dashboard
│ ├── public/
│ │ └── index.html
│ ├── src/
│ │ ├── components/
│ │ │ ├── Login.js # Login page
│ │ │ ├── Login.css # Login styles
│ │ │ ├── Dashboard.js # Main dashboard
│ │ │ ├── Dashboard.css # Dashboard styles
│ │ │ ├── LoadingSpinner.js
│ │ │ └── LoadingSpinner.css
│ │ ├── App.js # Root component
│ │ ├── App.css # Global styles
│ │ └── index.js # Entry point
│ ├── package.json
│ └── node_modules/
│
├── backups/ # Database backups (auto-created)
│ └── adminpy_backup_*.sql.gz
│
├── debian_packages/ # Downloaded .deb files (temp)
│
├── test.py # CLI package manager tool
├── save_db.py # Database backup script
├── restore_db.py # Database restore script
├── requirements.txt # Python dependencies
├── start.bat # Windows startup script
├── start.sh # Linux startup script
├── stop.bat # Windows stop script
├── .env # Root env (CLI credentials)
└── README.md # This file

text

---

## API Documentation

### Authentication Endpoints

#### POST `/register`
Register new user
Request:
{
"username": "johndoe",
"password": "securepass123",
"role": "user"
}

Response:
{
"message": "User registered"
}

text

#### POST `/login`
Admin login (frontend only)
Request:
{
"username": "admin",
"password": "adminpass"
}

Response:
{
"token": "eyJhbGciOiJIUzI1...",
"role": "admin"
}

text

#### POST `/login-cli`
CLI login (all users)
Request:
{
"username": "johndoe",
"password": "userpass"
}

Response:
{
"token": "eyJhbGciOiJIUzI1...",
"role": "user",
"username": "johndoe"
}

text

### Data Endpoints (Require Authentication)

#### GET `/api/packages`
List packages with pagination
Query Parameters:

search: string (optional)

page: number (default: 1)

Headers:
Authorization: Bearer <token>

Response:
{
"data": [...],
"total": 100000,
"page": 1,
"totalPages": 1000
}

text

#### GET `/api/dependencies`
List package dependencies

#### GET `/api/packagedownloads`
List installation logs

#### POST `/api/log-download`
Log package installation

#### POST `/api/update-packages`
Update packages from Ubuntu repositories (Admin only)
Headers:
Authorization: Bearer <admin_token>

Response:
{
"status": "Updated 99953 packages from Ubuntu 24.04 (Noble)"
}

text

---

## Troubleshooting

### Common Issues

#### 1. Connection Refused (WSL → Windows)
Problem: test.py can't connect to backend
Error: Connection refused

Solution: Update BACKEND_URL in test.py
Get Windows IP from WSL:
cat /etc/resolv.conf | grep nameserver | awk '{print $2}'

Update user.py to the appropiate ip address ( This is main as i encountered this error. ).


#### 2. Package Version Conflicts
Problem: t64 transition conflicts
Error: libpcap0.8t64 breaks libpcap0.8

Solution: Update package database to Ubuntu 24.04
In backend/index.js, use 'noble' instead of 'jammy'
Then click "Update Packages" in dashboard


#### 3. MySQL Connection Failed
Problem: Backend can't connect to MySQL
Error: ER_ACCESS_DENIED_ERROR

Solution: Check .env credentials
mysql -u admin -p adminpy



#### 4. Frontend Build Errors
Problem: React app won't start
Error: Module not found

Solution: Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start



#### 5. Fix Broken System After Wrong Package Install
If you accidentally installed incompatible packages:
sudo apt --fix-broken install
sudo dpkg --remove --force-remove-reinstreq libpcap0.8 libssl3
sudo apt autoremove


---

##  Security

### Best Practices

1. **Change Default Credentials**
Generate strong JWT secret:
node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"


2. **Firewall Configuration**
Only allow local connections
sudo ufw allow from 127.0.0.1 to any port 8000

text

3. **HTTPS in Production**
- Use SSL certificates
- Enable CORS only for trusted origins
- Implement rate limiting

4. **Database Security**
- Use strong passwords
- Regular backups
- Limit user privileges

---

## Performance

### Database Optimization
-- Add indexes for faster searches
CREATE INDEX idx_package_name ON packages(name);
CREATE INDEX idx_dependency_name ON dependencies(dependency_name);

text

### Stats
- **Total Ubuntu Packages:** ~100,000
- **Dependencies Tracked:** ~235,000
- **API Response Time:** < 100ms average
- **Database Size:** ~500MB (with full Noble repository)

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

##  License

This project is licensed under the MIT License.

---

##  Acknowledgments

- Ubuntu Package Management team
- React.js community
- Express.js documentation
- MySQL team

---

##  Support

For support, open an issue on GitHub.

---

##  Roadmap

### Version 1.1
- [ ] Package conflict resolution
- [ ] Rollback functionality
- [ ] Docker containerization
- [ ] API rate limiting per user

### Version 2.0
- [ ] Multi-distro support (Debian, Fedora)
- [ ] Web-based package installation
- [ ] Analytics dashboard
- [ ] Mobile app

---
*Last Updated: October 16, 2025*