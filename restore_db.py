import os
from dotenv import load_dotenv
import subprocess

load_dotenv()

MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')

backup_file = 'adminpy_backup.sql'

if not os.path.exists(backup_file):
    print(f"Backup file '{backup_file}' not found!")
    exit(1)

cmd = [
    'mysql',
    '-h', MYSQL_HOST,
    '-u', MYSQL_USER,
    f'-p{MYSQL_PASSWORD}',
    MYSQL_DB
]

try:
    with open(backup_file, 'rb') as f:
        proc = subprocess.Popen(cmd, stdin=f)
        proc.communicate()
    if proc.returncode == 0:
        print("Restore successful.")
    else:
        print("Restore failed.")
except Exception as e:
    print(f"Error during restore: {e}")
