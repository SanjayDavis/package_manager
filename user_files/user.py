#!/usr/bin/env python3

"""
Production-Ready Backend-Integrated Package Manager
- Smart recursive dependency resolution
- Ubuntu version compatibility checking
- System conflict protection (t64 transitions)
- Progress bars for downloads
- NO apt-get dependency - pure manual installation
- Logs everything to backend
"""

import os
import requests
import subprocess
import sys
import json
import time
import socket
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

# Try to import tqdm for progress bars
try:
    from tqdm import tqdm
    HAVE_TQDM = True
except ImportError:
    HAVE_TQDM = False
    print("Install tqdm for progress bars: pip3 install tqdm")

# Backend API Configuration
BACKEND_URL = "http://172.30.112.1:8000"
ENV_FILE = Path(".env")
CACHE_DIR = Path.home() / ".cache" / "pkg-manager"
DOWNLOAD_DIR = Path("debian_packages")

# ANSI Colors
BLUE = '\033[94m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
RESET = '\033[0m'

# System-critical packages
FORBIDDEN_PACKAGES = {
    'libc6', 'libc-bin', 'libgcc-s1', 'dpkg', 'apt', 'bash',
    'coreutils', 'systemd', 'init', 'base-files', 'ubuntu-minimal'
}


@dataclass
class InstalledPackage:
    """Represents an installed package"""
    name: str
    version: str
    architecture: str


class CredentialManager:
    """Manages user credentials in .env file"""
    
    @staticmethod
    def save_credentials(username: str, password: str):
        with open(ENV_FILE, 'w') as f:
            f.write(f"PKG_MANAGER_USER={username}\n")
            f.write(f"PKG_MANAGER_PASS={password}\n")
        os.chmod(ENV_FILE, 0o600)
        print(f"{GREEN}Credentials saved to .env file{RESET}")
    
    @staticmethod
    def load_credentials() -> tuple:
        if not ENV_FILE.exists():
            return None, None
        
        username = None
        password = None
        
        with open(ENV_FILE, 'r') as f:
            for line in f:
                if line.startswith('PKG_MANAGER_USER='):
                    username = line.split('=', 1)[1].strip()
                elif line.startswith('PKG_MANAGER_PASS='):
                    password = line.split('=', 1)[1].strip()
        
        return username, password
    
    @staticmethod
    def clear_credentials():
        if ENV_FILE.exists():
            ENV_FILE.unlink()
            print(f"{GREEN}Credentials cleared{RESET}")


class SystemPackageManager:
    """Manages system package information"""
    
    @staticmethod
    def get_installed_packages() -> Dict[str, InstalledPackage]:
        """Get all installed packages with versions"""
        installed = {}
        try:
            result = subprocess.run(
                ['dpkg-query', '-W', '-f=${Package}|${Version}|${Architecture}\n'],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.strip().split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        name, version, arch = parts[0], parts[1], parts[2]
                        installed[name] = InstalledPackage(name, version, arch)
        except subprocess.CalledProcessError:
            pass
        
        return installed
    
    @staticmethod
    def parse_version(version_str: str) -> tuple:
        """Parse version string for comparison"""
        # Remove epoch if present
        if ':' in version_str:
            version_str = version_str.split(':', 1)[1]
        
        # Split into parts
        parts = re.split(r'[.-]', version_str)
        numeric_parts = []
        
        for part in parts:
            try:
                numeric_parts.append(int(part))
            except ValueError:
                numeric_parts.append(part)
        
        return tuple(numeric_parts)


class BackendClient:
    """Client for communicating with Express backend"""
    
    def __init__(self):
        self.token = None
        self.username = None
        self.auto_login()
    
    def auto_login(self):
        username, password = CredentialManager.load_credentials()
        if username and password:
            try:
                response = requests.post(
                    f"{BACKEND_URL}/login-cli",
                    json={'username': username, 'password': password},
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    self.token = data['token']
                    self.username = username
                    print(f"{GREEN}Auto-login successful as {username}{RESET}")
                    return True
            except:
                pass
        return False
    
    def register(self, username: str, password: str) -> bool:
        try:
            response = requests.post(
                f"{BACKEND_URL}/register",
                json={'username': username, 'password': password, 'role': 'user'}
            )
            if response.status_code == 201:
                print(f"{GREEN}Registration successful!{RESET}")
                CredentialManager.save_credentials(username, password)
                return self.login(username, password)
            else:
                error_msg = response.json().get('error', 'Unknown error')
                print(f"{RED}Registration failed: {error_msg}{RESET}")
                return False
        except Exception as e:
            print(f"{RED}Error connecting to backend: {str(e)}{RESET}")
            return False
    
    def login(self, username: str, password: str) -> bool:
        try:
            response = requests.post(
                f"{BACKEND_URL}/login-cli",
                json={'username': username, 'password': password}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data['token']
                self.username = username
                CredentialManager.save_credentials(username, password)
                print(f"{GREEN}Login successful!{RESET}")
                return True
            else:
                print(f"{RED}Login failed: {response.json().get('error', 'Unknown error')}{RESET}")
                return False
        except Exception as e:
            print(f"{RED}Error connecting to backend: {str(e)}{RESET}")
            return False
    
    def search_packages(self, query: str) -> List[dict]:
        if not self.token:
            print(f"{RED}Not logged in. Run: python3 test.py register <username> <password>{RESET}")
            return []
        
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/packages",
                params={'search': query, 'page': 1},
                headers={'Authorization': f'Bearer {self.token}'}
            )
            if response.status_code == 200:
                return response.json()['data']
            else:
                print(f"{RED}Error fetching packages: {response.status_code}{RESET}")
                return []
        except Exception as e:
            print(f"{RED}Error: {str(e)}{RESET}")
            return []
    
    def get_package_info(self, pkg_name: str) -> Optional[dict]:
        if not self.token:
            return None
        
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/packages",
                params={'search': pkg_name, 'page': 1},
                headers={'Authorization': f'Bearer {self.token}'}
            )
            if response.status_code == 200:
                packages = response.json()['data']
                for pkg in packages:
                    if pkg['name'] == pkg_name:
                        return pkg
            return None
        except Exception as e:
            print(f"{RED}Error: {str(e)}{RESET}")
            return None
    
    def get_dependencies(self, pkg_name: str) -> List[Tuple[str, str]]:
        """Get list of dependencies for a package"""
        if not self.token:
            return []
        
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/dependencies",
                params={'search': pkg_name, 'page': 1},
                headers={'Authorization': f'Bearer {self.token}'}
            )
            if response.status_code == 200:
                data = response.json()['data']
                deps = []
                for item in data:
                    if item['package_name'] == pkg_name:
                        deps.append((item['dependency_name'], item.get('version_constraint', '')))
                return deps
        except:
            pass
        
        return []
    
    def log_download(self, pkg_name: str, version: str, download_duration: float, 
                     install_duration: float, download_status: str, install_status: str):
        if not self.token:
            return
        
        try:
            hostname = socket.gethostname()
            client_ip = socket.gethostbyname(hostname)
            
            response = requests.post(
                f"{BACKEND_URL}/api/log-download",
                json={
                    'user_id': self.username,
                    'package_name': pkg_name,
                    'version': version,
                    'download_duration_seconds': round(download_duration, 2),
                    'install_duration_seconds': round(install_duration, 2),
                    'client_ip': client_ip,
                    'download_status': download_status,
                    'install_status': install_status
                },
                headers={'Authorization': f'Bearer {self.token}'}
            )
        except Exception as e:
            print(f"{YELLOW}Warning: Could not log download: {str(e)}{RESET}")


class PackageManager:
    """Package manager with recursive dependency resolution"""
    
    def __init__(self):
        self.backend = BackendClient()
        self.installed_packages = SystemPackageManager.get_installed_packages()
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def search(self, query: str):
        packages = self.backend.search_packages(query)
        
        if packages:
            print(f"\nFound {len(packages)} package(s):")
            for pkg in packages[:20]:
                name = pkg['name']
                status = f"{RED}[blocked]{RESET} " if self._is_forbidden(name) else ""
                installed = f"{GREEN}[installed]{RESET} " if self._is_installed(name) else ""
                print(f"\n{BOLD}{status}{installed}{name}{RESET} - {pkg.get('version', '?')}")
                print(f"  Arch: {pkg.get('architecture', '?')}")
            
            if len(packages) > 20:
                print(f"\n...and {len(packages) - 20} more matches")
        else:
            print(f"{RED}No packages found matching '{query}'{RESET}")
    
    def info(self, pkg_name: str):
        pkg = self.backend.get_package_info(pkg_name)
        
        if not pkg:
            print(f"{RED}Package '{pkg_name}' not found{RESET}")
            return
        
        print(f"\n{'='*70}")
        print(f"Package: {pkg_name}")
        print(f"{'='*70}\n")
        
        if self._is_forbidden(pkg_name):
            print(f"{RED}BLOCKED: This is a system-critical package{RESET}")
            print("Cannot be installed via this tool\n")
        
        if self._is_installed(pkg_name):
            installed_pkg = self.installed_packages[pkg_name]
            print(f"{GREEN}Status: Installed{RESET}")
            print(f"Installed Version: {installed_pkg.version}")
        
        print(f"Available Version: {pkg.get('version', 'unknown')}")
        print(f"Architecture: {pkg.get('architecture', 'unknown')}")
        print(f"Filename: {pkg.get('filename', 'unknown')}\n")
        
        # Show dependencies
        deps = self.backend.get_dependencies(pkg_name)
        if deps:
            print(f"Dependencies ({len(deps)}):")
            for dep_name, version_constraint in deps[:10]:
                if self._is_installed(dep_name):
                    print(f"  {GREEN}✓{RESET} {dep_name} {version_constraint or ''}")
                else:
                    print(f"  {RED}✗{RESET} {dep_name} {version_constraint or ''}")
            if len(deps) > 10:
                print(f"  ... and {len(deps) - 10} more")
    
    def install(self, pkg_name: str, recursive=True):
        """Install package with automatic dependency resolution"""
        if not self.backend.token:
            print(f"{RED}Not logged in. Run: python3 test.py register <username> <password>{RESET}")
            return False
        
        # Check Ubuntu version compatibility
        ubuntu_version = self._get_ubuntu_version()
        pkg = self.backend.get_package_info(pkg_name)
        
        if ubuntu_version == 'noble' and pkg:
            # Check if the package version looks like Jammy (22.04)
            if 'ubuntu1' in pkg['version'] and '24.04' not in pkg['version']:
                print(f"\n{YELLOW}{'='*70}{RESET}")
                print(f"{YELLOW}WARNING: Package Database Mismatch{RESET}")
                print(f"{YELLOW}{'='*70}{RESET}")
                print(f"Your system: Ubuntu 24.04 (Noble)")
                print(f"Package version: {pkg['version']} (possibly from Jammy)")
                print(f"\nThis MAY cause conflicts with system libraries (t64 transitions).")
                print(f"If issues occur, ask admin to verify package database version.\n")
                response = input("Continue? (yes/no): ").strip().lower()
                if response not in ['yes', 'y']:
                    print(f"{GREEN}Installation cancelled.{RESET}")
                    return False
        
        # Safety checks
        if self._is_forbidden(pkg_name):
            print(f"{RED}Error: '{pkg_name}' is a protected system package{RESET}")
            return False
        
        if self._is_installed(pkg_name) and recursive:
            print(f"{YELLOW}'{pkg_name}' is already installed{RESET}")
            print(f"Installed version: {self.installed_packages[pkg_name].version}")
            response = input("Reinstall anyway? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                return True
        
        # Get package info
        pkg = self.backend.get_package_info(pkg_name)
        if not pkg:
            print(f"{RED}Package '{pkg_name}' not found in repository{RESET}")
            return False
        
        # Resolve dependencies
        if recursive:
            print(f"\n{BLUE}Analyzing dependencies for {pkg_name}...{RESET}")
            deps_to_install = self._resolve_dependencies(pkg_name)
            
            if deps_to_install:
                print(f"\n{YELLOW}Need to install {len(deps_to_install)} dependencies:{RESET}")
                for dep in deps_to_install:
                    print(f"  - {dep}")
                
                response = input(f"\nContinue with installation? (yes/no): ").strip().lower()
                if response not in ['yes', 'y']:
                    print("Installation cancelled")
                    return False
                
                # Install dependencies first
                print(f"\n{BLUE}Installing dependencies...{RESET}")
                failed_deps = []
                for dep_name in deps_to_install:
                    print(f"\n{BLUE}→ Installing dependency: {dep_name}{RESET}")
                    if not self._install_single(dep_name):
                        failed_deps.append(dep_name)
                        print(f"{YELLOW}Warning: Failed to install dependency: {dep_name}{RESET}")
                
                if failed_deps:
                    print(f"\n{YELLOW}Some dependencies failed to install:{RESET}")
                    for dep in failed_deps:
                        print(f"  - {dep}")
                    response = input(f"\nContinue installing {pkg_name} anyway? (yes/no): ").strip().lower()
                    if response not in ['yes', 'y']:
                        print("Installation cancelled")
                        return False
            else:
                print(f"{GREEN}All dependencies satisfied{RESET}")
                response = input(f"\nInstall {pkg_name} ({pkg['version']})? (yes/no): ").strip().lower()
                if response not in ['yes', 'y']:
                    print("Installation cancelled")
                    return False
        
        # Install main package
        print(f"\n{BLUE}→ Installing main package: {pkg_name}{RESET}")
        return self._install_single(pkg_name)
    
    def _resolve_dependencies(self, pkg_name: str, visited: Optional[Set[str]] = None) -> List[str]:
        """Recursively resolve all dependencies"""
        if visited is None:
            visited = set()
        
        if pkg_name in visited:
            return []
        
        visited.add(pkg_name)
        to_install = []
        
        # Get dependencies
        deps = self.backend.get_dependencies(pkg_name)
        
        for dep_name, version_constraint in deps:
            # Skip if forbidden
            if self._is_forbidden(dep_name):
                continue
            
            # Smart skip for installed/compatible packages
            if self._should_skip_dependency(dep_name, version_constraint):
                continue
            
            # Recursively resolve dependencies of this dependency
            sub_deps = self._resolve_dependencies(dep_name, visited)
            for sub_dep in sub_deps:
                if sub_dep not in to_install:
                    to_install.append(sub_dep)
            
            # Add this dependency
            if dep_name not in to_install:
                to_install.append(dep_name)
        
        return to_install
    
    def _should_skip_dependency(self, dep_name: str, version_constraint: str) -> bool:
        """Check if we should skip installing a dependency"""
        if not self._is_installed(dep_name):
            # Check if a t64 version is installed
            t64_name = dep_name + 't64'
            if t64_name in self.installed_packages:
                print(f"  {GREEN}✓ Using system {t64_name} (t64 transition){RESET}")
                return True
            return False
        
        installed_version = self.installed_packages[dep_name].version
        
        # If version constraint is satisfied, skip
        if version_constraint and self._check_version_constraint(installed_version, version_constraint):
            print(f"  {GREEN}✓ {dep_name} already satisfied ({installed_version}){RESET}")
            return True
        
        # Version mismatch warning
        if version_constraint:
            print(f"  {YELLOW}Warning: {dep_name} version mismatch{RESET}")
            print(f"    Installed: {installed_version}")
            print(f"    Required: {version_constraint}")
        
        return True  # Use existing version anyway
    
    def _check_version_constraint(self, installed_version: str, constraint: str) -> bool:
        """Check if installed version satisfies constraint"""
        try:
            if '=' in constraint:
                required = constraint.split('=')[-1].strip().strip(')')
                inst_parts = installed_version.split('.')[:2]
                req_parts = required.split('.')[:2]
                return inst_parts == req_parts
            elif '>=' in constraint:
                required = constraint.split('>=')[-1].strip().strip(')')
                return SystemPackageManager.parse_version(installed_version) >= \
                       SystemPackageManager.parse_version(required)
            elif '<<' in constraint:
                required = constraint.split('<<')[-1].strip().strip(')')
                return SystemPackageManager.parse_version(installed_version) < \
                       SystemPackageManager.parse_version(required)
            return True
        except:
            return True
    
    def _install_single(self, pkg_name: str) -> bool:
        """Install a single package without dependency resolution"""
        pkg = self.backend.get_package_info(pkg_name)
        
        if not pkg:
            print(f"  {RED}Package '{pkg_name}' not found in repository{RESET}")
            return False
        
        # Check for system conflicts
        if self._would_break_system(pkg_name):
            print(f"  {RED}✗ Cannot install {pkg_name} - would break system packages{RESET}")
            print(f"  {YELLOW}This package conflicts with newer system libraries (t64){RESET}")
            return False
        
        download_start = time.time()
        download_status = "success"
        install_status = "failed"
        install_duration = 0
        
        try:
            # Download
            filename = pkg['filename']
            url = f"http://archive.ubuntu.com/ubuntu/{filename}"
            deb_path = DOWNLOAD_DIR / os.path.basename(filename)
            
            print(f"  {BLUE}Downloading{RESET} {pkg_name}...")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            if HAVE_TQDM and total_size > 0:
                with open(deb_path, 'wb') as f:
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"    {pkg_name}", 
                             bar_format='    {desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}') as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                            pbar.update(len(chunk))
            else:
                with open(deb_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r    Progress: {percent:.1f}%", end='', flush=True)
                if not HAVE_TQDM:
                    print()
            
            download_duration = time.time() - download_start
            print(f"  {GREEN}Downloaded in {download_duration:.2f}s{RESET}")
            
            # Install
            install_start = time.time()
            print(f"  {BLUE}Installing{RESET} {pkg_name}...")
            
            result = subprocess.run(
                ['sudo', 'dpkg', '-i', str(deb_path)],
                capture_output=True,
                text=True
            )
            
            install_duration = time.time() - install_start
            
            if result.returncode == 0:
                print(f"  {GREEN}✓ Installed successfully in {install_duration:.2f}s{RESET}")
                install_status = "success"
                self.installed_packages = SystemPackageManager.get_installed_packages()
            else:
                print(f"  {RED}✗ Installation failed{RESET}")
                if 'breaks' in result.stderr.lower() or 'conflicts' in result.stderr.lower():
                    print(f"  {RED}Package conflicts with existing system packages{RESET}")
                error_lines = result.stderr.split('\n')[:3]
                for line in error_lines:
                    if line.strip():
                        print(f"  {YELLOW}{line.strip()}{RESET}")
            
            # Clean up
            if deb_path.exists():
                os.remove(deb_path)
                
        except Exception as e:
            download_status = "failed"
            download_duration = time.time() - download_start
            print(f"  {RED}Error: {str(e)}{RESET}")
        finally:
            # Log to backend
            self.backend.log_download(
                pkg_name=pkg_name,
                version=pkg['version'],
                download_duration=download_duration,
                install_duration=install_duration if install_status == "success" else 0,
                download_status=download_status,
                install_status=install_status
            )
        
        return install_status == "success"
    
    def _would_break_system(self, pkg_name: str) -> bool:
        """Check if installing this package would break system packages"""
        # Common t64 conflicts in Ubuntu 24.04
        t64_conflicts = {
            'libpcap0.8': 'libpcap0.8t64',
            'libssl3': 'libssl3t64',
            'libgcc-s1': 'libgcc-s1t64',
            'libc6': 'libc6t64',
        }
        
        if pkg_name in t64_conflicts:
            t64_version = t64_conflicts[pkg_name]
            if t64_version in self.installed_packages:
                return True
        
        return False
    
    def _get_ubuntu_version(self) -> str:
        """Detect Ubuntu version"""
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('VERSION_CODENAME='):
                        return line.split('=')[1].strip()
        except:
            pass
        return 'unknown'
    
    def _is_forbidden(self, pkg_name: str) -> bool:
        return pkg_name in FORBIDDEN_PACKAGES
    
    def _is_installed(self, pkg_name: str) -> bool:
        return pkg_name in self.installed_packages


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Production Package Manager")
    parser.add_argument('command', choices=['register', 'login', 'logout', 'install', 'search', 'info'])
    parser.add_argument('arg1', nargs='?', help='username or package name')
    parser.add_argument('arg2', nargs='?', help='password')
    
    args = parser.parse_args()
    
    if len(sys.argv) == 1:
        parser.print_help()
        print(f"\n{YELLOW}First time? Run: python3 test.py register <username> <password>{RESET}")
        print(f"{YELLOW}Commands:{RESET}")
        print(f"  register <username> <password>  - Create new account")
        print(f"  login <username> <password>     - Login")
        print(f"  search <query>                  - Search packages")
        print(f"  info <package>                  - Show package info")
        print(f"  install <package>               - Install package with dependencies")
        print(f"  logout                          - Logout")
        return
    
    mgr = PackageManager()
    
    try:
        if args.command == 'register':
            if not args.arg1:
                username = input("Username: ")
                password = input("Password: ")
            else:
                username = args.arg1
                password = args.arg2 or input("Password: ")
            mgr.backend.register(username, password)
        
        elif args.command == 'login':
            if not args.arg1:
                username = input("Username: ")
                password = input("Password: ")
            else:
                username = args.arg1
                password = args.arg2 or input("Password: ")
            mgr.backend.login(username, password)
        
        elif args.command == 'logout':
            CredentialManager.clear_credentials()
            print(f"{GREEN}Logged out successfully{RESET}")
        
        elif args.command == 'install':
            if not args.arg1:
                print("Package name required")
                return
            mgr.install(args.arg1)
        
        elif args.command == 'search':
            if not args.arg1:
                print("Search query required")
                return
            mgr.search(args.arg1)
        
        elif args.command == 'info':
            if not args.arg1:
                print("Package name required")
                return
            mgr.info(args.arg1)
    
    except KeyboardInterrupt:
        print("\n\nCancelled")


if __name__ == "__main__":
    main()
