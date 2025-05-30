import calendar
from itertools import count
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from .models import *
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Max, F ,Sum,Min,Count
# from django.contrib.postgres.aggregates import ArrayAgg
import json
from django.db.models.functions import TruncDate
from LMS_Project.Blobstorage import *
from .AppUsage import update_app_usage
from django.core.cache import cache
from.ErrorLog import *


@api_view(['POST'])
def submit_Tickets(request):
    try:
        data = json.loads(request.body)
        ticket = issue_details.objects.using('mongodb').create(
            student_id = data.get('student_id'),
            image_path = data.get('img_path'),
            issue_description = data.get('issue_description'),
            issue_status = data.get('issue_status','Pending'),
            issue_type = data.get('issue_type'),
            resolved_time = None,
            reported_time = timezone.now() + timedelta(hours=5, minutes=30),
        )
        update_app_usage(data.get('student_id'))
        return JsonResponse({"message": "Success"},safe=False,status=200)
    except Exception as e:
        print(e)
        update_app_usage(data.get('student_id'))
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
@api_view(['GET'])
def fetch_all_tickets(request,student_id):
    try:
        tickets = list(issue_details.objects.using('mongodb').filter(student_id = student_id,del_row = 'False').order_by('-reported_time').values())
        update_app_usage(student_id)
        return JsonResponse({'ticket_details':tickets},safe=False,status=200)
    except Exception as e:
        print(e)
        update_app_usage(student_id)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
@api_view(['PUT'])
def student_side_comments_for_tickets(request):
    try:
        data = json.loads(request.body)
        ticket = issue_details.objects.using('mongodb').get(student_id = data.get('student_id'),sl_id = data.get('t_id'),del_row = 'False')
        keys = sorted([int(str(tk).replace('stu','')) for tk in ticket.comments if str(tk).startswith('stu')])
        print(keys[-1]+1 if len(keys)>0 else [0] )
        ticket.comments.update({
            "stu"+str(keys[-1]+1 if len(keys)>0 else 1): {
                    "role": "student",
                    "comment": data.get('comment'),
                    "timestamp": timezone.now() + timedelta(hours=5, minutes=30)
                    },})
        ticket.save()
        responnse=ticket.comments
        update_app_usage(data.get('student_id'))
        return JsonResponse({'message':responnse},safe=False,status=200)
    except Exception as e:
        print(e)
        update_app_usage(data.get('student_id'))
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)