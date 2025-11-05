# User Setup Guide

## First Time Setup

### 1. Install Python Dependencies

```bash
cd user_files
pip3 install -r requirements.txt
```

### 2. Get Help

Run without arguments to see detailed help:

```bash
python3 user.py
```

Or explicitly:

```bash
python3 user.py help
```

### 3. Register an Account

```bash
python3 user.py register myusername mypassword
```

Your password will be:
- Hashed with bcrypt before storage
- Saved to `.env` file with 600 permissions
- Never stored in plain text

### 4. Use the Package Manager

After registration, you'll be auto-logged in. You can now:

```bash
# Search for packages
python3 user.py search firefox

# Get package info
python3 user.py info sl

# Install a package
python3 user.py install sl
```

## Security Features

**Bcrypt Password Hashing**
- Passwords are hashed client-side before sending to server
- Only hashed passwords are stored in `.env` file
- Backend compares hashed passwords

**Auto-Login**
- Credentials stored securely in `.env`
- Automatic authentication on subsequent runs
- Expires after 30 days (token)

**Authentication Required**
- Cannot search, info, or install without being logged in
- All actions are logged to backend for admin review

## Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `register <user> <pass>` | Create new account | `python3 user.py register john pass123` |
| `login <user> <pass>` | Login to account | `python3 user.py login john pass123` |
| `logout` | Clear credentials | `python3 user.py logout` |
| `search <query>` | Search packages | `python3 user.py search curl` |
| `info <package>` | Package details | `python3 user.py info htop` |
| `install <package>` | Install package | `python3 user.py install neofetch` |
| `help` | Show help | `python3 user.py help` |

## Notes

- **Protected Packages**: System-critical packages (libc6, bash, dpkg, etc.) cannot be installed
- **Dependencies**: Automatically resolved and installed
- **Progress Bars**: Shown during downloads (requires tqdm)
- **Logging**: All downloads/installs logged to backend
- **Ubuntu 24.04**: Handles t64 library transitions
