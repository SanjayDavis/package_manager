#!/usr/bin/env python3
"""
Database Restore Script
Restores MySQL database from backup
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

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def list_backups():
    """List all available backups and return them"""
    if not BACKUP_DIR.exists():
        print(f"{RED}Error: Backup directory not found{RESET}")
        return []
    
    backups = sorted(BACKUP_DIR.glob(f"{MYSQL_DB}_backup_*.sql*"), reverse=True)
    
    if not backups:
        print(f"{YELLOW}No backups found in {BACKUP_DIR}{RESET}")
        return []
    
    print(f"\n{BLUE}Available backups:{RESET}")
    for i, backup in enumerate(backups, 1):
        size = backup.stat().st_size / (1024 * 1024)  # MB
        modified = datetime.fromtimestamp(backup.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        compressed = " [compressed]" if backup.suffix == '.gz' else ""
        print(f"  {i}. {backup.name} ({size:.2f} MB) - {modified}{compressed}")
    
    return backups


def restore_backup(backup_file):
    """Restore database from backup file"""
    
    # Validate environment variables
    if not all([MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB]):
        print(f"{RED}Error: Missing database credentials in .env file{RESET}")
        return False
    
    if not backup_file.exists():
        print(f"{RED}Error: Backup file not found: {backup_file}{RESET}")
        return False
    
    print(f"\n{YELLOW}{'='*70}{RESET}")
    print(f"{YELLOW}WARNING: This will OVERWRITE the current database!{RESET}")
    print(f"{YELLOW}{'='*70}{RESET}")
    print(f"Database: {MYSQL_DB}")
    print(f"Host: {MYSQL_HOST}")
    print(f"Backup file: {backup_file}")
    
    confirm = input(f"\n{RED}Are you sure you want to restore? (yes/no): {RESET}").strip().lower()
    if confirm not in ['yes', 'y']:
        print(f"{GREEN}Restore cancelled{RESET}")
        return False
    
    # mysql command
    cmd = [
        'mysql',
        '-h', MYSQL_HOST,
        '-u', MYSQL_USER,
        f'-p{MYSQL_PASSWORD}',
        MYSQL_DB
    ]
    
    try:
        start_time = datetime.now()
        print(f"\n{BLUE}Starting restore...{RESET}")
        
        if backup_file.suffix == '.gz':
            # Decompress and restore
            print(f"{YELLOW}Decompressing and restoring...{RESET}")
            with gzip.open(backup_file, 'rb') as f:
                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Read and pipe the data
                for chunk in iter(lambda: f.read(8192), b''):
                    proc.stdin.write(chunk)
                
                proc.stdin.close()
                proc.wait()
        else:
            # Restore without decompression
            print(f"{YELLOW}Restoring...{RESET}")
            with open(backup_file, 'rb') as f:
                proc = subprocess.Popen(cmd, stdin=f, stderr=subprocess.PIPE)
                proc.wait()
        
        if proc.returncode == 0:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"{GREEN}✓ Restore successful!{RESET}")
            print(f"Time: {duration:.2f} seconds")
            
            # Show table counts
            show_database_stats()
            
            return True
        else:
            error = proc.stderr.read().decode('utf-8')
            print(f"{RED}✗ Restore failed!{RESET}")
            print(f"Error: {error}")
            return False
            
    except FileNotFoundError:
        print(f"{RED}Error: mysql client not found. Install MySQL client tools.{RESET}")
        return False
    except Exception as e:
        print(f"{RED}Error during restore: {e}{RESET}")
        return False


def show_database_stats():
    """Show database statistics after restore"""
    try:
        cmd = [
            'mysql',
            '-h', MYSQL_HOST,
            '-u', MYSQL_USER,
            f'-p{MYSQL_PASSWORD}',
            '-e', f"SELECT TABLE_NAME, TABLE_ROWS FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{MYSQL_DB}'",
            MYSQL_DB
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"\n{BLUE}Database statistics:{RESET}")
            print(result.stdout)
    except:
        pass


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Restore MySQL Database from Backup')
    parser.add_argument('backup_file', nargs='?', help='Backup file to restore')
    parser.add_argument('--list', action='store_true', help='List available backups')
    parser.add_argument('--latest', action='store_true', help='Restore the latest backup')
    
    args = parser.parse_args()
    
    if args.list:
        list_backups()
        return
    
    backups = list_backups()
    
    if not backups:
        sys.exit(1)
    
    # Determine which backup to restore
    if args.latest:
        backup_file = backups[0]
        print(f"\n{BLUE}Selected latest backup: {backup_file.name}{RESET}")
    elif args.backup_file:
        backup_file = Path(args.backup_file)
        if not backup_file.is_absolute():
            backup_file = BACKUP_DIR / backup_file
    else:
        # Interactive selection
        print()
        try:
            choice = int(input(f"Enter backup number to restore (1-{len(backups)}): "))
            if 1 <= choice <= len(backups):
                backup_file = backups[choice - 1]
            else:
                print(f"{RED}Invalid choice{RESET}")
                sys.exit(1)
        except (ValueError, KeyboardInterrupt):
            print(f"\n{YELLOW}Cancelled{RESET}")
            sys.exit(1)
    
    # Perform restore
    success = restore_backup(backup_file)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
