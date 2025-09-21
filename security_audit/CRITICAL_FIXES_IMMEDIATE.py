#!/usr/bin/env python3
"""
CRITICAL SECURITY FIXES - Execute Immediately
Run this script to apply critical security patches
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run command and handle errors"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def fix_encryption_key():
    """Remove hard-coded encryption key"""
    print("\n🚨 FIXING HARDCODED ENCRYPTION KEY")

    # Path to the problematic file
    file_path = Path("backend/libs/encrypted_model_fields/fields/core.py")

    if file_path.exists():
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()

        # Replace the hard-coded key with an environment variable requirement
        old_content = '''    key = os.environ.get("FERNET_KEY")
    if not key:
        key = "aQl1cJsC2OJ3n4PY9KruMCOqJpPfeNlL8A9aqXyipN4="
        os.environ["FERNET_KEY"] = key'''

        new_content = '''    key = os.environ.get("FERNET_KEY")
    if not key:
        raise ValueError("FERNET_KEY environment variable is required for encryption")'''

        if old_content in content:
            content = content.replace(old_content, new_content)

            # Backup original file
            backup_path = file_path.with_suffix('.py.backup')
            file_path.rename(backup_path)

            # Write fixed file
            with open(file_path, 'w') as f:
                f.write(content)

            print("✅ Hard-coded encryption key removed")
            print("⚠️  IMPORTANT: Set FERNET_KEY environment variable before restarting")
        else:
            print("ℹ️  Hard-coded key already removed or file changed")
    else:
        print("❌ File not found:", file_path)

def upgrade_dependencies():
    """Upgrade vulnerable dependencies"""
    print("\n🔄 UPGRADING VULNERABLE DEPENDENCIES")

    # Upgrade pip first
    run_command("python -m pip install --upgrade pip>=25.0", "Upgrading pip")

    # Upgrade mlflow to latest version
    run_command("python -m pip install --upgrade mlflow>=4.0.0", "Upgrading mlflow")

    # Run safety check again
    print("\n🔍 Running safety check after upgrades...")
    result = run_command("python -m safety check --json", "Safety check")

    if result:
        vulnerabilities = result.count('"vulnerability_id"')
        if vulnerabilities == 0:
            print("✅ No vulnerabilities found after upgrades")
        else:
            print(f"⚠️  Still {vulnerabilities} vulnerabilities remain")

def enable_database_ssl():
    """Add SSL requirement to database settings"""
    print("\n🔒 ENABLING DATABASE SSL")

    settings_files = [
        "backend/hms/settings.py",
        "backend/hms/settings/production.py"
    ]

    for settings_file in settings_files:
        if Path(settings_file).exists():
            with open(settings_file, 'r') as f:
                content = f.read()

            # Add SSL requirement if not present
            if 'sslmode' not in content:
                # Find DATABASES section
                if 'DATABASES' in content:
                    # Add SSL requirement
                    new_content = content.replace(
                        "'OPTIONS': {},",
                        "'OPTIONS': {'sslmode': 'require'},"
                    )

                    with open(settings_file, 'w') as f:
                        f.write(new_content)

                    print(f"✅ SSL requirement added to {settings_file}")

def add_authentication_rate_limiting():
    """Add rate limiting to authentication endpoints"""
    print("\n⚡ ADDING AUTHENTICATION RATE LIMITING")

    # Add django-ratelimit to requirements
    requirements_file = Path("backend/requirements.txt")
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            content = f.read()

        if 'django-ratelimit' not in content:
            with open(requirements_file, 'a') as f:
                f.write("\n# Security enhancements\ndjango-ratelimit==4.1.0\n")
            print("✅ django-ratelimit added to requirements")

    # Update settings to add rate limiting
    settings_file = Path("backend/hms/settings.py")
    if settings_file.exists():
        with open(settings_file, 'r') as f:
            content = f.read()

        if 'django-ratelimit' not in content:
            # Add to installed apps
            content = content.replace(
                "INSTALLED_APPS = [",
                "INSTALLED_APPS = [\n    'django_ratelimit',"
            )

            # Add rate limiting configuration
            rate_limiting_config = """
# Rate limiting configuration
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Authentication rate limiting
AUTH_RATELIMIT = '5/h'
LOGIN_RATELIMIT = '3/m'
PASSWORD_RESET_RATELIMIT = '2/h'

"""

            # Insert before DATABASES configuration
            if 'DATABASES =' in content:
                content = content.replace('DATABASES =', rate_limiting_config + 'DATABASES =')

            with open(settings_file, 'w') as f:
                f.write(content)

            print("✅ Rate limiting configuration added")

def reduce_session_timeout():
    """Reduce session timeout for security"""
    print("\n⏰ REDUCING SESSION TIMEOUT")

    settings_file = Path("backend/hms/settings.py")
    if settings_file.exists():
        with open(settings_file, 'r') as f:
            content = f.read()

        # Update session timeout to 15 minutes (900 seconds)
        if 'SESSION_COOKIE_AGE' in content:
            content = content.replace(
                'SESSION_COOKIE_AGE =',
                '# Reduced from default 2 weeks to 15 minutes for security\nSESSION_COOKIE_AGE ='
            )
            # Set to 15 minutes
            import re
            content = re.sub(
                r'SESSION_COOKIE_AGE\s*=\s*\d+',
                'SESSION_COOKIE_AGE = 900  # 15 minutes',
                content
            )
        else:
            # Add session timeout
            content += "\n\n# Security: Reduced session timeout\nSESSION_COOKIE_AGE = 900  # 15 minutes\n"

        with open(settings_file, 'w') as f:
            f.write(content)

        print("✅ Session timeout reduced to 15 minutes")

def create_environment_template():
    """Create secure environment template"""
    print("\n📝 CREATING SECURE ENVIRONMENT TEMPLATE")

    env_template = """# HMS Security Configuration - PRODUCTION
# Generate secure values for all secrets

# Django Settings
DJANGO_SECRET_KEY=$(openssl rand -base64 64)
DEBUG=False

# Database Security
DB_HOST=your-db-host
DB_PORT=5432
DB_NAME=hms_enterprise
DB_USER=hms_user
DB_PASSWORD=your-secure-db-password
DB_SSLMODE=require

# Encryption Keys (Generate these securely!)
FERNET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
FIELD_ENCRYPTION_KEY=$(openssl rand -hex 32)

# JWT Settings
JWT_SECRET=$(openssl rand -base64 64)
JWT_ACCESS_TOKEN_LIFETIME=15
JWT_REFRESH_TOKEN_LIFETIME=1440

# Redis
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# Email
EMAIL_HOST=your-smtp-server
EMAIL_PORT=587
EMAIL_USER=your-email-user
EMAIL_PASSWORD=your-email-password
EMAIL_USE_TLS=True

# Security Headers
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True

# CORS Settings
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com

# Monitoring and Logging
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO
"""

    with open(".env.template", "w") as f:
        f.write(env_template)

    print("✅ Secure environment template created")
    print("⚠️  Copy to .env and generate actual secure values")

def main():
    """Execute all critical fixes"""
    print("=" * 60)
    print("🚨 HMS CRITICAL SECURITY FIXES")
    print("=" * 60)
    print("\nThis script will apply immediate security patches")
    print("Backup your code before proceeding!")

    confirm = input("\nContinue with security fixes? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled")
        return

    # Execute fixes
    fix_encryption_key()
    upgrade_dependencies()
    enable_database_ssl()
    add_authentication_rate_limiting()
    reduce_session_timeout()
    create_environment_template()

    print("\n" + "=" * 60)
    print("✅ CRITICAL FIXES COMPLETED")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Generate secure environment variables")
    print("2. Restart all services")
    print("3. Verify encryption still works")
    print("4. Test authentication flow")
    print("5. Run full security scan again")
    print("\n📋 See SECURITY_AUDIT_REPORT.md for complete remediation plan")

if __name__ == "__main__":
    main()