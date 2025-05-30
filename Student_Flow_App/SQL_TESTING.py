import calendar
from itertools import count
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse,StreamingHttpResponse
from rest_framework.decorators import api_view
from .models import *
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Max, F ,Sum,Min,Count
# from django.contrib.postgres.aggregates import ArrayAgg
import mimetypes
from urllib.parse import urlparse
import json
import requests
from django.db.models.functions import TruncDate
from LMS_Project.Blobstorage import *
from LMS_Project.settings import * 
from .AppUsage import update_app_usage, create_app_usage
from django.core.cache import cache
from .ErrorLog import *
@api_view(['GET'])
def get_mcqs (request):
    try:
        Questions = questions.objects.filter(question_type="mcq",del_row = False).order_by('question_id')
        container_client = get_blob_container_client()
        question_list = []
        for question in Questions:
            if question.question_id[1:3] != 'sq':
                continue
            Qn = question.question_id
            path = f"subjects/{Qn[1:3]}/{Qn[1:-7]}/{Qn[1:-5]}/{'mcq' if Qn[-5]=='m' else 'coding'}/{Qn}.json"
            print(path)
            if cache.get(path) == None:
                blobdata = container_client.get_blob_client(path)
                blob_data = json.loads(blobdata.download_blob().readall())
                blob_data.update({'Qn_name':Qn})
                cache.set(path,blob_data)
            else:
                blob_data = cache.get(path)
                cache.set(path,blob_data)
            question_list.append(blob_data)
        print(len(question_list))
        container_client.close()
        return JsonResponse(question_list,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)