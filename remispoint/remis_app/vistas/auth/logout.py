from django.shortcuts import redirect
from django.contrib.auth import logout

def custom_logout(request):
    logout(request)  # ❌ No necesita "user"
    return redirect('login')

