from django.http import HttpResponse


def home(request):
    # ...

    # Return a "created" (201) response code.
    response = "<h3> Welcome to Purple Pay! </h3>"
    return HttpResponse(response, status=200)
