from django.http import HttpResponse
from django.conf import settings
import json


def home(request):
    # ...

    # Return a "created" (201) response code.
    response = "<h3> Welcome to Purple Pay! </h3>"
    #value = json.dumps({"api_key": "jsdljfdsjdfldksjfdslfjlsdf", "data": {"a": "hi"}}).encode('utf-8')
    #settings.KAFKA_PRODUCER.produce('my-kafka-topic', key='test', value=value)
    return HttpResponse(response, status=200)
