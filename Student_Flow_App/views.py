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
from django.core.exceptions import ObjectDoesNotExist
ONTIME = datetime.utcnow().__add__(timedelta(hours=5,minutes=30))
CONTAINER ="internship"
@api_view(['GET'])
def home(request):
    return JsonResponse({
        "message": f"Successfully Deployed LMS on Azure at {ONTIME}"
    }, safe=False, status=200)
@api_view(['GET'])
def login(request, email):          # function name in lower‑snake‑case is conventional
    try:
        user = (
            students_info.objects
            .select_related('batch_id', 'course_id')      # joins on one query
            .only('student_id', 'batch_id__batch_id', 'course_id__course_id')
            .get(student_email=email, del_row=False)
        )
        create_app_usage(user.student_id)

        return JsonResponse(
            {
                "message": "Successfully Logged In",
                "student_id": user.student_id,
                "batch_id": user.batch_id.batch_id,
                "course_id": user.course_id.course_id,
            },
            safe=False,
            status=200,
        )

    except ObjectDoesNotExist:
        payload = {
            "Error_msg": str(e),
            "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}"),
            "Url": request.build_absolute_uri(),
            "Body": "{}",
        }
        return JsonResponse(
            {"message": f"No active student found for email {email}", 
             "error": str(encrypt_message(str(payload)))},
            safe=False,
            status=404,
        )

    except Exception as e:
        payload = {
            "Error_msg": str(e),
            "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}"),
            "Url": request.build_absolute_uri(),
            "Body": "{}",
        }
        return JsonResponse(
            {"message": "Failed", "error": str(encrypt_message(str(payload)))},
            safe=False,
            status=400,
        )
@api_view(['GET'])
def logout(request, student_id):  # lowercase function name for consistency
    try:
        update_app_usage(student_id)
        return JsonResponse({"message": "Successfully Logged Out"}, safe=False, status=200)

    except Exception as e:
        payload = {
            "Error_msg": str(e),
            "Stack_trace": traceback.format_exc()+\
                '\nUrl:-'+str(request.build_absolute_uri())+\
                    '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}"),
            "Url": request.build_absolute_uri(),
            "Body": "{}",
        }
        return JsonResponse(
            {"message": "Failed", "error": str(encrypt_message(str(payload)))},
            safe=False,
            status=400,
        )
    
@api_view(['GET'])
def fetch_FAQ(request):
    try: 
        return JsonResponse(json.loads(get_blob('faq/faq.json')),safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)

@api_view(['POST'])
def get_media(request):
    try:
        data = json.loads(request.body)
        blob_name = data.get('file_url')
        if blob_name == '':
            return JsonResponse({"message": "Failed",
                                 "error":str(encrypt_message(str({
                                        "Error_msg": "file_url is empty",
                                        "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                        })))},safe=False,status=400)
        sas_token = generate_blob_sas(
            account_name=AZURE_ACCOUNT_NAME,
            container_name=AZURE_CONTAINER,
            blob_name=blob_name,
            account_key=AZURE_ACCOUNT_KEY,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(minutes=15)
        )
        blob_path =f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_CONTAINER}/{blob_name}?{sas_token}"
        response = requests.get(blob_path, stream=True)
        response.raise_for_status()
        path = urlparse(blob_path).path
        content_type, _ = mimetypes.guess_type(path)
        if content_type is None:
            content_type = 'application/octet-stream'
        return StreamingHttpResponse(
            response.iter_content(chunk_size=10*1024),  # 10 KB chunks
            content_type=content_type
        )
    except requests.RequestException as err:
        print(err)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(err),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
# ===========================================================TESTING SPACE ===========================================================================================
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
# from datetime import datetime, timedelta

@api_view(['POST'])
def generate_secure_blob_url(request):
    try:
        data = json.loads(request.body)
        blob_name = data.get('file_url')
        if blob_name == '':
            return JsonResponse({"message": "Failed",
                                 "error":str(encrypt_message(str({
                                        "Error_msg": "file_url is empty",
                                        "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                        })))},safe=False,status=400)
        sas_token = generate_blob_sas(
            account_name=AZURE_ACCOUNT_NAME,
            container_name=AZURE_CONTAINER,
            blob_name=blob_name,
            account_key=AZURE_ACCOUNT_KEY,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(minutes=15)
        )
        blob_path =f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_CONTAINER}/{blob_name}?{sas_token}"
        if  blob_name.split('.')[1] == 'pdf':
            response = requests.get(blob_path, stream=True)
            response.raise_for_status()
            path = urlparse(blob_path).path
            content_type, _ = mimetypes.guess_type(path)
            if content_type is None:
                content_type = 'application/octet-stream'
            return StreamingHttpResponse(
                response.iter_content(chunk_size=10*1024),  # 10 KB chunks
                content_type=content_type
            )
        return JsonResponse({"message": "Successfully Logged Out",
                             "url":blob_path}, safe=False, status=200)
    
    except requests.RequestException as err:
        print(err)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(err),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
