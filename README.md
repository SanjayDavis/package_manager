# Debian Package Manager

A lightweight, command-line Debian package manager written in Python that allows you to install, remove, search, and manage Debian packages directly from the official repositories.

## Features

-  **Fast package operations** with intelligent caching
-  **Search packages** by name or description
-  **Install packages** with automatic dependency resolution
-  **Remove/purge packages** safely
-  **Display detailed package information**
-  **List installed packages**
-  **Safety checks** to prevent removal of essential system packages
## Requirements

- Python 3.6+
- `sudo` privileges for package installation/removal
- Debian-based system (Debian, Ubuntu, etc.)

### Python Dependencies

```bash
pip3 install requests
```

## Installation

1. Clone or download the script:
```bash
curl -O https://raw.githubusercontent.com/yourusername/debian-pkg-manager/main/package_manager.py
chmod +x package_manager.py
```

2. Optionally, move it to your PATH:
```bash
sudo mv package_manager.py /usr/local/bin/deb-pkg-manager
```

## Usage

### Basic Syntax
```bash
python3 package_manager.py <command> [package] [options]
```

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `update` | Update package list from repositories | `python3 package_manager.py update` |
| `search` | Search for packages | `python3 package_manager.py search nginx` |
| `info` | Show detailed package information | `python3 package_manager.py info curl` |
| `install` | Install a package with dependencies | `python3 package_manager.py install curl` |
| `remove` | Remove a package | `python3 package_manager.py remove curl` |
| `list` | List all installed packages | `python3 package_manager.py list` |

### Options

| Option | Description |
|--------|-------------|
| `--no-deps` | Install package without resolving dependencies |
| `--purge` | Remove package and its configuration files |
| `--refresh` | Force refresh of package list cache |

## Examples

### Update Package List
```bash
python3 package_manager.py update
```

### Search for Packages
```bash
# Search for web servers
python3 package_manager.py search nginx

# Search for text editors
python3 package_manager.py search editor
```

### Get Package Information
```bash
python3 package_manager.py info curl
```
Output:
```
Package: curl
Version: 7.88.1-10+deb12u4
Architecture: amd64
Description: command line tool for transferring data with URL syntax
Depends: libc6, libcurl4, zlib1g
Size: 194560 bytes
```

### Install Packages
```bash
# Install with dependencies (recommended)
python3 package_manager.py install htop

# Install without dependencies
python3 package_manager.py install --no-deps htop

# Install with forced package list refresh
python3 package_manager.py install --refresh htop
```

### Remove Packages
```bash
# Remove package (keep config files)
python3 package_manager.py remove htop

# Completely remove package and config files
python3 package_manager.py remove --purge htop
```

### List Installed Packages
```bash
python3 package_manager.py list
```

## How It Works

1. **Package List Download**: Downloads the latest package list from Debian repositories
2. **Caching**: Caches the package list locally for 24 hours to improve performance
3. **Dependency Resolution**: Automatically resolves and installs package dependencies
4. **Safety Checks**: Prevents installation/removal of essential system packages
5. **Package Management**: Uses `dpkg` for actual package installation and removal

## Cache Location

Package cache is stored at: `~/.cache/deb-pkg-manager/packages_cache`

To manually clear cache:
```bash
rm -rf ~/.cache/deb-pkg-manager/
```

## Safety Features

### Blacklisted Packages
The following essential packages are protected from removal:
- `gcc-14-base`
- `libtinfo6`
- `libc6`
- `libcrypt1`
- `libstdc++6`
- `systemd`
- `linux-image`
- `base-files`
- `bash`

### Installation Checks
- Verifies package exists in repository
- Checks if package is already installed
- Validates dependencies before installation

## Troubleshooting

### Permission Denied
Make sure you have sudo privileges:
```bash
sudo python3 package_manager.py install package-name
```

### Package Not Found
Update the package list:
```bash
python3 package_manager.py update
```

### Network Issues
Check your internet connection and try again. The script will timeout after 30 seconds for downloads.

### Dependency Conflicts
If you encounter dependency conflicts, try:
```bash
sudo apt --fix-broken install
```

## Limitations

- Only supports Debian stable repository
- Requires internet connection for first-time package list download
- Does not handle complex dependency conflicts automatically
- Limited to amd64 architecture packages


