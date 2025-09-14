import requests
from pybreaker import CircuitBreaker
from tenacity import retry, stop_after_attempt, wait_exponential

# Circuit breaker for external API calls
api_breaker = CircuitBreaker(fail_max=5, reset_timeout=60)


@api_breaker
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def safe_api_call(url, method="GET", **kwargs):
    """
    Make API calls with circuit breaker and retry logic.
    """
    return requests.request(method, url, **kwargs)
