# import calendar
# from itertools import count
# from django.shortcuts import render
# from django.http import HttpResponse, JsonResponse
# from rest_framework.decorators import api_view
# from LMS_MSSQLdb_App.models import *
# from LMS_Mongodb_App.models import *
# from datetime import datetime, timedelta
# from django.utils import timezone
# from django.db.models import Max, F ,Sum,Min,Count
# # from django.contrib.postgres.aggregates import ArrayAgg
# import json
# from django.db.models.functions import TruncDate
# # from LMS_Project.Blobstorage import *
# from .AppUsage import update_app_usage
# from django.core.cache import cache
# from LMS_Project.Blobstorage import *
# from .sqlrun import get_all_tables

# @api_view(['GET'])
# def final_test_insturction(request,student_id,test_id):
#     try:
#         student = students_assessments.objects.get(
#             student_id = student_id,
#             test_id = test_id,
#             del_row = False
#         )
#         if student.assessment_status == 'Completed':
#             update_app_usage(student_id)
#             return JsonResponse({"message": "Test Already Completed"},safe=False,status=400)
#         if timezone.now().__add__(timedelta(hours=5,minutes=30)) >= (student.test_id.test_date_and_time + timedelta(minutes=student.test_id.test_duration)):
#             update_app_usage(student_id)
#             student.assessment_completion_time = timezone.now().__add__(timedelta(hours=5,minutes=30))
#             student.assessment_status = 'Completed'
#             student.save()
#             return JsonResponse({"message": "Test Completed due to time limit reached."},safe=False,status=400)
#         test_detaile_queryset = test_sections.objects.filter(
#                                                         test_id=test_id, 
#                                                         del_row=False
#                                                     ).values('section_number','test_id__test_duration').annotate(
#                                                         section_count=Count('id')
#                                                     )
#         test_detaile = {
#             'duration':0,
#             'section_count':{}
#         }
#         [test_detaile.update({'duration':item.get('test_id__test_duration')}) for item in test_detaile_queryset]
#         test_detaile.update({'section_count': {'section_'+str(item.get('section_number')): item.get('section_count') for item in test_detaile_queryset} })
#         return JsonResponse(test_detaile,safe=False,status=200)
#     except Exception as e:
#         print(e)
#         return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)

# @api_view(['GET'])
# def final_test_section_details(request,student_id,test_id):
#     try:
#         print(test_id)
#         student = students_assessments.objects.get(
#             student_id = student_id,
#             test_id = test_id,
#             del_row = False
#         )
#         if student.assessment_status == 'Completed':
#             update_app_usage(student_id)
#             return JsonResponse({"message": "Test Already Completed"},safe=False,status=400)
#         if timezone.now().__add__(timedelta(hours=5,minutes=30)) >= (student.test_id.test_date_and_time + timedelta(minutes=student.test_id.test_duration)):
#             update_app_usage(student_id)
#             student.assessment_completion_time = timezone.now().__add__(timedelta(hours=5,minutes=30))
#             student.assessment_status = 'Completed'
#             student.save()
#             return JsonResponse({"message": "Test Completed due to time limit reached."},safe=False,status=400)
#         test_section = test_sections.objects.filter(test_id = test_id,del_row = False)
#         answers = student_test_questions_details.objects.filter(
#                                                     test_id = test_id,
#                                                     student_id = student_id,
#                                                     del_row = False
#                                                     ).order_by('question_id')
        
#         if test_section == [] :
#             update_app_usage(student_id)
#             return JsonResponse({"message": "No Test Available"},safe=False,status=400)
#         answers = {ans.question_id:ans for ans in answers}
#         response ={}
#         container_client = get_blob_container_client()
#         rules = container_client.get_blob_client('lms_rules/rules.json')
#         Rules = json.loads(rules.download_blob().readall())
#         rules_Json = {}
#         Completed_Questions = {
#             'total':0,'completed':0
#         }
#         Qns_data = {}
#         for rule in Rules:
#             if rules_Json.get(rule) == None:
#                 rules_Json.update({rule:{}})
#             rules_Json.get(rule).update({i.get('level').lower():{
#                 'score':i.get('score'),
#                 'time':i.get('time')    } for i in Rules.get(rule)})
#         for test in test_section:
#             if response.get(test.section_name) == None:
#                 response.update({test.section_name:[]})
#             Qn = test.question_id.question_id
#             path = f"subjects/{Qn[1:3]}/{Qn[1:-7]}/{Qn[1:-5]}/{'mcq' if Qn[-5]=='m' else 'coding'}/{Qn}.json"
#             if cache.get(path) == None:
#                 blobdata = container_client.get_blob_client(path)
#                 blob_data = json.loads(blobdata.download_blob().readall())
#                 blob_data.update({'Qn_name':Qn})
#                 cache.set(path,blob_data)
#             else:
#                 blob_data = cache.get(path)
#                 cache.set(path,blob_data)
#             level = blob_data.get('Level','') if blob_data.get('Level') else blob_data.get('level','')
#             if answers.get(Qn):
#                 Completed_Questions.update({'completed':Completed_Questions.get('completed')+1})
#             Completed_Questions.update({'total':Completed_Questions.get('total')+1})
#             response.get(test.section_name).append({
#                              "qn_id"            : Qn,
#                              "question_type"    : 'Coding' if Qn[-5] == 'c' else 'MCQ',
#                              "level"            : level,
#                              "question"         : blob_data.get('Qn') if blob_data.get('Qn') else blob_data.get('question'),
#                              "score"            : rules_Json.get('coding',{}).get(level)['score'] if Qn[-5] == 'c' else rules_Json.get('mcq',{}).get(level)['score'],
#                              "time"             : rules_Json.get('coding',{}).get(level)['time'] if Qn[-5] == 'c' else rules_Json.get('mcq',{}).get(level)['time'],
#                              "status"           : answers.get(Qn).question_status if answers.get(Qn) else 'Pending',
#                             })
#             if Qns_data.get('coding' if Qn[-5] == 'c' else 'mcq') == None:
#                 Qns_data.update({'coding' if Qn[-5] == 'c' else 'mcq':[]})
#             Qns_data.get('coding' if Qn[-5] == 'c' else 'mcq').append(blob_data)
#         container_client.close()
#         response.update({'Completed_Questions':str(Completed_Questions.get('completed'))+'/'+str(Completed_Questions.get('total')),
#                         'Qns_data':Qns_data})
#         student.student_test_start_time = timezone.now() + timedelta(hours=5, minutes=30)
#         student.save()
#         update_app_usage(student_id)
#         return JsonResponse(response,safe=False,status=200)
#     except Exception as e:
#         print(e)
#         update_app_usage(student_id)
#         return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)

# @api_view(['GET'])
# def submit_final_test(request,student_id,test_id):
#     try:
#         student = students_assessments.objects.get(
#             student_id = student_id,
#             test_id = test_id,
#             del_row = False
#         )
#         if student.assessment_status == 'Completed':
#             student.assessment_status = 'Pending'
#             student.save()
#             return JsonResponse({"message": "Test Already Completed"},safe=False,status=400)
#         student.assessment_completion_time = timezone.now().__add__(timedelta(hours=5,minutes=30))
#         student.assessment_status = 'Completed'
#         student.save()
#         update_app_usage(student_id)
#         return JsonResponse({"message": "Test Successfully Completed"},safe=False,status=200)
#     except Exception as e:
#         print(e)
#         return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)

# @api_view(['GET'])  
# def get_final_test_Qns(request,student_id,test_id,section_name):
#     try:
#         student = students_assessments.objects.get(
#             student_id = student_id,
#             test_id = test_id,
#             del_row = False
#         )
#         if student.assessment_status == 'Completed':
#             return JsonResponse({"message": "Test Already Completed"},safe=False,status=400)
#         if timezone.now().__add__(timedelta(hours=5,minutes=30)) >= (student.test_id.test_date_and_time + timedelta(minutes=student.test_id.test_duration)):
#             update_app_usage(student_id)
#             student.assessment_completion_time = timezone.now().__add__(timedelta(hours=5,minutes=30))
#             student.assessment_status = 'Completed'
#             student.save()
#             return JsonResponse({"message": "Test Completed due to time limit reached."},safe=False,status=400)
#         student.assessment_completion_time = timezone.now().__add__(timedelta(hours=5,minutes=30))
#         container_client = get_blob_container_client()
#         response = {}
#         test_section = test_sections.objects.filter(test_id=test_id,section_name=section_name,del_row=False).order_by('section_number').values('question_id')
#         answers = student_test_questions_details.objects.filter(
#                                                     test_id = test_id,
#                                                     student_id = student_id,
#                                                     question_id__in = [item.get('question_id') for item in test_section],
#                                                     del_row = 'False'
#                                                     ).order_by('question_id').values('question_id','question_status')
#         answers = {item.get('question_id'):item for item in answers}
#         Qn_data = {}
#         table_required = False
#         for test in test_section:
#             Qn = test.get('question_id')
#             path = f"subjects/{Qn[1:3]}/{Qn[1:-7]}/{Qn[1:-5]}/{'mcq' if Qn[-5]=='m' else 'coding'}/{Qn}.json"
#             # print(path)
#             if cache.get(path) == None:
#                 blobdata = container_client.get_blob_client(path)
#                 blob_data = json.loads(blobdata.download_blob().readall())
#                 blob_data.update({'Qn_name':Qn})
#                 cache.set(path,blob_data)
#             else:
#                 blob_data = cache.get(path)
#                 cache.set(path,blob_data)
#             blob_data.update({
#                 'question_status':answers.get(Qn).get('question_status') if answers.get(Qn) != None else 'Pending',
#                 'user_answer':answers.get(Qn).get('student_answer') if answers.get(Qn) != None else '',
#             })
#             if Qn_data.get('coding' if Qn[-5] == 'c' else 'mcq') == None:
#                 Qn_data.update({'coding' if Qn[-5] == 'c' else 'mcq':[]})
#             Qn_data.get('coding' if Qn[-5] == 'c' else 'mcq').append( blob_data )
#             if blob_data.get('Table',None):
#                 table_required = True
#         container_client.close()
#         if table_required :
#             response.update({'tables':get_all_tables()} )
#         response.update({'qns_data':Qn_data})
#         update_app_usage(student_id)
#         return JsonResponse(response,safe=False,status=200)
#     except Exception as e:
#         print(e)
#         update_app_usage(student_id)
#         return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)

# @api_view(['PUT'])
# def submit_final_test_mcq_questions(request):
#     # if submit_type.lower() == 'mcq': 
#         try:
#             data = json.loads(request.body)
#             student_id = data.get('student_id')
#             question_id = data.get('question_id')
#             # blob_rules_data = json.loads(get_blob('LMS_Rules/Rules.json'))
#             student_assessment = students_assessments.objects.get(student_id = student_id,test_id = data.get('test_id'),del_row = False)
#             if student_assessment.assessment_status == 'Completed':
#                  return JsonResponse({"message": "Test Already Completed"},safe=False,status=400)
#             if timezone.now().__add__(timedelta(hours=5,minutes=30)) >= (student_assessment.test_id.test_date_and_time + timedelta(minutes=student_assessment.test_id.test_duration)):
#                  update_app_usage(student_id)
#                  student_assessment.assessment_completion_time = timezone.now().__add__(timedelta(hours=5,minutes=30))
#                  student_assessment.assessment_status = 'Completed'
#                  student_assessment.save()
#                  return JsonResponse({"message": "Test Completed due to time limit reached."},safe=False,status=400)
            
#             blob_rules_data = json.loads(get_blob('lms_rules/rules.json'))
#             blob_rules_data = blob_rules_data.get('mcq')
#             score = 0
#             outoff = 0
#             if question_id[-4]=='e':
#                 outoff = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level1'][0]
#             elif question_id[-4]=='m':
#                 outoff = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level2'][0]
#             elif question_id[-4]=='h':
#                 outoff = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level3'][0]
            
#             if data.get('correct_ans') == data.get('entered_ans'):
#                     score = int(outoff)
#             student_practiceMCQ_answer ,created= student_practiceMCQ_answers.objects.using('mongodb'
#                                                                 ).get_or_create(student_id = student_id,
#                                                                      question_id = question_id,
#                                                                      question_done_at=data.get('test_id'),
#                                                                      del_row = 'False' ,
#                                                                      defaults={
#                                                                          'student_id':student_id,
#                                                                          'question_id':question_id,
#                                                                          'question_done_at' :data.get('test_id'),
#                                                                          'correct_ans': data.get('correct_ans'),
#                                                                          'entered_ans': data.get('entered_ans'),
#                                                                          'subject_id':data.get('subject_id'),
#                                                                          'score':int(score),
#                                                                          'answered_time':timezone.now() + timedelta(hours=5, minutes=30)
#                                                                      })
#             response ={'message':'Already Submited'}
#             if created:
#              #    student_assessment = students_assessments.objects.get(student_id = student_id,test_id = data.get('test_id'),del_row = False)
#                 question = questions.objects.get(question_id = question_id, del_row = False)
#                 student,student_created = student_test_questions_details.objects.get_or_create(student_id = student_id,
#                                                                               test_id = data.get('test_id'),
#                                                                               question_id = question_id,
#                                                                         del_row = 'False',
#                                                                         defaults={
#                                                                             'student_id':student_assessment.student_id,
#                                                                             'subject_id':question.sub_topic_id.topic_id.subject_id,
#                                                                             'question_id':question,
#                                                                             'test_id': student_assessment.test_id,
#                                                                             'question_status':'Submitted',
#                                                                             'score_secured':float(score),
#                                                                             'week_number':student_assessment.assessment_week_number,
#                                                                             'max_score':int(outoff),
#                                                                             'completion_time':timezone.now() + timedelta(hours=5, minutes=30)
#                                                                         })
#                 if student_created:
#                      student_assessment.student_id.student_score = int(student_assessment.student_id.student_score) + int(score)
#                      student_assessment.student_id.student_total_score = int(student_assessment.student_id.student_total_score) + int(outoff)
#                      student_assessment.assessment_status = 'Started'
#                      student_assessment.assessment_completion_time = timezone.now() + timedelta(hours=5, minutes=30)
#                      student_assessment.assessment_score_secured = float(student_assessment.assessment_score_secured) + float(score)
#                      student_assessment.save()
#                      student_assessment.student_id.save()
#                      response ={'message':'Submited'}
#                      response.update({
#                         'user_answer':student.student_answer,
#                         'question_status':student.question_status
#                         })
#             update_app_usage(student_id)
#             return JsonResponse(response,safe=False,status=200)
#         except Exception as e:
#             print(e)
#             update_app_usage( json.loads(request.body).get('student_id') )
#             return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
# @api_view(['PUT'])
# def submit_final_test_coding_questions(request):
#     try:
#         data = json.loads(request.body)
#         student_id = data.get('student_id')
#         question_id = data.get('Qn')
#         student_assessment = students_assessments.objects.get(student_id = student_id,test_id = data.get('test_id'),del_row = False)
#         if student_assessment.assessment_status == 'Completed':
#             return JsonResponse({"message": "Test Already Completed"},safe=False,status=400)
#         if timezone.now().__add__(timedelta(hours=5,minutes=30)) >= (student_assessment.test_id.test_date_and_time + timedelta(minutes=student_assessment.test_id.test_duration)):
#             update_app_usage(student_id)
#             student_assessment.assessment_completion_time = timezone.now().__add__(timedelta(hours=5,minutes=30))
#             student_assessment.assessment_status = 'Completed'
#             student_assessment.save()
#             return JsonResponse({"message": "Test Completed due to time limit reached."},safe=False,status=400)
#         blob_rules_data = json.loads(get_blob(f'lms_rules/rules.json')).get('coding')
#         score = 0
#         outoff = 0
#         if question_id[-4]=='e':
#             score = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level1'][0]
#         elif question_id[-4]=='m':
#             score = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level2'][0]
#         elif question_id[-4]=='h':
#             score = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level3'][0]
#         score = int(score)
#         outoff = score
#         result = {}
#         i = 0
#         passedcases = 0
#         totalcases = 0
#         if data.get("subject") == 'HTML' or data.get("subject") == 'HTML CSS' or data.get("subject") == 'CSS' or data.get("subject") == 'Java Script':
#                 passedcases = float(str(data.get("final_score")).split('/')[0])
#                 totalcases = float(str(data.get("final_score")).split('/')[1])
#                 result = { 'TestCases':data.get("final_score")}
#         else:
#             for r in data.get('Result'):
#                 i += 1
#                 if r.get("TestCase" + str(i)) == 'Passed' or r.get("TestCase" + str(i)) == 'Failed':
#                     totalcases += 1
#                     if r.get("TestCase" + str(i)) == 'Passed':
#                         passedcases += 1
#                     result.update(r)
#                 if r.get("Result") == 'True' or r.get("Result") == 'False':
#                     result.update(r)
#             if passedcases == totalcases and passedcases ==0:
#                 score = 0
#         score = round(score*(passedcases/totalcases),2)
#         user , created = student_practice_coding_answers.objects.using('mongodb').get_or_create(student_id=data.get('student_id'),
#                                                                                           subject_id=data.get('subject_id'),
#                                                                                           question_id=data.get('Qn'),
#                                                                                           question_done_at=data.get('test_id'),
#                                                                                           del_row='False',
#                                                                                           defaults={
#                                                                                               'student_id'          :data.get('student_id'),
#                                                                                               'subject_id'          :data.get('subject_id'),
#                                                                                               'question_done_at'    :data.get('test_id'),
#                                                                                               'question_id'         :data.get('Qn'),
#                                                                                               'entered_ans'         :data.get('Ans'),
#                                                                                               'answered_time'       :timezone.now() + timedelta(hours=5, minutes=30),
#                                                                                               'testcase_results'    :result,
#                                                                                               'Attempts'            :1,
#                                                                                               'score'               :score,
#                                                                                               'del_row'             :'False' 
#                                                                                         })
#         response ={'message':'Submited','status':True}
#         if created:
#                question = questions.objects.get(question_id = question_id, del_row = False)
#                student,student_created = student_test_questions_details.objects.get_or_create(student_id = student_id,
#                                                                              test_id = data.get('test_id'),
#                                                                              question_id = question_id,
#                                                                        del_row = 'False',
#                                                                        defaults={
#                                                                            'student_id':student_assessment.student_id,
#                                                                            'subject_id':question.sub_topic_id.topic_id.subject_id,
#                                                                            'question_id':question,
#                                                                            'test_id': student_assessment.test_id,
#                                                                            'question_status':'Submitted',
#                                                                            'score_secured':float(score),
#                                                                            'week_number':student_assessment.assessment_week_number,
#                                                                            'max_score':int(outoff),
#                                                                            'completion_time':timezone.now() + timedelta(hours=5, minutes=30)
#                                                                        })
#                if student_created:
#                     student_assessment.student_id.student_score         = int(student_assessment.student_id.student_score) + int(score)
#                     student_assessment.student_id.student_total_score   = int(student_assessment.student_id.student_total_score) + int(outoff)
#                     student_assessment.assessment_status                = 'Started'
#                     student_assessment.assessment_completion_time       = timezone.now() + timedelta(hours=5, minutes=30)
#                     student_assessment.assessment_score_secured         = float(student_assessment.assessment_score_secured) + float(score)
#                     student_assessment.save()
#                     student_assessment.student_id.save()
#                     response ={'message':'Submited'}
#                     response.update({
#                         'user_answer':student.student_answer,
#                         'question_status':student.question_status
#                         })
#         update_app_usage(student_id)
#         return JsonResponse(response,safe=False,status=200)
#     except Exception as e:
#         print(e)
#         update_app_usage(json.loads(request.body).get('student_id'))
#         return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
