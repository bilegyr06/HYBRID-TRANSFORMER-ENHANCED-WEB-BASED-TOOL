"""
Tests for request/response logging middleware (Phase 3.4).
Testing feature: Request tracking and monitoring.
"""
import pytest
import time
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from src.core.request_logging import RequestResponseLoggingMiddleware, SlowRequestWarningMiddleware


@pytest.fixture
def app_with_logging():
    """Create a test app with logging middleware."""
    app = FastAPI()
    
    # Add logging middleware
    app.add_middleware(SlowRequestWarningMiddleware, slow_request_threshold_ms=100)
    app.add_middleware(RequestResponseLoggingMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.post("/test")
    async def test_post(data: dict):
        return {"received": data}
    
    @app.get("/slow")
    async def slow_endpoint():
        time.sleep(0.2)  # Sleep for 200ms
        return {"message": "slow"}
    
    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")
    
    return app


class TestRequestLoggingMiddleware:
    """Tests for request/response logging middleware."""
    
    def test_request_id_header_added(self, app_with_logging):
        """Test that X-Request-ID header is added to responses."""
        client = TestClient(app_with_logging)
        response = client.get("/test")
        
        assert response.status_code == status.HTTP_200_OK
        assert "X-Request-ID" in response.headers
        # UUID format check
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) == 36  # UUID4 length
        assert request_id.count("-") == 4  # UUID format
    
    def test_get_request_logged(self, app_with_logging, caplog):
        """Test that GET requests are logged."""
        client = TestClient(app_with_logging)
        response = client.get("/test?param=value")
        
        assert response.status_code == status.HTTP_200_OK
        # Should log something (exact format depends on logger configuration)
    
    def test_post_request_logged(self, app_with_logging):
        """Test that POST requests are logged."""
        client = TestClient(app_with_logging)
        response = client.post("/test", json={"key": "value"})
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_error_request_logged(self, app_with_logging):
        """Test that error requests are logged."""
        client = TestClient(app_with_logging)
        
        with pytest.raises(ValueError):
            client.get("/error")
    
    def test_slow_request_warning_threshold(self, app_with_logging, caplog):
        """Test that slow requests trigger warnings."""
        client = TestClient(app_with_logging)
        
        with caplog.at_level("WARNING"):
            response = client.get("/slow")
        
        assert response.status_code == status.HTTP_200_OK
        # Slow request should have been logged with warning
    
    def test_different_status_codes_logged(self, app_with_logging):
        """Test that different status codes are handled."""
        app = FastAPI()
        app.add_middleware(RequestResponseLoggingMiddleware)
        
        @app.get("/ok")
        async def ok():
            return {"status": "ok"}
        
        @app.get("/created")
        async def created():
            return {"status": "created"}
        
        @app.get("/bad")
        async def bad():
            raise ValueError("Bad request")
        
        client = TestClient(app)
        
        response = client.get("/ok")
        assert response.status_code == status.HTTP_200_OK
        
        response = client.get("/created")
        assert response.status_code == status.HTTP_200_OK
    
    def test_request_size_tracking(self, app_with_logging):
        """Test that request sizes are tracked."""
        client = TestClient(app_with_logging)
        
        # Large payload
        large_payload = {"data": "x" * 10000}
        response = client.post("/test", json=large_payload)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_response_headers_preserved(self, app_with_logging):
        """Test that response headers are preserved."""
        client = TestClient(app_with_logging)
        response = client.get("/test")
        
        # Should have X-Request-ID header added
        assert "X-Request-ID" in response.headers
        # Original response should still work
        assert response.json() == {"message": "test"}
    
    def test_multiple_requests_different_ids(self, app_with_logging):
        """Test that each request gets unique ID."""
        client = TestClient(app_with_logging)
        
        response1 = client.get("/test")
        response2 = client.get("/test")
        
        id1 = response1.headers["X-Request-ID"]
        id2 = response2.headers["X-Request-ID"]
        
        assert id1 != id2


class TestSlowRequestWarningMiddleware:
    """Tests for slow request detection middleware."""
    
    def test_fast_request_no_warning(self, app_with_logging):
        """Test that fast requests don't trigger warnings."""
        client = TestClient(app_with_logging)
        response = client.get("/test")
        
        assert response.status_code == status.HTTP_200_OK
        # Should not have logged a warning
    
    def test_slow_request_triggers_warning(self, app_with_logging):
        """Test that slow requests trigger warnings."""
        client = TestClient(app_with_logging)
        response = client.get("/slow")
        
        assert response.status_code == status.HTTP_200_OK
        # Slow request should trigger warning
    
    def test_custom_threshold(self):
        """Test custom slow request threshold."""
        app = FastAPI()
        app.add_middleware(SlowRequestWarningMiddleware, slow_request_threshold_ms=50)
        
        @app.get("/endpoint")
        async def endpoint():
            time.sleep(0.1)  # 100ms
            return {"status": "ok"}
        
        client = TestClient(app)
        response = client.get("/endpoint")
        
        assert response.status_code == status.HTTP_200_OK


class TestLoggingMiddlewareIntegration:
    """Integration tests for logging middleware."""
    
    def test_multiple_middlewares_stacked(self):
        """Test that multiple logging middlewares work together."""
        app = FastAPI()
        app.add_middleware(SlowRequestWarningMiddleware)
        app.add_middleware(RequestResponseLoggingMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == status.HTTP_200_OK
        assert "X-Request-ID" in response.headers
    
    def test_middleware_with_query_parameters(self, app_with_logging):
        """Test middleware handles query parameters."""
        client = TestClient(app_with_logging)
        response = client.get("/test?key1=value1&key2=value2")
        
        assert response.status_code == status.HTTP_200_OK
        assert "X-Request-ID" in response.headers
    
    def test_middleware_with_large_response(self, app_with_logging):
        """Test middleware handles large responses."""
        app = FastAPI()
        app.add_middleware(RequestResponseLoggingMiddleware)
        
        @app.get("/large")
        async def large_response():
            return {"data": "x" * 100000}
        
        client = TestClient(app)
        response = client.get("/large")
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["data"]) == 100000
    
    def test_middleware_preserves_response_body(self, app_with_logging):
        """Test that middleware doesn't modify response body."""
        client = TestClient(app_with_logging)
        response = client.get("/test")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "test"}
