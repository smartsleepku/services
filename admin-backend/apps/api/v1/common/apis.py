from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from apps.users.models import User
from django.conf import settings

def get_settings(request):
    return JsonResponse({'csv_url':settings.CSV_DL_URL})
