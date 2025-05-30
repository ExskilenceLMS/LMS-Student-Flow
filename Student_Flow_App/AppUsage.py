
from .models import *
from django.db.models import Max, F ,Sum
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from rest_framework.decorators import api_view
def update_app_usage(student_id):
    try:
        student_app_usages = student_app_usage.objects.filter(
            student_id = student_id,del_row = False).order_by('-logged_out').first()

        if student_app_usages:
            student_app_usages.logged_out = timezone.now().__add__(timedelta(hours=5,minutes=30))
            student_app_usages.save()

        return 
    except Exception as e:
        print(e)
        return 
def create_app_usage(student_id):
    try:
        student = students_info.objects.get(student_id = student_id,del_row = False)
        student_app_usages = student_app_usage.objects.create(
            student_id = student,
            # app_name = 'TEST',
            logged_in = timezone.now().__add__(timedelta(hours=5,minutes=30)),
            logged_out = timezone.now().__add__(timedelta(hours=5,minutes=30)),
            del_row = False
        )
        return  
    except Exception as e:
        print(e)
        return
@api_view(['GET'])   
def clear_blob_ceche(request):
    cache.clear()
    return JsonResponse({"message": "cache cleared"},safe=False,status=200)