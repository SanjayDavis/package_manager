#!/usr/bin/env python3
import os
import gzip
import requests
import subprocess
import shutil
import re
import argparse
import sys
from pathlib import Path

BASE_URL = "http://deb.debian.org/debian/dists/stable/main/binary-amd64/"
PACKAGES_GZ = "Packages.gz"
PACKAGES_FILE = "Packages"
DOWNLOAD_DIR = "Downloaded_packages"

BLACKLISTED_PACKAGES = {
    "gcc-14-base",
    "libtinfo6",
    "libc6",
    "libcrypt1",
    "libstdc++6",
    "systemd",
    "linux-image",
    "base-files",
    "bash",
    "essential"
}


class DebianPackageManager:
    def __init__(self):
        self.packages = {}
        self.cache_file = Path.home() / ".cache" / "deb-pkg-manager" / "packages_cache"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

    def download_packages_file(self, force_refresh=False):
        if not force_refresh and self.cache_file.exists() and self._is_cache_fresh():
            print("Using cached package list...")
            return self._load_cache()
        
        print("Downloading package list...")
        url = BASE_URL + PACKAGES_GZ
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"Error downloading package list: {e}")
            return False

        with open(PACKAGES_GZ, "wb") as f:
            f.write(r.content)

        try:
            with gzip.open(PACKAGES_GZ, "rb") as f_in, open(PACKAGES_FILE, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        except Exception as e:
            print(f"Error extracting package list: {e}")
            return False

        self.packages = self._parse_packages()
        self._save_cache()
        return True

    def _is_cache_fresh(self):
        import time
        return (time.time() - self.cache_file.stat().st_mtime) < 86400

    def _save_cache(self):
        import pickle
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.packages, f)

    def _load_cache(self):
        import pickle
        try:
            with open(self.cache_file, 'rb') as f:
                self.packages = pickle.load(f)
            return True
        except Exception as e:
            print(f"Error loading cache: {e}")
            return False

    def _parse_packages(self):
        packages = {}
        try:
            with open(PACKAGES_FILE, "r", encoding="utf-8", errors="ignore") as f:
                block = {}
                for line in f:
                    line = line.strip()
                    if not line:
                        if "Package" in block and "Filename" in block:
                            packages[block["Package"]] = block
                        block = {}
                    else:
                        if ":" in line:
                            key, _, value = line.partition(":")
                            block[key.strip()] = value.strip()
        except Exception as e:
            print(f"Error parsing packages file: {e}")
        return packages

    def search_packages(self, query):
        if not self.packages:
            print("Package list not loaded. Run with --refresh first.")
            return

        matches = []
        query_lower = query.lower()
        
        for pkg_name, pkg_info in self.packages.items():
            if query_lower in pkg_name.lower():
                matches.append((pkg_name, pkg_info.get("Description", "").split('\n')[0]))
            elif query_lower in pkg_info.get("Description", "").lower():
                matches.append((pkg_name, pkg_info.get("Description", "").split('\n')[0]))

        if matches:
            print(f"Found {len(matches)} package(s):")
            for name, desc in sorted(matches)[:20]: 
                print(f"  {name}: {desc}")
            if len(matches) > 20:
                print(f"  ... and {len(matches) - 20} more")
        else:
            print(f"No packages found matching '{query}'")

    def show_package_info(self, pkg_name):
        if pkg_name not in self.packages:
            print(f"Package '{pkg_name}' not found")
            return

        pkg = self.packages[pkg_name]
        print(f"Package: {pkg_name}")
        print(f"Version: {pkg.get('Version', 'Unknown')}")
        print(f"Architecture: {pkg.get('Architecture', 'Unknown')}")
        print(f"Description: {pkg.get('Description', 'No description available')}")
        print(f"Depends: {pkg.get('Depends', 'None')}")
        print(f"Size: {pkg.get('Size', 'Unknown')} bytes")

    def resolve_dependencies(self, pkg_name, resolved=None, seen=None):
        if resolved is None:
            resolved = []
        if seen is None:
            seen = set()

        if pkg_name in seen or pkg_name in BLACKLISTED_PACKAGES:
            return resolved
        
        seen.add(pkg_name)

        if pkg_name not in self.packages:
            print(f"Warning: Package {pkg_name} not found in repository")
            return resolved

        deps_str = self.packages[pkg_name].get("Depends", "")
        if deps_str:
            deps = []
            for dep in deps_str.split(","):
                dep = dep.strip()
                if dep:
                    alternatives = [d.strip() for d in dep.split("|")]
                    main_dep = re.split(r'\s*[\(\<\>\=]', alternatives[0])[0].strip()
                    if main_dep and main_dep not in BLACKLISTED_PACKAGES:
                        deps.append(main_dep)
            
            for dep in deps:
                self.resolve_dependencies(dep, resolved, seen)

        if pkg_name not in resolved:
            resolved.append(pkg_name)
        
        return resolved

    def is_package_installed(self, pkg_name):
        try:
            result = subprocess.run(
                ["dpkg", "-l", pkg_name], 
                capture_output=True, 
                text=True, 
                check=False
            )
            return result.returncode == 0 and "ii" in result.stdout
        except Exception:
            return False

    def install_package(self, pkg_name, resolve_deps=True):
        if not self.packages:
            print("Package list not loaded. Run with --refresh first.")
            return False

        if pkg_name not in self.packages:
            print(f"Package '{pkg_name}' not found in repository")
            return False

        if pkg_name in BLACKLISTED_PACKAGES:
            print(f"Package '{pkg_name}' is blacklisted and cannot be installed")
            return False

        if self.is_package_installed(pkg_name):
            print(f"Package '{pkg_name}' is already installed")
            return True

        packages_to_install = []
        if resolve_deps:
            print(f"Resolving dependencies for {pkg_name}...")
            packages_to_install = self.resolve_dependencies(pkg_name)
            print(f"Packages to install: {', '.join(packages_to_install)}")
        else:
            packages_to_install = [pkg_name]

        packages_to_install = [p for p in packages_to_install if not self.is_package_installed(p)]
        
        if not packages_to_install:
            print("All required packages are already installed")
            return True

        print(f"Installing {len(packages_to_install)} package(s)...")
        
        success = True
        for pkg in packages_to_install:
            if not self._download_and_install_single(pkg):
                success = False

        return success

    def _download_and_install_single(self, pkg_name):
        """Download and install a single package"""
        if pkg_name not in self.packages:
            print(f"Package {pkg_name} not found in repository")
            return False

        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        
        filename = self.packages[pkg_name]["Filename"]
        url = BASE_URL.replace("dists/stable/main/binary-amd64/", "") + filename
        deb_path = os.path.join(DOWNLOAD_DIR, os.path.basename(filename))

        if not os.path.exists(deb_path):
            print(f"Downloading {pkg_name}...")
            try:
                r = requests.get(url, timeout=30)
                r.raise_for_status()
                with open(deb_path, "wb") as f:
                    f.write(r.content)
            except requests.RequestException as e:
                print(f"Error downloading {pkg_name}: {e}")
                return False

        print(f"Installing {pkg_name}...")
        try:
            subprocess.run(["sudo", "dpkg", "-i", deb_path], check=True, capture_output=True)
            print(f" Package {pkg_name} installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f" Package {pkg_name} failed to install")
            if e.stderr:
                print(f"Error: {e.stderr.decode()}")
            return False

    def remove_package(self, pkg_name, purge=False):
        if not self.is_package_installed(pkg_name):
            print(f"Package '{pkg_name}' is not installed")
            return False

        if pkg_name in BLACKLISTED_PACKAGES:
            print(f"Package '{pkg_name}' is essential and cannot be removed")
            return False

        action = "purge" if purge else "remove"
        print(f"{'Purging' if purge else 'Removing'} package {pkg_name}...")
        
        try:
            subprocess.run(["sudo", "dpkg", f"--{action}", pkg_name], check=True)
            print(f" Package {pkg_name} {'purged' if purge else 'removed'} successfully")
            return True
        except subprocess.CalledProcessError:
            print(f" Failed to {'purge' if purge else 'remove'} package {pkg_name}")
            return False

    def list_installed(self):
        try:
            result = subprocess.run(
                ["dpkg", "-l"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            print("Installed packages:")
            for line in result.stdout.split('\n'):
                if line.startswith('ii'):
                    parts = line.split()
                    if len(parts) >= 3:
                        print(f"  {parts[1]} ({parts[2]})")
        except subprocess.CalledProcessError:
            print("Error listing installed packages")

    def cleanup(self):
        files_to_remove = [PACKAGES_GZ, PACKAGES_FILE]
        dirs_to_remove = [DOWNLOAD_DIR]
        
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        for dir_path in dirs_to_remove:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)


def main():
    parser = argparse.ArgumentParser(description="Debian Package Manager")
    parser.add_argument("command", choices=["install", "remove", "search", "info", "list", "update"], 
                       help="Command to execute")
    parser.add_argument("package", nargs="?", help="Package name")
    parser.add_argument("--no-deps", action="store_true", 
                       help="Don't resolve dependencies when installing")
    parser.add_argument("--purge", action="store_true", 
                       help="Purge package (remove config files too)")
    parser.add_argument("--refresh", action="store_true", 
                       help="Force refresh of package list")

    args = parser.parse_args()
    
    if len(sys.argv) == 1:
        parser.print_help()
        return

    manager = DebianPackageManager()

    try:
        if args.command == "update" or args.refresh:
            if not manager.download_packages_file(force_refresh=True):
                print("Failed to update package list")
                return
            print("Package list updated successfully")
            if args.command == "update":
                return

        elif args.command in ["install", "search", "info"]:
            if not manager.download_packages_file():
                print("Failed to load package list")
                return

        if args.command == "install":
            if not args.package:
                print("Package name required for install command")
                return
            manager.install_package(args.package, resolve_deps=not args.no_deps)
        
        elif args.command == "remove":
            if not args.package:
                print("Package name required for remove command")
                return
            manager.remove_package(args.package, purge=args.purge)
        
        elif args.command == "search":
            if not args.package:
                print("Search query required for search command")
                return
            manager.search_packages(args.package)
        
        elif args.command == "info":
            if not args.package:
                print("Package name required for info command")
                return
            manager.show_package_info(args.package)
        
        elif args.command == "list":
            manager.list_installed()

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    finally:
        manager.cleanup()


if __name__ == "__main__":
    main()
