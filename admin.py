import gzip
import requests
import mysql.connector
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from dotenv import load_dotenv
import os

# Load env variables from .env file
load_dotenv()

MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')

PACKAGES_GZ_URL = "http://archive.ubuntu.com/ubuntu/dists/jammy/main/binary-amd64/Packages.gz"

# -- Your parse_dependencies, insert_package, insert_dependencies, update_packages_and_dependencies functions remain unchanged --

def parse_dependencies(dep_string):
    dependencies = []
    if dep_string:
        for dep in dep_string.split(","):
            parts = dep.strip().split()
            name = parts[0]
            version = None
            if len(parts) > 1:
                version = ' '.join(parts[1:]).replace('(', '').replace(')', '')
            dependencies.append((name, version))
    return dependencies

def insert_package(cursor, package):
    sql = """
        INSERT INTO Packages
            (name, version, architecture, filename, maintainer, description, homepage, md5sum, sha256, section, priority, size)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            maintainer=VALUES(maintainer), description=VALUES(description), homepage=VALUES(homepage),
            md5sum=VALUES(md5sum), sha256=VALUES(sha256), section=VALUES(section),
            priority=VALUES(priority), size=VALUES(size)
    """
    values = (
        package.get('Package'), package.get('Version'), package.get('Architecture'),
        package.get('Filename'), package.get('Maintainer'), package.get('Description'),
        package.get('Homepage'), package.get('MD5sum'), package.get('SHA256'),
        package.get('Section'), package.get('Priority'), int(package.get('Size', 0))
    )
    cursor.execute(sql, values)
    if cursor.lastrowid != 0:
        return cursor.lastrowid
    cursor.execute(
        "SELECT id FROM Packages WHERE name=%s AND version=%s AND architecture=%s",
        (package.get('Package'), package.get('Version'), package.get('Architecture'))
    )
    return cursor.fetchone()[0]

def insert_dependencies(cursor, package_id, depends):
    cursor.execute("DELETE FROM Dependencies WHERE package_id = %s", (package_id,))
    for dep_name, version in parse_dependencies(depends):
        version = version[:1000] if version else None
        cursor.execute(
            "INSERT INTO Dependencies (package_id, dependency_name, version_constraint) VALUES (%s, %s, %s)",
            (package_id, dep_name, version)
        )

def update_packages_and_dependencies(status_callback=None):
    if status_callback:
        status_callback("Downloading Packages.gz...")
    response = requests.get(PACKAGES_GZ_URL)
    response.raise_for_status()
    file_content = gzip.decompress(response.content).decode()

    conn = mysql.connector.connect(
        host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB
    )
    cursor = conn.cursor()

    package = {}
    if status_callback:
        status_callback("Parsing and uploading packages...")
    for line in file_content.splitlines():
        if not line.strip():
            if 'Package' in package and 'Version' in package:
                package_id = insert_package(cursor, package)
                if package.get('Depends'):
                    insert_dependencies(cursor, package_id, package.get('Depends'))
                package = {}
            continue
        if ':' in line:
            key, value = line.split(':', 1)
            package[key.strip()] = value.strip()
        else:
            if package and key:
                package[key] += '\n' + line.strip()
    conn.commit()
    cursor.close()
    conn.close()
    if status_callback:
        status_callback("Update complete.")

class AdminGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Package Manager Admin Interface")
        self.geometry("900x600")
        self.configure(padx=15, pady=15)
        self.style = ttk.Style(self)
        self.setup_style()

        # Top frame
        top_frame = ttk.Frame(self)
        top_frame.pack(fill='x', pady=(0, 15))

        # Buttons with custom style
        self.view_var = tk.StringVar(value="Packages")
        self.packages_btn = ttk.Button(top_frame, text="Packages Table", command=self.show_packages, style='Rounded.TButton')
        self.packages_btn.pack(side='left', padx=5)
        self.dependencies_btn = ttk.Button(top_frame, text="Dependencies Table", command=self.show_dependencies, style='Rounded.TButton')
        self.dependencies_btn.pack(side='left', padx=5)

        # Search label and entry
        ttk.Label(top_frame, text="Search:").pack(side='left', padx=(20, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.update_search)
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side='left')

        # Treeview frame with scrollbars
        tree_frame = ttk.Frame(self)
        tree_frame.pack(expand=True, fill='both')

        self.tree = ttk.Treeview(tree_frame, show='headings')
        self.tree.pack(side='left', expand=True, fill='both')

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        hsb.pack(side='bottom', fill='x')

        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self, textvariable=self.status_var, font=('Segoe UI', 10, 'italic'))
        self.status_label.pack(anchor='w', pady=(10, 0))

        # Update button
        update_btn = ttk.Button(self, text="Update Packages & Dependencies", command=self.start_update, style='Rounded.TButton')
        update_btn.pack(pady=15)

        # Load default view
        self.current_table = "Packages"
        self.show_packages()

    def setup_style(self):
        self.style.theme_use('clam')
        self.style.configure('Rounded.TButton',
                             font=('Segoe UI', 10, 'bold'),
                             foreground='white',
                             background='#007acc',
                             borderwidth=0,
                             focuscolor='none',
                             padding=10)
        self.style.map('Rounded.TButton',
                       background=[('active', '#005f99'), ('disabled', '#cccccc')])
        self.style.configure('Treeview.Heading',
                             font=('Segoe UI', 10, 'bold'))
        self.style.configure('Treeview',
                             font=('Segoe UI', 9),
                             rowheight=25)

    def set_status(self, message):
        self.status_var.set(message)
        self.update_idletasks()

    def start_update(self):
        thread = threading.Thread(target=self.do_update)
        thread.start()

    def do_update(self):
        try:
            update_packages_and_dependencies(status_callback=self.set_status)
            self.load_table()
            messagebox.showinfo("Success", "Packages and dependencies updated successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_table(self, filter_str=None):
        try:
            conn = mysql.connector.connect(
                host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB
            )
            cursor = conn.cursor()

            if self.current_table == "Packages":
                columns = ("ID", "Name", "Version", "Architecture", "Filename")
                self.tree.config(columns=columns)
                for col in columns:
                    self.tree.heading(col, text=col)
                    self.tree.column(col, minwidth=50, width=150, stretch=True)

                if filter_str:
                    query = "SELECT id, name, version, architecture, filename FROM Packages WHERE name LIKE %s ORDER BY name ASC"
                    cursor.execute(query, (f"%{filter_str}%",))
                else:
                    query = "SELECT id, name, version, architecture, filename FROM Packages ORDER BY name ASC"
                    cursor.execute(query)

                rows = cursor.fetchall()

            else:  # Dependencies table
                columns = ("ID", "Package ID", "Dependency Name", "Version Constraint")
                self.tree.config(columns=columns)
                for col in columns:
                    self.tree.heading(col, text=col)
                    self.tree.column(col, minwidth=50, width=200, stretch=True)

                if filter_str:
                    query = "SELECT id, package_id, dependency_name, version_constraint FROM Dependencies WHERE dependency_name LIKE %s ORDER BY dependency_name ASC"
                    cursor.execute(query, (f"%{filter_str}%",))
                else:
                    query = "SELECT id, package_id, dependency_name, version_constraint FROM Dependencies ORDER BY dependency_name ASC"
                    cursor.execute(query)

                rows = cursor.fetchall()

            cursor.close()
            conn.close()

            self.tree.delete(*self.tree.get_children())
            for row in rows:
                self.tree.insert("", "end", values=row)

            self.set_status(f"Loaded {len(rows)} records from {self.current_table} table.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load {self.current_table}:\n{e}")

    def show_packages(self):
        self.current_table = "Packages"
        self.search_entry.config(state='normal')
        self.search_var.set("")
        self.load_table()

    def show_dependencies(self):
        self.current_table = "Dependencies"
        self.search_entry.config(state='normal')
        self.search_var.set("")
        self.load_table()

    def update_search(self, *args):
        search_term = self.search_var.get()
        self.load_table(search_term)


if __name__ == "__main__":
    app = AdminGUI()
    app.mainloop()
