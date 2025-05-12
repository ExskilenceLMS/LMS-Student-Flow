
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
# from django.contrib.postgres.aggregates import ArrayAgg
import json
from django.db.models.functions import TruncDate    

rule_for_weekly_test = {
    'MCQ':10,'Coding':3
    # 'MCQ':7,'Coding':3
}

# @api_view(['GET'])
# def Automated_weekly_test(request,student_id,week_number,subject_id): 
#     try:
#         student_detaile = students_details.objects.using('mongodb').get(student_id = student_id,del_row = False)
#         week_status = []
#         all_sub_topics =[]
#         all_practice_Questions = []
#         for day in student_detaile.student_question_details.get(subject_id).get('week_'+str(week_number)):
#             day = student_detaile.student_question_details.get(subject_id).get('week_'+str(week_number)).get(day)
#             [ week_status.append(day.get('sub_topic_status',{}).get(sub,0)==2) for sub in day.get('sub_topic_status',{})]
#             all_practice_Questions.extend(day.get('mcq_questions',[]))
#             all_practice_Questions.extend(day.get('coding_questions',[]))
#             all_sub_topics.extend([sub for sub in day.get('sub_topic_status',{})])
#         if week_status.count(True) == len(week_status):
#             sub_topic_wise_mcq_qns = {}
#             sub_topic_wise_coding_qns = {}
#             sub_topic_wise_mcq_qns.update({sub :[] for sub in all_sub_topics})
#             sub_topic_wise_coding_qns.update({sub :[] for sub in all_sub_topics})
#        # print('completed',all_sub_topics)
#             Qns_list_obj = questions.objects.filter(sub_topic_id__sub_topic_id__in=all_sub_topics,del_row=False) 
#             [sub_topic_wise_mcq_qns.get(qn.sub_topic_id.sub_topic_id).append(qn.question_id) for qn in Qns_list_obj if qn.question_id not in all_practice_Questions and str(qn.question_id)[-5].lower()=='m']
#             [sub_topic_wise_coding_qns.get(qn.sub_topic_id.sub_topic_id).append(qn.question_id) for qn in Qns_list_obj if qn.question_id not in all_practice_Questions and str(qn.question_id)[-5].lower()=='c']
#             all_mcq_qns = []
#             all_coding = []
#        # print(len(all_mcq_qns)< rule_for_weekly_test.get('MCQ'),len(all_coding)< rule_for_weekly_test.get('Coding'))
#             while len(all_mcq_qns)< rule_for_weekly_test.get('MCQ') or len(all_coding)< rule_for_weekly_test.get('Coding') :
#                 # if  len(sub_topic_wise_mcq_qns.get(sub_qn))==0 and  len(sub_topic_wise_coding_qns.get(sub_qn))==0:
#                 #     break
#                 for sub_qn in all_sub_topics:
#                # print('1',sub_topic_wise_mcq_qns.get(sub_qn))
#                     if len(sub_topic_wise_mcq_qns.get(sub_qn)) >0 :
#                         # print('1.1')
#                         mcq_qns = random.sample(sub_topic_wise_mcq_qns.get(sub_qn),len(sub_topic_wise_mcq_qns.get(sub_qn)))
#                         # print('1.2')
#                         qn = mcq_qns[0]
#                         if len(all_mcq_qns)< rule_for_weekly_test.get('MCQ'):
#                             all_mcq_qns.append(qn)
#                        # print('1.3',qn)
#                         sub_topic_wise_mcq_qns.get(sub_qn).remove(qn)
                    
#                     if  len(sub_topic_wise_coding_qns.get(sub_qn))>0:
#                    # print('2',sub_topic_wise_coding_qns.get(sub_qn))
#                         codin_qns = random.sample(sub_topic_wise_coding_qns.get(sub_qn),len(sub_topic_wise_coding_qns.get(sub_qn)))
#                         # print('3')
#                         cqn = codin_qns[0]
#                         if len(all_coding)< rule_for_weekly_test.get('Coding'):
#                             # print('4',cqn)
#                             all_coding.append(cqn)
#                    # print('4',cqn)
#                         sub_topic_wise_coding_qns.get(sub_qn).remove(cqn)
#                    # print('4',sub_topic_wise_coding_qns.get(sub_qn))
#                         # print('5')
                    
#                # print(all_mcq_qns ,all_coding)
#                # print()
#             # container_client =  get_blob_container_client()
#             # for subtop in all_sub_topics:
#             #     cacheed_lists = cache.get(f'subjects/{subtop[0:2]}/{subtop[0:-2]}/{subtop}/{type.lower()}/')
#             #     if cacheed_lists:
#             #         cache.set(f'subjects/{subtop[0:2]}/{subtop[0:-2]}/{subtop}/{type.lower()}/',cacheed_lists)
#             #         all_qns_list = cacheed_lists
#             #     else:
#             #         all_qns_list =container_client.list_blobs(
#             #                         name_starts_with =f'subjects/{subtop[0:2]}/{subtop[0:-2]}/{subtop}/{type.lower()}/')
#             #         cache.set(f'subjects/{subtop[0:2]}/{subtop[0:-2]}/{subtop}/{type.lower()}/',all_qns_list)
#             #     all_qns = [blob.name.split('/')[-1].split('.')[0] for blob in all_qns_list]
#             return JsonResponse(all_practice_Questions,safe=False,status=200)
#         else:
#             return JsonResponse({"message": "Not Unlocked yet"},safe=False,status=400)
#     except Exception as e:
#    # print(e)
#         return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)


@api_view(['GET'])
def Automated_weekly_test(request,student_id,week_number,subject_id): 
    try:
        student_detaile = students_details.objects.using('mongodb').get(student_id = student_id,del_row = False)
        student_info = students_info.objects.get(student_id=student_id,del_row=False)
        week_status = []
        all_sub_topics =[]
        sections = {}
        all_practiced_Questions = []
        for day in student_detaile.student_question_details.get(student_info.course_id.course_id+'_'+subject_id).get('week_'+str(week_number)):
            day = student_detaile.student_question_details.get(student_info.course_id.course_id+'_'+subject_id).get('week_'+str(week_number)).get(day)
            [ week_status.append(day.get('sub_topic_status',{}).get(sub,0)==2) for sub in day.get('sub_topic_status',{})]
            all_practiced_Questions.extend(day.get('mcq_questions',[]))
            all_practiced_Questions.extend(day.get('coding_questions',[]))
            all_sub_topics.extend([sub for sub in day.get('sub_topic_status',{})])
        if week_status.count(True) == len(week_status):
            sub_topic_wise_mcq_qns = {}
            sub_topic_wise_coding_qns = {}
            sub_topic_wise_mcq_qns.update({sub :[] for sub in all_sub_topics})
            sub_topic_wise_coding_qns.update({sub :[] for sub in all_sub_topics})
            Qns_list_obj = questions.objects.filter(sub_topic_id__sub_topic_id__in=all_sub_topics,\
                                                    sub_topic_id__topic_id__subject_id__subject_id = subject_id,\
                                                    del_row=False) 
            all_Qns =[]
            all_mcq_qns = []
            all_coding = []
            mcqsection =[]
            codingsections=[]
            for qn in Qns_list_obj:
                if  str(qn.question_id)[-5].lower()=='m':
                    sub_topic_wise_mcq_qns.get(qn.sub_topic_id.sub_topic_id).append(qn.question_id)
                    all_mcq_qns.append(qn.question_id)
                if  str(qn.question_id)[-5].lower()=='c':
                    sub_topic_wise_coding_qns.get(qn.sub_topic_id.sub_topic_id).append(qn.question_id)
                    all_coding.append(qn.question_id)
                all_Qns.append(qn.question_id)
            maxMCQ = rule_for_weekly_test.get('MCQ')
            maxCoding = rule_for_weekly_test.get('Coding')

            if len(all_mcq_qns) < maxMCQ:
                if len(all_coding) >= (maxCoding + round((maxMCQ-len(all_mcq_qns))/2)):
                    maxCoding+=round((maxMCQ-len(all_mcq_qns))/2)
                   
                else :
                    maxCoding =(maxCoding + round((maxMCQ-len(all_mcq_qns))/2) )
                maxMCQ=maxMCQ-(maxMCQ-len(all_mcq_qns))
            if len(all_coding) < maxCoding:
                if len(all_mcq_qns) >= (maxMCQ + round((maxCoding-len(all_coding))*2)):
                    maxMCQ+=round((maxCoding-len(all_coding))*2)
                    # maxCoding=maxCoding-(maxCoding-len(all_coding))
                else:
                    maxMCQ =(maxMCQ + round((maxCoding-len(all_coding))*2))
                maxCoding =maxCoding-(maxCoding-len(all_coding))
            while True:
                if all_Qns ==[]  :
               # print('break by allQNS')
                    break
                if len(mcqsection) == maxMCQ and len(codingsections) == maxCoding:
                    break
            #     if all_mcq_qns ==[]  :
            #    # print('break by all_mcq_qns')
            #         break
            #     if all_coding ==[]  :
               # print('break by all_coding')
                    break
                for sub_qn in all_sub_topics:
                    if len(sub_topic_wise_mcq_qns.get(sub_qn)) >0 :
                        mcq_qns = random.sample(sub_topic_wise_mcq_qns.get(sub_qn),len(sub_topic_wise_mcq_qns.get(sub_qn)))
                        qn = mcq_qns[0]
                        if len(mcqsection)< maxMCQ:
                            mcqsection.append(qn)
                        sub_topic_wise_mcq_qns.get(sub_qn).remove(qn) 
                        all_Qns.remove(qn)
                        all_mcq_qns.remove(qn)             
                    if  len(sub_topic_wise_coding_qns.get(sub_qn))>0:
                        codin_qns = random.sample(sub_topic_wise_coding_qns.get(sub_qn),len(sub_topic_wise_coding_qns.get(sub_qn)))
                        cqn = codin_qns[0]
                        if len(codingsections)< maxCoding:
                            codingsections.append(cqn)
                        sub_topic_wise_coding_qns.get(sub_qn).remove(cqn)
                        all_Qns.remove(cqn)
                        all_coding.remove(cqn)
                    

            # sections.update({'all_Qns':all_Qns,'mcq':sub_topic_wise_mcq_qns,
            #                  'ciding':sub_topic_wise_coding_qns,
            #                  'sections':{
            #                      'mcq':mcqsection,'coding':codingsections
            #                  }})
            # print('inside')
            sections.update(create_weekly_test(student_info,week_number,subject_id ,mcqsection,codingsections))
            return JsonResponse(sections,safe=False,status=200)
        else:
            return JsonResponse({"message": "Not Unlocked yet"},safe=False,status=400)
    except Exception as e:
        # print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
    
def create_weekly_test(student,week_number,subject_id,mcqsection,codingsections):
    try:
        subject = course_subjects.objects.get(subject_id__subject_id = subject_id,\
                                              course_id = student.course_id,\
                                              batch_id = student.batch_id,\
                                              del_row = False)
        # print('subject',subject)
        test_count = test_details.objects.annotate(
         test_number=Cast(Substr('test_id', 5), IntegerField())  # 'Test' is 4 characters
                ).order_by('-test_number').first()
        # print('test_count',test_count)
        blob_rules_data = json.loads(get_blob('lms_rules/rules.json'))
        # print('blob_rules_data',blob_rules_data)
        mcq_rules =blob_rules_data.get('mcq')
        coding_rules = blob_rules_data.get('coding')
        dureation = 0
        marks = 0
        test_section_list = []
        all_sections_Qns = []
        all_sections_Qns.extend(mcqsection)
        all_sections_Qns.extend(codingsections)

        # print('mcqsection',all_sections_Qns)
        for i in all_sections_Qns:
            level = 'Level1' if i[-4].lower() == 'e' else 'Level2' if i[-4].lower() == 'm' else 'Level3'
            if i[-5].lower()=='m':
                for l in mcq_rules:
                    if l.get('level') == level:
                        dureation += float(l.get('time'))
                        marks += int(l.get('score'))
            elif i[-5].lower()=='c':
                for l in coding_rules:
                    if l.get('level') == level:
                        dureation += int(l.get('time'))
                        marks += int(l.get('score'))
        # print(dureation,marks)
         
        weekly_test,created = test_details.objects.get_or_create(test_name = 'Week '+str(week_number)+' Test',\
                                                    subject_id = subject.subject_id,\
                                                    track_id = subject.subject_id.track_id,\
                                                    course_id = subject.course_id,\
                                                    batch_id = student.batch_id,\
                                                    test_type = 'Weekly Test',\
                                                    test_created_by = "Auto generated",\
                                                    del_row=False,\
                                                    defaults={
                                                        'test_id': 'Test'+str( test_count.test_number+1 if test_count !=None else 0+1) ,#auto generated like test1, test2
                                                        'test_description': 'Weekly test for Week '+ str(week_number)+ ' for '+ str(subject.subject_id.subject_name), 
                                                        'test_duration': dureation,
                                                        'test_marks': marks,
                                                        'test_created_date_time': timezone.now().__add__(timedelta(hours=5,minutes=30)),
                                                        'test_date_and_time': timezone.now().__add__(timedelta(hours=5,minutes=30)),
                                                        'course_id':subject.course_id,
                                                        'subject_id':subject.subject_id,
                                                        'track_id':subject.subject_id.track_id,
                                                        'batch_id':student.batch_id
                                                    } )
        # print('weekly_test',created)
        Questons_objs = questions.objects.filter(question_id__in=all_sections_Qns\
                                                ,del_row=False)
        Questons = {i.question_id:i for i in Questons_objs}
        for i in mcqsection:
            test_section_list.append(test_sections(
                test_id = weekly_test,
                section_number = 1,
                section_name = 'MCQ',
                question_id = Questons.get(i),
                topic_id = Questons.get(i).sub_topic_id.topic_id,
                sub_topic_id = Questons.get(i).sub_topic_id,
            ))
        for i in codingsections:
            test_section_list.append(test_sections(
                test_id = weekly_test,
                section_number = 2,
                section_name = 'Coding',
                question_id = Questons.get(i),
                topic_id = Questons.get(i).sub_topic_id.topic_id,
                sub_topic_id = Questons.get(i).sub_topic_id,
            ))
        # print('test_section_list Exists',test_sections.objects.filter(test_id = weekly_test).exists())
        if not test_sections.objects.filter(test_id = weekly_test).exists():
            # print('test_section_list Uploading')
            saved_test_sections = test_sections.objects.bulk_create(test_section_list) 
        # print('test_section_list Uploaded')  
        # print('Assigning test to student')        
        students_assessment,created_assessment =students_assessments.objects.get_or_create(
            student_id = student,
            course_id = subject.course_id,
            subject_id = subject.subject_id,
            assessment_type = 'Weekly Test',
            test_id = weekly_test,
            defaults={
                'student_id': student,
                'course_id':subject.course_id,
                'subject_id':subject.subject_id,
                'assessment_type': 'Weekly Test',
                'test_id': weekly_test,
                'assessment_status': 'Pending',
                'assessment_score_secured':  0,
                'assessment_max_score':  weekly_test.test_marks,
                'assessment_week_number': week_number,
                'assessment_completion_time':  timezone.now().__add__(timedelta(hours=5,minutes=30)) + timedelta(days=(9 - timezone.now().__add__(timedelta(hours=5,minutes=30)).weekday())),
                'assessment_rank': 0,
                'assessment_overall_rank': 0,
                'student_duration': 0
            }
        )
        # print('Assigning test to student',created_assessment)

        return {"status": "success","message":"Weekly Test Created" if created else "Weekly Test Already Exists","test_id":weekly_test.test_id}                       
    except Exception as e:
        # print(e)
        return {"status": "error: "+str(e) }