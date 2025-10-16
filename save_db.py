#!/usr/bin/env python3
"""
Database Backup Script
Backs up MySQL database with compression and timestamps
"""

import os
import sys
import subprocess
import gzip
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')

# Backup directory
BACKUP_DIR = Path('backups')
BACKUP_DIR.mkdir(exist_ok=True)

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def create_backup(compress=True):
    """Create database backup"""
    
    # Validate environment variables
    if not all([MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB]):
        print(f"{RED}Error: Missing database credentials in .env file{RESET}")
        return False
    
    # Create timestamped backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = BACKUP_DIR / f"{MYSQL_DB}_backup_{timestamp}.sql"
    
    if compress:
        backup_file = Path(str(backup_file) + '.gz')
    
    print(f"{BLUE}Starting backup...{RESET}")
    print(f"Database: {MYSQL_DB}")
    print(f"Host: {MYSQL_HOST}")
    print(f"Backup file: {backup_file}")
    
    # mysqldump command
    cmd = [
        'mysqldump',
        '-h', MYSQL_HOST,
        '-u', MYSQL_USER,
        f'-p{MYSQL_PASSWORD}',
        '--single-transaction',
        '--quick',
        '--lock-tables=false',
        MYSQL_DB
    ]
    
    try:
        start_time = datetime.now()
        
        if compress:
            # Dump and compress
            print(f"{YELLOW}Dumping and compressing...{RESET}")
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            with gzip.open(backup_file, 'wb') as f:
                for chunk in iter(lambda: proc.stdout.read(8192), b''):
                    f.write(chunk)
            
            proc.wait()
        else:
            # Dump without compression
            print(f"{YELLOW}Dumping...{RESET}")
            with open(backup_file, 'wb') as f:
                proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.PIPE)
                proc.wait()
        
        if proc.returncode == 0:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
            
            print(f"{GREEN}✓ Backup successful!{RESET}")
            print(f"File: {backup_file}")
            print(f"Size: {file_size:.2f} MB")
            print(f"Time: {duration:.2f} seconds")
            
            # List recent backups
            list_backups()
            
            return True
        else:
            error = proc.stderr.read().decode('utf-8')
            print(f"{RED}✗ Backup failed!{RESET}")
            print(f"Error: {error}")
            
            # Clean up failed backup file
            if backup_file.exists():
                backup_file.unlink()
            
            return False
            
    except FileNotFoundError:
        print(f"{RED}Error: mysqldump not found. Install MySQL client tools.{RESET}")
        return False
    except Exception as e:
        print(f"{RED}Error during backup: {e}{RESET}")
        return False


def list_backups():
    """List all available backups"""
    backups = sorted(BACKUP_DIR.glob(f"{MYSQL_DB}_backup_*.sql*"), reverse=True)
    
    if backups:
        print(f"\n{BLUE}Available backups:{RESET}")
        for i, backup in enumerate(backups[:10], 1):
            size = backup.stat().st_size / (1024 * 1024)  # MB
            modified = datetime.fromtimestamp(backup.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            print(f"  {i}. {backup.name} ({size:.2f} MB) - {modified}")
        
        if len(backups) > 10:
            print(f"  ... and {len(backups) - 10} more")
    else:
        print(f"\n{YELLOW}No backups found{RESET}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Backup MySQL Database')
    parser.add_argument('--no-compress', action='store_true', help='Disable compression')
    parser.add_argument('--list', action='store_true', help='List available backups')
    
    args = parser.parse_args()
    
    if args.list:
        list_backups()
    else:
        compress = not args.no_compress
        success = create_backup(compress=compress)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
