from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "api_requests_total", "Total API requests", ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds", "API request latency", ["method", "endpoint"]
)
TRANSACTIONS_INGESTED = Counter("transactions_ingested_total", "Transactions ingested")
ALERTS_GENERATED = Counter(
    "alerts_generated_total", "Alerts generated", ["type", "severity"]
)
