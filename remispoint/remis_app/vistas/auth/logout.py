from django.shortcuts import redirect
from django.contrib.auth import logout

def custom_logout(request):
    logout(request)
    return redirect('login')
