from django.shortcuts import render


def home(request):
    """Render the server-side Django frontend."""
    return render(request, "index.html")
