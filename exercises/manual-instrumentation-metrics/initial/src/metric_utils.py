# OTel API
from opentelemetry import metrics as metric_api
from opentelemetry.metrics import Counter, Histogram, ObservableGauge
# OTel SDK
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader, MetricReader

import psutil

from opentelemetry.sdk.metrics.view import View, DropAggregation, ExplicitBucketHistogramAggregation

def create_views() -> list[View]:
    views = []
    traffic_volume_drop_attributes = View(
        instrument_type=Counter,
        instrument_name="traffic_volume",
        attribute_keys={}, # <-- drop all attributes
    )
    views.append(traffic_volume_drop_attributes)

    # change name of an instrument
    traffic_volume_change_name = View(
        instrument_type=Counter,
        instrument_name="traffic_volume",
        name="test", # <-- change name
    )
    views.append(traffic_volume_change_name)

    # drop entire instrument
    drop_instrument = View(
        instrument_type=ObservableGauge,
        instrument_name="process.cpu.utilization",
        aggregation=DropAggregation(), # <-- drop measurements
    )
    views.append(drop_instrument)
    # change the aggregation (buckets) for all histogram instruments
    histrogram_explicit_buckets = View(
        instrument_type=Histogram,
        instrument_name="*",  #  supports wildcard pattern matching
        aggregation=ExplicitBucketHistogramAggregation((1, 21, 50, 100, 1000)),
    )
    views.append(histrogram_explicit_buckets) # type: ignore

    return views

def create_metrics_pipeline(export_interval: int) -> MetricReader:
    console_exporter = ConsoleMetricExporter()
    reader = PeriodicExportingMetricReader(
        exporter=console_exporter,
        export_interval_millis=export_interval
    )
    return reader


def create_meter(name: str, version: str) -> metric_api.Meter:
    # configure provider
    metric_reader = create_metrics_pipeline(5000) # millisecond
    views = create_views()
    provider = MeterProvider(
        metric_readers=[metric_reader],
        views=views
    )
    
    # obtain meter
    metric_api.set_meter_provider(provider)
    meter = metric_api.get_meter(name, version)
    return meter


def create_request_instruments(meter: metric_api.Meter) -> dict:
    traffic_volume = meter.create_counter(
        name="traffic_volume",
        unit="request",
        description="total volume of requests to an endpoint",
    )

    error_rate = meter.create_counter(
    name="error_rate",
    unit="request",
    description="rate of failed requests"
    )

    request_latency = meter.create_histogram(
        name="http.server.request.duration",
        unit="s",
        description="latency for a request to be served",
    )

    instruments = {
        "traffic_volume": traffic_volume,
        "error_rate": error_rate,
        "request_latency": request_latency,
    }

    return instruments

# callbacks for asynchronous instruments
def get_cpu_utilization(opt: metric_api.CallbackOptions) -> metric_api.Observation:
    cpu_util = psutil.cpu_percent(interval=None) / 100
    yield metric_api.Observation(cpu_util)

def create_resource_instruments(meter: metric_api.Meter) -> dict:
    cpu_util_gauge = meter.create_observable_gauge(
        name="process.cpu.utilization",
        callbacks=[get_cpu_utilization],
        unit="1",
        description="CPU utilization since last call",
    )

    instruments = {
        "cpu_utilization": cpu_util_gauge
    }
    return instruments