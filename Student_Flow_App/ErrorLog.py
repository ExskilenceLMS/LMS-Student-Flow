from datetime import datetime, timedelta
import json
from django.http import JsonResponse
from LMS_Mongodb_App.models import *
from LMS_MSSQLdb_App.models import *
import traceback
from django.utils import timezone
from rest_framework.decorators import api_view
from cryptography.fernet import Fernet
import ast, json

# key = Fernet.generate_key()
key = b'kOt0aprdFA1-Zj-w6fENiZOf7IVfgnPjv_-usgnBA5s='
# print("key:", key, len(key.split()))
cipher_suite = Fernet(key)

def encrypt_message(message: str) -> bytes:
    return cipher_suite.encrypt(message.encode())

def decrypt_message(encrypted_message: bytes) -> str:
    return cipher_suite.decrypt(encrypted_message).decode()
def ErrorLog(req,e):
    try:
        u_agent = str(req.META.get('HTTP_USER_AGENT'))
        os_info = str(u_agent)[u_agent.find("(")+1:u_agent.find(")")]
        error = {
            "student_id": json.loads( req.body).get('student_id'),
            "Error_msg": str(e),
            "Stack_trace": str(traceback.format_exc())+'\nUrl:-'+str(req.build_absolute_uri())+'\nBody:-'+str(json.loads( req.body)),
            "User_agent": u_agent,
            "Operating_sys": os_info ,
        }
        try:
            std   = students_info.objects.get(student_id=error.get('student_id'))
        except:
            std = None
        Time  = timezone.now().__add__(timedelta(hours=5,minutes=30))
        ErrorLog = ErrorLogs.objects.using('mongodb').create(
            student_id=error.get('student_id'),
            Email=std.student_email if std else json.loads(req.body).get('Email'),
            Name = str(std.student_firstname)+' '+str(std.student_lastname) if std else json.loads(req.body).get('Name'),
            Occurred_time = Time,
            URL_and_Body = 'Url:-'+str(req.build_absolute_uri())+'\nBody:-'+str(json.loads( req.body)),
            Error_msg = error.get('Error_msg'),
            Stack_trace = error.get('Stack_trace'),
            User_agent = error.get('User_agent'),
            Operating_sys = error.get('Operating_sys'),
            )
        return True 
    except Exception as e:
        print(e)
        return False
    
@api_view(['POST'])
def Upload_ErrorLog(req):
    try:
        data = json.loads(req.body)
        enc_data = data.get('error')
        Time  = datetime.now(timezone.utc).__add__(timedelta(hours=5,minutes=30))
        if isinstance(enc_data, str) and enc_data.startswith("b'"):
            enc_data = eval(enc_data) 
        raw = cipher_suite.decrypt(enc_data).decode()
        decrypted_data = json.loads(raw) if raw.strip().startswith('{"') else ast.literal_eval(raw)
        u_agent = str(req.META.get('HTTP_USER_AGENT'))
        ErrorLog = ErrorLogs.objects.using('mongodb').create(
            student_id  =data.get('student_id'),
            Email       =data.get('Email'),
            Name        = data.get('Name'),
            URL_and_Body = data.get('URL_and_Body'),
            Occurred_time = Time,
            Error_msg = decrypted_data.get('Error_msg'),
            Stack_trace =  decrypted_data.get('Stack_trace'),
            User_agent =  u_agent,
            Operating_sys = str(u_agent)[u_agent.find("(")+1:u_agent.find(")")],
            )
        return JsonResponse({"message": "Successfully Uploaded Error Log"},safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)