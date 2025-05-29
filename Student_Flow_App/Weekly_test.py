
from LMS_Project.Blobstorage import *
from django.http import JsonResponse
from rest_framework.decorators import api_view
from LMS_MSSQLdb_App.models import *
from LMS_Mongodb_App.models import *
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Max, F ,Sum,Min,Count
from django.db.models.functions import Substr, Cast
from django.db.models import IntegerField
from django.db import transaction
import json
from django.db.models.functions import TruncDate    
from .ErrorLog import *
rule_for_weekly_test = {
    'MCQ':10,'Coding':3
    # 'MCQ':7,'Coding':3
}
@api_view(['GET'])
def Automated_weekly_test(request, student_id, week_number, subject_id):
    try:
        student_detail = students_details.objects.using('mongodb').get(student_id=student_id, del_row=False)
        student_info = students_info.objects.get(student_id=student_id, del_row=False)

        course_key = f"{student_info.course_id.course_id}_{subject_id}"
        week_key = f"week_{week_number}"
        week_data = student_detail.student_question_details.get(course_key, {}).get(week_key, {})

        week_status = []
        all_sub_topics = set()
        all_practiced_Questions = []

        for day_data in week_data.values():
            sub_topic_status = day_data.get('sub_topic_status', {})
            week_status.extend(v == 2 for v in sub_topic_status.values())
            all_sub_topics.update(sub_topic_status.keys())
            all_practiced_Questions.extend(day_data.get('mcq_questions', []))
            all_practiced_Questions.extend(day_data.get('coding_questions', []))

        if not week_status or week_status.count(True) != len(week_status):
            return JsonResponse({"message": "Not Unlocked yet"}, safe=False, status=400)

        sub_topic_list = list(all_sub_topics)
        questions_queryset = questions.objects.filter(
            sub_topic_id__sub_topic_id__in=sub_topic_list,
            sub_topic_id__topic_id__subject_id__subject_id=subject_id,
            del_row=False
        )

        sub_topic_wise_mcq_qns = {sub: [] for sub in sub_topic_list}
        sub_topic_wise_coding_qns = {sub: [] for sub in sub_topic_list}
        all_mcq_qns, all_coding_qns, all_qns = [], [], []

        for qn in questions_queryset:
            qid_str = str(qn.question_id).lower()
            sub_id = qn.sub_topic_id.sub_topic_id
            all_qns.append(qn.question_id)
            if qid_str[-5] == 'm':
                sub_topic_wise_mcq_qns[sub_id].append(qn.question_id)
                all_mcq_qns.append(qn.question_id)
            elif qid_str[-5] == 'c':
                sub_topic_wise_coding_qns[sub_id].append(qn.question_id)
                all_coding_qns.append(qn.question_id)

        maxMCQ = rule_for_weekly_test.get('MCQ', 0)
        maxCoding = rule_for_weekly_test.get('Coding', 0)

        if len(all_mcq_qns) < maxMCQ:
            shortfall = maxMCQ - len(all_mcq_qns)
            extra = round(shortfall / 2)
            maxCoding += extra if len(all_coding_qns) >= (maxCoding + extra) else 0
            maxMCQ = len(all_mcq_qns)

        if len(all_coding_qns) < maxCoding:
            shortfall = maxCoding - len(all_coding_qns)
            extra = round(shortfall * 2)
            maxMCQ += extra if len(all_mcq_qns) >= (maxMCQ + extra) else 0
            maxCoding = len(all_coding_qns)

        mcqsection, codingsections = [], []

        while all_qns and (len(mcqsection) < maxMCQ or len(codingsections) < maxCoding):
            for sub_id in sub_topic_list:
                if len(mcqsection) < maxMCQ and sub_topic_wise_mcq_qns[sub_id]:
                    q = sub_topic_wise_mcq_qns[sub_id].pop()
                    mcqsection.append(q)
                    all_qns.remove(q)
                    all_mcq_qns.remove(q)

                if len(codingsections) < maxCoding and sub_topic_wise_coding_qns[sub_id]:
                    q = sub_topic_wise_coding_qns[sub_id].pop()
                    codingsections.append(q)
                    all_qns.remove(q)
                    all_coding_qns.remove(q)

        result = create_weekly_test(student_info, week_number, subject_id, mcqsection, codingsections)
        return JsonResponse(result, safe=False, status=200)

    except Exception as e:
        return JsonResponse({
            "message": "Failed",
            "error": str(encrypt_message(str({
                "Error_msg": str(e),
                "Stack_trace": traceback.format_exc(),
                "Url": str(request.build_absolute_uri()),
                "Body": str(json.loads(request.body)) if request.body else "{}"
            })))
        }, safe=False, status=400)
def create_weekly_test(student, week_number, subject_id, mcqsection, codingsections):
    try:
        now = timezone.now() + timedelta(hours=5, minutes=30)

        subject = course_subjects.objects.select_related(
            'subject_id', 'course_id', 'batch_id', 'subject_id__track_id'
        ).get(
            subject_id__subject_id=subject_id,
            course_id=student.course_id,
            batch_id=student.batch_id,
            del_row=False
        )

        max_num = (
            test_details.objects
            .annotate(num=Cast(Substr('test_id', 5), IntegerField()))
            .aggregate(mx=Max('num'))['mx'] or 0
        )
        new_test_id = f'Test{max_num + 1}'

        rules = cache.get('rules_json')
        if rules is None:
            rules = json.loads(get_blob('lms_rules/rules.json'))
            cache.set('rules_json', rules, 3600)
        mcq_map = {l['level'].lower(): (l['score'], l['time']) for l in rules['mcq']}
        cod_map = {l['level'].lower(): (l['score'], l['time']) for l in rules['coding']}

        dur, marks = 0, 0
        all_qns = mcqsection + codingsections
        for q in all_qns:
            lvl = 'level1' if q[-4] == 'e' else 'level2' if q[-4] == 'm' else 'level3'
            if q[-5] == 'm':
                sc, tm = mcq_map[lvl]
            else:
                sc, tm = cod_map[lvl]
            marks += int(sc)
            dur += float(tm)

        with transaction.atomic():
            weekly_test, created = test_details.objects.get_or_create(
                test_name=f'Week {week_number} Test',
                track_id=subject.subject_id.track_id,
                subject_id=subject.subject_id,
                course_id=subject.course_id,
                batch_id=student.batch_id,
                test_type='Weekly Test',
                test_created_by='Auto generated',
                del_row=False,
                defaults={
                    'test_id': new_test_id,
                    'track_id': subject.subject_id.track_id,
                    'test_description': f'Weekly test for Week {week_number} for {subject.subject_id.subject_name} of {subject.course_id.course_name} of {student.batch_id.batch_name}',
                    'test_duration': dur,
                    'test_marks': marks,
                    'test_created_by': 'Auto generated',
                    'test_created_date_time': now,
                    'test_date_and_time': now
                }
            )

            if not test_sections.objects.filter(test_id=weekly_test).exists():
                q_map = {
                    q.question_id: q for q in
                    questions.objects.filter(question_id__in=all_qns, del_row=False)
                    .select_related('sub_topic_id__topic_id')
                }
                bulk_sec = [
                    test_sections(
                        test_id=weekly_test,
                        section_number=1,
                        section_name='MCQ',
                        question_id=q_map[q],
                        topic_id=q_map[q].sub_topic_id.topic_id,
                        sub_topic_id=q_map[q].sub_topic_id
                    ) for q in mcqsection
                ] + [
                    test_sections(
                        test_id=weekly_test,
                        section_number=2,
                        section_name='Coding',
                        question_id=q_map[q],
                        topic_id=q_map[q].sub_topic_id.topic_id,
                        sub_topic_id=q_map[q].sub_topic_id
                    ) for q in codingsections
                ]
                test_sections.objects.bulk_create(bulk_sec)

            students_assessments.objects.get_or_create(
                student_id=student,
                course_id=subject.course_id,
                subject_id=subject.subject_id,
                assessment_type='Weekly Test',
                test_id=weekly_test,
                defaults={
                    'assessment_status': 'Pending',
                    'assessment_score_secured': 0,
                    'assessment_max_score': marks,
                    'assessment_week_number': week_number,
                    'assessment_completion_time': now + timedelta(days=(9 - now.weekday())),
                    'assessment_rank': 0,
                    'assessment_overall_rank': 0,
                    'student_duration': 0
                }
            )

        return {
            'status': 'success',
            'message': 'Weekly Test Created' if created else 'Weekly Test Already Exists',
            'test_id': weekly_test.test_id
        }

    except Exception as e:
        return {'status': f'error: {e}'}