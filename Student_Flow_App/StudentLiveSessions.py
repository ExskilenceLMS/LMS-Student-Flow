import calendar
from itertools import count
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from LMS_MSSQLdb_App.models import *
from LMS_Mongodb_App.models import *
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
# FETCH STUDENT ONLINE SESSION FOR ENROLLED SUBJECTS

@api_view(['GET'])
def fetch_all_live_session(request,student_id):
    try:
        live_session = list(live_sessions.objects.using('mongodb').filter(student_ids__contains = student_id,
                                                                     del_row = "False"
                                                                     ).order_by('-session_starttime').values(
                                                                         'session_id',
                                                                         'session_title',
                                                                         'session_starttime',
                                                                         'session_meetlink',
                                                                         'session_video_link',
                                                                         'session_status',
                                                                         'session_endtime'
                                                                     ))
        if live_session == []:
            return JsonResponse({"message": "No Live Session"},safe=False,status=200)
        attendance = participant.objects.using('mongodb').filter(session_id__in = [session.get('session_id') for session in live_session],
                                                                     student_id = student_id,
                                                                     del_row = "False"
                                                                     ).order_by('-attended_time').values(
                                                                         'session_id',
                                                                         'student_id',
                                                                         'attended_time',
                                                                     )
        response = [{
                    'id':  session.get('session_id'),
                    'name': session.get('session_title'),
                    'date': session.get('session_starttime').strftime("%Y-%m-%d"),
                    'time': session.get('session_starttime').strftime("%I:%M") + " " + session.get('session_starttime').strftime("%p"),
                    'meet_link': session.get('session_meetlink'),
                    # 'duration': [duration.get('attended_time') for duration in attendance if duration.get('session_id'  ) == str(session.get('session_id'))][0],
                    # 'total_duration': (session.get('session_endtime')-session.get('session_starttime')).total_seconds(),
                    'attendance': '-/-'if session.get('session_status') != 'Completed' else round(([duration.get('attended_time'
                                                                                                                  ) for duration in attendance if duration.get('session_id'  
                                                                                                                                                               ) == str(session.get('session_id'))][0]/(session.get('session_endtime')-session.get('session_starttime')).total_seconds())*100,2),
                    'video_link': session.get('session_video_link'),
                    'ended': True if session.get('session_status') == 'Completed' else False,
                    'status':session.get('session_status')
                    }            for session in live_session ]
        update_app_usage(student_id)
        return JsonResponse((response),safe=False,status=200)
    except Exception as e:
        print(e)
        update_app_usage(student_id)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)