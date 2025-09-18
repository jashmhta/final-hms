import asyncio
import aiohttp
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
import logging
from typing import List, Dict
import json
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class PerformanceTestSuite:
    def __init__(self, base_url: str, concurrent_users: int = 100):
        self.base_url = base_url.rstrip('/')
        self.concurrent_users = concurrent_users
        self.session = None
    async def setup(self):
        self.session = aiohttp.ClientSession()
    async def teardown(self):
        if self.session:
            await self.session.close()
    async def measure_response_time(self, url: str, method: str = 'GET',
                                  data: Dict = None, headers: Dict = None) -> float:
        start_time = time.time()
        try:
            async with self.session.request(
                method, url, json=data, headers=headers, timeout=30
            ) as response:
                await response.text()  
                end_time = time.time()
                return end_time - start_time
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return float('inf')
    async def load_test_endpoint(self, endpoint: str, method: str = 'GET',
                               data: Dict = None, num_requests: int = 1000) -> Dict:
        async def single_request():
            url = f"{self.base_url}{endpoint}"
            return await self.measure_response_time(url, method, data)
        tasks = [single_request() for _ in range(num_requests)]
        response_times = await asyncio.gather(*tasks)
        valid_times = [t for t in response_times if t != float('inf')]
        return {
            'endpoint': endpoint,
            'total_requests': num_requests,
            'successful_requests': len(valid_times),
            'failed_requests': num_requests - len(valid_times),
            'min_response_time': min(valid_times) if valid_times else 0,
            'max_response_time': max(valid_times) if valid_times else 0,
            'avg_response_time': statistics.mean(valid_times) if valid_times else 0,
            'median_response_time': statistics.median(valid_times) if valid_times else 0,
            '95th_percentile': statistics.quantiles(valid_times, n=20)[18] if len(valid_times) >= 20 else 0,
            '99th_percentile': statistics.quantiles(valid_times, n=100)[98] if len(valid_times) >= 100 else 0,
        }
    async def run_comprehensive_test(self) -> Dict:
        test_endpoints = [
            {'endpoint': '/api/appointments/', 'method': 'GET'},
            {'endpoint': '/api/patients/', 'method': 'GET'},
            {'endpoint': '/api/billing/bills/', 'method': 'GET'},
            {'endpoint': '/api/appointments/available_slots/', 'method': 'GET'},
            {'endpoint': '/health/', 'method': 'GET'},
        ]
        results = {}
        for endpoint_config in test_endpoints:
            logger.info(f"Testing {endpoint_config['endpoint']}")
            result = await self.load_test_endpoint(
                endpoint_config['endpoint'],
                endpoint_config['method'],
                num_requests=500
            )
            results[endpoint_config['endpoint']] = result
            if result['95th_percentile'] > 0.1:  
                logger.warning(f"SLA breach: {endpoint_config['endpoint']} 95th percentile = {result['95th_percentile']:.3f}s")
        return results
    def generate_report(self, results: Dict) -> str:
        report = []
        report.append("
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        sla_breaches = []
        for endpoint, result in results.items():
            if result['95th_percentile'] > 0.1:
                sla_breaches.append(endpoint)
        if sla_breaches:
            report.append("
            for endpoint in sla_breaches:
                result = results[endpoint]
                report.append(f"- {endpoint}: 95th percentile = {result['95th_percentile']:.3f}s")
            report.append("")
        else:
            report.append("
            report.append("")
        report.append("
        for endpoint, result in results.items():
            report.append(f"
            report.append(f"- Total Requests: {result['total_requests']}")
            report.append(f"- Successful: {result['successful_requests']}")
            report.append(f"- Failed: {result['failed_requests']}")
            report.append(".3f")
            report.append(".3f")
            report.append(".3f")
            report.append(".3f")
            report.append(".3f")
            report.append("")
        return "\n".join(report)
async def main():
    base_url = "http://localhost:8000"  
    suite = PerformanceTestSuite(base_url, concurrent_users=50)
    await suite.setup()
    try:
        logger.info("Starting comprehensive performance test...")
        results = await suite.run_comprehensive_test()
        report = suite.generate_report(results)
        print(report)
        with open('performance_report.md', 'w') as f:
            f.write(report)
        logger.info("Performance test completed. Report saved to performance_report.md")
    finally:
        await suite.teardown()
if __name__ == "__main__":
    asyncio.run(main())