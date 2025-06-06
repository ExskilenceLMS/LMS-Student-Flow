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
from django.views.decorators.cache import cache_page
from decouple import config
keys =[
    'SECRET_KEY',
    'DEBUG',
    'MONGO_DB_NAME',
    'MONGO_USER',
    'MONGO_PASSWORD',
    'MONGO_HOST',
    'MONGO_AUTH_MECHANISM',
    'MONGO_CONNECTION_STRING',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
    'DB_HOST',
    'REDIS_HOST',
    'REDIS_CONN_STRING_KEY',
    'REDIS_CONNECTION_STRING',
    'AZURE_ACCOUNT_NAME',
    'AZURE_ACCOUNT_KEY',
    'AZURE_CONTAINER',
    'MSSQL_SERVER_NAME',
    'MSSQL_DATABASE_NAME',
    'MSSQL_USERNAME',
    'MSSQL_PWD',
    'MSSQL_DRIVER'
]
ONTIME = datetime.utcnow().__add__(timedelta(hours=5,minutes=30))
CONTAINER ="internship"
@api_view(['GET'])
def home(request):
    data = {
       key:config(key) for key in keys
    }
    return JsonResponse({
        "message": f"Successfully Deployed LMS on Azure at {ONTIME}",
        "data": data
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
@cache_page(60 * 60 * 24)
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

def migrate():
    try:
        students_data = students_details.objects.using('mongodb').all()
        for student in students_data:
             if student.student_id[3:].startswith('ABC'): 
            #     print(student.student_id,student.student_id[3:])
            #  if student.student_id == "25SABCXIS006":
                 print(student.student_id[3:])
                 old_data = student.student_question_details
                 new_data = {}
                 for course_sub_key in old_data.keys():
                     new_data = {
                         "total_practice_mcq": "0/0",
                        "total_practice_coding": "0/0",
                     }
                     course_id , sub_id = course_sub_key.split('_')
                     for week_num in old_data[course_sub_key].keys():
                         week_id= week_num.split('_')[1]
                         for days_keys in old_data[course_sub_key][week_num].keys():
                            day_id = days_keys.split('_')[1]
                            for days_data in old_data[course_sub_key][week_num][days_keys].keys():
                                if days_data == 'sub_topic_status':
                                    sts =[v for  v  in old_data[course_sub_key][week_num][days_keys][days_data].values()]
                                    if sum(sts) == len(sts)*2:
                                        new_data.update({
                                            f'{course_id}_{sub_id}_{week_id}_{day_id}_sub_topic_status':2
                                        })
                                    elif sum(sts) == 0 :
                                        new_data.update({
                                            f'{course_id}_{sub_id}_{week_id}_{day_id}_sub_topic_status':0
                                        })
                                    elif sum(sts)>0 and sum(sts)<len(sts)*2:
                                        new_data.update({
                                            f'{course_id}_{sub_id}_{week_id}_{day_id}_sub_topic_status':1
                                        })
                                    else: 
                                        print("error")
                                if days_data == 'mcq_score':
                                    mcq = old_data[course_sub_key][week_num][days_keys][days_data]
                                    sec , tot = mcq.split('/')
                                    old_sec , old_tot = new_data.get(f'total_practice_mcq','0/0').split('/')
                                    new_sec = float(old_sec) + float(sec)
                                    new_tot = float(old_tot) + float(tot)
                                    new_data.update({
                                        f'{course_id}_{sub_id}_{week_id}_{day_id}_mcq':mcq,
                                        'total_practice_mcq':f'{new_sec}/{new_tot}'
                                    })
                                if days_data == 'coding_score':
                                    coding = old_data[course_sub_key][week_num][days_keys][days_data]
                                    sec , tot = coding.split('/')
                                    old_sec , old_tot = new_data.get(f'total_practice_coding','0/0').split('/')
                                    new_sec = float(old_sec) + float(sec)
                                    new_tot = float(old_tot) + float(tot)
                                    new_data.update({
                                        f'{course_id}_{sub_id}_{week_id}_{day_id}_coding':coding,
                                        'total_practice_coding':f'{new_sec}/{new_tot}'
                                    })
                                if days_data == 'mcq_questions_status':
                                    mcq = old_data[course_sub_key][week_num][days_keys][days_data]
                                    completed_mcq = [v for  v  in old_data[course_sub_key][week_num][days_keys][days_data].values() if v == 2]
                                    new_data.update({
                                        f'{course_id}_{sub_id}_{week_id}_{day_id}_mcq_questions':str(len(completed_mcq))+'/'+str(len(mcq))
                                    })
                                if days_data == 'coding_questions_status':
                                    coding = old_data[course_sub_key][week_num][days_keys][days_data]
                                    completed_coding = [v for  v  in old_data[course_sub_key][week_num][days_keys][days_data].values() if v == 2]
                                    new_data.update({
                                        f'{course_id}_{sub_id}_{week_id}_{day_id}_coding_questions':  str(len(completed_coding))+'/'+str(len(coding))
                                    })
                #  print(new_data)
                 student.student_score_details = new_data
                 student.save(update_fields=['student_score_details'])

                        

                      

                 
        return JsonResponse({"message": "Successfully Logged Out",
                             }, safe=False, status=200)
    except Exception as e:  
        print(e)
        print(traceback.format_exc())
        return JsonResponse({"message": "Failed",
                             "error": str(e)},safe=False,status=400)    