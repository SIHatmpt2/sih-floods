from django.shortcuts import render


def home(request):
    """Render the server-side Django frontend shell."""
    return render(request, "home.html")
