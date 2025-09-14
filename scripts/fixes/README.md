# HMS Enterprise Security Fix Scripts

## Overview
Automated Python scripts to address critical Bandit security issues identified in the HMS Enterprise Grade system.

## Available Fixes

1. **fix_exec_eval.py** - Replaces dangerous `eval()` with `ast.literal_eval()` and flags `exec()` for manual review
2. **fix_subprocess_shell.py** - Converts `subprocess` calls with `shell=True` to list-based arguments
3. **fix_insecure_crypto.py** - Replaces MD5/SHA1/DES with SHA256/AES equivalents
4. **fix_ftp_usage.py** - Converts FTP usage to SFTP using paramiko
5. **fix_marshal_deserialization.py** - Replaces marshal serialization with JSON

## Usage

### Run Individual Fix
```bash
cd /root/hms-enterprise-grade/scripts/fixes
python3 fix_exec_eval.py
```

### Run All Fixes
```bash
python3 run_all_fixes.py
```

## Important Notes

- **Backups**: All modified files are backed up with `.py.backup` extension
- **Healthcare Compliance**: These fixes preserve functionality while eliminating security risks
- **Manual Review**: Some complex cases (exec, complex subprocess commands) require manual intervention
- **Testing**: Always run validation tests after fixes
- **HIPAA/GDPR**: Fixes address encryption, transmission security, and injection vulnerabilities

## Execution Order
1. `fix_exec_eval.py` (RCE prevention)
2. `fix_subprocess_shell.py` (Command injection)
3. `fix_insecure_crypto.py` (Data protection)
4. `fix_ftp_usage.py` (Secure transmission)
5. `fix_marshal_deserialization.py` (Deserialization attacks)

## Dependencies
- Python 3.8+
- paramiko (for SFTP fixes): `pip install paramiko`

---
**Generated:** $(date)
**Security Impact:** Addresses 182+ critical issues automatically
