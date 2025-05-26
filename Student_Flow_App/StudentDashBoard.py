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
from .ErrorLog import *
# FETCH STUDENT ENROLLED SUBJECTS
@api_view(['GET'])
def fetch_enrolled_subjects(request,student_id):
    try:
        student_data = students_info.objects.get(student_id = student_id,del_row = False)
        enrolled_subjects = course_subjects.objects.filter(course_id = student_data.course_id, batch_id = student_data.batch_id,del_row = False)
        latest_activities = student_activities.objects.filter(student_id=student_id,del_row=False).values('subject_id__subject_name').annotate(latest_day=Max('activity_day'))
        sub_days_count = {}
        [sub_days_count.update({activity['subject_id__subject_name']:{'day':activity['latest_day']}})for activity in latest_activities]
        
        demo = [
             {
        "title": "Python",
        "subject": "Python",
        "subject_id": "sr",
        "image": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?q=80&w=2069&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "duration": "25th Apr 25 - 15th May 25",
        "progress": {
            "student_progress": 0,
            "progress": 100
        },
        'status': 'Closed'
    },
      {
        "title": "Web Application",
        "subject": "Web Application",
        "subject_id": "sr",
        "image": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?q=80&w=2069&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "duration": "15th May 25 - 15th June 25",
        "progress": {
            "student_progress": 0,
            "progress": 100
        },
        'status': 'Closed'
    },
      {
        "title": "480hrs Internship",
        "subject": "480hrs Internship",
        "subject_id": "sr",
        "image": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?q=80&w=2069&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "duration": "15th June 25 - 15th Sept 25",
        "progress": {
            "student_progress": 0,
            "progress": 100
        },
        'status': 'Closed'
    },{
        "title": "DSA ",
        "subject": "DSA ",
        "subject_id": "sr",
        "image": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?q=80&w=2069&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "duration": "15th Sept 25 - 15th Oct 25",
        "progress": {
            "student_progress": 0,
            "progress": 100
        },
        'status': 'Closed'
    },
    {
        "title": "Placement Preparation",
        "subject": "Placement Preparation",
        "subject_id": "sr", 
        "image": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?q=80&w=2069&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "duration": "15th Oct 25 - 15th Nov 25",
        "progress": {
            "student_progress": 0,
            "progress": 100
        },
        'status': 'Closed'
    }
        ]
        response = []
        current_time = timezone.now() + timedelta(hours=5, minutes=30)
        if timezone.is_naive(current_time):
            current_time = timezone.make_aware(current_time, timezone.get_current_timezone())
        for subject in enrolled_subjects:
            if subject.subject_id.del_row :
                continue
            subject_data = {}
            # print(sub_days_count,subject.duration_in_days)
            subject_data.update({
                "title": subject.subject_id.subject_name,
                "subject": str(subject.subject_id.subject_name).replace(' ',''),
                "subject_id": subject.subject_id.subject_id,
                "image": subject.path,
                "duration": f"{getdays(subject.start_date)} - {getdays(subject.end_date)}",
                "progress": calculate_progress(subject.start_date,subject.end_date,sub_days_count.get(subject.subject_id.subject_name,{'day':0}),subject.duration_in_days),
                'status': 'Open' if (subject.end_date > current_time and subject.start_date < current_time) or (subject.end_date < current_time ) else 'Closed'
            })
            response.append(subject_data)
        # if str(student_data.course_id) == 'DEMO15' :
        #     if str(student_data.batch_id) == 'DEMOBatch1' :  
        #        response.extend(demo)
        # update_app_usage(student_id)
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        # update_app_usage(student_id)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
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
    start_date = datetime.strptime(str(start_date).split('.')[0].split('+')[0], "%Y-%m-%d %H:%M:%S")
    end_date = datetime.strptime(str(end_date).split('.')[0].split('+')[0], "%Y-%m-%d %H:%M:%S")
    progress =(((current_date - start_date).days / (end_date - start_date).days) * 100)
    response.update({"progress": int(progress) if progress <= 100 else 100})
    return  response

def getdays(date):
       date = datetime.strptime(str(date).split('.')[0].split('+')[0], "%Y-%m-%d %H:%M:%S")
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
            "date":getdays(session[1]),#+" "+session[1].strftime("%Y")[2:],
            "time":session[1].strftime("%I:%M") + " " + session[1].strftime("%p")}            for session in live_session ]
        # update_app_usage(student_id)
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
    
@api_view(['GET'])
def fetch_upcoming_events(request,Course_id,batch_id):
    try:
        current_time = datetime.utcnow() + timedelta(days=0,hours=5, minutes=30)
        # blob_data = json.loads(get_blob('LMS_DayWise/Course0001.json'))
        blob_data = json.loads(get_blob(f'lms_daywise/{Course_id}/{Course_id}_{batch_id}.json'))
        response = extract_events(blob_data,current_time)
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
    
def extract_events(blob_data,current_time):
    events = []
    for event in blob_data:
        for i in blob_data.get(event):
            if i.get('topic') == 'Weekly Test' or i.get('topic') == 'Onsite Workshop' or i.get('topic') == 'Internship':
                date = datetime.strptime(str(i.get('date').replace('T',' ')).split('.')[0], "%Y-%m-%d %H:%M:%S") if str(i.get('date')).__contains__('T') else datetime.strptime(str(i.get('date')+" 00:00:00").split('.')[0], "%Y-%m-%d %H:%M:%S")
                events.append({
                    "title":i.get('topic'),
                    'subject':event,
                    "date":getdays(date),#+" "+date.strftime("%Y")[2:],
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
        today =timezone.now() + timedelta(days=0,hours=5, minutes=30)
        start_of_week = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        if timezone.is_naive(today):
            today = timezone.make_aware(today, timezone.get_current_timezone())
        if week.isdigit():
            current_week = int(week)
        else:
            current_weeks = course_plan_details.objects.filter(course_id = student.course_id,
                                                           batch_id = student.batch_id,
                                                            day_date__date__lte=today.date(),
                                                            del_row =False).values('week','day_date').order_by('-week')
            if current_weeks is None or len(current_weeks) == 0 :
                current_week = 1
            else:
                if current_weeks[0].get('day_date').date() < today.date():
                    diff = today.date() - current_weeks[0].get('day_date').date()
                    diff_in_weeks = diff.days // 7
                    current_week = current_weeks[0].get('week') + diff_in_weeks
                else:
                    current_week=current_weeks[0].get('week')
        course_details = list(course_plan_details.objects.filter(course_id=student.course_id,
                                                                batch_id = student.batch_id,
                                                            week=current_week).values('duration_in_hours','week','day_date').order_by('-week'))
        if len(course_details) == 0:
            course_details = list(course_plan_details.objects.filter(course_id=student.course_id,
                                                                batch_id = student.batch_id).values('duration_in_hours','week','day_date').order_by('-week'))
            start_of_week = today.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=today.weekday())
        else:
            if week.isdigit():
                start_of_week = (course_details[0].get('day_date') - timedelta(days=course_details[0].get('day_date').weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        student_app_usages = student_app_usage.objects.filter(student_id = student_id,
                                                            #   logged_in__gte = course_details[0].get('day_date'),
                                                            #   logged_in__lte = course_details[-1].get('day_date')+timedelta(days=1),
                                                              logged_in__gte = start_of_week,
                                                              logged_in__lte = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59),
                                                              del_row = False
                                                            ).annotate(date=TruncDate('logged_in'),duration_in_hours=Sum(F('logged_out') - F('logged_in'))).values('date','duration_in_hours','student_id')\
                                                                .annotate(
                                                            total_study_hours=Sum(F('logged_out') - F('logged_in'))).order_by('date')       
        list_of_duration = [i.get("duration_in_hours")  for i in  course_details]
        response = {'daily_limit':round(sum(list_of_duration)/len(list_of_duration)) if list_of_duration else 0,
                    'weekly_limit':course_details[0].get('week')+(today.date() - course_details[0].get('day_date').date()).days//7,
                    'hours':[]}
        hour_spent ={ i.get('date'):i.get('total_study_hours') for i in student_app_usages}
        hour_spent2 ={ i.get('date'):round(i.get('duration_in_hours').total_seconds()/3600,2) for i in student_app_usages}
        for i in range(7):
            response.get('hours').append({
                "date":start_of_week + timedelta(days=i),
                "day_name":calendar.day_name[(start_of_week + timedelta(days=i)).weekday()][0:3],
                "isUpcoming":True if (start_of_week + timedelta(days=i)).date() > today.date() else False,
                "isCurrent":True if (start_of_week + timedelta(days=i)).date() == today.date() else False,
                "hours":round(hour_spent.get((start_of_week + timedelta(days=i)).date()).total_seconds()/3600,2) if hour_spent.get((start_of_week + timedelta(days=i)).date()) else 0
            })
        # update_app_usage(student_id) 
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        # update_app_usage(student_id)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)

#    FETCH CALENDAR
      
@api_view(['GET'])
def fetch_calendar(request,student_id):
    try:
        current_time = datetime.utcnow() + timedelta(days=0,hours=5, minutes=30)
        # blob_data = json.loads(get_blob('LMS_DayWise/Course0001.json'))
        student = students_info.objects.get(student_id = student_id,del_row = False)
        blob_data = json.loads(get_blob(f'lms_daywise/{student.course_id.course_id}/{student.course_id.course_id}_{student.batch_id.batch_id}.json'))
        response = extract_calendar_events(blob_data,current_time)
        # update_app_usage(student_id)
        return JsonResponse({'year':(current_time.strftime("%Y")),
                              'month':str(int(current_time.strftime("%m"))-1),
                              "calendar":response},
                              safe=False,status=200)    
    except Exception as e:
        print(e)
        # update_app_usage(student_id)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
def extract_calendar_events(blob_data,current_time):
    events = []
    for event in blob_data:
        for i in blob_data.get(event):
            if i.get('topic') == 'Weekly Test' or i.get('topic') == 'Onsite Workshop' or i.get('topic') == 'Internship':
                date = datetime.strptime(str(i.get('date').replace('T',' ')).split('.')[0], "%Y-%m-%d %H:%M:%S") if str(i.get('date')).__contains__('T') else datetime.strptime(str(i.get('date')+" 00:00:00").split('.')[0], "%Y-%m-%d %H:%M:%S")
                events.append({
                    "title":i.get('topic'),
                    'subject':event,
                    "date":getdays(date),#+" "+date.strftime("%Y"),
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
        
        student_app_usages_by_student = {student_id:student_app_usages.get('total_seconds') for i in student_app_usages}
        # student_app_usages = student_app_usage.objects.filter(student_id = student_id,
        #                                                     #   logged_in__gte = course_details[0].get('day_date'),
        #                                                     #   logged_in__lte = course_details[-1].get('day_date')+timedelta(days=1),
        #                                                     #   logged_in__gte = start_of_week,
        #                                                     #   logged_in__lte = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59),
        #                                                       del_row = False
        #                                                     ).annotate(date=TruncDate('logged_in')).values('date').annotate(
        #                                                     total_study_hours=Sum(F('logged_out') - F('logged_in'))).order_by('date')
        # student_app_usages_by_student = {student_id:i.get('total_study_hours') for i in student_app_usages}
        # print(student_app_usages)
        # print(student_app_usages_by_student)
        response ={
            'student_id': student.student_id,
            'name': student.student_firstname+' '+student.student_lastname,
            'score':student.student_score,
            'hour_spent':round(student_app_usages_by_student.get(student_id).total_seconds()/3600,2),
            'category':student.student_catogory,
            'college_rank':student.student_college_rank if student.student_college_rank >=0 else '--',
            'overall_rank':student.student_overall_rank if student.student_college_rank >=0 else '--',
        }
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400) 
    
#    FETCH WEEKLY PROGRESS

# @api_view(['GET'])
# def get_weekly_progress(request,student_id):
#     try:
#         # obj = students_info.objects.get( student_id = student_id,del_row = False)
#         assessment_data = students_assessments.objects.using('mongodb').filter(
#             student_id = student_id,
#             del_row = "False"
#             ).order_by('-assessment_week_number').values_list('assessment_week_number','assessment_score_secured','assessment_max_score')
#         practice_data = student_test_questions.objects.using('mongodb').filter(
#             student_id = student_id,
#             del_row = "False"
#             ).order_by('-practice_week_number').values_list('practice_week_number','practice_score_secured','practice_max_score')
#         return JsonResponse({
#             "assessment":list(assessment_data),
#             "practice":list(practice_data),
#                 })
#     except Exception as e:
#         print(e)
#         return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++[OLD METHODS]+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++# 
    
@api_view(['GET'])
def get_weekly_progress(request,student_id):
    try:
        All_scores ={
            'Weekly Tests' : '0/0',
            'Practice MCQs':'0/0',
            'Practice Codings':'0/0'
        }
        filters_subject =['All']
        filters_weeks =[]        
        filters_subject_week ={
            'All':["Weekly Tests","Practice MCQs","Practice Codings"]
        }
        mcqScores ={}
        codingScore ={}
        delays ={
            'All':0
        }
        student_info = students_info.objects.get( student_id = student_id,del_row = False)
        PracticeQNs_score = students_details.objects.using('mongodb').get( student_id = student_id,\
                                                                del_row = "False"\
                                                                )
        assessments = students_assessments.objects.filter(
                                    student_id=student_id,
                                    del_row=False
                                    ).values('assessment_type','subject_id__subject_id','subject_id__subject_name','course_id__course_id','assessment_week_number',
                                         'assessment_status','assessment_completion_time','assessment_max_score','assessment_score_secured',
                                         'student_test_completion_time')
                                # ).values('assessment_type','subject_id__subject_name','assessment_week_number').annotate(
                                #     count=Count('id'),
                                #     max_score=Sum('assessment_max_score'),
                                #     total_secured_score=Sum('assessment_score_secured')
                                # )
        # print (assessments)
        subject_names = {student_info.course_id.course_id+'_'+sub.subject_id:sub.subject_name for sub in subjects.objects.filter(del_row =False).all()}
        subject_names_with_id = {sub.subject_id:sub.subject_name for sub in subjects.objects.filter(del_row =False).all()}
        # print(subject_names)
        # print("subject_names_with_id\n",subject_names_with_id)          
        for i in PracticeQNs_score.student_question_details:
            filters_subject.append(subject_names.get(i))
            for week in PracticeQNs_score.student_question_details.get(i):
                filters_weeks.append(week.replace('_',' '))
                if filters_subject_week.get(subject_names.get(i)) == None:
                    filters_subject_week.update({subject_names.get(i):[]})
                filters_subject_week.get(subject_names.get(i)).append(week.replace('_',' '))
                week_mcq_scores =0
                week_coding_scores =0
                week_mcq_total_scores =0
                week_coding_total_scores =0
                for day in PracticeQNs_score.student_question_details.get(i).get(week):
                    day = PracticeQNs_score.student_question_details.get(i).get(week).get(day)
                    week_mcq_scores = week_mcq_scores + float(day.get('mcq_score','0/0').split('/')[0])
                    week_mcq_total_scores = week_mcq_total_scores + float(day.get('mcq_score','0/0').split('/')[1])
                    week_coding_scores = week_coding_scores + float(day.get('coding_score','0/0').split('/')[0])
                    week_coding_total_scores = week_coding_total_scores + float(day.get('coding_score','0/0').split('/')[1])
                if mcqScores.get(subject_names.get(i)) == None:
                    mcqScores.update({subject_names.get(i):{
                        'All':'0/0'
                    }})
                if codingScore.get(subject_names.get(i)) == None:
                    codingScore.update({subject_names.get(i):{
                        'All':'0/0'
                    }})
                if mcqScores.get(subject_names.get(i)).get(week.replace('_',' ')) == None:
                    mcqScores.get(subject_names.get(i)).update({week.replace('_',' '):'0/0'})
                if codingScore.get(subject_names.get(i)).get(week.replace('_',' ')) == None:
                    codingScore.get(subject_names.get(i)).update({week.replace('_',' '):'0/0'})
                oldmcqScores = mcqScores.get(subject_names.get(i)).get('All').split('/')[0]
                oldcodingScore = codingScore.get(subject_names.get(i)).get('All').split('/')[0]
                oldtotalmcqScores = mcqScores.get(subject_names.get(i)).get('All').split('/')[1]
                oldtotalcodingScore = codingScore.get(subject_names.get(i)).get('All').split('/')[1]
                mcqScores.get(subject_names.get(i)).update({'All':str(float(week_mcq_scores)+float(oldmcqScores))+'/'+str(float(week_mcq_total_scores)+float(oldtotalmcqScores))})
                codingScore.get(subject_names.get(i)).update({'All':str(float(week_coding_scores)+float(oldcodingScore))+'/'+str(float(week_coding_total_scores)+float(oldtotalcodingScore))})
                mcqScores.get(subject_names.get(i)).update({week.replace('_',' '):(str(week_mcq_scores)+'/'+str(week_mcq_total_scores))})
                codingScore.get(subject_names.get(i)).update({week.replace('_',' '):(str(week_coding_scores)+'/'+str(week_coding_total_scores))})
                oldmcqcore = float(str(All_scores.get('Practice MCQs')).split('/')[0])
                oldmcqoutoff =float(str(All_scores.get('Practice MCQs')).split('/')[1])
                All_scores.update({'Practice MCQs':str(float(week_mcq_scores)+oldmcqcore)+'/'+str(float(week_mcq_total_scores)+oldmcqoutoff)})
                oldcodingcore = float(str(All_scores.get('Practice Codings')).split('/')[0])
                oldcodingoutoff =float(str(All_scores.get('Practice Codings')).split('/')[1])
                All_scores.update({'Practice Codings':str(float(week_coding_scores)+oldcodingcore)+'/'+str(float(week_coding_total_scores)+oldcodingoutoff)})
        tests_scores = {}
        for i in assessments:
            if i.get('assessment_type') == 'Weekly Test':
                oldscore = float(str(All_scores.get(i.get('assessment_type')+'s')).split('/')[0])
                oldoutoff =float(str(All_scores.get(i.get('assessment_type')+'s')).split('/')[1])
                All_scores.update({str(i.get('assessment_type'))+'s':str(float(i.get('assessment_score_secured','0'))+oldscore)+'/'+str(float(i.get('assessment_max_score'))+oldoutoff)})
                # tests_scores.update({i.get('subject_id__subject_name'):{
                #     'week_'+str(i.get('assessment_week_number')):str(i.get('assessment_score_secured','0'))+'/'+str(i.get('assessment_max_score'))
                # }})
            # print(i.get('assessment_type'))
            if filters_subject_week.get(subject_names_with_id.get(i.get('subject_id__subject_id'))) == None:
                filters_subject_week.update({subject_names_with_id.get(i.get('subject_id__subject_id')):[]})
            if i.get('assessment_type') != 'Weekly Test':
                filters_subject_week.get(subject_names_with_id.get(i.get('subject_id__subject_id'))).append(i.get('assessment_type')) 
            else:
                if tests_scores.get(subject_names_with_id.get(i.get('subject_id__subject_id'))).get('All') == None:
                    tests_scores.get(subject_names_with_id.get(i.get('subject_id__subject_id'))).update({
                        'All':'0/0'})
                oldtestscore = float(str(tests_scores.get(subject_names_with_id.get(i.get('subject_id__subject_id'))).get('All')).split('/')[0])
                oldtestoutoff =float(str(tests_scores.get(subject_names_with_id.get(i.get('subject_id__subject_id'))).get('All')).split('/')[1])
                tests_scores.get(subject_names_with_id.get(i.get('subject_id__subject_id'))).update({
                    'All':str(float(i.get('assessment_score_secured','0'))+oldtestscore)+'/'+str(float(i.get('assessment_max_score'))+oldtestoutoff)
                })
                if delays.get(subject_names_with_id.get(i.get('subject_id__subject_id')))== None:
                    delays.update({subject_names_with_id.get(i.get('subject_id__subject_id')):0})
                delay = (i.get('student_test_completion_time') if i.get('student_test_completion_time') != None else timezone.now().__add__(timedelta(hours=5,minutes=30))) - (i.get('assessment_completion_time') if i.get('assessment_completion_time') != None else timezone.now().__add__(timedelta(hours=5,minutes=30)))
                delay = delay.days
                old_delay = delays.get('All')
                delays.update({'All':delay if delay > old_delay else old_delay})
                delays.update({subject_names_with_id.get(i.get('subject_id__subject_id')):delay if delay > old_delay else old_delay})

            if tests_scores.get(subject_names_with_id.get(i.get('subject_id__subject_id')))== None:
                tests_scores.update({subject_names_with_id.get(i.get('subject_id__subject_id')):{}})
            tests_scores.get(subject_names_with_id.get(i.get('subject_id__subject_id'))).update({
                'week_'+str(i.get('assessment_week_number')) if i.get('assessment_type') == 'Weekly Test' else i.get('assessment_type') :str(i.get('assessment_score_secured','0'))+'/'+str(i.get('assessment_max_score'))})
        # all_scores_data ={}
        # all_scores_data.update({'All':All_scores})
        # All_scores.update(all_scores_data)
        response ={
            "filters_subject":list(filters_subject),
            "filters_subject_week":filters_subject_week,
            "mcqScores":mcqScores,
            "codingScore":codingScore,
            'tests': tests_scores,
            "All":{
                'Practice MCQs':str(All_scores.get('Practice MCQs','0/0')),'Practice Codings':str(All_scores.get('Practice Codings','0/0')),
                'Weekly Tests':str(All_scores.get('Weekly Tests','0/0')),
                'All':All_scores
            },
            'delay':delays
        }
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
# OLD 

@api_view(['GET'])
def fetch_study_hours_old(request,student_id,week):
    try:
        week = int(week)
        student = students_info.objects.get(student_id = student_id,del_row = False)
        course_subjects_data = course_subjects.objects.filter(course_id = student.course_id,batch_id = student.batch_id,del_row = False
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
                "isUpcoming":True if subjects.get('start') + timedelta(days=i) > timezone.now().__add__(timedelta(hours=5,minutes=30)).date() else False,
                "isCurrent":True if subjects.get('start') + timedelta(days=i) == timezone.now().__add__(timedelta(hours=5,minutes=30)).date() else False,
                "hours":round(hour_spent.get(subjects.get('start') + timedelta(days=i)).total_seconds()/3600,2) if hour_spent.get(subjects.get('start') + timedelta(days=i)) else 0
            })
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
