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

# FETCH STUDENT ENROLLED SUBJECTS
@api_view(['GET'])
def fetch_enrolled_subjects(request,student_id):
    try:
        student_data = students_info.objects.get(student_id = student_id,del_row = False)
        enrolled_subjects = course_subjects.objects.filter(course_id = student_data.course_id,del_row = False)
        latest_activities = student_activities.objects.filter(student_id=student_id,del_row=False).values('subject_id__subject_name').annotate(latest_day=Max('activity_day'))
        sub_days_count = {}
        [sub_days_count.update({activity['subject_id__subject_name']:{'day':activity['latest_day']}})for activity in latest_activities]
        # print(sub_days_count)
        response = []
        for subject in enrolled_subjects:
            subject_data = {}
            subject_data.update({
                "title": subject.subject_id.subject_name,
                "subject": str(subject.subject_id.subject_name).replace(' ',''),
                "subject_id": subject.subject_id.subject_id,
                "image": subject.path,
                "duration": f"{getdays(subject.start_date)} - {getdays(subject.end_date)}",
                "progress": calculate_progress(subject.start_date,subject.end_date,sub_days_count.get(subject.subject_id.subject_name,{'day':0}),subject.duration_in_days),
            })
            response.append(subject_data)
        update_app_usage(student_id)
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)    
def calculate_progress(start_date, end_date, student_progress,Total_days):
    days = student_progress.get('day')
    std_progress = int(days /int(Total_days) * 100)
    response = {
        "student_progress": std_progress if std_progress <= 100 else 100
    }
    current_date = datetime.utcnow().__add__(timedelta(days=17,hours=5,minutes=30))
    if current_date.date() < start_date.date() :
        response.update({"progress": 0})
        return response
    start_date = datetime.strptime(str(start_date).split('.')[0], "%Y-%m-%d %H:%M:%S")
    end_date = datetime.strptime(str(end_date).split('.')[0], "%Y-%m-%d %H:%M:%S")
    progress =(((current_date - start_date).days / (end_date - start_date).days) * 100)
    response.update({"progress": int(progress) if progress <= 100 else 100})
    return  response

def getdays(date):
       date = datetime.strptime(str(date).split('.')[0], "%Y-%m-%d %H:%M:%S")
       day = int(date.strftime("%d"))
       month = int(date.strftime("%m"))
       if 4 <= day <= 20 or 24 <= day <= 30:
           suffix = "th"
       else:
           suffix = ["st", "nd", "rd"][day % 10 - 1]
       formatted_date =  (f"{day}{suffix} {calendar.month_abbr[month]} {date.strftime('%Y')[2:]}")
       return formatted_date

# FETCH LIVE SESSION
@api_view(['GET'])
def fetch_live_session(request,student_id):
    try:
        print(student_id)
        current_time = timezone.now() + timedelta(hours=5, minutes=30)
        if timezone.is_naive(current_time):
            current_time = timezone.make_aware(current_time, timezone.get_current_timezone())
        live_session = live_sessions.objects.using('mongodb').filter(
            session_starttime__gte=current_time,
            student_ids__contains = student_id,
            del_row = "False"
            ).order_by('-session_starttime').values_list('session_title','session_starttime')
        response = [{
            "title":session[0],
            "date":getdays(session[1])+" "+session[1].strftime("%Y")[2:],
            "time":session[1].strftime("%I:%M") + " " + session[1].strftime("%p")}            for session in live_session ]
        update_app_usage(student_id)
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
    
@api_view(['GET'])
def fetch_upcoming_events(request,Course_id):
    try:
        print(Course_id)
        current_time = datetime.utcnow() + timedelta(days=0,hours=5, minutes=30)
        blob_data = json.loads(get_blob('LMS_DayWise/Course0001.json'))
        response = extract_events(blob_data,current_time)
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
    
def extract_events(blob_data,current_time):
    events = []
    for event in blob_data:
        for i in blob_data.get(event):
            if i.get('topic') == 'Weekly Test' or i.get('topic') == 'Onsite Workshop' or i.get('topic') == 'Internship':
                date = datetime.strptime(str(i.get('date').replace('T',' ')).split('.')[0], "%Y-%m-%d %H:%M:%S") if str(i.get('date')).__contains__('T') else datetime.strptime(str(i.get('date')+" 00:00:00").split('.')[0], "%Y-%m-%d %H:%M:%S")
                events.append({
                    "title":i.get('topic'),
                    'subject':event,
                    "date":getdays(date)+" "+date.strftime("%Y")[2:],
                    "time":date.strftime("%I:%M") + " " + date.strftime("%p"),
                    'datetime':date
                })
    events = sorted(events, key=lambda k: k['datetime'])
    upcoming = [ event for event in events if event['datetime'].date() >= current_time.date()]
    return upcoming

# FETCH  STUDY HOURS

@api_view(['GET'])
def fetch_study_hours(request,student_id,week):
    try:
        student = students_info.objects.get(student_id = student_id,del_row = False)
        today =timezone.now() + timedelta(hours=5, minutes=30)
        start_of_week = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        if timezone.is_naive(today):
            today = timezone.make_aware(today, timezone.get_current_timezone())
        if week.isdigit():
            current_week = int(week)
        else:
            current_week = course_plan_details.objects.get(course_id = student.course_id,
                                                            day_date__date=today.date(),
                                                            del_row =False)
            if current_week is None:
                current_week =1,
            else:
                current_week=current_week.week
        course_details = list(course_plan_details.objects.filter(course_id=student.course_id,
                                                            week=current_week).values('duration_in_hours','day_date'))
        if week.isdigit():
            start_of_week = (course_details[0].get('day_date') - timedelta(days=course_details[0].get('day_date').weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        student_app_usages = student_app_usage.objects.filter(student_id = student_id,
                                                            #   logged_in__gte = course_details[0].get('day_date'),
                                                            #   logged_in__lte = course_details[-1].get('day_date')+timedelta(days=1),
                                                              logged_in__gte = start_of_week,
                                                              logged_in__lte = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59),
                                                              del_row = False
                                                            ).annotate(date=TruncDate('logged_in')).values('date').annotate(
                                                            total_study_hours=Sum(F('logged_out') - F('logged_in'))).order_by('date')
        list_of_duration = [i.get("duration_in_hours")  for i in  course_details]
        response = {'daily_limit':sum(list_of_duration)/len(list_of_duration) if list_of_duration else 0,
                    'weekly_limit':current_week,
                    'hours':[]}
        hour_spent ={ i.get('date'):i.get('total_study_hours') for i in student_app_usages}
        for i in range(7):
            response.get('hours').append({
                "date":start_of_week + timedelta(days=i),
                "day_name":calendar.day_name[(start_of_week + timedelta(days=i)).weekday()][0:3],
                "isUpcoming":True if (start_of_week + timedelta(days=i)).date() > today.date() else False,
                "isCurrent":True if (start_of_week + timedelta(days=i)).date() == today.date() else False,
                "hours":round(hour_spent.get((start_of_week + timedelta(days=i)).date()).total_seconds()/3600,2) if hour_spent.get((start_of_week + timedelta(days=i)).date()) else 0
            })
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)

#    FETCH CALENDAR
      
@api_view(['GET'])
def fetch_calendar(request,student_id):
    try:
        current_time = datetime.utcnow() + timedelta(days=0,hours=5, minutes=30)
        blob_data = json.loads(get_blob('LMS_DayWise/Course0001.json'))
        student = students_info.objects.get(student_id = student_id,del_row = False)
        response = extract_calendar_events(blob_data,current_time)
        return JsonResponse({'year':(current_time.strftime("%Y")),
                              'month':str(int(current_time.strftime("%m"))-1),
                              "calendar":response},
                              safe=False,status=200)    
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
def extract_calendar_events(blob_data,current_time):
    events = []
    for event in blob_data:
        for i in blob_data.get(event):
            if i.get('topic') == 'Weekly Test' or i.get('topic') == 'Onsite Workshop' or i.get('topic') == 'Internship':
                date = datetime.strptime(str(i.get('date').replace('T',' ')).split('.')[0], "%Y-%m-%d %H:%M:%S") if str(i.get('date')).__contains__('T') else datetime.strptime(str(i.get('date')+" 00:00:00").split('.')[0], "%Y-%m-%d %H:%M:%S")
                events.append({
                    "title":i.get('topic'),
                    'subject':event,
                    "date":getdays(date)+" "+date.strftime("%Y"),
                    "time":date.strftime("%I:%M") + " " + date.strftime("%p"),
                    'datetime':date.date()
                })
    events = sorted(events, key=lambda k: k['datetime'])
    this_month = [event for event in events if calendar.month_abbr[int(event['datetime'].strftime("%m"))]==calendar.month_abbr[int(current_time.strftime("%m"))]]
    return this_month 

#    FETCH STUDENT SUMMARY

@api_view(['GET'])
def fetch_student_summary(request,student_id):
    try:
        student = students_info.objects.get(student_id = student_id,del_row = False)
        student_app_usages = student_app_usage.objects.filter(student_id = student_id,
                                                              del_row = False
                                                            ).aggregate(
                                                            total_seconds=Sum(F('logged_out') - F('logged_in')))
        print(student_app_usages.get('total_seconds'))
        response ={
            'student_id': student.student_id,
            'name': student.student_firstname+' '+student.student_lastname,
            'score':student.student_score,
            'hour_spent':round(student_app_usages.get('total_seconds').total_seconds()/3600,2),
            'category':student.student_catogory,
            'college_rank':student.student_college_rank,
            'overall_rank':student.student_overall_rank

        }
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)   
    
#    FETCH WEEKLY PROGRESS

@api_view(['GET'])
def get_weekly_progress(request,student_id):
    try:
        # obj = students_info.objects.get( student_id = student_id,del_row = False)
        assessment_data = students_assessments.objects.using('mongodb').filter(
            student_id = student_id,
            del_row = "False"
            ).order_by('-assessment_week_number').values_list('assessment_week_number','assessment_score_secured','assessment_max_score')
        practice_data = practice_questions.objects.using('mongodb').filter(
            student_id = student_id,
            del_row = "False"
            ).order_by('-practice_week_number').values_list('practice_week_number','practice_score_secured','practice_max_score')
        return JsonResponse({
            "assessment":list(assessment_data),
            "practice":list(practice_data),
                })
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++[OLD METHODS]+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++# 
    
# OLD 

@api_view(['GET'])
def fetch_study_hours_old(request,student_id,week):
    try:
        week = int(week)
        student = students_info.objects.get(student_id = student_id,del_row = False)
        course_subjects_data = course_subjects.objects.filter(course_id = student.course_id,del_row = False
                                                              ).values('subject_id__subject_name','duration_in_days','start_date','end_date')
        subjects ={}
        currentweek = {}
        for subject in course_subjects_data:
            weeks = []
            initial_date = subject.get('start_date')
            final_date = subject.get('end_date')
            today = timezone.now() + timedelta(days=7,hours=5, minutes=30)
            if  final_date < today or today < initial_date :
                break
            i = 1
            while initial_date <= final_date:
                week_start = initial_date - timedelta(days=initial_date.weekday())
                week_end = week_start + timedelta(days=6)  
                weeks.append({
                    'start': week_start.date(),
                    'end': week_end.date()
                })
                if timezone.is_naive(today):
                    today = timezone.make_aware(today, timezone.get_current_timezone())
                if week_start <= today<= week_end:
                    currentweek.update({subject.get('subject_id__subject_name'):i})
                    break
                i += 1
                initial_date = week_end + timedelta(days=1)
            subjects.update({subject.get('subject_id__subject_name'):weeks})
        subjects = subjects.get(list(currentweek.keys())[0])[currentweek.get(list(currentweek.keys())[0]) - 1]
        student_app_usages = student_app_usage.objects.filter(student_id = student_id,
                                                              logged_in__gte = subjects.get('start'),
                                                              logged_in__lte = subjects.get('end')+timedelta(days=1),
                                                              del_row = False
                ).annotate(date=TruncDate('logged_in')).values('date').annotate(
                total_study_hours=Sum(F('logged_out') - F('logged_in'))).order_by('date')
        response = {'daily_limit':2.0,
                    'weekly_limit':currentweek.get(list(currentweek.keys())[0]),
                    'hours':[]}
        hour_spent ={ i.get('date'):i.get('total_study_hours') for i in student_app_usages}
        for i in range(7):
            response.get('hours').append({
                "date":subjects.get('start') + timedelta(days=i),
                "day_name":calendar.day_name[(subjects.get('start') + timedelta(days=i)).weekday()][0:3],
                "isUpcoming":True if subjects.get('start') + timedelta(days=i) > datetime.utcnow().__add__(timedelta(hours=5,minutes=30)).date() else False,
                "isCurrent":True if subjects.get('start') + timedelta(days=i) == datetime.utcnow().__add__(timedelta(hours=5,minutes=30)).date() else False,
                "hours":round(hour_spent.get(subjects.get('start') + timedelta(days=i)).total_seconds()/3600,2) if hour_spent.get(subjects.get('start') + timedelta(days=i)) else 0
            })
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
