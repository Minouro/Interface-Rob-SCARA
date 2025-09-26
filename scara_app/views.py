# scara_app/views.py
from django.shortcuts import render

def interface_view(request):
    return render(request, 'scara_app/interface.html')