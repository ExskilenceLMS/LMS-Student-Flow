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
from .ErrorLog import *
from .StudentDashBoard import getdays
import logging
logger = logging.getLogger(__name__)
def _parse_blob_date(s):
    if 'T' in s or 'Z' in s or len(s) > 10:
        return datetime.strptime(s.replace('T', ' ').split('.')[0].replace('Z', ''), '%Y-%m-%d %H:%M:%S')
    return datetime.strptime(f'{s} 00:00:00', '%Y-%m-%d %H:%M:%S')

@api_view(['GET'])
def fetch_roadmap0(request, student_id, course_id, subject_id):
    try:
        logger.info("Roadmap student details, started at " + str(timezone.now()) + "")
        start_time1=timezone.now()
        now = timezone.now()        
        student = students_info.objects.select_related('batch_id', 'course_id').get(student_id=student_id, del_row=False)
        logger.info("student details, fetched in " + str((timezone.now()-start_time1).total_seconds()) + " seconds.")

        course = student.course_id
        course_id = course.course_id
        batch_id = student.batch_id.batch_id
        sub = subjects.objects.get(subject_id=subject_id, del_row=False)
        logger.info("student subject details, fetched in " + str((timezone.now()-start_time1).total_seconds()) + " seconds." ) 
        blob_json = json.loads(get_blob(f'lms_daywise/{course_id}/{course_id}_{batch_id}.json'))
        raw_days = blob_json.get(sub.subject_name, [])
        blob_days = [{'topic':d['topic'], 'dt': _parse_blob_date(d['date']), 'key': d['day'].split(' ')[-1]} for d in raw_days]
        logger.info("student blob days, fetched in " + str((timezone.now()-start_time1).total_seconds()) + " seconds." )
        weeks = list(
            course_plan_details.objects.filter(
                course_id=course, subject_id=sub, batch_id_id=student.batch_id.batch_id, del_row=False
            )
            .values('week')
            .annotate(startDate=Min('day_date'), endDate=Max('day_date'), totalHours=Sum('duration_in_hours'))
            .order_by('week')
        )
        logger.info("Student weeks details, fetched in " + str((timezone.now()-start_time1).total_seconds()) + " seconds.")
        mongo_student = students_details.objects.using('mongodb').get(student_id=student_id, del_row=False)
        logger.info("Student details from Mongo DB, fetched in " + str((timezone.now()-start_time1).total_seconds()) + " seconds.")

        score_details = mongo_student.student_score_details
        assess_qs = students_assessments.objects.filter(student_id=student, subject_id=sub, del_row=False)
        logger.info("Student assessments, fetched in " + str((timezone.now()-start_time1).total_seconds()) + " seconds.")

        assessments = {a.test_id.test_name: a for a in assess_qs}
        start_count = 0

        out_weeks, extra_days, day_counter, last_day_cache = [], {'Onsite Workshop': [], 'Internship': [], 'Final Test': []}, 0, {}
        base_key = f'{course.course_id}_{sub.subject_id}'
        weeks_count = 0
        for w in weeks:
            weeks_count = weeks_count + 1
            wk_days = []
            week_number = w["week"]
            start = w['startDate'].date()
            end = w['endDate'].date()
            filtered_days = [x for x in blob_days if start <= x['dt'].date() <= end]
            for d in filtered_days:
                day_number = d["key"]
                status = score_details.get(f'{base_key}_{week_number}_{day_number}_sub_topic_status', 0)
                topic = d['topic']
                topic_lower = topic.lower()
                if status == 2:
                    status = 'Completed'
                elif status == 1:
                    start_count = start_count + 1
                    status = 'Resume'
                # # elif prev_stats  == 2 :
                else:
                    if start_count == 0 and  topic_lower not in ('festivals', 'preparation day', 'semester exam', 'internship'):
                            if topic == 'Weekly Test':
                                test_name = f'Week {week_number} Test' if topic == 'Weekly Test' else topic
                                ass = assessments.get(test_name)
                                test_status = ass.assessment_status if ass else ''
                                if test_status in ('Pending', 'Started'):
                                    start_count = start_count + 1
                                    status = 'Start' if test_status == 'Pending' else 'Resume'
                                else:
                                    status = test_status
                            else:
                                start_count = start_count + 1
                                status = 'Start'
                    else:
                        status = ''
                if not status and not day_counter:
                    status = 'Start'
                
                if topic in ('Weekly Test', 'Onsite Workshop', 'Internship', 'Final Test'):
                    test_name = f'Week {week_number} Test' if topic == 'Weekly Test' else topic
                    ass = assessments.get(test_name)
                    if topic == 'Weekly Test':
                        assessment_score = round(ass.assessment_score_secured, 2) if ass else 0
                        assessment_max_score = round(ass.assessment_max_score, 2) if ass else 0
                        score = f'{assessment_score}/{assessment_max_score}'
                        wk_days.append({'day': day_counter + 1, 'day_key': day_number, 'date': getdays(d['dt']),
                                        'week': week_number, 'topics': topic,
                                        'score': score, 'status': ass.assessment_status if ass else status})
                    else:
                        extra_days[topic].append({'day_key': day_number, 'date': getdays(d['dt']),
                                                  'week': weeks_count, 'topics': topic,
                                                  'score': '0/0', 'days': [], 'status': ''})
                else:
                    wk_days.append({'day': day_counter + 1, 'day_key': day_number, 'date': getdays(d['dt']),
                                    'week': week_number, 'topics': topic,
                                    'practiceMCQ': {'questions': score_details.get(f'{base_key}_{week_number}_{day_number}_mcq_questions', '0/0'),
                                                    'score': score_details.get( f'{base_key}_{week_number}_{day_number}_mcq', '0/0')},
                                    'practiceCoding': {'questions': score_details.get(f'{base_key}_{week_number}_{day_number}_coding_questions', '0/0'),
                                                       'score':   score_details.get(f'{base_key}_{week_number}_{day_number}_coding', '0/0')},
                                    'status': status if topic_lower not in ('festivals', 'preparation day', 'semester exam', 'internship') else ''})
                day_counter += 1
            w['days'] = wk_days
            out_weeks.append(w)
        out_weeks.extend([
            {'week': weeks_count + 1, 'startDate': extra_days['Onsite Workshop'][0]['date'] if extra_days['Onsite Workshop'] else '',
             'endDate': extra_days['Onsite Workshop'][-1]['date'] if extra_days['Onsite Workshop'] else '',
             'days': extra_days['Onsite Workshop'], 'topics': 'Onsite Workshop'},
            {'week': weeks_count + 2, 'startDate': extra_days['Final Test'][0]['date'] if extra_days['Final Test'] else '',
             'endDate': extra_days['Final Test'][-1]['date'] if extra_days['Final Test'] else '',
             'days': extra_days['Final Test'], 'topics': 'Final Test'},
            {'week': weeks_count + 3, 'startDate': extra_days['Internship'][0]['date'] if extra_days['Internship'] else '',
             'endDate': extra_days['Internship'][-1]['date'] if extra_days['Internship'] else '',
             'days': extra_days['Internship'], 'topics': 'Internship Challenge'},
        ])
        logger.info("Student roadmap, processed in " + str((timezone.now()-start_time1).total_seconds()) + " seconds.")
        logger.info("Roadmap student details API, completed in " + str((timezone.now()-start_time1).total_seconds()) + " seconds.")

        return JsonResponse({'weeks': out_weeks}, safe=False, status=200)

    except Exception as exc:
        logger.error(exc)
        update_app_usage(student_id)
        return JsonResponse(
            {'message': 'Failed', 
             'error': str(encrypt_message(str({
                 'Error_msg': str(exc),
                 'Stack_trace': str(traceback.format_exc()) + '\nUrl:-' + str(request.build_absolute_uri()) + '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
             })))},
            safe=False, status=400
        )
