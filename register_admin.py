\

import mysql.connector
import bcrypt
import getpass
import sys
from dotenv import load_dotenv
import os

load_dotenv('backend/.env')

MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print application header"""
    print("=" * 60)
    print("      PACKAGE MANAGER - ADMIN REGISTRATION SYSTEM")
    print("=" * 60)
    print()

def connect_database():
    """Connect to MySQL database"""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        return conn
    except mysql.connector.Error as err:
        print(f"[ERROR] Database connection failed: {err}")
        print(f"\nPlease check your database configuration:")
        print(f"  Host: {MYSQL_HOST}")
        print(f"  User: {MYSQL_USER}")
        print(f"  Database: {MYSQL_DB}")
        sys.exit(1)

def check_username_exists(cursor, username):
    """Check if username already exists"""
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    return cursor.fetchone() is not None

def list_admins(cursor):
    """List all admin users"""
    cursor.execute(
        "SELECT id, username, role FROM users WHERE role = 'admin' ORDER BY id ASC"
    )
    admins = cursor.fetchall()
    
    if not admins:
        print("No admin users found in database.\n")
        return
    
    print("\nCurrent Admin Users:")
    print("-" * 60)
    print(f"{'ID':<5} {'Username':<30} {'Role':<10}")
    print("-" * 60)
    
    for admin_id, username, role in admins:
        print(f"{admin_id:<5} {username:<30} {role:<10}")
    
    print("-" * 60)
    print(f"Total: {len(admins)} admin(s)\n")

def register_admin():
    """Register a new admin user"""
    clear_screen()
    print_header()
    
    # Connect to database
    print("Connecting to database...")
    conn = connect_database()
    cursor = conn.cursor()
    print("Connected successfully!\n")
    
    # Show existing admins
    list_admins(cursor)
    
    # Get username
    while True:
        username = input("Enter admin username (or 'q' to quit): ").strip()
        
        if username.lower() == 'q':
            print("\nRegistration cancelled.")
            conn.close()
            sys.exit(0)
        
        if not username:
            print("[ERROR] Username cannot be empty.\n")
            continue
        
        if len(username) < 3:
            print("[ERROR] Username must be at least 3 characters long.\n")
            continue
        
        if check_username_exists(cursor, username):
            print(f"[ERROR] Username '{username}' already exists. Please choose another.\n")
            continue
        
        break
    
    # Get password
    while True:
        password = getpass.getpass("Enter admin password: ")
        
        if not password:
            print("[ERROR] Password cannot be empty.\n")
            continue
        
        if len(password) < 6:
            print("[ERROR] Password must be at least 6 characters long.\n")
            continue
        
        password_confirm = getpass.getpass("Confirm admin password: ")
        
        if password != password_confirm:
            print("[ERROR] Passwords do not match. Please try again.\n")
            continue
        
        break
    
    # Confirm registration
    print(f"\nRegistration Summary:")
    print(f"   Username: {username}")
    print(f"   Role: admin")
    print(f"   Database: {MYSQL_DB}")
    
    confirm = input("\nProceed with registration? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("\nRegistration cancelled.")
        conn.close()
        sys.exit(0)
    
    # Hash password
    print("\nHashing password...")
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Insert into database
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            (username, password_hash, 'admin')
        )
        conn.commit()
        
        print("\n" + "=" * 60)
        print("ADMIN REGISTRATION SUCCESSFUL!")
        print("=" * 60)
        print(f"\nAdmin user '{username}' has been created.")
        print(f"\nYou can now login at: http://localhost:3000")
        print(f"   Username: {username}")
        print(f"   Password: ********")
        print("\n" + "=" * 60 + "\n")
        
    except mysql.connector.Error as err:
        print(f"\n[ERROR] Registration failed: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def interactive_menu():
    """Interactive menu for admin management"""
    clear_screen()
    print_header()
    
    conn = connect_database()
    cursor = conn.cursor()
    
    while True:
        print("\nADMIN MANAGEMENT MENU")
        print("-" * 60)
        print("1. Register New Admin")
        print("2. List All Admins")
        print("3. Delete Admin User")
        print("4. Exit")
        print("-" * 60)
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            cursor.close()
            conn.close()
            register_admin()
            break
            
        elif choice == '2':
            list_admins(cursor)
            
        elif choice == '3':
            list_admins(cursor)
            user_id = input("\nEnter admin ID to delete (or 'c' to cancel): ").strip()
            
            if user_id.lower() == 'c':
                print("Deletion cancelled.\n")
                continue
            
            try:
                user_id = int(user_id)
                cursor.execute("SELECT username, role FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                
                if not user:
                    print(f"[ERROR] User ID {user_id} not found.\n")
                    continue
                
                username, role = user
                
                if role != 'admin':
                    print(f"[ERROR] User '{username}' is not an admin.\n")
                    continue
                
                confirm = input(f"\n[WARNING] Are you sure you want to delete admin '{username}'? (yes/no): ").strip().lower()
                
                if confirm in ['yes', 'y']:
                    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                    conn.commit()
                    print(f"\nAdmin '{username}' has been deleted.\n")
                else:
                    print("Deletion cancelled.\n")
                    
            except ValueError:
                print("[ERROR] Invalid ID. Please enter a number.\n")
            except mysql.connector.Error as err:
                print(f"[ERROR] {err}\n")
                conn.rollback()
                
        elif choice == '4':
            print("\nGoodbye!")
            cursor.close()
            conn.close()
            break
            
        else:
            print("[ERROR] Invalid choice. Please enter 1-4.\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--menu':
            interactive_menu()
        else:
            print("Usage:")
            print("  python register_admin.py          # Quick registration")
            print("  python register_admin.py --menu   # Interactive menu")
    else:
        register_admin()
