import logging
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, Tracer
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
# from arize_phoenix.otel import PhoenixSpanExporter # Not needed if using OTLP directly

# Constants
SERVICE_NAME = "paper-search-agent"
PHOENIX_ENDPOINT = os.getenv("PHOENIX_COLLECTOR_URL", "http://localhost:4317")

logger = logging.getLogger(__name__)

class MonitoringManager:
    """
    Singleton to manage OpenTelemetry and Phoenix configuration.
    """
    _instance = None
    _tracer_provider = None
    
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if MonitoringManager._instance:
            raise Exception("MonitoringManager is a singleton")
        self._setup_telemetry()
        
    def _setup_telemetry(self):
        """Configure OpenTelemetry and Phoenix"""
        try:
            resource = Resource(attributes={
                "service.name": SERVICE_NAME,
            })
            
            # Use Phoenix exporter if available, otherwise fallback to standard OTLP or console
            # For this setup, we assume Phoenix is running via docker-compose
            
            trace_provider = TracerProvider(resource=resource)
            
            # Configure Phoenix Exporter (using gRPC)
            # Phoenix listens on 4317 for gRPC by default
            phoenix_exporter = OTLPSpanExporter(endpoint=PHOENIX_ENDPOINT, insecure=True)
            span_processor = BatchSpanProcessor(phoenix_exporter)
            trace_provider.add_span_processor(span_processor)
            
            trace.set_tracer_provider(trace_provider)
            self._tracer_provider = trace_provider
            
            # Instrument LlamaIndex (Auto-instrumentation for RAG)
            LlamaIndexInstrumentor().instrument(tracer_provider=trace_provider)
            
            logger.info(f"✅ Telemetry initialized. Sending traces to {PHOENIX_ENDPOINT}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize telemetry: {e}")
            # Do not crash the app if monitoring fails
            
    def get_tracer(self, name: str) -> Tracer:
        """Get a tracer for manual instrumentation"""
        if not self._tracer_provider:
             return trace.get_tracer(name)
        return self._tracer_provider.get_tracer(name)

# Global helper
def get_tracer(name: str):
    print(f"DEBUG: get_tracer called for {name}")
    return MonitoringManager.get_instance().get_tracer(name)
