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
# from LMS_Project.Blobstorage import *
from .AppUsage import update_app_usage
from django.core.cache import cache
from LMS_Project.Blobstorage import *
from .sqlrun import get_all_tables
from .ErrorLog import *


@api_view(['GET'])
def fetch_all_test_details(request, student_id):
    try:
        now = timezone.now() + timedelta(hours=5, minutes=30)

        assessments = (
            students_assessments.objects
            .select_related('test_id', 'test_id__subject_id', 'course_id')
            .filter(student_id=student_id, del_row=False)
            .order_by('-test_id__test_date_and_time')
        )

        if not assessments.exists():
            update_app_usage(student_id)
            return JsonResponse({'message': 'No Test Available'}, safe=False, status=400)

        test_ids = [a.test_id_id for a in assessments]

        detail_qs = (
            test_sections.objects
            .select_related('test_id', 'topic_id', 'test_id__subject_id')
            .filter(test_id__test_id__in=test_ids, del_row=False)
        )
        detail_map = {d.test_id.test_id: d for d in detail_qs}

        if not detail_map:
            update_app_usage(student_id)
            return JsonResponse({'message': 'No Test Available'}, safe=False, status=400)

        resp = []
        for a in assessments:
            d = detail_map.get(a.test_id_id)
            if not d:
                continue
            t = d.test_id
            weekly = t.test_type == 'Weekly Test'
            end_dt = (t.test_date_and_time + timedelta(minutes=float(t.test_duration))) if not weekly else a.assessment_completion_time
            status = (
                'Completed' if a.assessment_status == 'Completed'
                else 'Upcomming' if t.test_date_and_time > now
                else 'Ongoing' if (a.assessment_completion_time or t.test_date_and_time) > now > t.test_date_and_time
                else 'Completed'
            )
            resp.append({
                'test_type': t.test_type,
                'test_id': a.test_id_id,
                'test_status': a.assessment_status,
                'score': f'{a.assessment_score_secured}/{t.test_marks}',
                'topic': d.topic_id.topic_name,
                'subject': t.subject_id.subject_name,
                'subject_id': t.subject_id.subject_id,
                'startdate': t.test_date_and_time.strftime('%Y-%m-%d'),
                'starttime': t.test_date_and_time.strftime('%I:%M %p'),
                'enddate': end_dt.strftime('%Y-%m-%d'),
                'endtime': end_dt.strftime('%I:%M %p'),
                'title': t.test_name,
                'status': status
            })

        update_app_usage(student_id)
        return JsonResponse({'test_details': resp}, safe=False, status=200)

    except Exception as e:
        update_app_usage(student_id)
        payload = {'Error_msg': str(e), 
                   'Stack_trace': traceback.format_exc()+\
                    '\nUrl:-'+str(request.build_absolute_uri())+\
                        '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")}
        return JsonResponse({'message': 'Failed', 
                             'error': str(encrypt_message(str(payload)))}, safe=False, status=400)
    


@api_view(['GET'])
def test_instruction(request, student_id, test_id):
    try:
        sa = (
            students_assessments.objects
            .select_related('test_id')
            .only('assessment_status', 'test_id__test_duration')
            .get(student_id=student_id, test_id=test_id, del_row=False)
        )

        if sa.assessment_status == 'Completed':
            update_app_usage(student_id)
            return JsonResponse({'message': 'Test Already Completed'}, safe=False, status=400)

        duration = float(sa.test_id.test_duration) * 60

        section_qs = (
            test_sections.objects
            .filter(test_id=test_id, del_row=False)
            .values('section_number')
            .annotate(section_count=Count('id'))
        )
        sections = {f'section_{r["section_number"]}': r['section_count'] for r in section_qs}

        update_app_usage(student_id)
        return JsonResponse({'duration': duration, 'section_count': sections}, safe=False, status=200)

    except students_assessments.DoesNotExist:
        payload = {'Error_msg': str(e), 'Stack_trace': traceback.format_exc()+\
            '\nUrl:-'+str(request.build_absolute_uri())+\
                '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")}
        return JsonResponse({'message': 'Invalid student_id or test_id',
                             'error': str(encrypt_message(str(payload)))}, safe=False, status=400)
    except Exception as e:
        payload = {'Error_msg': str(e), 'Stack_trace': traceback.format_exc()+\
            '\nUrl:-'+str(request.build_absolute_uri())+\
                '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")}
        update_app_usage(student_id)
        return JsonResponse({'message': 'Failed', 'error': str(encrypt_message(str(payload)))}, safe=False, status=400)
    

@api_view(['GET'])
def section_details(request, student_id, test_id):
    try:
        student = students_assessments.objects.select_related('test_id').get(
            student_id=student_id,
            test_id=test_id,
            del_row=False
        )

        if student.assessment_status == 'Completed':
            return JsonResponse({"message": "Test Already Completed"}, safe=False, status=400)

        test_sections_qs = test_sections.objects.filter(
            test_id=test_id,
            del_row=False
        )

        if not test_sections_qs.exists():
            update_app_usage(student_id)
            return JsonResponse({"message": "No Test Available"}, safe=False, status=400)

        question_ids = test_sections_qs.values_list('question_id__question_id', flat=True)
        answers_qs = student_test_questions_details.objects.filter(
            test_id=test_id,
            student_id=student_id,
            del_row=False,
            question_id__question_id__in=question_ids
        ).select_related('question_id').order_by('question_id')
        answers = {ans.question_id.question_id: ans for ans in answers_qs}

        container_client = get_blob_container_client()

        rules_blob = container_client.get_blob_client('lms_rules/rules.json')
        rules_json = json.loads(rules_blob.download_blob().readall())
        rules_map = {
            rule_type: {
                entry['level'].lower(): {'score': entry['score'], 'time': entry['time']}
                for entry in rules_json[rule_type]
            }
            for rule_type in rules_json
        }
        completed = 0
        total = 0
        response = {}
        qns_data = {}

        for section in test_sections_qs:
            sec_name = section.section_name
            if sec_name not in response:
                response[sec_name] = []

            qid = section.question_id.question_id
            qtype = 'coding' if qid[-5] == 'c' else 'mcq'
            path = f"subjects/{qid[1:3]}/{qid[1:-7]}/{qid[1:-5]}/{qtype}/{qid}.json"

            if cache.get(path) is None:
                blob_client = container_client.get_blob_client(path)
                qn_data = json.loads(blob_client.download_blob().readall())
                qn_data['Qn_name'] = qid
                cache.set(path, qn_data)
            else:
                qn_data = cache.get(path)

            qns_data.setdefault(qtype, []).append(qn_data)

            level = qn_data.get('Level') or qn_data.get('level', '')
            level = str(level).lower()

            if qid in answers:
                completed += 1
            total += 1

            response[sec_name].append({
                'qn_id': qid,
                'question_type': 'Coding' if qtype == 'coding' else 'MCQ',
                'level': level,
                'question': qn_data.get('Qn') or qn_data.get('question'),
                'score': rules_map[qtype].get(level, {}).get('score'),
                'time': rules_map[qtype].get(level, {}).get('time'),
                'status': answers[qid].question_status if qid in answers else 'Pending'
            })

        container_client.close()

        response.update({
            'Completed_Questions': f'{completed}/{total}',
            'Duration': round(student.student_duration / 60, 2) if str(student.test_id.test_type).lower() != 'final test' else 0,
            'Qns_data': qns_data
        })

        # now = timezone.now() + timedelta(hours=5, minutes=30)
        # if not student.student_test_start_time:
        #     student.student_test_start_time = now
        # student.assessment_status = 'Started'
        # student.student_test_completion_time = now
        # student.save()

        # Test_duration_update(student_id, test_id)
        return JsonResponse(response, safe=False, status=200)

    except students_assessments.DoesNotExist:
        return JsonResponse({"message": "Invalid student or test",
                             "error": str(encrypt_message(str({
                                 "Error_msg": "Invalid student or test",
                                 "Stack_trace": traceback.format_exc()+\
                                     '\nUrl:-'+request.build_absolute_uri()+\
                                         '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                 })))}, safe=False, status=400)
    except Exception as e:
        update_app_usage(student_id)
        return JsonResponse({
            "message": "Failed",
            "error": str(encrypt_message(str({
                "Error_msg": str(e),
                "Stack_trace": traceback.format_exc() + '\nUrl:-' + request.build_absolute_uri() +
                               '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
            })))
        }, safe=False, status=400)
@api_view(['PATCH'])
def Start_TEST(request, student_id, test_id):
    try:
        student = students_assessments.objects.select_related('test_id').get(
            student_id=student_id,
            test_id=test_id,
            del_row=False
        )

        if student.assessment_status == 'Completed':
            return JsonResponse({"message": "Test Already Completed"},safe=False,status=400)

        now = timezone.now() + timedelta(hours=5, minutes=30)
        if student.assessment_status == 'Started':
            student.student_test_completion_time = now
            student.save(update_fields=['student_test_completion_time'])
            return JsonResponse({"message": "Test Already Started"},safe=False,status=200)
        if student.student_test_start_time is None:
            student.student_test_start_time = now
        student.assessment_status = 'Started'
        student.student_test_completion_time = now
        student.save(update_fields=['assessment_status', 'student_test_start_time', 'student_test_completion_time'])

        return JsonResponse({"message": "Test Successfully Started"},safe=False,status=200) #Start_TEST_update(student_id,test_id)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
@api_view(['GET'])
def Qns_status_update(request,student_id,test_id):
    try:
        test_sections_qs = test_sections.objects.filter(
            test_id=test_id,
            del_row=False
        )

        if not test_sections_qs.exists():
            update_app_usage(student_id)
            return JsonResponse({"message": "No Test Available"}, safe=False, status=400)

        question_ids = test_sections_qs.values_list('question_id__question_id', flat=True)
        answers_qs = student_test_questions_details.objects.filter(
            test_id=test_id,
            student_id=student_id,
            del_row=False,
            question_id__question_id__in=question_ids
        ).select_related('question_id').order_by('question_id')
        answers = {ans.question_id.question_id: ans for ans in answers_qs}
        completed ,total = 0,0
        response = {}
        for section in test_sections_qs:
            sec_name = section.section_name
            if sec_name not in response:
                response[sec_name] = []
            qid = section.question_id.question_id
            if qid in answers:
                completed += 1
            total += 1

            response[sec_name].append({
                'qn_id': qid,
                'status': answers[qid].question_status if qid in answers else 'Pending'
            })
        response.update({
            'Completed_Questions': f'{completed}/{total}'
        })
        return JsonResponse (response, safe=False, status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)

def Test_duration_update(student_id, test_id):
    try:
        student = students_assessments.objects.select_related('test_id').get(
            student_id=student_id,
            test_id=test_id,
            del_row=False
        )

        if student.assessment_status == 'Completed':
            return {
                "status": "Test Already Completed",
                "time_left": 0
            }

        now = timezone.now() + timedelta(hours=5, minutes=30)

        if student.student_test_completion_time is None:
            student.student_test_completion_time = now

        elapsed = (now - student.student_test_completion_time).total_seconds()
        student.student_duration += elapsed
        student.student_test_completion_time = now

        test_type = str(student.test_id.test_type).lower()
        test_duration_secs = float(student.test_id.test_duration) * 60
        user_duration_secs = student.student_duration

        if test_type == 'final test':
            if now > student.assessment_completion_time:
                student.assessment_status = 'Completed'
                student.save()
                return {
                    "status": "Completed",
                    "time_left": 0
                }

            total_allowed_duration = (student.assessment_completion_time - student.test_id.test_date_and_time).total_seconds()
            if user_duration_secs >= total_allowed_duration:
                student.assessment_status = 'Completed'

            student.save()
            return {
                "status": "success" if student.assessment_status != 'Completed' else "Completed",
                "time_left": round((student.assessment_completion_time - now).total_seconds()),
                "test_duration": total_allowed_duration / 60,
                "user_duration": round(user_duration_secs / 60, 2)
            }

        # Non-final test
        time_left = test_duration_secs - user_duration_secs
        if time_left <= 0:
            student.assessment_status = 'Completed'
            student.save()
            return {
                "status": "Completed",
                "time_left": 0,
                "test_duration": (student.assessment_completion_time - student.test_id.test_date_and_time).total_seconds() / 60,
                "user_duration": round(user_duration_secs / 60, 2)
            }

        student.save()
        return {
            "status": "success",
            "time_left": round(time_left),
            "test_duration": (student.assessment_completion_time - student.test_id.test_date_and_time).total_seconds() / 60,
            "user_duration": round(user_duration_secs / 60, 2)
        }

    except Exception as e:
        return {'Error': str(e)}

@api_view(['PATCH'])
def Test_duration(request,student_id,test_id):
    try:
        return JsonResponse(Test_duration_update(student_id,test_id),safe=False,status=200) #Test_duration_update(student_id,test_id)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
    
from django.db import transaction
@api_view(['POST'])
def submit_test(request, student_id, test_id):
    try:
        with transaction.atomic():
            student = (
                students_assessments.objects
                .select_related('test_id')
                .select_for_update()
                .get(student_id=student_id, test_id=test_id, del_row=False)
            )

            if student.assessment_status == 'Completed':
                return JsonResponse({'message': 'Test Already Completed'}, safe=False, status=400)
            
            now = timezone.now() + timedelta(hours=5, minutes=30)

            if student.student_test_completion_time is None:
                student.student_test_completion_time = now

            elapsed = (now - student.student_test_completion_time).total_seconds()
            student.student_duration += elapsed
            student.student_test_completion_time = now
            student.assessment_status = 'Completed'
            student.save()

        return JsonResponse({'message': 'Test Successfully Completed'}, safe=False, status=200)

    except students_assessments.DoesNotExist:
        return JsonResponse({'message': 'Invalid student or test',
                             "error":str(encrypt_message(str({
                                    "Error_msg":  "Invalid student or test",
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
    except Exception as e:
        payload = {'Error_msg': str(e), 'Stack_trace': traceback.format_exc()}
        return JsonResponse({'message': 'Failed', 'error': str(encrypt_message(str(payload)))}, safe=False, status=400)



@api_view(['PUT'])
def submit_test_mcq_questions(request):
    try:
        data = json.loads(request.body)
        student_id = data['student_id']
        test_id = data['test_id']
        qid = data['question_id']
        now = timezone.now() + timedelta(hours=5, minutes=30)

        with transaction.atomic():
            sa = (
                students_assessments.objects
                .select_related('student_id', 'test_id')
                .get(student_id=student_id, test_id=test_id, del_row=False)
            )
            if sa.assessment_status == 'Completed':
                return JsonResponse({'message': 'Test Already Completed'}, safe=False, status=400)

            rules = cache.get('mcq_rules')
            if rules is None:
                rules = {
                    r['level'].lower(): r['score']
                    for r in json.loads(get_blob('lms_rules/rules.json'))['mcq']
                }
                cache.set('mcq_rules', rules, 3600)

            diff_map = {'e': 'level1', 'm': 'level2', 'h': 'level3'}
            outof = int(rules[diff_map[qid[-4]]])
            score = int(outof) if data['correct_ans'] == data['entered_ans'] else 0

            spm, created_m = student_practiceMCQ_answers.objects.using('mongodb').get_or_create(
                student_id=student_id,
                question_id=qid,
                question_done_at=test_id,
                del_row='False',
                defaults={
                    'subject_id': data['subject_id'],
                    'question_id': qid,
                    'question_done_at': test_id,
                    'correct_ans': data['correct_ans'],
                    'entered_ans': data['entered_ans'],
                    'subject_id': data['subject_id'],
                    'score': score,
                    'answered_time': now
                }
            )
            if not created_m:
                Test_duration_update(student_id, test_id)
                return JsonResponse({'message': 'Already Submited'}, safe=False, status=200)

            q = questions.objects.only('sub_topic_id__topic_id__subject_id', 'question_type').get(
                question_id=qid, del_row=False
            )

            stq, created_q = student_test_questions_details.objects.get_or_create(
                student_id=student_id,
                test_id=test_id,
                question_id=qid,
                del_row='False',
                defaults={
                    'student_id': sa.student_id,
                    'subject_id': q.sub_topic_id.topic_id.subject_id,
                    'question_id': q,
                    'question_type': q.question_type,
                    'test_id': sa.test_id,
                    'question_status': 'Submitted',
                    'student_answer': data['entered_ans'],
                    'score_secured': score,
                    'week_number': sa.assessment_week_number,
                    'max_score': outof,
                    'completion_time': now
                }
            )

            if created_q:
                s = sa.student_id
                s.student_score += score
                s.student_total_score += outof
                s.save(update_fields=['student_score', 'student_total_score'])

                sa.assessment_status = 'Started'
                sa.assessment_score_secured += score
                sa.student_test_completion_time = now
                sa.save(update_fields=['assessment_status', 'assessment_score_secured', 'student_test_completion_time'])
            else:
                stq.question_status = 'Submitted'
                stq.save(update_fields=['question_status'])

        return JsonResponse(
            {
                'message': 'Submited',
                'user_answer': stq.student_answer,
                'question_status': stq.question_status
            },
            safe=False,
            status=200
        )

    except students_assessments.DoesNotExist:
        return JsonResponse({'message': 'Invalid student or test',
                             'error': str(encrypt_message(str({'Error_msg': 'Invalid student or test',
                                                               'Stack_trace': traceback.format_exc()+\
                                                                '\nUrl:-'+str(request.build_absolute_uri())+\
                                                                    '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")})))}, safe=False, status=400)
    except Exception as e:
        payload = {'Error_msg': str(e), 'Stack_trace': traceback.format_exc()+\
            '\nUrl:-'+str(request.build_absolute_uri())+\
            '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")}
        return JsonResponse({'message': 'Failed', 'error': str(encrypt_message(str(payload)))}, safe=False, status=400)


@api_view(['PUT'])
def submit_test_coding_questions(request):
    try:
        data = json.loads(request.body)
        student_id = data['student_id']
        test_id = data['test_id']
        qid = data['Qn']
        now = timezone.now() + timedelta(hours=5, minutes=30)

        rules = cache.get('coding_rules')
        if rules is None:
            rules = {
                r['level'].lower(): r['score']
                for r in json.loads(get_blob('lms_rules/rules.json'))['coding']
            }
            cache.set('coding_rules', rules, 3600)

        diff_map = {'e': 'level1', 'm': 'level2', 'h': 'level3'}
        outof = float(rules[diff_map[qid[-4]]])
        score = float(outof)

        passed, total = 0, 0
        result = {}

        if data['subject'] in {'HTML', 'HTML CSS', 'CSS', 'Java Script'}:
            passed, total = map(float, data['final_score'].split('/'))
            result = {'TestCases': data['final_score']}
        else:
            for idx, r in enumerate(data['Result'], 1):
                tc_val = r.get(f'TestCase{idx}')
                if tc_val in {'Passed', 'Failed'}:
                    total += 1
                    if tc_val == 'Passed':
                        passed += 1
                    result.update(r)
                if 'Result' in r:
                    result.update(r)
            if total == 0:
                score = 0.0

        score = round(score * (passed / total if total else 0), 2)

        spc, created_m = student_practice_coding_answers.objects.using('mongodb').get_or_create(
            student_id=student_id,
            subject_id=data['subject_id'],
            question_id=qid,
            question_done_at=test_id,
            del_row='False',
            defaults={
                'entered_ans': data['Ans'],
                'answered_time': now,
                'testcase_results': result,
                'Attempts': 1,
                'score': score,
                'del_row': 'False'
            }
        )
        if not created_m:
            Test_duration_update(student_id, test_id)
            return JsonResponse({'message': 'Submited', 'status': True}, safe=False, status=200)

        with transaction.atomic():
            sa = (
                students_assessments.objects
                .select_related('student_id', 'test_id')
                .get(student_id=student_id, test_id=test_id, del_row=False)
            )

            q = questions.objects.only('sub_topic_id__topic_id__subject_id', 'question_type').get(
                question_id=qid, del_row=False
            )

            stq, created_q = student_test_questions_details.objects.get_or_create(
                student_id=student_id,
                test_id=test_id,
                question_id=qid,
                del_row='False',
                defaults={
                    'student_id': sa.student_id,
                    'test_id': sa.test_id,
                    'subject_id': q.sub_topic_id.topic_id.subject_id,
                    'question_id': q,
                    'question_type': q.question_type,
                    'question_status': 'Submitted',
                    'student_answer': data['Ans'],
                    'score_secured': score,
                    'week_number': sa.assessment_week_number,
                    'max_score': outof,
                    'completion_time': now
                }
            )

            if created_q:
                s = sa.student_id
                s.student_score += score
                s.student_total_score += outof
                s.save(update_fields=['student_score', 'student_total_score'])

                sa.assessment_status = 'Started'
                sa.assessment_score_secured += score
                sa.student_test_completion_time = now
                sa.save(update_fields=['assessment_status', 'assessment_score_secured', 'student_test_completion_time'])
            else:
                stq.question_status = 'Submitted'
                stq.save(update_fields=['question_status'])

        return JsonResponse(
            {
                'message': 'Submited',
                'status': True,
                'user_answer': stq.student_answer,
                'question_status': stq.question_status
            },
            safe=False,
            status=200
        )

    except students_assessments.DoesNotExist:
        return JsonResponse({'message': 'Invalid student or test',
                             'error': str(encrypt_message(str({
                                 'Error_msg': 'Invalid student or test', 
                                 'Stack_trace': traceback.format_exc()+\
                                    '\nUrl:-'+str(request.build_absolute_uri())+\
                                        '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")})))}, safe=False, status=400)
    except Exception as e:
        payload = {'Error_msg': str(e), 'Stack_trace': traceback.format_exc()+\
            '\nUrl:-'+str(request.build_absolute_uri())+\
            '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")}
        return JsonResponse({'message': 'Failed', 'error': str(encrypt_message(str(payload)))}, safe=False, status=400)
    

@api_view(['GET'])
def student_test_report(request, student_id, test_id):
    try:
        sa = (
            students_assessments.objects
            .select_related('test_id', 'student_id')
            .get(student_id=student_id, test_id=test_id, del_row=False)
        )

        sections = list(
            test_sections.objects
            .select_related('question_id__sub_topic_id__topic_id')
            .filter(test_id=test_id, del_row=False)
        )
        qids = [s.question_id.question_id for s in sections]
        topics = {
            s.question_id.question_id: s.question_id.sub_topic_id.topic_id.topic_name
            for s in sections
        }

        ans_sql = list(
            student_test_questions_details.objects
            .filter(student_id=student_id, test_id=test_id, question_id__in=qids, del_row=False)
            .values('question_id', 'score_secured', 'max_score')
        )
        ans_sql_map = {r['question_id']: r for r in ans_sql}

        m_ans = {
            r['question_id']: r
            for r in student_practiceMCQ_answers.objects.using('mongodb')
            .filter(student_id=student_id, question_id__in=qids, question_done_at=test_id, del_row=False)
            .values('question_id', 'entered_ans')
        }
        c_ans = {
            r['question_id']: r
            for r in student_practice_coding_answers.objects.using('mongodb')
            .filter(student_id=student_id, question_id__in=qids, question_done_at=test_id, del_row=False)
            .values('question_id', 'entered_ans', 'testcase_results')
        }

        now_taken = round(sa.student_duration / 60)
        ttl_given = (
            round((sa.assessment_completion_time - sa.test_id.test_date_and_time).total_seconds() / 60)
            if sa.assessment_type != 'Weekly Test' else float(sa.test_id.test_duration)
        )
        test_summary = {
            'time_taken_for_completion': f'{now_taken} min' if now_taken < 60 else f'{now_taken//60} hrs {now_taken%60} min',
            'total_time': f'{ttl_given} min' if ttl_given < 60 else f'{ttl_given//60} hrs {ttl_given%60} min',
            'score_secured': sum(r['score_secured'] for r in ans_sql),
            'max_score': sa.assessment_max_score,
            'percentage': round((sa.assessment_score_secured / sa.assessment_max_score) * 100, 2),
            'status': sa.assessment_status,
            'attempted_questions': len(ans_sql),
            'total_questions': len(qids),
            'test_start_time': format_time_with_zone(sa.student_test_start_time),
            'test_end_time': format_time_with_zone(sa.student_test_completion_time)
        }
        if sa.assessment_type == 'Final Test':
            test_summary.update({
                'overall_rank': sa.student_id.student_overall_rank,
                'college_rank': sa.student_id.student_college_rank
            })

        cache_get = cache.get
        cache_set = cache.set
        blob = get_blob
        rules = cache_get('rules_json')
        if rules is None:
            rules = json.loads(blob('lms_rules/rules.json'))
            cache_set('rules_json', rules, 3600)

        mcq, coding, topic_scores = [], [], {}
        for q in qids:
            path = f"subjects/{q[1:3]}/{q[1:-7]}/{q[1:-5]}/{'mcq' if q[-5]=='m' else 'coding'}/{q}.json"
            qdata = cache_get(path)
            if qdata is None:
                qdata = json.loads(get_blob_container_client().get_blob_client(path).download_blob().readall())
                qdata['Qn_name'] = q
                cache_set(path, qdata)

            sql_row = ans_sql_map.get(q, {'score_secured': 0, 'max_score': 0})
            status_val = 'Not Attempted'
            if sql_row['max_score']:
                if sql_row['score_secured'] == sql_row['max_score']:
                    status_val = 'Correct'
                elif sql_row['score_secured'] > 0:
                    status_val = 'Partial Correct'
                else:
                    status_val = 'Wrong'

            qdata.update({
                'score_secured': sql_row['score_secured'],
                'max_score': int(sql_row['max_score']),
                'status': status_val,
                'topic': topics[q]
            })

            topic_scores.setdefault(topics[q], [0, 0])
            topic_scores[topics[q]][0] += sql_row['score_secured']
            topic_scores[topics[q]][1] += sql_row['max_score']

            if q[-5] == 'm':
                qdata['user_answer'] = m_ans.get(q, {}).get('entered_ans', '')
                mcq.append(qdata)
            else:
                tc_res = c_ans.get(q, {})
                tcs = tc_res.get('testcase_results', {})
                passed = len([k for k, v in tcs.items() if k.startswith('TestCase') and v == 'Passed'])
                total = len([k for k in tcs if k.startswith('TestCase')])
                qdata.update({
                    'user_answer': tc_res.get('entered_ans', ''),
                    'testcases': f'{passed}/{total or len(qdata.get("TestCases", []))}'
                })
                coding.append(qdata)

        topic_buckets = {'good': [], 'average': [], 'poor': []}
        topic_scores_str = {}
        for t, (sc, mx) in topic_scores.items():
            topic_scores_str[t] = f'{sc}/{mx}'
            ratio = sc / mx if mx else 0
            if ratio >= 0.7:
                topic_buckets['good'].append(t)
            elif ratio >= 0.4:
                topic_buckets['average'].append(t)
            else:
                topic_buckets['poor'].append(t)

        resp = {
            'test_summary': test_summary,
            'topics_wise_scores': topic_scores_str,
            'topics': topic_buckets,
            'answers': {'mcq': mcq, 'coding': coding}
        }
        return JsonResponse(resp, safe=False, status=200)

    except students_assessments.DoesNotExist:
        return JsonResponse({'message': 'Invalid student or test',
                             "error":str(encrypt_message(str({
                                    "Error_msg":  "Invalid student or test",
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
    except Exception as e:
        payload = {'Error_msg': str(e), 'Stack_trace': traceback.format_exc()+\
                   '\nUrl:-'+str(request.build_absolute_uri())+\
                    '\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")}
        return JsonResponse({'message': 'Failed', 'error': str(encrypt_message(str(payload)))}, safe=False, status=400)
    


def format_time_with_zone(date):
    if not date:
        return None
    if isinstance(date, str):
        date = datetime.strptime(date.split('.')[0].split('+')[0], "%Y-%m-%d %H:%M:%S")
    return f"{calendar.month_abbr[date.month]} {date.day} {date.year} {date.strftime('%H:%M:%S')} IST"
