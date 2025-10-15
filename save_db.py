import os
from dotenv import load_dotenv
import subprocess
from datetime import datetime

load_dotenv()

MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')

# Create a timestamped backup filename
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = f"{MYSQL_DB}_backup_{timestamp}.sql"

cmd = [
    'mysqldump',
    '-h', MYSQL_HOST,
    '-u', MYSQL_USER,
    f'-p{MYSQL_PASSWORD}',
    MYSQL_DB
]

try:
    with open(backup_file, 'wb') as f:
        proc = subprocess.Popen(cmd, stdout=f)
        proc.communicate()
    if proc.returncode == 0:
        print(f"Backup successful: {backup_file}")
    else:
        print("Backup failed.")
except Exception as e:
    print(f"Error during backup: {e}")
