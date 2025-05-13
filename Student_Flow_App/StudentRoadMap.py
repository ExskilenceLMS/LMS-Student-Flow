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

from .StudentDashBoard import getdays



@api_view(['GET'])
def fetch_top_navigation(request,student_id):
    try:
        notifications = list(notification.objects.using('mongodb').filter(
                                                                     student_id = student_id,
                                                                     status = 'U',
                                                                     del_row = False
                                                                     ).order_by('-notification_timestamp'
                                                                                ).values('notification_id','notification_title','notification_timestamp'))
        response = {
            'student_id': student_id,
            'count': len(notifications),
            'notifications': notifications
        }
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)

@api_view(['GET'])
def fetch_roadmap(request,student_id,course_id,subject_id):
    try:
        student = students_info.objects.get(student_id = student_id,del_row = False) 
        course = student.course_id
        blob_data = json.loads(get_blob(f'lms_daywise/{course.course_id}/{course.course_id}_{student.batch_id.batch_id}.json'))
        sub = subjects.objects.get(subject_id = subject_id,del_row = False)
        course_details = list(course_plan_details.objects.filter(course_id=course, subject_id=sub,batch_id_id=student.batch_id.batch_id, del_row=False)
                  .values('week')
                  .annotate(#   day_date_count=Count('day_date'), 
                      startDate=Min('day_date'),
                      endDate=Max('day_date'),
                      totalHours=Sum('duration_in_hours'),
                  )
                  .order_by('week'))
        studentQuestions = students_details.objects.using('mongodb').get(
            student_id = student_id,
            del_row = False
            )
        student_assessments_objs = students_assessments.objects.filter(student_id = student,\
                                                                    subject_id = sub,\
                                                                    # assessment_type = 'Weekly Test',\
                                                                    del_row = False\
                                                                )
        student_assessments = { i.test_id.test_name:i for i in student_assessments_objs }
        final_assessments = { i.test_id.test_name:i for i in student_assessments_objs.filter(assessment_type = 'Final Test') }
        sub_data = studentQuestions.student_question_details.get(course.course_id+'_'+sub.subject_id,{})
        days = []
        other_weeks = []
        Onsite = []
        intern = []
        final = []
        daynumber=0
        last_day_data = {}
        current_date = timezone.now().__add__(timedelta(days=0,hours=5,minutes=30))
        max_date = timezone.now().__add__(timedelta(hours=5, minutes=30))
        for week in course_details:
            if week.get('startDate').date() <= current_date.date() and \
                    timezone.now().__add__(timedelta(hours=5, minutes=30)).date() <= week.get('endDate').date():
                current_week = week.get('week')
                max_date = week.get('endDate')
                break
        print('current_week',current_week)
        for i in course_details:
            week_data = sub_data.get('week_'+str(i.get('week')),{})
            if i.get('week') > 1:
                prev_week_data = sub_data.get('week_'+str(i.get('week')-1),{})
            else:
                prev_week_data = {}
            week_first_day = 0
            for d in blob_data.get(sub.subject_name):
                if d.get('date').__contains__('T') or d.get('date').__contains__('Z') or len(d.get('date'))>10: 
                    the_date = datetime.strptime(d.get('date').replace('T',' ').split('.')[0].replace('Z',''), "%Y-%m-%d %H:%M:%S") 
                else:
                    the_date = datetime.strptime(d.get('date')+" 00:00:00", "%Y-%m-%d %H:%M:%S")
                if i.get('startDate').date() <= the_date.date() and the_date.date() <= i.get('endDate').date():
                    if week_first_day == 0:
                        week_first_day = int(d.get('day').split(' ')[-1]) 
                        # print('week_first_day',week_first_day,"prev_week_data",prev_week_data)
                    day_data = week_data.get('day_'+str(d.get('day').split(' ')[-1]),{})
                    status = ''
                    mcq_qns =len(day_data.get('mcq_questions',[]))
                    coding_qns =  len(day_data.get('coding_questions',[]))
                    mcq_answered = len([dd for dd in day_data.get('mcq_questions_status',{}) if day_data.get('mcq_questions_status',{}).get(dd)==2])
                    coding_answered = len([dd for dd in day_data.get('coding_questions_status',{}) if day_data.get('coding_questions_status',{}).get(dd)==2])
                    
                    day_status = [ day_data.get('sub_topic_status',{}).get(day_stat) for day_stat in day_data.get('sub_topic_status',{}) ]
                    # print(day_status)
                    if sum(day_status) == len(day_status)*2 and len(day_status) != 0:
                        status = 'Completed'
                    elif sum(day_status) != 0:
                        status = 'Resume'
                    else:
                        prev_day_data = week_data.get('day_'+str(int(d.get('day').split(' ')[-1])-1),{})
                        if prev_day_data !={}:
                            last_day_data = prev_day_data
                        if prev_day_data == {}:
                            prev_day_data = last_day_data
                        
                        prev_day_status = [ prev_day_data.get('sub_topic_status',{}).get(day_stat) for day_stat in prev_day_data.get('sub_topic_status',{}) ]
                        if sum(prev_day_status) == len(prev_day_status)*2 and len(prev_day_status) != 0:
                            # if d.get('topic') == 'Weekly Test':
                            #     status = 'Start'
                            if current_date.date() >= i.get('startDate').date() and current_date.date() <= i.get('endDate').date():
                                test_data = student_assessments.get('Week '+str(int(i.get('week')-1))+' Test')
                                if test_data == None:
                                    test_data = students_assessments(
                                        assessment_status = '',
                                        assessment_score_secured = 0,
                                        assessment_max_score = 0
                                    )
                                if ([i for i in days if i.get('status') == 'Start'].__len__() == 0 and test_data.assessment_status == 'Completed') :#or \
                                    #   ([i for i in days if i.get('status') == 'Start'].__len__() == 0):
                                    status = 'Start'
                            if (current_date.date() >= i.get('startDate').date() and current_date.date() <= max_date.date()) and \
                                i.get('week') ==1  and ([i for i in days if i.get('status') == 'Start'].__len__() == 0): 
                                    status = 'Start'
                        last_weeks_last_day_data = prev_week_data.get('day_'+str(week_first_day-1),{})
                        last_weeks_last_day_status = [ last_weeks_last_day_data.get('sub_topic_status',{}).get(day_stat) for day_stat in last_weeks_last_day_data.get('sub_topic_status',{}) ]
                        if (status == '' and daynumber == 0 ):# or (sum(last_weeks_last_day_status) == len(last_weeks_last_day_status)*2 and len(last_weeks_last_day_status) != 0):
                            # if current_date.date() >= i.get('startDate').date() and current_date.date() <= i.get('endDate').date():
                                status = 'Start'
                    
                    if d.get('topic') == 'Weekly Test':# or d.get('topic') == 'Onsite Workshop' or d.get('topic') == 'Internship':
                        test_data = student_assessments.get('Week '+str(i.get('week'))+' Test')
                        if test_data == None:
                            test_data = students_assessments(
                                assessment_status = 'Pending',
                                assessment_score_secured = 0,
                                assessment_max_score = 0
                            )
                        week_status = []
                        for day in week_data:#student_detaile.student_question_details.get(subject_id).get('week_'+str(week_number)):
                            day = week_data.get(day)
                            [ week_status.append(day.get('sub_topic_status',{}).get(sub,0)==2) for sub in day.get('sub_topic_status',{})]
                            # all_practiced_Questions.extend(day.get('mcq_questions',[]))
                            # all_practiced_Questions.extend(day.get('coding_questions',[]))
                            # all_sub_topics.extend([sub for sub in day.get('sub_topic_status',{})])
                        if week_status.count(True) == len(week_status):
                            if (current_date.date() >= i.get('startDate').date() and current_date.date() <= max_date.date()) and \
                                i.get('week') ==1 : 
                                    status = 'Start'
                            # status = 'Stgart'
                        days.append({'day':daynumber+1,'day_key':d.get('day').split(' ')[-1],
                            "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
                            'week':i.get('week'),
                            'topics':d.get('topic'),
                            'score' : str(round(test_data.assessment_score_secured,2))+'/'+str(round(test_data.assessment_max_score)),#'0/0',
                            # 'status':test_data.assessment_status if test_data.assessment_status != 'Pending' else status,
                            'status':'' if [i for i in days if i.get('status') == 'Start'].__len__() != 0 else status if test_data.assessment_status == 'Pending' else test_data.assessment_status,
                            
                              })
                    elif d.get('topic') == 'Onsite Workshop' or d.get('topic') == 'Final Test':
                        Onsite.append({#'day':daynumber+1,
                            'day_key':d.get('day').split(' ')[-1],
                            "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
                            'week':len(course_details)+other_weeks.__len__()+1,
                            'topics':d.get('topic'),
                            'score' :'0/0',
                            'days':[],
                            'status':''
                              })
                    elif d.get('topic') == 'Internship':
                        intern.append({'day':'',
                            'day_key':d.get('day').split(' ')[-1],
                            "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
                            'week':len(course_details)+other_weeks.__len__()+1,
                            'topics':d.get('topic'),
                            'score' :'0/0',
                            'days':[],
                            'status':''
                              })
                    elif d.get('topic') == 'Final Test':
                        final.append({'day':'',
                            'day_key':d.get('day').split(' ')[-1],
                            "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
                            'week':len(course_details)+other_weeks.__len__()+1,
                            'topics':d.get('topic'),
                            'score' :'0/0',
                            'days':[],
                            'status':''
                              })
                    else:
                        days.append({'day':daynumber+1,'day_key':d.get('day').split(' ')[-1],
                            "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
                            'week':i.get('week'),
                            'topics':d.get('topic'),
                            'practiceMCQ': { 'questions': str(mcq_answered)
                                            +'/'+str(mcq_qns),
                                             'score': day_data.get('mcq_score','0/0') },
                            'practiceCoding': { 'questions': str(coding_answered)
                                            +'/'+str(coding_qns),
                                             'score': day_data.get('coding_score','0/0') },
                            'status':status if str(d.get('topic')).lower() != 'Festivals'.lower() 
                                                and str(d.get('topic')).lower() != 'Preparation Day'.lower() 
                                                and str(d.get('topic')).lower() != 'Semester Exam'.lower()  
                                                and  str(d.get('topic')).lower() != 'Internship'.lower()
                                            else ''
                              })
                    daynumber+=1 
          
            i.update({'days': days})
            days = []
        other_weeks.extend([{
            'week':len(course_details)+1,
            'startDate': Onsite[0].get('date') if Onsite!=[] else '',
            'endDate': Onsite[-1].get('date') if Onsite!=[] else '',
            'days':Onsite,
            'topics':'Onsite Workshop'
        },
        {
            'week':len(course_details)+2,
            'startDate': final[0].get('date') if final!=[] else '',
            'endDate': final[-1].get('date') if final!=[] else '',
            'days':final,
            'topics':'Final Test'
        },
        {
            'week':len(course_details)+3,
            'startDate': intern[0].get('date') if intern!=[] else '',
            'endDate': intern[-1].get('date') if intern!=[] else '',
            'days':intern,
            'topics':'Internship Challenge'
        }]
        )
        course_details.extend(other_weeks)
        response = {
            "weeks":course_details,
        }
        # print(prevDaysStatuses)     
        update_app_usage(student_id)
        return JsonResponse(response,safe=False,status=200)
                 
        # return fetch_roadmap_old(request,student_id,course_id,subject_id)
    except Exception as e:
        print(e)
        update_app_usage(student_id)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)


                                                           

# @api_view(['GET'])
def fetch_roadmap_old(request,student_id,course_id,subject_id):
    try:
        student = students_info.objects.get(student_id = student_id,del_row = False)
        course = student.course_id
        # blob_data = json.loads(get_blob(f'LMS_DayWise/Course0001.json')) #json.loads(get_blob(f'lms_daywise/{course.course_id}/{course_id}.json'))
        blob_data = json.loads(get_blob(f'lms_daywise/{course.course_id}/{course.course_id}_{student.batch_id.batch_id}.json'))
        # course = courses.objects.get(course_id=course_id)
        sub = subjects.objects.get(subject_id = subject_id,del_row = False)
        course_details = list(course_plan_details.objects.filter(course_id=course, subject_id=sub, del_row=False)
                  .values('week')
                  .annotate(#   day_date_count=Count('day_date'), 
                      startDate=Min('day_date'),
                      endDate=Max('day_date'),
                      totalHours=Sum('duration_in_hours'),
                  )
                  .order_by('week'))
        studentQuestions = students_details.objects.using('mongodb').get(
            student_id = student_id,del_row = 'False'
        )
        sub_data = studentQuestions.student_question_details.get(course.course_id+'_'+sub.subject_name,{})
        days = []
        other_weeks = []
        Onsite = []
        intern = []
        final = []
        daynumber=0
        for i in course_details:
            week_data = sub_data.get('week_'+str(i.get('week')),{})
            if i.get('week') > 1:
                prev_week_data = sub_data.get('week_'+str(i.get('week')-1),{})
            else:
                prev_week_data = {}
            week_first_day = 0
            for d in blob_data.get(sub.subject_name):
                if d.get('date').__contains__('T') or d.get('date').__contains__('Z') or len(d.get('date'))>10: 
                    the_date = datetime.strptime(d.get('date').replace('T',' ').split('.')[0].replace('Z',''), "%Y-%m-%d %H:%M:%S") 
                else:
                    the_date = datetime.strptime(d.get('date')+" 00:00:00", "%Y-%m-%d %H:%M:%S")
                if i.get('startDate').date() <= the_date.date() and the_date.date() <= i.get('endDate').date():
                    if week_first_day == 0:
                        week_first_day = int(d.get('day').split(' ')[-1]) 
                        # print('week_first_day',week_first_day,"prev_week_data",prev_week_data)
                    day_data = week_data.get('day_'+str(d.get('day').split(' ')[-1]),{})
                    status = ''
                    mcq_qns =len(day_data.get('mcq_questions',[]))
                    coding_qns =  len(day_data.get('coding_questions',[]))
                    mcq_answered = len([dd for dd in day_data.get('mcq_questions_status',{}) if day_data.get('mcq_questions_status',{}).get(dd)==2])
                    coding_answered = len([dd for dd in day_data.get('coding_questions_status',{}) if day_data.get('coding_questions_status',{}).get(dd)==2])
                    if (day_data.get('mcq_questions') is None and coding_qns == coding_answered and coding_qns > 0
                        ) or (day_data.get('coding_questions') is None and mcq_qns == mcq_answered and mcq_qns > 0
                              )or(mcq_qns == mcq_answered and coding_qns == coding_answered and mcq_qns > 0 and coding_qns > 0):
                        status = 'Completed'
                    elif mcq_answered > 0 or coding_answered > 0 or day_data != {} :
                        status = 'Resume'
                    else:
                        prev_day_data = week_data.get('day_'+str(int(d.get('day').split(' ')[-1])-1),{})
                        prev_mcq_qns =len(prev_day_data.get('mcq_questions',[]))
                        prev_coding_qns =  len(prev_day_data.get('coding_questions',[]))
                        prev_mcq_answered = len([dd for dd in prev_day_data.get('mcq_questions_status',{}) if prev_day_data.get('mcq_questions_status',{}).get(dd)==2])
                        prev_coding_answered = len([dd for dd in prev_day_data.get('coding_questions_status',{}) if prev_day_data.get('coding_questions_status',{}).get(dd)==2])
                        if prev_mcq_qns == prev_mcq_answered and prev_coding_qns == prev_coding_answered and prev_mcq_qns > 0 and prev_coding_qns > 0:
                            status = 'Start'
                        last_weeks_last_day_data = prev_week_data.get('day_'+str(week_first_day-1),{})
                        last_weeks_mcq_qns =len(last_weeks_last_day_data.get('mcq_questions',[]))
                        last_weeks_coding_qns =  len(last_weeks_last_day_data.get('coding_questions',[]))
                        last_weeks_mcq_answered = len([dd for dd in last_weeks_last_day_data.get('mcq_questions_status',{}) if last_weeks_last_day_data.get('mcq_questions_status',{}).get(dd)==2])
                        last_weeks_coding_answered = len([dd for dd in last_weeks_last_day_data.get('coding_questions_status',{}) if last_weeks_last_day_data.get('coding_questions_status',{}).get(dd)==2])
                        if (status == '' and daynumber == 0 ) or (last_weeks_mcq_qns == last_weeks_mcq_answered and last_weeks_coding_qns == last_weeks_coding_answered and last_weeks_mcq_qns > 0 and last_weeks_coding_qns > 0):
                            status = 'Start'
                    if d.get('topic') == 'Weekly Test':# or d.get('topic') == 'Onsite Workshop' or d.get('topic') == 'Internship':
                        days.append({'day':daynumber+1,'day_key':d.get('day').split(' ')[-1],
                            "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
                            'week':i.get('week'),
                            'topics':d.get('topic'),
                            'score' :'0/0',

                            'status':""
                              })
                    elif d.get('topic') == 'Onsite Workshop' or d.get('topic') == 'Final Test':
                        Onsite.append({#'day':daynumber+1,
                            'day_key':d.get('day').split(' ')[-1],
                            "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
                            'week':len(course_details)+other_weeks.__len__()+1,
                            'topics':d.get('topic'),
                            'score' :'0/0',
                            'days':[],
                            'status':''
                              })
                    elif d.get('topic') == 'Internship':
                        intern.append({'day':'',
                            'day_key':d.get('day').split(' ')[-1],
                            "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
                            'week':len(course_details)+other_weeks.__len__()+1,
                            'topics':d.get('topic'),
                            'score' :'0/0',
                            'days':[],
                            'status':''
                              })
                    elif d.get('topic') == 'Final Test':
                        final.append({'day':'',
                            'day_key':d.get('day').split(' ')[-1],
                            "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
                            'week':len(course_details)+other_weeks.__len__()+1,
                            'topics':d.get('topic'),
                            'score' :'0/0',
                            'days':[],
                            'status':''
                              })
                    else:
                        days.append({'day':daynumber+1,'day_key':d.get('day').split(' ')[-1],
                            "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
                            'week':i.get('week'),
                            'topics':d.get('topic'),
                            'practiceMCQ': { 'questions': str(mcq_answered)
                                            +'/'+str(mcq_qns),
                                             'score': day_data.get('mcq_score','0/0') },
                            'practiceCoding': { 'questions': str(coding_answered)
                                            +'/'+str(coding_qns),
                                             'score': day_data.get('coding_score','0/0') },
                            'status':status if str(d.get('topic')).lower() != 'Festivals'.lower() and str(d.get('topic')).lower() != 'Preparation Day'.lower() and str(d.get('topic')).lower() != 'Semester Exam'.lower()  and  str(d.get('topic')).lower() != 'Internship'.lower() else ''
                              })
                    daynumber+=1    
            i.update({'days': days})
            days = []
        other_weeks.extend([{
            'week':len(course_details)+1,
            'startDate': Onsite[0].get('date') if Onsite!=[] else '',
            'endDate': Onsite[-1].get('date') if Onsite!=[] else '',
            'days':Onsite,
            'topics':'Onsite Workshop'
        },
        {
            'week':len(course_details)+2,
            'startDate': final[0].get('date') if final!=[] else '',
            'endDate': final[-1].get('date') if final!=[] else '',
            'days':final,
            'topics':'Final Test'
        },
        {
            'week':len(course_details)+3,
            'startDate': intern[0].get('date') if intern!=[] else '',
            'endDate': intern[-1].get('date') if intern!=[] else '',
            'days':intern,
            'topics':'Internship Challenge'
        }]
        )
        course_details.extend(other_weeks)
        response = {
            "weeks":course_details,
        }
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)