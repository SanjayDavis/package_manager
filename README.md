# Package Manager

A minimal **custom package manager** built in Python to handle software installation from Debian repositories.
This project explores how package management works under the hood by implementing key features such as:

## Features

* **Fetch Package Metadata** – Downloads and parses Debian `Packages.gz` files.
* **Dependency Resolution** – Detects and resolves dependencies before installation.
* **Package Download & Install** – Fetches `.deb` files and installs them using `dpkg`.
* **Progress Tracking** – Displays a progress bar during downloads/updates.
* **Error Handling** – Detects broken installs and allows reinstallation or fixing missing dependencies.

## Why This Project?

Modern package managers like `apt`, `pacman`, or `dnf` are powerful but complex.
This project focuses on learning the **internals of package managers** by building a simplified version from scratch.

## Requirements

* Python 3.8+
* Linux (Debian/Ubuntu-based)
* `dpkg` installed

## Usage

```bash
# Run package fetch and installation
python3 main.py <package-name>
```
