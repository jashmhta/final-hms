import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
class DatabaseModelFixer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.services_dir = self.project_root / "services"
        self.fixed_models = 0
        self.total_models = 0
    def validate_model_file(self, model_file: Path) -> Dict:
        validation_result = {
            "file_path": str(model_file),
            "valid": True,
            "has_class": False,
            "has_imports": False,
            "has_sqlalchemy": False,
            "compiles": False,
            "issues": []
        }
        if not model_file.exists():
            validation_result["valid"] = False
            validation_result["issues"].append("Model file does not exist")
            return validation_result
        try:
            with open(model_file, 'r') as f:
                content = f.read()
            if "from sqlalchemy" in content or "import sqlalchemy" in content:
                validation_result["has_sqlalchemy"] = True
                validation_result["has_imports"] = True
            if "class " in content and "(Base)" in content:
                validation_result["has_class"] = True
            if "__tablename__" not in content:
                validation_result["issues"].append("Missing __tablename__ in model")
            if "Column(" not in content:
                validation_result["issues"].append("Missing Column definitions")
            try:
                subprocess.run(
                    ['python3', '-m', 'py_compile', str(model_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                validation_result["compiles"] = True
            except subprocess.TimeoutExpired:
                validation_result["issues"].append("Compilation timeout")
                validation_result["compiles"] = False
            except Exception as e:
                validation_result["issues"].append(f"Compilation error: {e}")
                validation_result["compiles"] = False
            validation_result["valid"] = (
                validation_result["has_sqlalchemy"] and
                validation_result["has_class"] and
                validation_result["compiles"] and
                len(validation_result["issues"]) == 0
            )
        except Exception as e:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Error reading file: {e}")
        return validation_result
    def fix_model_file(self, model_file: Path):
        service_name = model_file.parent.name
        current_content = ""
        if model_file.exists():
            with open(model_file, 'r') as f:
                current_content = f.read()
        if ("from sqlalchemy" in current_content and
            "class " in current_content and
            "(Base)" in current_content and
            "__tablename__" in current_content):
            print(f"   ✅ {service_name} - Already properly structured")
            return True
        proper_model = f
        with open(model_file, 'w') as f:
            f.write(proper_model)
        print(f"   ✅ {service_name} - Fixed model structure")
        self.fixed_models += 1
        return True
    def validate_all_models(self) -> Dict:
        print("🔍 Validating all database models...")
        if not self.services_dir.exists():
            print("❌ Services directory not found")
            return {"error": "Services directory not found"}
        model_files = list(self.services_dir.glob("*/models.py"))
        self.total_models = len(model_files)
        validation_results = []
        valid_models = 0
        for model_file in model_files:
            result = self.validate_model_file(model_file)
            validation_results.append(result)
            if result["valid"]:
                valid_models += 1
                print(f"   ✅ {model_file.parent.name} - Valid")
            else:
                print(f"   ❌ {model_file.parent.name} - Invalid")
                for issue in result["issues"]:
                    print(f"      - {issue}")
        success_rate = (valid_models / self.total_models) * 100 if self.total_models > 0 else 0
        summary = {
            "total_models": self.total_models,
            "valid_models": valid_models,
            "success_rate": success_rate,
            "validation_results": validation_results
        }
        return summary
    def fix_all_models(self, validation_results: List[Dict]):
        print("🔧 Fixing invalid database models...")
        for result in validation_results:
            if not result["valid"]:
                file_path = Path(result["file_path"])
                self.fix_model_file(file_path)
    def run_complete_model_fix(self):
        print("🚀 Starting complete database model validation...")
        initial_summary = self.validate_all_models()
        print(f"\n📊 Initial Results:")
        print(f"   Total Models: {initial_summary['total_models']}")
        print(f"   Valid Models: {initial_summary['valid_models']}")
        print(f"   Success Rate: {initial_summary['success_rate']:.1f}%")
        if initial_summary['valid_models'] < initial_summary['total_models']:
            print("\n🔧 Fixing invalid models...")
            self.fix_all_models(initial_summary['validation_results'])
            print("\n🔄 Re-validating after fixes...")
            final_summary = self.validate_all_models()
            print(f"\n📊 Final Results:")
            print(f"   Total Models: {final_summary['total_models']}")
            print(f"   Valid Models: {final_summary['valid_models']}")
            print(f"   Success Rate: {final_summary['success_rate']:.1f}%")
            print(f"\n✅ Database model validation and fixing completed!")
            print(f"   Models improved from {initial_summary['valid_models']} to {final_summary['valid_models']}")
            return final_summary
        else:
            print("✅ All database models are already valid!")
            return initial_summary
if __name__ == "__main__":
    fixer = DatabaseModelFixer()
    fixer.run_complete_model_fix()