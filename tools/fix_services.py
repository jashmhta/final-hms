"""
fix_services module
"""

import os
from pathlib import Path


def create_missing_files():
    services_dir = Path("services")
    services_to_fix = [
        "prescription",
        "operation_theatre",
        "graphql_gateway",
        "ot_scheduling",
        "ambulance",
        "triage",
        "lab",
        "facilities",
        "mrd",
        "consent",
        "pharmacy",
        "compliance_checklists",
        "billing",
        "price_estimator",
        "appointments",
        "feedback",
        "audit",
        "notifications",
        "erp",
        "hr",
        "analytics_service",
        "radiology",
        "er_alerts",
        "patients",
    ]
    for service_name in services_to_fix:
        service_path = services_dir / service_name
        if not service_path.exists():
            service_path.mkdir(exist_ok=True)
            print(f"Created directory: {service_path}")
        models_file = service_path / "models.py"
        if not models_file.exists():
            models_content = f
            with open(models_file, "w") as f:
                f.write(models_content)
            print(f"Created models.py for {service_name}")
        main_file = service_path / "main.py"
        if not main_file.exists():
            main_content = f
            with open(main_file, "w") as f:
                f.write(main_content)
            print(f"Created main.py for {service_name}")
        schemas_file = service_path / "schemas.py"
        if not schemas_file.exists():
            schemas_content = f
            with open(schemas_file, "w") as f:
                f.write(schemas_content)
            print(f"Created schemas.py for {service_name}")


if __name__ == "__main__":
    print("🔧 Fixing HMS services...")
    create_missing_files()
    print("✅ Service fixing completed!")
