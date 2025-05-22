from datetime import datetime, timedelta
import json
from LMS_Mongodb_App.models import *
from LMS_MSSQLdb_App.models import *
import traceback
from django.utils import timezone

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