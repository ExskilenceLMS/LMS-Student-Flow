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
# from LMS_Project.Blobstorage import *
from .AppUsage import update_app_usage
from django.core.cache import cache
from LMS_Project.Blobstorage import *
from .sqlrun import get_all_tables


@api_view(['GET'])
def fetch_all_test_details(request,student_id):
    try:
        students_assessment = students_assessments.objects.filter(student_id = student_id,
                                                                     del_row = False
                                                                     ).values(
                                                                         'assessment_type',
                                                                         'subject_id',
                                                                         'test_id',
                                                                         'course_id',
                                                                         'assessment_status',
                                                                         'assessment_score_secured',
                                                                         'assessment_max_score',
                                                                         'assessment_week_number',
                                                                         'assessment_completion_time'
                                                                     ).order_by('-test_id__test_date_and_time')
        # students_assessment_end_time =  {test.get('test_id'):test.get('assessment_completion_time') for test in students_assessment}
        if students_assessment == []:
            update_app_usage(student_id)
            return JsonResponse({"message": "No Test Available"},safe=False,status=400)
        test_detail_obj = test_sections.objects.filter(test_id__test_id__in = [test.get('test_id') for test in students_assessment],
                                                  del_row = False) 
        test_detail = {test.test_id.test_id:test for test in test_detail_obj} 
        if test_detail == {}:
            update_app_usage(student_id)
            return JsonResponse({"message": "No Test Available"},safe=False,status=400)
        response =[{
            "test_type"     : test_detail.get(test.get('test_id')).test_id.test_type,
            "test_id"       : test.get('test_id'),
            "test_status"   : test.get('assessment_status'),
            "score"         : str(test.get('assessment_score_secured'))+'/'+str(test_detail.get(test.get('test_id')).test_id.test_marks),
            'topic'         : test_detail.get(test.get('test_id')).topic_id.topic_name,
            "subject"       : test_detail.get(test.get('test_id')).test_id .subject_id.subject_name,
            'subject_id'    : test_detail.get(test.get('test_id')).test_id .subject_id.subject_id,
            "startdate"     : test_detail.get(test.get('test_id')).test_id .test_date_and_time.strftime("%Y-%m-%d"),
            "starttime"     : test_detail.get(test.get('test_id')).test_id .test_date_and_time.strftime("%I:%M %p"),# + " " + test_detail.get(test.get('test_id')).test_id .test_date_and_time.strftime("%p"),
            "enddate"       : (test_detail.get(test.get('test_id')).test_id .test_date_and_time.__add__(timedelta(minutes = float(test_detail.get(test.get('test_id')).test_id.test_duration))).strftime("%Y-%m-%d"))\
                                   if test_detail.get(test.get('test_id')).test_id.test_type != 'Weekly Test' else test.get('assessment_completion_time').strftime("%Y-%m-%d"),
            "endtime"       : (test_detail.get(test.get('test_id')).test_id .test_date_and_time.__add__(timedelta(minutes = float(test_detail.get(test.get('test_id')).test_id.test_duration)))).strftime("%I:%M %p")\
                                   if test_detail.get(test.get('test_id')).test_id.test_type != 'Weekly Test' else test.get('assessment_completion_time').strftime("%I:%M %p")   ,# + " " + (test_detail.get(test.get('test_id')).test_id .test_date_and_time.__add__(timedelta(minutes = int(test_detail.get(test.get('test_id')).test_id.test_duration)))).strftime("%p"),
            "title"         : test_detail.get(test.get('test_id')).test_id .test_name,
            "status"        : 'Completed' if test.get('assessment_status') == 'Completed' else 'Upcomming' if  test_detail.get(test.get('test_id')).test_id .test_date_and_time > timezone.now().__add__(timedelta(hours=5,minutes=30)) else 'Ongoing' if test.get('assessment_completion_time',0) > timezone.now().__add__(timedelta(hours=5,minutes=30)) and test_detail.get(test.get('test_id')).test_id .test_date_and_time < timezone.now().__add__(timedelta(hours=5,minutes=30))  else 'Completed'          
            # ,'test_duration' : test_detail.get(test.get('test_id')).test_id.test_duration,
            # 'testc to,end'  : test.get('assessment_completion_time',0),'now': timezone.now().__add__(timedelta(hours=5,minutes=30))
        }  for test in students_assessment if test_detail.get(test.get('test_id')) != None]
        update_app_usage(student_id)
        return JsonResponse({'test_details':response},safe=False,status=200)
    except Exception as e:
        print(e)
        update_app_usage(student_id)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
def date_formater(date_time):
    return str(date_time.day)+'-'+str(date_time.month)+'-'+str(date_time.year)[-2:]+' '+str(date_time.strftime('%I:%M %p'))
@api_view(['GET'])
def test_insturction(request,student_id,test_id):
    try:
        student = students_assessments.objects.get(
            student_id = student_id,
            test_id = test_id,
            del_row = False
        )
        if student.assessment_status == 'Completed':
            update_app_usage(student_id)
            return JsonResponse({"message": "Test Already Completed"},safe=False,status=400)
        # if student.student_duration >= (student.test_id.test_date_and_time - student.student_test_completion_time).total_seconds():
        #     update_app_usage(student_id)
        #     return JsonResponse({"message": "Test Completed due to time limit reached."},safe=False,status=400)
        test_detaile_queryset = test_sections.objects.filter(
                                                        test_id=test_id, 
                                                        del_row=False
                                                    ).values('section_number','test_id__test_duration').annotate(
                                                        section_count=Count('id')
                                                    )
        test_detaile = {
            'duration'      :0,
            'section_count' :{}
        }
        [test_detaile.update({'duration'    :item.get('test_id__test_duration')}) for item in test_detaile_queryset]
        test_detaile.update({'section_count': {'section_'+str(item.get('section_number')): item.get('section_count') for item in test_detaile_queryset} })
        return JsonResponse(test_detaile,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)

@api_view(['GET'])
def section_details(request,student_id,test_id):
    try:
        # print(test_id)
        student = students_assessments.objects.get(
            student_id = student_id,
            test_id = test_id,
            del_row = False
        )
        if student.assessment_status == 'Completed':
            # update_app_usage(student_id)
            return JsonResponse({"message": "Test Already Completed"},safe=False,status=400)
        # if student.student_duration >= (student.test_id.test_date_and_time - student.student_test_completion_time).total_seconds():
        #     update_app_usage(student_id)
        #     return JsonResponse({"message": "Test Completed due to time limit reached."},safe=False,status=400)
        test_section = test_sections.objects.filter(test_id = test_id,del_row = False)
        answers = student_test_questions_details.objects.filter(
                                                    test_id = test_id,
                                                    student_id = student_id,
                                                    del_row = False
                                                    ).order_by('question_id')
        
        if test_section == [] :
            update_app_usage(student_id)
            return JsonResponse({"message": "No Test Available"},safe=False,status=400)
        answers = {ans.question_id.question_id:ans for ans in answers}
        # print(answers)
        response ={}
        container_client = get_blob_container_client()
        rules = container_client.get_blob_client('lms_rules/rules.json')
        Rules = json.loads(rules.download_blob().readall())
        rules_Json = {}
        Completed_Questions = {
            'total':0,'completed':0
        }
        Qns_data = {}
        for rule in Rules:
            if rules_Json.get(rule) == None:
                rules_Json.update({rule:{}})
            rules_Json.get(rule).update({i.get('level').lower():{
                'score':i.get('score'),
                'time':i.get('time')    } for i in Rules.get(rule)})
        for test in test_section:
            if response.get(test.section_name) == None:
                response.update({test.section_name:[]})
            Qn = test.question_id.question_id
            path = f"subjects/{Qn[1:3]}/{Qn[1:-7]}/{Qn[1:-5]}/{'mcq' if Qn[-5]=='m' else 'coding'}/{Qn}.json"
            # print(path)
            if cache.get(path) == None:
                blobdata = container_client.get_blob_client(path)
                blob_data = json.loads(blobdata.download_blob().readall())
                blob_data.update({'Qn_name':Qn})
                cache.set(path,blob_data)
            else:
                blob_data = cache.get(path)
                cache.set(path,blob_data)
            level = blob_data.get('Level','') if blob_data.get('Level') else blob_data.get('level','')
            if answers.get(Qn):
                Completed_Questions.update({'completed':Completed_Questions.get('completed')+1})
            Completed_Questions.update({'total':Completed_Questions.get('total')+1})
            response.get(test.section_name).append({
                             "qn_id"            : Qn,
                             "question_type"    : 'Coding' if Qn[-5] == 'c' else 'MCQ',
                             "level"            : str(level).lower().replace('level',''),
                             "question"         : blob_data.get('Qn') if blob_data.get('Qn') else blob_data.get('question'),
                             "score"            : rules_Json.get('coding',{}).get(level)['score'] if Qn[-5] == 'c' else rules_Json.get('mcq',{}).get(level)['score'],
                             "time"             : rules_Json.get('coding',{}).get(level)['time'] if Qn[-5] == 'c' else rules_Json.get('mcq',{}).get(level)['time'],
                             "status"           : answers.get(Qn).question_status if answers.get(Qn) else 'Pending',
                            })
            if Qns_data.get('coding' if Qn[-5] == 'c' else 'mcq') == None:
                Qns_data.update({'coding' if Qn[-5] == 'c' else 'mcq':[]})
            Qns_data.get('coding' if Qn[-5] == 'c' else 'mcq').append(blob_data)
        container_client.close()
        response.update({'Completed_Questions':str(Completed_Questions.get('completed'))+'/'+str(Completed_Questions.get('total')),
                         'Duration':round(student.student_duration/60,2) if str(student.test_id.test_type).lower() != 'final test' else 0,
                        'Qns_data':Qns_data})
        if student.student_test_start_time == None:
            student.student_test_start_time = timezone.now() + timedelta(hours=5, minutes=30)
        student.assessment_status = 'Started'
        student.student_test_completion_time = timezone.now() + timedelta(hours=5, minutes=30)
        student.save()
        # update_app_usage(student_id)
        Test_duration_update(student_id,test_id)
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        update_app_usage(student_id)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)

@api_view(['GET'])
def Test_duration(req,student_id,test_id):
    try:
        return JsonResponse(Test_duration_update(student_id,test_id),safe=False,status=200) #Test_duration_update(student_id,test_id)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)

def Test_duration_update(student_id,test_id):
    try:
        student = students_assessments.objects.get(
            student_id = student_id,
            test_id = test_id,
            del_row = False
        )
        if student.assessment_status == 'Completed':
            # update_app_usage(student_id)
            return {"status": "Test Already Completed",
                                 "time_left":0
                                 }
        if student.student_test_completion_time == None:
            student.student_test_completion_time= timezone.now() + timedelta(hours=5, minutes=30)
        now = timezone.now() + timedelta(hours=5, minutes=30)
        student.student_duration += (now-student.student_test_completion_time).total_seconds()
        student.student_test_completion_time = now
        if str(student.test_id.test_type).lower() == 'Final Test'.lower():
            if now > student.assessment_completion_time:
                student.assessment_status = 'Completed'
                student.student_test_completion_time = now 
                student.save()
                # update_app_usage(student_id)
                return {"status": "Completed",
                                     "time_left":0}
            if (student.assessment_completion_time-student.test_id.test_date_and_time).total_seconds()/60 <= round(student.student_duration/60,2):
                student.assessment_status = 'Completed'
                student.student_test_completion_time = now
                print(student.assessment_completion_time-student.test_id.test_date_and_time,student.assessment_status)            
            # student.assessment_status = 'Completed'
            student.save()
            # update_app_usage(student_id)
            return {"status": "success",
                                 "time_left": round((student.assessment_completion_time-now).total_seconds()),
                                 'test_duration':(student.assessment_completion_time-student.test_id.test_date_and_time).total_seconds()/60,
                                 'user_duration':round(student.student_duration/60,2)
                                 }
        if round(float(student.test_id.test_duration)*60-student.student_duration,2) <= 0:
            student.assessment_status = 'Completed'
            student.student_test_completion_time = now 
            student.save()
            # update_app_usage(student_id)
            return  {
                'status': 'Completed',
                'time_left':0,
                'test_duration':(student.assessment_completion_time-student.test_id.test_date_and_time).total_seconds()/60,
                'user_duration':round(student.student_duration/60,2)
            }
        student.save()
        return  {
            'status': 'success',
            'time_left':round(float(student.test_id.test_duration)*60-student.student_duration),
            'test_duration':(student.assessment_completion_time-student.test_id.test_date_and_time).total_seconds()/60,
            'user_duration':round(student.student_duration/60,2)
            }
    
    except Exception as e:
        return {'Error':str(e)}
    
@api_view(['GET'])
def submit_test(request,student_id,test_id):
    try:
        student = students_assessments.objects.get(
            student_id = student_id,
            test_id = test_id,
            del_row = False
        )
        if student.assessment_status == 'Completed':
            # student.assessment_status = 'Pending'
            # student.save()
            return JsonResponse({"message": "Test Already Completed"},safe=False,status=400)
        # if student.student_duration >= (student.test_id.test_date_and_time - student.student_test_completion_time).total_seconds():
        #     return JsonResponse({"message": "Test Completed due to time limit reached."},safe=False,status=400)
        Test_duration_update(student_id,test_id)
        student.student_test_completion_time = timezone.now().__add__(timedelta(hours=5,minutes=30))
        student.assessment_status = 'Completed'
        student.save()
        
        # Update_CollegeRank_and_OverallRank(student.student_id.course_id,student.student_id.college)
        # update_app_usage(student_id)
        return JsonResponse({"message": "Test Successfully Completed"},safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
def Update_CollegeRank_and_OverallRank(course_id,College):
    try:
        all_students_objs = students_info.objects.filter(course_id=course_id,del_row=False).order_by('-student_score')
        all_student_objes_college_wise = [stud for stud in all_students_objs if stud.college == College]
        Update_Studente_Rank =[]
        for student in all_students_objs:
            # print(student.student_id,student.student_overall_rank ,student.student_college_rank)
            student.student_overall_rank = list(all_students_objs).index(student)+1
            student.student_college_rank = list(all_student_objes_college_wise).index(student)+1
            Update_Studente_Rank.append(student)
            # print(student.student_id,student.student_overall_rank, student.student_college_rank)
            
        updated_objs = students_info.objects.bulk_update(Update_Studente_Rank,fields=['student_overall_rank','student_college_rank'],batch_size=100)
        return JsonResponse({"message": "Successfully Updated"},safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
@api_view(['GET'])  
def get_test_Qns(request,student_id,test_id,section_name):
    try:
        student = students_assessments.objects.get(
            student_id = student_id,
            test_id = test_id,
            del_row = False
        )
        if student.assessment_status == 'Completed':
            return JsonResponse({"message": "Test Already Completed"},safe=False,status=400)
        # if student.student_duration >= (student.test_id.test_date_and_time - student.student_test_completion_time).total_seconds():
        #     return JsonResponse({"message": "Test Completed due to time limit reached."},safe=False,status=400)
        # student.assessment_completion_time = timezone.now().__add__(timedelta(hours=5,minutes=30))
        container_client = get_blob_container_client()
        response = {}
        test_section = test_sections.objects.filter(test_id=test_id,section_name=section_name,del_row=False).order_by('section_number').values('question_id')
        answers = student_test_questions_details.objects.filter(
                                                    test_id = test_id,
                                                    student_id = student_id,
                                                    question_id__in = [item.get('question_id') for item in test_section],
                                                    del_row = 'False'
                                                    ).order_by('question_id').values('question_id','question_status','student_answer')
        answers = {item.get('question_id'):item for item in answers}
        Qn_data = {}
        table_required = False
        for test in test_section:
            Qn = test.get('question_id')
            path = f"subjects/{Qn[1:3]}/{Qn[1:-7]}/{Qn[1:-5]}/{'mcq' if Qn[-5]=='m' else 'coding'}/{Qn}.json"
            # print(path)
            if cache.get(path) == None:
                blobdata = container_client.get_blob_client(path)
                blob_data = json.loads(blobdata.download_blob().readall())
                blob_data.update({'Qn_name':Qn})
                cache.set(path,blob_data)
            else:
                blob_data = cache.get(path)
                cache.set(path,blob_data)
            blob_data.update({
                'question_status':answers.get(Qn).get('question_status') if answers.get(Qn) != None else 'Pending',
                'user_answer':answers.get(Qn).get('student_answer') if answers.get(Qn) != None else '',
            })
            if Qn_data.get('coding' if Qn[-5] == 'c' else 'mcq') == None:
                Qn_data.update({'coding' if Qn[-5] == 'c' else 'mcq':[]})
            Qn_data.get('coding' if Qn[-5] == 'c' else 'mcq').append( blob_data )
            if blob_data.get('Table',None):
                table_required = True
        container_client.close()
        if table_required :
            response.update({'tables':get_all_tables()} )
        response.update({'qns_data':Qn_data})
        # update_app_usage(student_id)
        Test_duration_update(student_id,test_id)
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        # update_app_usage(student_id)
        Test_duration_update(student_id,test_id)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
    
@api_view(['PUT'])
def submit_test_mcq_questions(request):
    # if submit_type.lower() == 'mcq': 
        try:
           data = json.loads(request.body)
           student_id = data.get('student_id')
           question_id = data.get('question_id')
           # blob_rules_data = json.loads(get_blob('LMS_Rules/Rules.json'))
           student_assessment = students_assessments.objects.get(student_id = student_id,test_id = data.get('test_id'),del_row = False)
           if student_assessment.assessment_status == 'Completed':
                Test_duration_update(student_id,data.get('test_id'))
                return JsonResponse({"message": "Test Already Completed"},safe=False,status=400)
           
           blob_rules_data = json.loads(get_blob('lms_rules/rules.json'))
           blob_rules_data = blob_rules_data.get('mcq')
           score = 0
           outoff = 0
           if question_id[-4]=='e':
               outoff = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level1'][0]
           elif question_id[-4]=='m':
               outoff = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level2'][0]
           elif question_id[-4]=='h':
               outoff = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level3'][0]
           
           if data.get('correct_ans') == data.get('entered_ans'):
                   score = int(outoff)
           student_practiceMCQ_answer ,created= student_practiceMCQ_answers.objects.using('mongodb'
                                                               ).get_or_create(student_id = student_id,
                                                                    question_id = question_id,
                                                                    question_done_at=data.get('test_id'),
                                                                    del_row = 'False' ,
                                                                    defaults={
                                                                        'student_id':student_id,
                                                                        'question_id':question_id,
                                                                        'question_done_at' :data.get('test_id'),
                                                                        'correct_ans': data.get('correct_ans'),
                                                                        'entered_ans': data.get('entered_ans'),
                                                                        'subject_id':data.get('subject_id'),
                                                                        'score':int(score),
                                                                        'answered_time':timezone.now() + timedelta(hours=5, minutes=30)
                                                                    })
           response ={'message':'Already Submited'}
           if created:
            #    student_assessment = students_assessments.objects.get(student_id = student_id,test_id = data.get('test_id'),del_row = False)
               question = questions.objects.get(question_id = question_id, del_row = False)
               student,student_created = student_test_questions_details.objects.get_or_create(student_id = student_id,
                                                                             test_id = data.get('test_id'),
                                                                             question_id = question_id,
                                                                       del_row = 'False',
                                                                       defaults={
                                                                           'student_id':student_assessment.student_id,
                                                                           'subject_id':question.sub_topic_id.topic_id.subject_id,
                                                                           'question_id':question,
                                                                           'question_type':question.question_type,
                                                                           'test_id': student_assessment.test_id,
                                                                           'question_status':'Submitted',
                                                                           'student_answer':data.get('entered_ans'),
                                                                           'score_secured':float(score),
                                                                           'week_number':student_assessment.assessment_week_number,
                                                                           'max_score':int(outoff),
                                                                           'completion_time':timezone.now() + timedelta(hours=5, minutes=30)
                                                                       })
               
               if student_created:
                    student_assessment.student_id.student_score = int(student_assessment.student_id.student_score) + int(score)
                    student_assessment.student_id.student_total_score = int(student_assessment.student_id.student_total_score) + int(outoff)
                    student_assessment.assessment_status = 'Started'
                    student_assessment.student_test_completion_time = timezone.now() + timedelta(hours=5, minutes=30)
                    student_assessment.assessment_score_secured = float(student_assessment.assessment_score_secured) + float(score)
                    student_assessment.save()
                    student_assessment.student_id.save()
                    response ={'message':'Submited'}
                    response.update({
                        'user_answer':student.student_answer,
                        'question_status':student.question_status
                        })
               else:
                    student.question_status = 'Submitted'
                    student.save()
                    response ={'message':'Submited'}
                    response.update({
                        'user_answer':student.student_answer,
                        'question_status':student.question_status
                        })
        #    update_app_usage(student_id)
           Test_duration_update(student_id,data.get('test_id'))
           return JsonResponse(response,safe=False,status=200)
        except Exception as e:
            print(e)
            # update_app_usage( json.loads(request.body).get('student_id') )
            return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
@api_view(['PUT'])
def submit_test_coding_questions(request):
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        question_id = data.get('Qn')
        blob_rules_data = json.loads(get_blob(f'lms_rules/rules.json')).get('coding')
        score = 0
        outoff = 0
        if question_id[-4]=='e':
            score = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level1'][0]
        elif question_id[-4]=='m':
            score = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level2'][0]
        elif question_id[-4]=='h':
            score = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level3'][0]
        score = int(score)
        outoff = score
        result = {}
        i = 0
        passedcases = 0
        totalcases = 0
        if data.get("subject") == 'HTML' or data.get("subject") == 'HTML CSS' or data.get("subject") == 'CSS' or data.get("subject") == 'Java Script':
                passedcases = float(str(data.get("final_score")).split('/')[0])
                totalcases = float(str(data.get("final_score")).split('/')[1])
                result = { 'TestCases':data.get("final_score")}
        else:
            for r in data.get('Result'):
                i += 1
                if r.get("TestCase" + str(i)) == 'Passed' or r.get("TestCase" + str(i)) == 'Failed':
                    totalcases += 1
                    if r.get("TestCase" + str(i)) == 'Passed':
                        passedcases += 1
                    result.update(r)
                if r.get("Result") == 'True' or r.get("Result") == 'False':
                    result.update(r)
            if passedcases == totalcases and passedcases ==0:
                score = 0
        score = round(score*(passedcases/totalcases),2)
        user , created = student_practice_coding_answers.objects.using('mongodb').get_or_create(student_id=data.get('student_id'),
                                                                                          subject_id=data.get('subject_id'),
                                                                                          question_id=data.get('Qn'),
                                                                                          question_done_at=data.get('test_id'),
                                                                                          del_row='False',
                                                                                          defaults={
                                                                                              'student_id'          :data.get('student_id'),
                                                                                              'subject_id'          :data.get('subject_id'),
                                                                                              'question_done_at'    :data.get('test_id'),
                                                                                              'question_id'         :data.get('Qn'),
                                                                                              'entered_ans'         :data.get('Ans'),
                                                                                              'answered_time'       :timezone.now() + timedelta(hours=5, minutes=30),
                                                                                              'testcase_results'    :result,
                                                                                              'Attempts'            :1,
                                                                                              'score'               :score,
                                                                                              'del_row'             :'False' 
                                                                                        })
        response ={'message':'Submited','status':True}
        if created:
               student_assessment = students_assessments.objects.get(student_id = student_id,test_id = data.get('test_id'),del_row = False)
               question = questions.objects.get(question_id = question_id, del_row = False)
               student,student_created = student_test_questions_details.objects.get_or_create(student_id = student_id,
                                                                             test_id = data.get('test_id'),
                                                                             question_id = question_id,
                                                                       del_row = 'False',
                                                                       defaults={
                                                                           'student_id':student_assessment.student_id,
                                                                           'subject_id':question.sub_topic_id.topic_id.subject_id,
                                                                           'question_id':question,
                                                                           'question_type':question.question_type,
                                                                           'test_id': student_assessment.test_id,
                                                                           'question_status':'Submitted',
                                                                           'student_answer':data.get('Ans'),
                                                                           'score_secured':float(score),
                                                                           'week_number':student_assessment.assessment_week_number,
                                                                           'max_score':int(outoff),
                                                                           'completion_time':timezone.now() + timedelta(hours=5, minutes=30)
                                                                       })
               if student_created:
                    student_assessment.student_id.student_score         = int(student_assessment.student_id.student_score) + int(score)
                    student_assessment.student_id.student_total_score   = int(student_assessment.student_id.student_total_score) + int(outoff)
                    student_assessment.assessment_status                = 'Started'
                    student_assessment.student_test_completion_time       = timezone.now() + timedelta(hours=5, minutes=30)
                    student_assessment.assessment_score_secured         = float(student_assessment.assessment_score_secured) + float(score)
                    student_assessment.save()
                    student_assessment.student_id.save()
                    response                                            = {'message':'Submited'}
                    response.update({
                        'user_answer':student.student_answer,
                        'question_status':student.question_status
                        })
        # update_app_usage(student_id)
        Test_duration_update(student_id,data.get('test_id'))
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        # update_app_usage(json.loads(request.body).get('student_id'))
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)

def format_time_with_zone(date):
    if date == None:
        return None
    date = datetime.strptime(str(date).split('.')[0].split('+')[0], "%Y-%m-%d %H:%M:%S")
    return (f"{calendar.month_abbr[int(date.strftime("%m"))]} {int(date.strftime("%d"))} {date.strftime('%Y')} {date.strftime('%H:%M:%S')} IST")
@api_view(['GET'])
def student_test_report(request,student_id,test_id):
    try: 
        student_assessment = students_assessments.objects.get(student_id = student_id,test_id = test_id,del_row = False)
        test_questions_list = list(test_sections.objects.filter(test_id = test_id,del_row = False))
        test_questions = [i.question_id.question_id for i in test_questions_list]
        # print(test_questions)
        answers_status = student_test_questions_details.objects.filter(student_id = student_id,test_id = test_id,question_id__in = test_questions,del_row = False).values('question_id','score_secured','max_score','question_status')
        coding_answers = student_practice_coding_answers.objects.using('mongodb').filter(student_id = student_id,question_id__in = test_questions,question_done_at = test_id,del_row = False).values('question_id','score','entered_ans','testcase_results')
        mcq_answers = student_practiceMCQ_answers.objects.using('mongodb').filter(student_id = student_id,question_id__in = test_questions,question_done_at = test_id,del_row = False).values('question_id','score','entered_ans')
        coding_answers = {i.get('question_id'):i for i in coding_answers}#{i.question_id:i for i in coding_answers}
        mcq_answers = { i.get('question_id'):i for i in mcq_answers}#{i.question_id:i for i in mcq_answers}
        topics_list ={i.question_id.question_id:i.question_id.sub_topic_id.topic_id.topic_name for i in test_questions_list}
        # print(topics_list)
        test_time_taken = round(student_assessment.student_duration/60) 
        Total_time_given = round((student_assessment.assessment_completion_time-student_assessment.test_id.test_date_and_time).total_seconds()/60)\
                            if student_assessment.assessment_type != 'Weekly Test' else float(student_assessment.test_id.test_duration)
        test_summary ={}
        test_summary.update({
            # 'time_taken_for_completion':round((student_assessment.student_test_start_time - student_assessment.student_test_completion_time ).total_seconds()/60,2),
            'time_taken_for_completion':str(test_time_taken)+' min' if test_time_taken < 60 else str(int(test_time_taken/60))+' hrs '+str(test_time_taken%60)+' min',
            'total_time'            :str(Total_time_given)+' min' if Total_time_given < 60 else str(int(Total_time_given/60))+' hrs '+str(Total_time_given%60)+' min',
            'score_secured'         :student_assessment.assessment_score_secured,
            'max_score'             :student_assessment.assessment_max_score,
            'percentage'            :round((student_assessment.assessment_score_secured/student_assessment.assessment_max_score)*100,2),
            'status'                :student_assessment.assessment_status,
            'attempted_questions'   :len(answers_status),
            'total_questions'       :len(test_questions),
            'test_start_time'       :format_time_with_zone (student_assessment.student_test_start_time) ,
            'test_end_time'         :format_time_with_zone (student_assessment.student_test_completion_time) 
        })
        if student_assessment.assessment_type == 'Final Test':
            test_summary.update({
                'overall_rank'  :student_assessment.student_id.student_overall_rank,
                'college_rank'  :student_assessment.student_id.student_college_rank,
            })
        test_topics_wise_scores ={}
        mcq=[]
        coding=[]
        container_client = get_blob_container_client()
        for ans in answers_status:
            Qn = ans.get('question_id') 
            path = f"subjects/{Qn[1:3]}/{Qn[1:-7]}/{Qn[1:-5]}/{'mcq' if Qn[-5]=='m' else 'coding'}/{Qn}.json"
            if cache.get(path) == None:
                blobdata = container_client.get_blob_client(path)
                blob_data = json.loads(blobdata.download_blob().readall())
                blob_data.update({'Qn_name':Qn})
                cache.set(path,blob_data)
            else:
                blob_data = cache.get(path)
                cache.set(path,blob_data)
            blob_data.update({'score_secured':ans.get('score_secured'),
                              'max_score':int(ans.get('max_score')),
                            #   'status':ans.get('question_status'),
                              'status':'Correct' if float(ans.get('score_secured'))==float(ans.get('max_score')) else 'Partial Correct' if float(ans.get('score_secured'))>0 else 'Wrong',
                              'topic':topics_list.get(ans.get('question_id'))
                              })
            if Qn[-5] == 'm':
                blob_data.update({
                    'user_answer':mcq_answers.get(ans.get('question_id'),{}).get('entered_ans',''),
                })
                mcq.append(blob_data)
            else:

                testcases =coding_answers.get(ans.get('question_id'),{}).get('testcase_results','')
                testcases_result =str(len([tc for tc in testcases if str(tc).startswith('TestCase') and testcases.get(tc) == 'Passed']))+'/'+str(len([tc for tc in testcases if str(tc).startswith('TestCase')]))
                blob_data.update({
                    'user_answer':coding_answers.get(ans.get('question_id'),{}).get('entered_ans',''),
                    'testcases' : testcases_result
                })
                coding.append(blob_data)
            test_topics_wise_scores.update({topics_list.get(ans.get('question_id')):
                                            f'{float(test_topics_wise_scores.get(topics_list.get(ans.get('question_id')),'0/0').split("/")[0])+float(ans.get("score_secured"))}/{float(test_topics_wise_scores.get(topics_list.get(ans.get('question_id')),'0/0').split("/")[1])+float(ans.get("max_score"))}'
                                            })
        not_attemted_Qns =[Qn for Qn in test_questions if Qn not in [answered.get('question_id')  for answered in answers_status]]
        rulesdata = container_client.get_blob_client('lms_rules/rules.json')
        rules = json.loads(rulesdata.download_blob().readall())
        for Qn in not_attemted_Qns:
            path = f"subjects/{Qn[1:3]}/{Qn[1:-7]}/{Qn[1:-5]}/{'mcq' if Qn[-5]=='m' else 'coding'}/{Qn}.json"
            if cache.get(path) == None:
                blobdata = container_client.get_blob_client(path)
                blob_data = json.loads(blobdata.download_blob().readall())
                blob_data.update({'Qn_name':Qn})
                cache.set(path,blob_data)
            else:
                blob_data = cache.get(path)
                cache.set(path,blob_data)
            outoff = 0
            blob_rules_data = rules.get('mcq' if Qn[-5]=='m' else 'coding') 
            if Qn[-4]=='e':
                outoff = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level1'][0]
            elif Qn[-4]=='m':
                outoff = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level2'][0]
            elif Qn[-4]=='h':
                outoff = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level3'][0]
            outoff = int(outoff)
            blob_data.update({'score_secured':0,
                              'max_score':outoff,
                            #   'status':ans.get('question_status'),
                              'status':'Not Attempted',
                              'topic':topics_list.get(Qn)
                              })
            if Qn[-5] == 'm':
                blob_data.update({
                    'user_answer':'',
                })
                mcq.append(blob_data)
            else:
                blob_data.update({
                    'user_answer':'',
                    'testcases' : '0/'+str(len(blob_data.get('TestCases')))
                })
                coding.append(blob_data)
        test_topics ={

        }
        for ans_score in test_topics_wise_scores:
            if float(test_topics_wise_scores.get(ans_score,'0/0').split("/")[0])/float(test_topics_wise_scores.get(ans_score,'0/0').split("/")[1]) >= 0.7:
                print(ans_score)
                if test_topics.get('good',[]) == []:
                    test_topics.update({'good': [ans_score]})
                else:
                    test_topics.get('good').append(ans_score)
            elif float(test_topics_wise_scores.get(ans_score,'0/0').split("/")[0])/float(test_topics_wise_scores.get(ans_score,'0/0').split("/")[1]) >= 0.4:
                print(ans_score)
                if test_topics.get('average',[]) == []:
                    test_topics.update({'average': [ans_score]})
                else:
                    test_topics.get('average').append(ans_score)
            else:
                print(ans_score)
                if test_topics.get('poor',[]) == []:
                    test_topics.update({'poor': [ans_score]})
                else:
                    test_topics.get('poor').append(ans_score)
                

        response ={
            'test_summary'  :test_summary,
            'topics_wise_scores':test_topics_wise_scores,
            'topics'        :test_topics,
            'answers'       :{
                'mcq'       :mcq,
                'coding'    :coding
            }
        }
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)