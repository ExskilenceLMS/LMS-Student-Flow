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
# FETCH STUDENT ENROLLED SUBJECTS
@api_view(['GET'])
def fetch_enrolled_subjects(request, student_id):
    try:
        student = students_info.objects.get(student_id=student_id, del_row=False)
        subjects = course_subjects.objects.filter(
            course_id=student.course_id,
            batch_id=student.batch_id,
            del_row=False
        )

        latest_activities = (
            student_activities.objects
            .filter(student_id=student_id, del_row=False)
            .values('subject_id__subject_name')
            .annotate(latest_day=Max('activity_day'))
        )

        sub_days_count = {
            activity['subject_id__subject_name']: {'day': activity['latest_day']}
            for activity in latest_activities
        }

        # now = timezone.localtime() + timedelta(hours=5, minutes=30)
        now = timezone.now() + timedelta(hours=5, minutes=30)

        response = []
        for subject in subjects:
            if subject.subject_id.del_row:
                continue

            subject_name = subject.subject_id.subject_name
            subject_data = {
                "title": subject_name,
                "subject": subject_name.replace(' ', ''),
                "subject_id": subject.subject_id.subject_id,
                "image": subject.path,
                "duration": f"{getdays(subject.start_date)} - {getdays(subject.end_date)}",
                "progress": calculate_progress(
                    subject.start_date,
                    subject.end_date,
                    sub_days_count.get(subject_name, {'day': 0}),
                    subject.duration_in_days
                ),
                'status': 'Open' if (subject.end_date > now and subject.start_date < now) or (subject.end_date < now ) else 'Closed'
            }
            response.append(subject_data)

        return JsonResponse(response, safe=False, status=200)

    except Exception as e:
        payload = {
            "Error_msg": str(e),
            "Stack_trace": traceback.format_exc()+\
                '\nUrl:-'+str(request.build_absolute_uri())+\
                    '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}"),
            "Url": request.build_absolute_uri(),
            "Body": "{}"
        }
        return JsonResponse({
            "message": "Failed",
            "error": str(encrypt_message(str(payload)))
        }, safe=False, status=400)
def calculate_progress(start_date, end_date, student_progress, total_days):
    response = {}

    days_completed = student_progress.get('day', 0)
    student_pct = int((days_completed / int(total_days)) * 100) if total_days else 0
    response["student_progress"] = min(student_pct, 100)

    current_date = timezone.now() + timedelta(hours=5, minutes=30)

    if current_date.date() < start_date.date():
        response["progress"] = 0
        return response

    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date.split('.')[0].split('+')[0], "%Y-%m-%d %H:%M:%S")
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date.split('.')[0].split('+')[0], "%Y-%m-%d %H:%M:%S")

    duration_days = (end_date - start_date).days or 1
    time_progress = ((current_date - start_date).days / duration_days) * 100
    response["progress"] = min(int(time_progress), 100)

    return response

def getdays(date):
    if isinstance(date, str):
        date = datetime.strptime(date.split('.')[0].split('+')[0], "%Y-%m-%d %H:%M:%S")

    day = date.day
    month = date.month

    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    formatted_date = f"{day}{suffix} {calendar.month_abbr[month]} {str(date.year)[2:]}"
    return formatted_date

# FETCH LIVE SESSION
@api_view(['GET'])
def fetch_live_session(request, student_id):
    try:
        current_time = timezone.now() + timedelta(hours=5, minutes=30)

        live_session = live_sessions.objects.using('mongodb').filter(
            session_starttime__gte=current_time,
            student_ids__contains=student_id,  # Or use `__in=[student_id]` based on your schema
            del_row="False"
        ).order_by('-session_starttime').values_list('session_title', 'session_starttime')

        response = [{
            "title": session[0],
            "date": getdays(session[1]),
            "time": session[1].strftime("%I:%M %p").upper()
        } for session in live_session]

        return JsonResponse(response, safe=False, status=200)

    except Exception as e:
        return JsonResponse({
            "message": "Failed",
            "error": str(encrypt_message(str({
                "Error_msg": str(e),
                "Stack_trace": str(traceback.format_exc()) + '\nUrl:-' + str(request.build_absolute_uri()) +
                                '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}"),
                "Url": request.build_absolute_uri(),
                "Body": "{}"
            })))
        }, safe=False, status=400)
    
@api_view(['GET'])
def fetch_upcoming_events(request, Course_id, batch_id):
    try:
        current_time = timezone.now() + timedelta(hours=5, minutes=30)

        blob_path = f'lms_daywise/{Course_id}/{Course_id}_{batch_id}.json'
        blob_content = get_blob(blob_path)
        blob_data = json.loads(blob_content)

        response = extract_events(blob_data, current_time)

        return JsonResponse(response, safe=False, status=200)

    except Exception as e:
        return JsonResponse({
            "message": "Failed",
            "error": str(encrypt_message(str({
                "Error_msg": str(e),
                "Stack_trace": str(traceback.format_exc()) + '\nUrl:-' + str(request.build_absolute_uri()) +
                                '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}"),
                "Url": request.build_absolute_uri(),
                "Body": "{}"
            })))
        }, safe=False, status=400)
    
def extract_events(blob_data, current_time):
    events = []
    for subject, items in blob_data.items():
        for item in items:
            topic = item.get('topic')
            if topic in ['Weekly Test', 'Onsite Workshop', 'Internship']:
                raw_date = item.get('date')
                try:
                    if 'T' in raw_date:
                        date = datetime.strptime(raw_date.split('.')[0].replace('T', ' '), "%Y-%m-%d %H:%M:%S")
                    else:
                        date = datetime.strptime(f"{raw_date} 00:00:00", "%Y-%m-%d %H:%M:%S")
                except Exception:
                    continue  

                events.append({
                    "title": topic,
                    "subject": subject,
                    "date": getdays(date),
                    "time": date.strftime("%I:%M %p"),
                    "datetime": date
                })

    upcoming = sorted(
        [event for event in events if event["datetime"].date() >= current_time.date()],
        key=lambda e: e["datetime"]
    )
    return upcoming

# FETCH  STUDY HOURS
def fetch_study_hours(request, student_id, week):
    try:
        student = students_info.objects.get(student_id=student_id, del_row=False)
        today = timezone.now() + timedelta(hours=5, minutes=30)
        if timezone.is_naive(today):
            today = timezone.make_aware(today, timezone.get_current_timezone())

        start_of_week = today.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=today.weekday())

        if week.isdigit():
            current_week = int(week)
        else:
            current_weeks = course_plan_details.objects.filter(
                course_id=student.course_id,
                batch_id=student.batch_id,
                day_date__date__lte=today.date(),
                del_row=False
            ).values('week', 'day_date').order_by('-week')

            if not current_weeks:
                current_week = 1
            else:
                latest_entry = current_weeks[0]
                diff_days = (today.date() - latest_entry['day_date'].date()).days
                current_week = latest_entry['week'] + (diff_days // 7 if diff_days > 0 else 0)

        course_details = list(course_plan_details.objects.filter(
            course_id=student.course_id,
            batch_id=student.batch_id,
            week=current_week
        ).values('duration_in_hours', 'week', 'day_date').order_by('-week'))

        if not course_details:
            course_details = list(course_plan_details.objects.filter(
                course_id=student.course_id,
                batch_id=student.batch_id
            ).values('duration_in_hours', 'week', 'day_date').order_by('-week'))
        else:
            if week.isdigit():
                first_day = course_details[0]['day_date']
                start_of_week = first_day.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=first_day.weekday())

        week_end = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
        usages = student_app_usage.objects.filter(
            student_id=student_id,
            logged_in__gte=start_of_week,
            logged_in__lte=week_end,
            del_row=False
        ).annotate(date=TruncDate('logged_in')) \
         .values('date') \
         .annotate(total_study_hours=Sum(F('logged_out') - F('logged_in'))) \
         .order_by('date')

        list_of_duration = [c.get("duration_in_hours") for c in course_details if c.get("duration_in_hours")]
        daily_limit = round(sum(list_of_duration) / len(list_of_duration)) if list_of_duration else 0
        weekly_limit = course_details[0]['week'] + ((today.date() - course_details[0]['day_date'].date()).days // 7)

        hour_spent = {
            usage['date']: round(usage['total_study_hours'].total_seconds() / 3600, 2)
            for usage in usages
        }

        hours = []
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            hours.append({
                "date": day,
                "day_name": calendar.day_name[day.weekday()][:3],
                "isUpcoming": day.date() > today.date(),
                "isCurrent": day.date() == today.date(),
                "hours": hour_spent.get(day.date(), 0)
            })

        response = {
            'daily_limit': daily_limit,
            'weekly_limit': weekly_limit,
            'hours': hours
        }

        return JsonResponse(response, safe=False, status=200)

    except Exception as e:
        print(e)
        return JsonResponse({
            "message": "Failed",
            "error": str(encrypt_message(str({
                "Error_msg": str(e),
                "Stack_trace": str(traceback.format_exc()) +
                               '\nUrl:-' + str(request.build_absolute_uri()) +
                               '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}"),
                "Url": request.build_absolute_uri(),
                "Body": "{}"
            })))
        }, safe=False, status=400)
#    FETCH CALENDAR
      
@api_view(['GET'])
def fetch_calendar(request, student_id):
    try:
        current_time = timezone.now() + timedelta(hours=5, minutes=30)
        if timezone.is_naive(current_time):
            current_time = timezone.make_aware(current_time, timezone.get_current_timezone())

        student = students_info.objects.get(student_id=student_id, del_row=False)

        blob_data = json.loads(get_blob(
            f'lms_daywise/{student.course_id.course_id}/{student.course_id.course_id}_{student.batch_id.batch_id}.json'
        ))

        response = extract_calendar_events(blob_data, current_time)

        return JsonResponse({
            'year': current_time.strftime("%Y"),
            'month': str(int(current_time.strftime("%m")) - 1),
            "calendar": response
        }, safe=False, status=200)

    except Exception as e:
        print(e)
        return JsonResponse({
            "message": "Failed",
            "error": str(encrypt_message(str({
                "Error_msg": str(e),
                "Stack_trace": traceback.format_exc() +
                               '\nUrl:-' + str(request.build_absolute_uri()) +
                               '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
            })))
        }, safe=False, status=400)
def extract_calendar_events(blob_data, current_time):
    events = []

    for subject, event_list in blob_data.items():
        for event in event_list:
            topic = event.get('topic')
            if topic in ['Weekly Test', 'Onsite Workshop', 'Internship']:
                raw_date = event.get('date')
                date = datetime.strptime(
                    raw_date.replace('T', ' ').split('.')[0],
                    "%Y-%m-%d %H:%M:%S"
                ) if 'T' in raw_date else datetime.strptime(
                    raw_date + " 00:00:00", "%Y-%m-%d %H:%M:%S"
                )

                events.append({
                    "title": topic,
                    "subject": subject,
                    "date": getdays(date),
                    "time": date.strftime("%I:%M %p"),
                    "datetime": date.date()
                })

    events = sorted(events, key=lambda k: k['datetime'])

    current_month = current_time.month
    current_year = current_time.year

    this_month = [
        event for event in events
        if event['datetime'].month == current_month and event['datetime'].year == current_year
    ]

    return this_month

#    FETCH STUDENT SUMMARY

@api_view(['GET'])
def fetch_student_summary(request, student_id):
    try:
        student = (
            students_info.objects
            .only(
                'student_id', 'student_firstname', 'student_lastname',
                'student_score', 'student_catogory',
                'student_college_rank', 'student_overall_rank'
            )
            .get(student_id=student_id, del_row=False)
        )

        usage = (
            student_app_usage.objects
            .filter(student_id=student_id, del_row=False)
            .aggregate(total=Sum(F('logged_out') - F('logged_in')))
        )
        total_td = usage['total'] or timedelta(0)
        hours_spent = round(total_td.total_seconds() / 3600, 2)

        response = {
            'student_id': student.student_id,
            'name': f'{student.student_firstname} {student.student_lastname}',
            'score': student.student_score,
            'hour_spent': hours_spent,
            'category': student.student_catogory,
            'college_rank': student.student_college_rank if student.student_college_rank >= 0 else '--',
            'overall_rank': student.student_overall_rank if student.student_overall_rank >= 0 else '--',
        }
        return JsonResponse(response, safe=False, status=200)

    except students_info.DoesNotExist:
        return JsonResponse({'message': 'Student not found',
                             'error': str(encrypt_message(str({'Error_msg': 'Student not found',
                                                               "Stack_trace": traceback.format_exc()+\
                                                                    '\nUrl:-'+str(request.build_absolute_uri())+\
                                                                        '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}"),
                                                                "Url": request.build_absolute_uri(),
                                                                "Body": "{}",
                                                               }))),
                             }, safe=False, status=404)

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
    
#    FETCH WEEKLY PROGRESS
from collections import defaultdict
def add_score(d: dict, key: str, add_secured: float, add_total: float):
    cur_sec, cur_tot = map(float, d[key].split("/"))
    d[key] = f"{cur_sec + add_secured}/{cur_tot + add_total}"
@api_view(["GET"])
def get_weekly_progress(request, student_id):
    try:
        now = timezone.now()+timedelta(hours=5,minutes=30)
        student = students_info.objects.only("course_id").get(student_id=student_id, del_row=False)

        subj_qs = subjects.objects.only("subject_id", "subject_name").filter(del_row=False)
        subj_id2name = {s.subject_id: s.subject_name for s in subj_qs}
        course_key2name = {
            f"{student.course_id.course_id}_{sid}": name for sid, name in subj_id2name.items()
        }

        # ---------- practice (Mongo) ----------
        practice_doc = students_details.objects.using("mongodb").get(
            student_id=student_id, del_row="False"
        ).student_question_details

        mcq_scores = defaultdict(lambda: defaultdict(lambda: "0/0"))
        coding_scores = defaultdict(lambda: defaultdict(lambda: "0/0"))
        filters_subject_week = defaultdict(list, {"All": ["Weekly Tests", "Practice MCQs", "Practice Codings"]})
        filters_subject = {"All"}
        filters_weeks = set()
        all_totals = defaultdict(lambda: float("0"))

        for course_key, weeks in practice_doc.items():
            subj_name = course_key2name.get(course_key)
            if not subj_name:
                continue
            filters_subject.add(subj_name)

            for week_key, days in weeks.items():
                week_label = week_key.replace("_", " ")
                filters_weeks.add(week_label)
                filters_subject_week[subj_name].append(week_label)

                w_mcq_sec = w_mcq_tot = w_cod_sec = w_cod_tot = float("0")

                for day_blob in days.values():
                    m_sec, m_tot = map(float, day_blob.get("mcq_score", "0/0").split("/"))
                    c_sec, c_tot = map(float, day_blob.get("coding_score", "0/0").split("/"))
                    w_mcq_sec += m_sec
                    w_mcq_tot += m_tot
                    w_cod_sec += c_sec
                    w_cod_tot += c_tot

                add_score(mcq_scores[subj_name], "All", w_mcq_sec, w_mcq_tot)
                mcq_scores[subj_name][week_label] = f"{w_mcq_sec}/{w_mcq_tot}"

                add_score(coding_scores[subj_name], "All", w_cod_sec, w_cod_tot)
                coding_scores[subj_name][week_label] = f"{w_cod_sec}/{w_cod_tot}"

                all_totals["Practice MCQs_sec"] += w_mcq_sec
                all_totals["Practice MCQs_tot"] += w_mcq_tot
                all_totals["Practice Codings_sec"] += w_cod_sec
                all_totals["Practice Codings_tot"] += w_cod_tot

        # ---------- assessments (SQL) ----------
        assess_qs = students_assessments.objects.filter(
            student_id=student_id, del_row=False
        ).values(
            "assessment_type",
            "subject_id",
            "subject_id__subject_id",
            "assessment_week_number",
            "assessment_score_secured",
            "assessment_max_score",
            "assessment_completion_time",
            "student_test_completion_time",
        )

        tests_scores = defaultdict(lambda: defaultdict(lambda: "0/0"))
        delays = defaultdict(int)

        for row in assess_qs:
            print(row)
            subj_name = subj_id2name.get(row["subject_id__subject_id"]) or "Unknown"
            filters_subject_week[subj_name]  # ensure key exists

            atype = row["assessment_type"]
            score_sec = float(row["assessment_score_secured"] or 0)
            score_max = float(row["assessment_max_score"] or 0)

            if atype == "Weekly Test":
                label = f"week_{row['assessment_week_number']}"
                add_score(tests_scores[subj_name], "All", score_sec, score_max)
                tests_scores[subj_name][label] = f"{score_sec}/{score_max}"

                all_totals["Weekly Tests_sec"] += score_sec
                all_totals["Weekly Tests_tot"] += score_max

                comp_time = row["student_test_completion_time"] or now
                due_time = row["assessment_completion_time"] or now
                delay_days = max((comp_time - due_time).days, 0)
                delays["All"] = max(delays["All"], delay_days)
                delays[subj_name] = max(delays[subj_name], delay_days)
            else:
                filters_subject_week[subj_name].append(atype)
                tests_scores[subj_name][atype] = f"{score_sec}/{score_max}"
        print(subj_id2name)
        # ---------- response ----------
        response = {
            "filters_subject": list(filters_subject),
            "filters_subject_week": filters_subject_week,
            "mcqScores": mcq_scores,
            "codingScore": coding_scores,
            "tests": tests_scores,
            "All": {
                "Practice MCQs": f"{all_totals['Practice MCQs_sec']}/{all_totals['Practice MCQs_tot']}",
                "Practice Codings": f"{all_totals['Practice Codings_sec']}/{all_totals['Practice Codings_tot']}",
                "Weekly Tests": f"{all_totals['Weekly Tests_sec']}/{all_totals['Weekly Tests_tot']}",
                "All":{
                    "Practice MCQs": f"{all_totals['Practice MCQs_sec']}/{all_totals['Practice MCQs_tot']}",
                    "Practice Codings": f"{all_totals['Practice Codings_sec']}/{all_totals['Practice Codings_tot']}",
                    "Weekly Tests": f"{all_totals['Weekly Tests_sec']}/{all_totals['Weekly Tests_tot']}",
                }
            },
            "delay": delays,
        }
        return JsonResponse(response, safe=False, status=200)

    except students_info.DoesNotExist:
        return JsonResponse({"message": "Student not found"}, safe=False, status=404)
    except Exception as e:
        print(e)
        payload = {"Error_msg": str(e), "Stack_trace": traceback.format_exc()}
        return JsonResponse({"message": "Failed", "error": str(encrypt_message(str(payload)))}, safe=False, status=400)

# def get_weekly_progress(request, student_id):
#     try:

#         return JsonResponse('',safe=False,status=200)
#     except Exception as e:
#         print(e)
#         return JsonResponse({"message": "Failed",
#                              "error":str(encrypt_message(str({
#                                     "Error_msg": str(e),
#                                     "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
#                                     })))},safe=False,status=400)