from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

def create_resource(name: str, version: str) -> Resource:
    svc_rc = Resource.create(
        {
            ResourceAttributes.SERVICE_NAME: name,
            ResourceAttributes.SERVICE_VERSION: version,
        }
    )
    return svc_rc

