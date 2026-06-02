"""
Performance metrics tracking (Phase 3.5).
Supporting feature: Endpoint performance monitoring and diagnostics.
"""
from collections import defaultdict
from datetime import datetime
import logging
import time
from typing import Dict, List
import threading

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    Track performance metrics for API endpoints.
    Thread-safe implementation for concurrent requests.
    """
    
    def __init__(self):
        """Initialize metrics container."""
        self._lock = threading.RLock()
        # metrics["{method} {endpoint}"] = {timings: [], errors: int, total_requests: int}
        self._metrics: Dict = defaultdict(lambda: {
            "timings": [],
            "errors": 0,
            "total_requests": 0,
            "last_error": None
        })
    
    def record_request(self, endpoint: str, method: str, execution_time_ms: float, error: bool = False):
        """
        Record a request metric.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            execution_time_ms: Execution time in milliseconds
            error: Whether request resulted in error
        """
        with self._lock:
            key = f"{method} {endpoint}"
            metrics = self._metrics[key]
            
            metrics["total_requests"] += 1
            metrics["timings"].append(execution_time_ms)
            
            if error:
                metrics["errors"] += 1
                metrics["last_error"] = datetime.utcnow().isoformat()
            
            # Keep only last 1000 timings to prevent memory bloat
            if len(metrics["timings"]) > 1000:
                metrics["timings"] = metrics["timings"][-1000:]
    
    def get_metrics(self, endpoint: str = None, method: str = None) -> Dict:
        """
        Get performance metrics for endpoint(s).
        
        Args:
            endpoint: Optional specific endpoint
            method: Optional specific method
            
        Returns:
            Dictionary with computed metrics
        """
        with self._lock:
            if endpoint and method:
                key = f"{method} {endpoint}"
                if key not in self._metrics:
                    return None
                return self._compute_metrics(self._metrics[key])
            
            # Return all metrics
            result = {}
            for key, metrics in self._metrics.items():
                result[key] = self._compute_metrics(metrics)
            return result
    
    @staticmethod
    def _compute_metrics(metrics: Dict) -> Dict:
        """Compute aggregate metrics from recorded data."""
        timings = metrics["timings"]
        
        if not timings:
            return {
                "total_requests": metrics["total_requests"],
                "errors": metrics["errors"],
                "error_rate": 0.0,
                "last_error": metrics["last_error"]
            }
        
        sorted_timings = sorted(timings)
        count = len(timings)
        
        # Calculate percentiles
        p50 = sorted_timings[int(count * 0.50)]
        p95 = sorted_timings[int(count * 0.95)]
        p99 = sorted_timings[int(count * 0.99)]
        
        return {
            "total_requests": metrics["total_requests"],
            "errors": metrics["errors"],
            "error_rate": metrics["errors"] / metrics["total_requests"] if metrics["total_requests"] > 0 else 0.0,
            "min_ms": min(timings),
            "max_ms": max(timings),
            "avg_ms": sum(timings) / count,
            "p50_ms": p50,  # Median
            "p95_ms": p95,  # 95th percentile
            "p99_ms": p99,  # 99th percentile
            "last_error": metrics["last_error"],
            "samples": count
        }
    
    def reset_metrics(self, endpoint: str = None):
        """
        Reset metrics for endpoint(s).
        
        Args:
            endpoint: Optional specific endpoint to reset
        """
        with self._lock:
            if endpoint:
                for key in list(self._metrics.keys()):
                    if endpoint in key:
                        del self._metrics[key]
            else:
                self._metrics.clear()
        logger.info(f"Performance metrics reset for {endpoint or 'all endpoints'}")
    
    def log_summary(self):
        """Log a summary of all metrics."""
        metrics = self.get_metrics()
        
        if not metrics:
            logger.info("No performance metrics available")
            return
        
        summary_lines = ["Performance Metrics Summary:", "=" * 60]
        
        for endpoint, stats in sorted(metrics.items()):
            if stats["total_requests"] > 0:
                summary_lines.append(
                    f"\n{endpoint}:\n"
                    f"  Total Requests: {stats['total_requests']}\n"
                    f"  Error Rate: {stats['error_rate']:.1%}\n"
                    f"  Avg: {stats.get('avg_ms', 0):.2f}ms | "
                    f"P50: {stats.get('p50_ms', 0):.2f}ms | "
                    f"P95: {stats.get('p95_ms', 0):.2f}ms | "
                    f"P99: {stats.get('p99_ms', 0):.2f}ms"
                )
        
        logger.info("\n".join(summary_lines))


# Global metrics instance
_metrics_instance = None


def get_metrics_instance() -> PerformanceMetrics:
    """Get or create global metrics instance."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = PerformanceMetrics()
    return _metrics_instance


def setup_performance_metrics():
    """Initialize performance metrics tracking."""
    metrics = get_metrics_instance()
    logger.info("Performance metrics tracking enabled")
    return metrics


# Decorator for manual endpoint tracking
def track_performance(endpoint_name: str = None):
    """
    Decorator to track performance of functions.
    
    Args:
        endpoint_name: Optional name for tracking
        
    Usage:
        @track_performance("some_service_operation")
        async def my_function():
            ...
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                metrics = get_metrics_instance()
                execution_time = (time.time() - start) * 1000
                metrics.record_request(
                    endpoint_name or func.__name__,
                    "ASYNC",
                    execution_time,
                    error=True
                )
                raise
        
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                metrics = get_metrics_instance()
                execution_time = (time.time() - start) * 1000
                metrics.record_request(
                    endpoint_name or func.__name__,
                    "SYNC",
                    execution_time,
                    error=True
                )
                raise
        
        # Return appropriate wrapper
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
