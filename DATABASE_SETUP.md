# Database Setup and SQL Queries

Complete guide for setting up and managing the Package Manager database.

---

## Table of Contents
- [Database Schema](#database-schema)
- [Initial Setup](#initial-setup)
- [Table Structures](#table-structures)
- [Common Queries](#common-queries)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)

---

## Database Schema

The system uses 4 main tables:

```
┌─────────────────┐
│     users       │  Authentication & Authorization
└─────────────────┘
         │
         │ (logs downloads)
         ▼
┌─────────────────┐
│ packagedownloads│  Download/Install History
└─────────────────┘
         │
         │ (references package_name)
         ▼
┌─────────────────┐      ┌─────────────────┐
│    packages     │◄─────┤  dependencies   │
│   (~100k rows)  │      │   (~235k rows)  │
└─────────────────┘      └─────────────────┘
     (package_id)
```

---

## Initial Setup

### 1. Create Database and User

```sql
-- Create database
CREATE DATABASE adminpy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (replace password)
CREATE USER 'adminuser'@'localhost' IDENTIFIED BY 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON adminpy.* TO 'adminuser'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify user
SELECT User, Host FROM mysql.user WHERE User = 'adminuser';
```

### 2. Select Database

```sql
USE adminpy;
```

---

## Table Structures

### Table 1: `users`

**Purpose:** Store user authentication and role information

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Columns:**
- `id`: Auto-incrementing user ID
- `username`: Unique username (3-255 chars)
- `password_hash`: bcrypt hashed password (60 chars)
- `role`: User role (`'admin'` or `'user'`)
- `created_at`: Registration timestamp
- `last_login`: Last successful login

**Sample Data:**
```sql
-- Insert admin user (password: admin123)
INSERT INTO users (username, password_hash, role) 
VALUES (
    'admin', 
    '$2b$10$rYwbmIwZKhKJ9FzQxJ9HqO7YqbHRQBvxJ9qcWx8pHKZmqB7bGzKCu',
    'admin'
);

-- Insert regular user
INSERT INTO users (username, password_hash, role) 
VALUES (
    'john_doe', 
    '$2b$10$abc123...', 
    'user'
);
```

---

### Table 2: `packages`

**Purpose:** Store Ubuntu package information

```sql
CREATE TABLE packages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(255),
    architecture VARCHAR(50),
    filename VARCHAR(1000),
    maintainer VARCHAR(500),
    description TEXT,
    homepage VARCHAR(500),
    md5sum VARCHAR(32),
    sha256 VARCHAR(64),
    section VARCHAR(100),
    priority VARCHAR(50),
    size BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_package (name, version, architecture),
    INDEX idx_name (name),
    INDEX idx_architecture (architecture),
    INDEX idx_section (section),
    FULLTEXT INDEX idx_description (description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Columns:**
- `id`: Package ID
- `name`: Package name (e.g., 'nginx', 'python3')
- `version`: Version string (e.g., '1.24.0-1ubuntu1')
- `architecture`: CPU architecture ('amd64', 'all', 'i386')
- `filename`: Repository path to .deb file
- `maintainer`: Package maintainer email
- `description`: Package description
- `homepage`: Project website
- `md5sum` / `sha256`: File checksums
- `section`: Category (e.g., 'web', 'python', 'libs')
- `priority`: Installation priority
- `size`: Package size in bytes

**Sample Data:**
```sql
INSERT INTO packages (name, version, architecture, filename, section, size) 
VALUES 
    ('nginx', '1.24.0-1ubuntu1', 'amd64', 'pool/main/n/nginx/nginx_1.24.0-1ubuntu1_amd64.deb', 'web', 1024000),
    ('python3', '3.12.3-0ubuntu1', 'amd64', 'pool/main/p/python3/python3_3.12.3-0ubuntu1_amd64.deb', 'python', 512000);
```

---

### Table 3: `dependencies`

**Purpose:** Track package dependency relationships

```sql
CREATE TABLE dependencies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    package_id INT NOT NULL,
    dependency_name VARCHAR(255) NOT NULL,
    version_constraint VARCHAR(1000),
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
    INDEX idx_package_id (package_id),
    INDEX idx_dependency_name (dependency_name),
    INDEX idx_combined (package_id, dependency_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Columns:**
- `id`: Dependency record ID
- `package_id`: Foreign key to packages.id
- `dependency_name`: Name of required package
- `version_constraint`: Version requirement (e.g., '>= 2.0', '= 1.5.3')

**Sample Data:**
```sql
-- nginx depends on multiple packages
INSERT INTO dependencies (package_id, dependency_name, version_constraint) 
VALUES 
    (1, 'libc6', '>= 2.34'),
    (1, 'libssl3', '>= 3.0.0'),
    (1, 'zlib1g', '>= 1:1.2.11');
```

---

### Table 4: `packagedownloads`

**Purpose:** Log package installation history and metrics

```sql
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
    error_message TEXT,
    INDEX idx_user_id (user_id),
    INDEX idx_package_name (package_name),
    INDEX idx_timestamp (download_timestamp),
    INDEX idx_status (download_status, install_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Columns:**
- `id`: Download log ID
- `user_id`: Username who installed
- `package_name`: Name of installed package
- `version`: Version installed
- `download_timestamp`: When installation occurred
- `download_duration_seconds`: Download time
- `install_duration_seconds`: Installation time
- `client_ip`: User's IP address
- `download_status`: 'success' or 'failed'
- `install_status`: 'success' or 'failed'
- `error_message`: Error details if failed

**Sample Data:**
```sql
INSERT INTO packagedownloads 
    (user_id, package_name, version, download_duration_seconds, 
     install_duration_seconds, client_ip, download_status, install_status) 
VALUES 
    ('john_doe', 'nginx', '1.24.0-1ubuntu1', 5.23, 2.15, '192.168.1.100', 'success', 'success');
```

---

## Common Queries

This section contains the actual SQL queries used by the project in backend/index.js and register_admin.py.

### User Management (Backend: index.js & register_admin.py)

#### Register New User
```sql
-- Backend: /register endpoint
INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?);
```

#### Login - Check Credentials
```sql
-- Backend: /login and /login-cli endpoints
SELECT id, password_hash, role FROM users WHERE username = ?;
```

#### List Admin Users
```sql
-- register_admin.py
SELECT id, username, role FROM users WHERE role = 'admin' ORDER BY id ASC;
```

#### Check If Username Exists
```sql
-- register_admin.py
SELECT id FROM users WHERE username = ?;
```

#### Delete Admin User
```sql
-- register_admin.py
SELECT username, role FROM users WHERE id = ?;
DELETE FROM users WHERE id = ?;
```

---

### Package Queries (Backend: /api/packages endpoint)

#### Search Packages with Relevance Ranking
```sql
-- When search term provided
SELECT id, name, version, architecture, filename,
 CASE 
   WHEN name = ? THEN 1
   WHEN name LIKE ? THEN 2
   ELSE 3
 END as relevance
FROM packages 
WHERE name LIKE ? 
ORDER BY relevance, name ASC;
```

#### Count Search Results
```sql
SELECT COUNT(*) as total FROM packages WHERE name LIKE ?;
```

#### List All Packages (No Search)
```sql
SELECT id, name, version, architecture, filename 
FROM packages 
ORDER BY name ASC;
```

#### Count All Packages
```sql
SELECT COUNT(*) as total FROM packages;
```

---

### Dependency Queries (Backend: /api/dependencies endpoint)

#### List Dependencies with Package Names
```sql
-- When search term provided
SELECT p.name as package_name, d.dependency_name, d.version_constraint 
FROM dependencies d 
JOIN packages p ON d.package_id = p.id 
WHERE p.name LIKE ? OR d.dependency_name LIKE ? 
ORDER BY p.name ASC ;
```

#### Count Filtered Dependencies
```sql
SELECT COUNT(*) as total 
FROM dependencies d 
JOIN packages p ON d.package_id = p.id 
WHERE p.name LIKE ? OR d.dependency_name LIKE ?;
```

#### List All Dependencies (No Search)
```sql
SELECT p.name as package_name, d.dependency_name, d.version_constraint 
FROM dependencies d 
JOIN packages p ON d.package_id = p.id 
ORDER BY p.name ASC 
;
```

#### Count All Dependencies
```sql
SELECT COUNT(*) as total FROM dependencies;
```

---

### Download History Queries (Backend: /api/packagedownloads endpoint)

#### Search Download Logs
```sql
SELECT * FROM packagedownloads 
WHERE user_id LIKE ? OR package_name LIKE ? 
ORDER BY download_timestamp DESC ;
```

#### Count Filtered Downloads
```sql
SELECT COUNT(*) as total FROM packagedownloads 
WHERE user_id LIKE ? OR package_name LIKE ?;
```

#### List All Download Logs
```sql
SELECT * FROM packagedownloads 
ORDER BY download_timestamp DESC 
;
```

#### Count All Downloads
```sql
SELECT COUNT(*) as total FROM packagedownloads;
```

#### Log New Download
```sql
-- Backend: /api/log-download endpoint
INSERT INTO packagedownloads 
(user_id, package_name, version, download_duration_seconds, 
 install_duration_seconds, client_ip, download_status, install_status) 
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
```

---

### Package Update Operations (Backend: /api/update-packages endpoint)

#### Clear Old Data (Within Transaction)
```sql
DELETE FROM dependencies;
DELETE FROM packages;
```

#### Insert Packages (Bulk)
```sql
-- Executed in loop for each package
INSERT INTO packages (name, version, architecture, filename) 
VALUES (?, ?, ?, ?);
```

#### Insert Dependencies (Bulk)
```sql
-- Executed in loop for each dependency
INSERT INTO dependencies (package_id, dependency_name, version_constraint) 
VALUES (?, ?, ?);
```

---

## Maintenance

### Database Statistics

#### Table Sizes
```sql
SELECT 
    table_name, 
    ROUND(((data_length + index_length) / 1024 / 1024), 2) as size_mb,
    table_rows as row_count
FROM information_schema.TABLES 
WHERE table_schema = 'adminpy' 
ORDER BY (data_length + index_length) DESC;
```

#### Index Usage
```sql
SHOW INDEX FROM packages;
SHOW INDEX FROM dependencies;
SHOW INDEX FROM users;
SHOW INDEX FROM packagedownloads;
```

### Optimization

#### Analyze Tables
```sql
ANALYZE TABLE packages;
ANALYZE TABLE dependencies;
ANALYZE TABLE users;
ANALYZE TABLE packagedownloads;
```

#### Optimize Tables
```sql
OPTIMIZE TABLE packages;
OPTIMIZE TABLE dependencies;
OPTIMIZE TABLE packagedownloads;
```

#### Check Table Health
```sql
CHECK TABLE packages;
CHECK TABLE dependencies;
```

### Cleanup

#### Delete Old Download Logs (older than 90 days)
```sql
DELETE FROM packagedownloads 
WHERE download_timestamp < DATE_SUB(NOW(), INTERVAL 90 DAY);
```

#### Clear All Data (Keep Structure)
```sql
TRUNCATE TABLE packagedownloads;
TRUNCATE TABLE dependencies;
TRUNCATE TABLE packages;
```

#### Reset Auto Increment
```sql
ALTER TABLE packages AUTO_INCREMENT = 1;
ALTER TABLE dependencies AUTO_INCREMENT = 1;
```

---

## Backup & Restore

### Manual Backup
```bash
# Backup entire database
mysqldump -u adminuser -p adminpy > backup.sql

# Backup with compression
mysqldump -u adminuser -p adminpy | gzip > backup.sql.gz

# Backup specific tables
mysqldump -u adminuser -p adminpy users packages > partial_backup.sql
```

### Restore
```bash
# Restore from backup
mysql -u adminuser -p adminpy < backup.sql

# Restore from compressed backup
gunzip < backup.sql.gz | mysql -u adminuser -p adminpy
```

### Python Backup Scripts
```bash
# Save database
python save_db.py

# Restore database (interactive)
python restore_db.py

# Restore latest backup
python restore_db.py --latest
```

---

## Troubleshooting

### Common Issues

#### Connection Refused
```

#### Foreign Key Constraint Fails
```sql
-- Check foreign key relationships
SELECT * FROM information_schema.KEY_COLUMN_USAGE 
WHERE REFERENCED_TABLE_NAME = 'packages';

-- Temporarily disable foreign key checks
SET FOREIGN_KEY_CHECKS = 0;
-- ... perform operation ...
SET FOREIGN_KEY_CHECKS = 1;
```

#### Table Already Exists
```sql
-- Drop existing table
DROP TABLE IF EXISTS packagedownloads;
DROP TABLE IF EXISTS dependencies;
DROP TABLE IF EXISTS packages;
DROP TABLE IF EXISTS users;

-- Then recreate with CREATE TABLE statements
```

---

## Security Best Practices

### 1. Password Requirements
```sql
-- MySQL 8.0+ password validation
SHOW VARIABLES LIKE 'validate_password%';

-- Set strong password policy
SET GLOBAL validate_password.policy = STRONG;
SET GLOBAL validate_password.length = 12;
```

### 2. Limit User Privileges
```sql
-- Create read-only user
CREATE USER 'readonly'@'localhost' IDENTIFIED BY 'password';
GRANT SELECT ON adminpy.* TO 'readonly'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Enable Query Logging
```sql
-- Enable general query log
SET GLOBAL general_log = 'ON';
SET GLOBAL general_log_file = '/var/log/mysql/queries.log';
```

### 4. Regular Backups
```bash
# Setup cron job for daily backups
0 2 * * * /usr/bin/python3 /path/to/save_db.py
```

---

## Performance Tuning

### Index Recommendations
```sql
-- Add indexes for frequently searched columns
CREATE INDEX idx_package_version ON packages(version);
CREATE INDEX idx_download_date ON packagedownloads(DATE(download_timestamp));

-- Composite index for common queries
CREATE INDEX idx_pkg_name_arch ON packages(name, architecture);
```

### Query Optimization
```sql
-- Use EXPLAIN to analyze queries
EXPLAIN SELECT * FROM packages WHERE name LIKE 'python%';

-- Add query hints
SELECT /*+ INDEX(packages idx_name) */ * FROM packages WHERE name = 'nginx';
```

---

**Last Updated:** October 21, 2025





DDL - all there
DML - all there
DQL - all there with subqueries
DCL - Grant all permissions for ADMIN , and removed insert and update permissions for USERS



