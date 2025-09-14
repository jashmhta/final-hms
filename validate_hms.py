import json
import os
from pathlib import Path


def validate_hms_modules():
    """Comprehensive validation of HMS module implementation"""

    # List of 28 required modules from original requirements
    required_modules = [
        "Patient Registration",
        "OPD Management",
        "IPD Management",
        "Operation Theatre",
        "Emergency Department",
        "Pharmacy Management",
        "Laboratory Management",
        "Radiology Management",
        "Blood Bank Management",
        "Insurance/TPA Management",
        "Billing & Invoicing",
        "Role-Based Access Control",
        "HR and Payroll",
        "Housekeeping and Maintenance",
        "Biomedical Equipment",
        "Dietary Management",
        "Ambulance Management",
        "Patient Portal",
        "Doctor Portal",
        "E-Prescription",
        "Notification System",
        "Feedback & Complaint Management",
        "Marketing CRM",
        "Analytics and Reporting",
        "Medical Records Department",
        "NABH / JCI Compliance",
        "Advanced Backup and Disaster Recovery",
        "Cybersecurity Measures",
    ]

    # Map module names to directory patterns
    module_mapping = {
        "Patient Registration": ["patients", "registration"],
        "OPD Management": ["opd", "outpatient"],
        "IPD Management": ["ipd", "inpatient"],
        "Operation Theatre": ["ot", "operation", "theatre"],
        "Emergency Department": ["emergency", "er", "triage"],
        "Pharmacy Management": ["pharmacy"],
        "Laboratory Management": ["lab", "laboratory"],
        "Radiology Management": ["radiology"],
        "Blood Bank Management": ["blood"],
        "Insurance/TPA Management": ["insurance", "tpa"],
        "Billing & Invoicing": ["billing", "invoice"],
        "Role-Based Access Control": ["rbac", "access", "users", "auth"],
        "HR and Payroll": ["hr", "payroll", "human"],
        "Housekeeping and Maintenance": ["housekeeping", "maintenance"],
        "Biomedical Equipment": ["biomedical", "equipment"],
        "Dietary Management": ["dietary", "nutrition"],
        "Ambulance Management": ["ambulance"],
        "Patient Portal": ["patient_portal", "portal"],
        "Doctor Portal": ["doctor_portal"],
        "E-Prescription": ["prescription", "e-prescription"],
        "Notification System": ["notification", "alert"],
        "Feedback & Complaint Management": ["feedback", "complaint"],
        "Marketing CRM": ["marketing", "crm"],
        "Analytics and Reporting": ["analytics", "reporting"],
        "Medical Records Department": ["mrd", "medical_records"],
        "NABH / JCI Compliance": ["compliance", "nabh", "jci"],
        "Advanced Backup and Disaster Recovery": ["backup", "disaster", "recovery"],
        "Cybersecurity Measures": ["security", "cyber"],
    }

    # Check backend directory
    backend_path = Path("backend")
    services_path = Path("services")

    implemented_modules = []
    module_details = {}

    # Check each module
    for module, patterns in module_mapping.items():
        found = False
        details = {"backend": False, "services": False, "files": []}

        # Check backend
        if backend_path.exists():
            for pattern in patterns:
                backend_dirs = [
                    d
                    for d in backend_path.iterdir()
                    if d.is_dir() and pattern in d.name.lower()
                ]
                if backend_dirs:
                    found = True
                    details["backend"] = True
                    details["files"].extend([str(d) for d in backend_dirs])

        # Check services
        if services_path.exists():
            for pattern in patterns:
                service_dirs = [
                    d
                    for d in services_path.iterdir()
                    if d.is_dir() and pattern in d.name.lower()
                ]
                if service_dirs:
                    found = True
                    details["services"] = True
                    details["files"].extend([str(d) for d in service_dirs])

        if found:
            implemented_modules.append(module)
            module_details[module] = details

    # Calculate percentages
    total_required = len(required_modules)
    implemented_count = len(implemented_modules)
    percentage = (implemented_count / total_required) * 100

    missing_modules = list(set(required_modules) - set(implemented_modules))

    return {
        "total_required": total_required,
        "implemented_count": implemented_count,
        "percentage": round(percentage, 2),
        "implemented_modules": implemented_modules,
        "missing_modules": missing_modules,
        "module_details": module_details,
    }


# Execute validation
result = validate_hms_modules()
print(json.dumps(result, indent=2))
