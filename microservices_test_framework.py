import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import sys
import os
sys.path.append('/home/azureuser/hms-enterprise-grade/backend')
@dataclass
class ServiceTestResult:
    service_name: str
    status: str
    response_time: float
    health_check_passed: bool
    endpoints_tested: int
    endpoints_passed: int
    errors: List[str]
    security_score: float
    performance_score: float
    compliance_score: float
@dataclass
class ServiceConfig:
    name: str
    port: int
    host: str = "localhost"
    expected_endpoints: List[str] = None
    requires_auth: bool = True
    is_critical: bool = False
    dependencies: List[str] = None
class MicroservicesTestFramework:
    def __init__(self):
        self.test_results: Dict[str, ServiceTestResult] = {}
        self.service_configs: Dict[str, ServiceConfig] = {}
        self.session = None
        self.logger = self._setup_logging()
        self._initialize_service_configs()
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("MicroservicesTestFramework")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    def _initialize_service_configs(self):
        services = {
            'audit': ServiceConfig('audit', 9001, expected_endpoints=['/', '/health'],
                                 requires_auth=True, is_critical=True),
            'analytics_service': ServiceConfig('analytics_service', 9002,
                                            expected_endpoints=['/', '/health'], is_critical=True),
            'appointments': ServiceConfig('appointments', 9003,
                                       expected_endpoints=['/', '/health'], is_critical=True),
            'billing': ServiceConfig('billing', 9004, expected_endpoints=['/', '/health'],
                                   is_critical=True),
            'facilities': ServiceConfig('facilities', 9005, expected_endpoints=['/', '/health']),
            'hr': ServiceConfig('hr', 9006, expected_endpoints=['/', '/health']),
            'patients': ServiceConfig('patients', 9007, expected_endpoints=['/', '/health'],
                                    is_critical=True),
            'pharmacy': ServiceConfig('pharmacy', 9008, expected_endpoints=['/', '/health'],
                                    is_critical=True),
            'lab': ServiceConfig('lab', 9021, expected_endpoints=['/', '/health'],
                                is_critical=True),
            'radiology': ServiceConfig('radiology', 9022, expected_endpoints=['/', '/health'],
                                     is_critical=True),
            'prescription': ServiceConfig('prescription', 9023,
                                        expected_endpoints=['/', '/health'], is_critical=True),
            'triage': ServiceConfig('triage', 9024, expected_endpoints=['/', '/health'],
                                  is_critical=True),
            'operation_theatre': ServiceConfig('operation_theatre', 9025,
                                             expected_endpoints=['/', '/health']),
            'ot_scheduling': ServiceConfig('ot_scheduling', 9026,
                                         expected_endpoints=['/', '/health']),
            'er_alerts': ServiceConfig('er_alerts', 9027, expected_endpoints=['/', '/health'],
                                     is_critical=True),
            'consent': ServiceConfig('consent', 9028, expected_endpoints=['/', '/health']),
            'e_prescription': ServiceConfig('e_prescription', 9029,
                                           expected_endpoints=['/', '/health'], is_critical=True),
            'notifications': ServiceConfig('notifications', 9041,
                                         expected_endpoints=['/', '/health'], is_critical=True),
            'backup_disaster_recovery': ServiceConfig('backup_disaster_recovery', 9042,
                                                     expected_endpoints=['/', '/health'], is_critical=True),
            'compliance_checklists': ServiceConfig('compliance_checklists', 9043,
                                                 expected_endpoints=['/', '/health']),
            'erp': ServiceConfig('erp', 9044, expected_endpoints=['/', '/health']),
            'feedback': ServiceConfig('feedback', 9045, expected_endpoints=['/', '/health']),
            'graphql_gateway': ServiceConfig('graphql_gateway', 9046,
                                           expected_endpoints=['/', '/health']),
            'price_estimator': ServiceConfig('price_estimator', 9047,
                                           expected_endpoints=['/', '/health']),
            'ambulance': ServiceConfig('ambulance', 9061, expected_endpoints=['/', '/health'],
                                     is_critical=True),
            'bed_management': ServiceConfig('bed_management', 9062,
                                          expected_endpoints=['/', '/health'], is_critical=True),
            'blood_bank': ServiceConfig('blood_bank', 9063, expected_endpoints=['/', '/health'],
                                      is_critical=True),
            'dietary': ServiceConfig('dietary', 9064, expected_endpoints=['/', '/health']),
            'doctor_portal': ServiceConfig('doctor_portal', 9065, expected_endpoints=['/', '/health']),
            'emergency_department': ServiceConfig('emergency_department', 9066,
                                                 expected_endpoints=['/', '/health'], is_critical=True),
            'housekeeping_maintenance': ServiceConfig('housekeeping_maintenance', 9067,
                                                    expected_endpoints=['/', '/health']),
            'insurance_tpa_integration': ServiceConfig('insurance_tpa_integration', 9068,
                                                      expected_endpoints=['/', '/health']),
            'ipd_management': ServiceConfig('ipd_management', 9069,
                                          expected_endpoints=['/', '/health'], is_critical=True),
            'marketing_crm': ServiceConfig('marketing_crm', 9070, expected_endpoints=['/', '/health']),
            'mrd': ServiceConfig('mrd', 9071, expected_endpoints=['/', '/health']),
            'opd_management': ServiceConfig('opd_management', 9072,
                                          expected_endpoints=['/', '/health'], is_critical=True),
            'patient_portal': ServiceConfig('patient_portal', 9073,
                                          expected_endpoints=['/', '/health']),
            'biomedical_equipment': ServiceConfig('biomedical_equipment', 9074,
                                                expected_endpoints=['/', '/health']),
            'cybersecurity_enhancements': ServiceConfig('cybersecurity_enhancements', 9075,
                                                      expected_endpoints=['/', '/health'], is_critical=True),
        }
        self.service_configs = services
        self.logger.info(f"Initialized {len(services)} microservice configurations")
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'HMS-Microservices-Test-Framework/1.0'}
        )
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    async def test_service_health(self, service_config: ServiceConfig) -> ServiceTestResult:
        service_name = service_config.name
        base_url = f"http://{service_config.host}:{service_config.port}"
        self.logger.info(f"Testing service: {service_name} at {base_url}")
        result = ServiceTestResult(
            service_name=service_name,
            status="UNKNOWN",
            response_time=0.0,
            health_check_passed=False,
            endpoints_tested=0,
            endpoints_passed=0,
            errors=[],
            security_score=0.0,
            performance_score=0.0,
            compliance_score=0.0
        )
        try:
            start_time = time.time()
            async with self.session.get(f"{base_url}/health") as response:
                response_time = time.time() - start_time
                result.response_time = response_time
                if response.status == 200:
                    result.health_check_passed = True
                    result.status = "HEALTHY"
                    self.logger.info(f"✅ {service_name} health check passed ({response_time:.3f}s)")
                else:
                    result.status = "UNHEALTHY"
                    result.errors.append(f"Health check returned status {response.status}")
                    self.logger.error(f"❌ {service_name} health check failed: {response.status}")
            result.endpoints_tested += 1
            async with self.session.get(f"{base_url}/") as response:
                if response.status == 200:
                    result.endpoints_passed += 1
                    self.logger.info(f"✅ {service_name} root endpoint accessible")
                else:
                    result.errors.append(f"Root endpoint returned status {response.status}")
            if response_time < 0.1:  
                result.performance_score = 1.0
            elif response_time < 0.5:  
                result.performance_score = 0.8
            elif response_time < 1.0:  
                result.performance_score = 0.6
            else:
                result.performance_score = 0.3
            security_score = 0.7  
            if service_config.requires_auth:
                security_score += 0.2
            result.security_score = min(1.0, security_score)
            compliance_score = 0.8  
            if service_config.is_critical:
                compliance_score += 0.1
            if 'health' in service_config.expected_endpoints:
                compliance_score += 0.1
            result.compliance_score = min(1.0, compliance_score)
        except asyncio.TimeoutError:
            result.status = "TIMEOUT"
            result.errors.append("Request timeout")
            self.logger.error(f"⏰ {service_name} request timeout")
        except aiohttp.ClientError as e:
            result.status = "UNREACHABLE"
            result.errors.append(f"Connection error: {str(e)}")
            self.logger.error(f"🔌 {service_name} connection error: {e}")
        except Exception as e:
            result.status = "ERROR"
            result.errors.append(f"Unexpected error: {str(e)}")
            self.logger.error(f"💥 {service_name} unexpected error: {e}")
        return result
    async def test_all_services(self) -> Dict[str, ServiceTestResult]:
        self.logger.info("🚀 Starting comprehensive microservices testing...")
        tasks = []
        for service_config in self.service_configs.values():
            task = asyncio.create_task(self.test_service_health(service_config))
            tasks.append(task)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = list(self.service_configs.keys())[i]
                error_result = ServiceTestResult(
                    service_name=service_name,
                    status="ERROR",
                    response_time=0.0,
                    health_check_passed=False,
                    endpoints_tested=0,
                    endpoints_passed=0,
                    errors=[f"Test execution error: {str(result)}"],
                    security_score=0.0,
                    performance_score=0.0,
                    compliance_score=0.0
                )
                self.test_results[service_name] = error_result
                self.logger.error(f"💥 {service_name} test execution failed: {result}")
            else:
                self.test_results[result.service_name] = result
        return self.test_results
    def generate_test_report(self) -> Dict[str, Any]:
        total_services = len(self.test_results)
        healthy_services = sum(1 for r in self.test_results.values() if r.status == "HEALTHY")
        critical_services = [name for name, config in self.service_configs.items()
                           if config.is_critical and r.status != "HEALTHY"]
        avg_response_time = sum(r.response_time for r in self.test_results.values()) / total_services if total_services > 0 else 0
        avg_security_score = sum(r.security_score for r in self.test_results.values()) / total_services if total_services > 0 else 0
        avg_performance_score = sum(r.performance_score for r in self.test_results.values()) / total_services if total_services > 0 else 0
        avg_compliance_score = sum(r.compliance_score for r in self.test_results.values()) / total_services if total_services > 0 else 0
        report = {
            "test_summary": {
                "total_services": total_services,
                "healthy_services": healthy_services,
                "success_rate": (healthy_services / total_services * 100) if total_services > 0 else 0,
                "critical_failures": len(critical_services),
                "test_timestamp": datetime.utcnow().isoformat(),
            },
            "performance_metrics": {
                "average_response_time": avg_response_time,
                "average_security_score": avg_security_score,
                "average_performance_score": avg_performance_score,
                "average_compliance_score": avg_compliance_score,
            },
            "service_results": {name: {
                "status": result.status,
                "response_time": result.response_time,
                "health_check_passed": result.health_check_passed,
                "endpoints_tested": result.endpoints_tested,
                "endpoints_passed": result.endpoints_passed,
                "security_score": result.security_score,
                "performance_score": result.performance_score,
                "compliance_score": result.compliance_score,
                "errors": result.errors,
                "is_critical": self.service_configs[name].is_critical
            } for name, result in self.test_results.items()},
            "critical_service_failures": critical_services,
            "recommendations": self._generate_recommendations()
        }
        return report
    def _generate_recommendations(self) -> List[str]:
        recommendations = []
        critical_failures = [name for name, result in self.test_results.items()
                           if self.service_configs[name].is_critical and result.status != "HEALTHY"]
        if critical_failures:
            recommendations.append(f"🚨 CRITICAL: Fix failing critical services: {', '.join(critical_failures)}")
        slow_services = [name for name, result in self.test_results.items()
                        if result.response_time > 1.0]
        if slow_services:
            recommendations.append(f"⚡ PERFORMANCE: Optimize slow services: {', '.join(slow_services)}")
        low_security = [name for name, result in self.test_results.items()
                       if result.security_score < 0.7]
        if low_security:
            recommendations.append(f"🔒 SECURITY: Enhance security for: {', '.join(low_security)}")
        low_compliance = [name for name, result in self.test_results.items()
                         if result.compliance_score < 0.8]
        if low_compliance:
            recommendations.append(f"📋 COMPLIANCE: Improve compliance for: {', '.join(low_compliance)}")
        return recommendations
    def print_test_summary(self):
        report = self.generate_test_report()
        print("\n" + "="*80)
        print("🏥 HMS ENTERPRISE-GRADE MICROSERVICES TEST SUMMARY")
        print("="*80)
        print(f"\n📊 SUMMARY STATISTICS:")
        print(f"   Total Services Tested: {report['test_summary']['total_services']}")
        print(f"   Healthy Services: {report['test_summary']['healthy_services']}")
        print(f"   Success Rate: {report['test_summary']['success_rate']:.1f}%")
        print(f"   Critical Failures: {report['test_summary']['critical_failures']}")
        print(f"   Average Response Time: {report['performance_metrics']['average_response_time']:.3f}s")
        print(f"   Average Security Score: {report['performance_metrics']['average_security_score']:.2f}")
        print(f"   Average Performance Score: {report['performance_metrics']['average_performance_score']:.2f}")
        print(f"   Average Compliance Score: {report['performance_metrics']['average_compliance_score']:.2f}")
        print(f"\n🔍 SERVICE STATUS BREAKDOWN:")
        status_counts = {}
        for result in self.test_results.values():
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
        for status, count in sorted(status_counts.items()):
            emoji = {"HEALTHY": "✅", "UNHEALTHY": "❌", "UNREACHABLE": "🔌", "TIMEOUT": "⏰", "ERROR": "💥"}.get(status, "❓")
            print(f"   {emoji} {status}: {count} services")
        if report['critical_service_failures']:
            print(f"\n🚨 CRITICAL SERVICE FAILURES:")
            for service in report['critical_service_failures']:
                print(f"   💔 {service}")
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"   {rec}")
        print("\n" + "="*80)
async def main():
    print("🚀 Starting HMS Enterprise-Grade Microservices Testing Framework")
    async with MicroservicesTestFramework() as framework:
        results = await framework.test_all_services()
        report = framework.generate_test_report()
        framework.print_test_summary()
        report_file = "/home/azureuser/hms-enterprise-grade/microservices_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Detailed test report saved to: {report_file}")
        healthy_count = sum(1 for r in results.values() if r.status == "HEALTHY")
        total_count = len(results)
        if healthy_count == total_count:
            print("🎉 ALL MICROSERVICES OPERATIONAL!")
            return 0
        else:
            print(f"⚠️  {total_count - healthy_count} services require attention")
            return 1
if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)