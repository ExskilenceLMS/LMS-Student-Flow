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
from .sqlrun import get_all_tables

# FETCH STUDENT LEARNING MODULEs

@api_view(['GET'])
def fetch_learning_modules(request,student_id,subject,subject_id,day_number,week_number):
    try:
        blob_path = f'https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_CONTAINER}/'
        student = students_info.objects.get(student_id = student_id,del_row = False)
        student_details = students_details.objects.using('mongodb').get(student_id = student_id,del_row = 'False')
        # print(1)
        if student_details.student_question_details.get(student.course_id.course_id+'_'+subject_id) == None:
            student_details.student_question_details.update({student.course_id.course_id+'_'+subject_id:add_day_to_student(student_id,subject_id,subject,1,day_number).get('data')})                                                              
        # print(2)

        # print(f'lms_daywise/{student.course_id.course_id}/{student.course_id.course_id}_{student.batch_id.batch_id}.json')
        # print('student_details',student_details.student_question_details.get(subject).get('week_'+str(1)).get('day_'+str(day_number)).get('sub_topic_status'))
        # blob_data = json.loads(get_blob('LMS_DayWise/'+student.course_id.course_id+'.json'))
        blob_data = json.loads(get_blob(f'lms_daywise/{student.course_id.course_id}/{student.course_id.course_id}_{student.batch_id.batch_id}.json'))
        # print(3)
        day_data = [day  for day in blob_data.get(subject) if day.get('day') == 'Day '+str(day_number)][0] 
        response_data =[]
        for i in day_data.get('subtopicids'):
            response_data.append({
                'subtopicid':i.get('subtopic_id'),
                'sub_topic':i.get('subtopic_name'),
                'lesson': [subdata.get('path').replace(blob_path,'') for subdata in day_data.get('content').get(i.get('subtopic_id'),[]) if subdata.get('type')=="video"],
                'notes': [subdata.get('path').replace(blob_path,'') for subdata in day_data.get('content').get(i.get('subtopic_id'),[]) if subdata.get('type')=="file"],
                'mcqQuestions':sum([ day_data.get('mcq').get(i.get('subtopic_id')).get(qn,0) for qn in day_data.get('mcq').get(i.get('subtopic_id'),{}) ]),
                'codingQuestions':sum([day_data.get('coding').get(i.get('subtopic_id')).get(qn,0) for qn in day_data.get('coding').get(i.get('subtopic_id'),{} )])
            })
        # print(4)
        status ={'current_id': ""}
        if student_details.student_question_details.get(student.course_id.course_id+'_'+subject_id,None) == None \
              or student_details.student_question_details.get(student.course_id.course_id+'_'+subject_id).get('week_'+str(1))== None\
                  or student_details.student_question_details.get(student.course_id.course_id+'_'+subject_id).get('week_'+str(1)).get('day_'+str(day_number)) == None \
                    or student_details.student_question_details.get(student.course_id.course_id+'_'+subject_id).get('week_'+str(1)).get('day_'+str(day_number)).get('sub_topic_status')==None:
            # print(5)
            pass
            
        else:
            [status.update({'current_id':i}) for i in student_details.student_question_details.get(student.course_id.course_id+'_'+subject_id).get('week_'+str(1)).get('day_'+str(day_number)).get('sub_topic_status')
                    if student_details.student_question_details.get(student.course_id.course_id+'_'+subject_id).get('week_'+str(1)).get('day_'+str(day_number)).get('sub_topic_status').get(i) == 1\
                        or student_details.student_question_details.get(student.course_id.course_id+'_'+subject_id).get('week_'+str(1)).get('day_'+str(day_number)).get('sub_topic_status').get(i) == 2]   
        # print(6)
        if status.get('current_id') == '': 
            # print(7)
            status.update({'current_id':[i for i in student_details.student_question_details.get(student.course_id.course_id+'_'+subject_id).get('week_'+str(week_number)).get('day_'+str(day_number)).get('sub_topic_status').keys()][0]})
            # print(8)
        if status.get('current_id') == [sb for sb in student_details.student_question_details.get(student.course_id.course_id+'_'+subject_id).get('week_'+str(week_number)).get('day_'+str(day_number)).get('sub_topic_status').keys()][-1]:
            daycompleted = True
        else:
            daycompleted = False
        response =  [
        {
            'Day': day_data.get('day'),
            'title':  day_data.get('topic'),
            'duration':  day_data.get('duration'),
            'user_subtopic_id': status.get('current_id'),
            'day_completed': daycompleted,
            'sub_topic_data':response_data
        }]
        # print(9)
        update_app_usage(student_id)
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        update_app_usage(student_id)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
    
# ADD DAILY QUESTIONS 

@api_view(['POST'])
def add_days_to_student(request):
    try:
        data = json.loads(request.body)
        subject = data.get('subject')
        subject_id = data.get('subject_id')
        week_number = data.get('week_number')
        student_id = data.get('student_id')
        day_number = data.get('day_number')
        response  = add_day_to_student(student_id,subject_id,subject,week_number,day_number)
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
    
def add_day_to_student(student_id,subject,subject_name,week_number,day_number):
    try:
        student_info = students_info.objects.get(student_id = student_id,del_row = False)
        student = students_details.objects.using('mongodb').get(student_id = student_id,
                                                                del_row = 'False')
        needTOsave = False
        if student.student_question_details.get(student_info.course_id.course_id+'_'+subject) == None:
            student.student_question_details.update({
                student_info.course_id.course_id+'_'+subject:{
                    'week_'+str(week_number):{}
            }})
            needTOsave = True
        if student.student_question_details.get(student_info.course_id.course_id+'_'+subject).get('week_'+str(week_number)) == None:
            student.student_question_details.get(student_info.course_id.course_id+'_'+subject).update({
                'week_'+str(week_number):{
                        'day_'+str(day_number):{}
                    }
            })
            needTOsave = True
        if student.student_question_details.get(student_info.course_id.course_id+'_'+subject).get('week_'+str(week_number)).get('day_'+str(day_number)) == None:
            student.student_question_details.get(student_info.course_id.course_id+'_'+subject).get('week_'+str(week_number)).update({
                'day_'+str(day_number):{}
            })
            needTOsave = True
        print('needTOsave',needTOsave)
        response = {'message':'not updated'}
        if needTOsave == True :
            # student_info = students_info.objects.get(student_id = student_id,del_row = False)
            # cache_data = cache.get('LMS_DayWise/'+student_info.course_id.course_id+'.json')
            cache_data = json.loads(get_blob(f'lms_daywise/{student_info.course_id.course_id}/{student_info.course_id.course_id}_{student_info.batch_id.batch_id}.json'))
            if cache_data :
                # cache.set('LMS_DayWise/'+student_info.course_id.course_id+'.json',cache_data)
                cache.set(f'lms_daywise/{student_info.course_id.course_id}/{student_info.course_id.course_id}_{student_info.batch_id.batch_id}.json',cache_data)
                blob_data = cache_data
            else:
                # blob_data = json.loads(get_blob('LMS_DayWise/'+student_info.course_id.course_id+'.json'))
                blob_data = json.loads(get_blob(f'lms_daywise/{student_info.course_id.course_id}/{student_info.course_id.course_id}_{student_info.batch_id.batch_id}.json'))
                # cache.set('LMS_DayWise/'+student_info.course_id.course_id+'.json',blob_data)
                cache.set(f'lms_daywise/{student_info.course_id.course_id}/{student_info.course_id.course_id}_{student_info.batch_id.batch_id}.json',blob_data)
            # print('blob_data',blob_data.get(subject_name),subject_name)
            day_data = [day  for day in blob_data.get(subject_name) if day.get('day') == 'Day '+str(day_number)][0]
            # print('day_data',day_data)
            types = []
            levels ={}
            if day_data.get('mcq'):
                types.append('MCQ')
                levels.update({'MCQ':day_data.get('mcq')})
            if day_data.get('coding'):
                types.append('Coding')
                levels.update({'Coding':day_data.get('coding')})
            qnslist = get_random_questions(types,[st.get('subtopic_id') for st in day_data.get('subtopicids')],levels)
            student.student_question_details.get(student_info.course_id.course_id+'_'+subject).get('week_'+str(week_number)).get('day_'+str(day_number)).update({
                "sub_topic_status": {st.get('subtopic_id'):0 for st in day_data.get('subtopicids')},
            })
            if qnslist.get('MCQ') is not None:
                student.student_question_details.get(student_info.course_id.course_id+'_'+subject).get('week_'+str(week_number)).get('day_'+str(day_number)).update({
                "mcq_questions": qnslist.get('MCQ',[]),
                "mcq_questions_status": {i:0 for i in qnslist.get('MCQ',[])},
                "mcq_score": "0/"+str(qnslist.get('MCQ_score',0))
            })
            if qnslist.get('Coding') is not None:
                student.student_question_details.get(student_info.course_id.course_id+'_'+subject).get('week_'+str(week_number)).get('day_'+str(day_number)).update({
                "coding_questions": qnslist.get('Coding',[]),
                "coding_questions_status": {i:0 for i in qnslist.get('Coding',[])},
                "coding_score": "0/"+str(qnslist.get('Coding_score',0))
            })
            student.save()
            response.update({'message':'updated',
                             'data':student.student_question_details.get(student_info.course_id.course_id+'_'+subject)})
        # else:
        #     day_Qna_data =student.student_question_details.get(subject).get('week_'+str(week_number)).get('day_'+str(day_number))
        #     sub_topics  = [ i[1:-5]  for i in day_Qna_data.get('mcq_questions_status')]
        #     res = {
        #         subtopic:{"mcq" :True if any([True for subtop in day_Qna_data.get('mcq_questions_status')if subtopic == subtop[1:-5] and day_Qna_data.get('mcq_questions_status').get(subtop) < 2]) else False ,
        #                   "coding":True if any([True for subtop in day_Qna_data.get('coding_questions_status')if subtopic == subtop[1:-5] and day_Qna_data.get('coding_questions_status').get(subtop) < 2]) else False} for subtopic in sub_topics}
        #     response.update({'message':'not updated',
        #                     'res':res})
        
        return response
    except Exception as e:
        print(e)
        return {"message": "Failed-","error":str(e)}
    
# FETCH OVERVIEW

@api_view(['GET'])
def fetch_overview_modules(request,student_id,subject,day_number):
    try:
        student = students_info.objects.get(student_id = student_id,del_row = False)
        # blob_data = json.loads(get_blob('LMS_DayWise/'+student.course_id.course_id+'.json'))
        blob_data = json.loads(get_blob(f'lms_daywise/{student.course_id.course_id}/{student.course_id.course_id}_{student.batch_id.batch_id}.json'))
        response = [day  for day in blob_data.get(subject) if day.get('day') == 'Day '+str(day_number)]
        update_app_usage(student_id)
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        update_app_usage(student_id)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
    
# FETCH QUESTIONS

@api_view(['GET'])
def fetch_questions(request,type,student_id,subject,subject_id,day_number,week_number,subTopic):
    try:
        student_info = students_info.objects.get(student_id = student_id,del_row = False)
        student = students_details.objects.using('mongodb').get(student_id = student_id,del_row = 'False')
        if student.student_question_details.get(student_info.course_id.course_id+'_'+subject_id) == None:
            student.student_question_details.update({student_info.course_id.course_id+'_'+subject_id:add_day_to_student(student_id,subject_id,subject,week_number,day_number).get('data')})
        if student.student_question_details.get(student_info.course_id.course_id+'_'+subject_id).get('week_'+week_number) == None:
            student.student_question_details.update({student_info.course_id.course_id+'_'+subject_id:add_day_to_student(student_id,subject_id,subject,week_number,day_number).get('data')})
        if student.student_question_details.get(student_info.course_id.course_id+'_'+subject_id).get('week_'+week_number).get('day_'+day_number) == None:
            student.student_question_details.update({student_info.course_id.course_id+'_'+subject_id:add_day_to_student(student_id,subject_id,subject,week_number,day_number).get('data')})
        questions_ids = (student.student_question_details.get(student_info.course_id.course_id+'_'+subject_id).get('week_'+week_number).get('day_'+day_number).get('mcq_questions' if type.lower() =='mcq' else 'coding_questions',[]))
        if type .lower() == 'mcq':
            student_answers = list(student_practiceMCQ_answers.objects.using('mongodb').filter(student_id = student_id,
                                                                                                subject_id = subject_id,
                                                                                                question_done_at = 'practice',
                                                                                                question_id__in = questions_ids,
                                                                                                del_row = 'False').values('question_id','score','entered_ans'))
        else:
            student_answers = list(student_practice_coding_answers.objects.using('mongodb').filter(student_id = student_id,
                                                                                                   subject_id = subject_id,
                                                                                                   question_done_at = 'practice',
                                                                                                   question_id__in = questions_ids,
                                                                                                   del_row = 'False').values('question_id','score','entered_ans'))
        student_answers = {
            ans.get('question_id'):{'entered_ans':ans.get('entered_ans'),'score':ans.get('score') if int(str(ans.get('score')).split('.')[1]) > 0 else int(str(ans.get('score')).split('.')[0])}
            for ans in student_answers}
        container_client =  get_blob_container_client()
        qn_data = []
        # blob_path = 'LMSData/'
        blob_path = 'subjects/'
        list_of_qns = [qn for qn in questions_ids if qn[1:-5] == subTopic]
        if list_of_qns == []:
            student.student_question_details.update({student_info.course_id.course_id+'_'+subject_id:add_day_to_student(student_id,subject_id,subject,week_number,day_number).get('data')})
            list_of_qns = [qn for qn in questions_ids if qn[1:-5] == subTopic]
        cacheresponse = cache.get('lms_rules/rules.json')
        if cacheresponse:
            # print('cache hit')
            cache.set('lms_rules/rules.json',cacheresponse)
            Rules = cacheresponse
        else:
            blob_client = container_client.get_blob_client('lms_rules/rules.json')
            Rules = json.loads(blob_client.download_blob().readall())
            cache.set('lms_rules/rules.json',Rules)
        # if type.lower() == 'mcq':
        for Qn in list_of_qns:
            path = f'{blob_path}{Qn[1:3]}/{Qn[1:-7]}/{Qn[1:-5]}/{type.lower()}/{Qn}.json'
            cacheres = cache.get(path)
            if cacheres:
                # print('cache hit')
                cache.set(path,cacheres)
                blob_data = cacheres
            else:
                blob_client = container_client.get_blob_client(path)
                blob_data = json.loads(blob_client.download_blob().readall())
                cache.set(path,blob_data)
            level = (  'Level'+('1' if Qn[-4].lower()=='e' else '2' if Qn[-4].lower()=='m' else '3' if Qn[-4].lower()=='h' else '3'))
            blob_data.update({'Qn_name':Qn,
                              'entered_ans':student_answers.get(Qn,{'entered_ans':'','score':0}).get('entered_ans'),
                              'score':str(student_answers.get(Qn,{'entered_ans':'','score':0}).get('score'))+'/'+''.join([str(i.get('score')) for i in Rules.get(type.lower(),[]) if i.get('level').lower() == level.lower()]),
                              'status': True if student.student_question_details.get(student_info.course_id.course_id+'_'+subject_id).get('week_'+week_number).get('day_'+day_number).get(type.lower()+'_questions_status').get(Qn) == 2 else False
                              })
            qn_data.append(blob_data)
        # elif type.lower() == 'coding':
        #     for Qn in list_of_qns:
        #         path = f'{blob_path}{Qn[1:3]}/{Qn[1:-7]}/{Qn[1:-5]}/{type.lower()}/{Qn}.json'
        #         cacheres = cache.get(path)
        #         if cacheres:
        #             # print('cache hit')
        #             cache.set(path,cacheres)
        #             blob_data = cacheres
        #         else:
        #             blob_client = container_client.get_blob_client(path)
        #             blob_data = json.loads(blob_client.download_blob().readall())
        #             cache.set(path,blob_data)
        #         level = (  'Level'+('1' if Qn[-4].lower()=='e' else '2' if Qn[-4].lower()=='m' else '3' if Qn[-4].lower()=='h' else '3'))
        #         blob_data.update({'Qn_name':Qn,
        #                           'entered_ans':student_answers.get(Qn,{'entered_ans':'','score':0}).get('entered_ans'),
        #                           'score':str(student_answers.get(Qn,{'entered_ans':'','score':0}).get('score'))+'/'+''.join([str(i.get('score')) for i in Rules.get(type.lower(),[]) if i.get('level').lower() == level.lower()]),
        #                           'status': True if student.student_question_details.get(subject).get('week_'+week_number).get('day_'+day_number).get(type.lower()+'_questions_status').get(Qn) == 2 else False
        #                           })
        #         qn_data.append(blob_data)
        container_client.close()
        update_app_usage(student_id)
        return JsonResponse(qn_data,safe=False,status=200)
    except Exception as e:
        print(e)
        update_app_usage(student_id)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)

# SUBMIT MCQ QUESTION  

@api_view(['POST'])
def submit_MCQ_Question(request):
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        question_id = data.get('question_id')
        # blob_rules_data = json.loads(get_blob('LMS_Rules/Rules.json'))
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
                                                                 question_done_at='practice',
                                                                 del_row = 'False' ,
                                                                 defaults={
                                                                     'student_id':student_id,
                                                                     'question_id':question_id,
                                                                     'question_done_at' :'practice',
                                                                     'correct_ans': data.get('correct_ans'),
                                                                     'entered_ans': data.get('entered_ans'),
                                                                     'subject_id':data.get('subject_id'),
                                                                     'score':int(score),
                                                                     'answered_time':timezone.now() + timedelta(hours=5, minutes=30)
                                                                 })
        response ={'message':'Already Submited'}
        if created:
            student = students_details.objects.using('mongodb').get(student_id = student_id,
                                                                    del_row = 'False')
            student_info = students_info.objects.get(student_id = student_id,del_row = False)   
            if student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')) == None:
                student.student_question_details.update({
                    student_info.course_id.course_id+'_'+data.get('subject_id'):{
                        'week_'+str(data.get('week_number')):{}
                }})
            if student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')).get('week_'+str(data.get('week_number'))) == None:
                student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')).update({
                    'week_'+str(data.get('week_number')):{
                            'day_'+str(data.get('day_number')):{}
                        }
                })
            if student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')).get('week_'+str(data.get('week_number'))).get('day_'+str(data.get('day_number'))) == None:
                student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')).get('week_'+str(data.get('week_number'))).update({
                    'day_'+str(data.get('day_number')):{
                            'mcq_questions_status':{},
                            'mcq_score':'0/0'
                    }
                })
            old_score = student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')).get('week_'+str(data.get('week_number'))).get('day_'+str(data.get('day_number'))).get('mcq_score','0/0').split('/')
            newscore = str(int(old_score[0]) + int(score)) + '/' + old_score[1]
            student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')
                                                 ).get('week_'+str(data.get('week_number'))
                                                       ).get('day_'+str(data.get('day_number'))
                                                             ).get('mcq_questions_status'
                                                                   ).update({question_id:2}) 
            student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')
                                                 ).get('week_'+str(data.get('week_number'))
                                                       ).get('day_'+str(data.get('day_number'))
                                                             ).update({'mcq_score':newscore})
            student.save()
            student_info.student_score = int(student_info.student_score) + int(score)
            student_info.student_total_score = int(student_info.student_total_score) + int(outoff)
            student_info.save()
            response ={'message':'Submited','score':str(student_practiceMCQ_answer.score)+'/'+str(outoff)}
        update_app_usage(student_id)
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        update_app_usage( json.loads(request.body).get('student_id') )
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
    
# SUBMIT CODING QUESTION

@api_view(['PUT']) 
def submition_coding_question(request):
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        question_id = data.get('Qn')
        student_info = students_info.objects.get(student_id = student_id,del_row = False)
        student = students_details.objects.using('mongodb').get(student_id = student_id,
                                                                del_row = 'False')
        if student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')).get('week_'+str(data.get('week_number'))).get('day_'+str(data.get('day_number'))).get('coding_questions_status').get(question_id) ==2:
            update_app_usage(student_id)
            return JsonResponse({ "message": "Already Submited","status":True},safe=False,status=200)
        # blob_rules_data = json.loads(get_blob('LMS_Rules/Rules.json')).get('coding')
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
                                                                                          question_done_at='practice',
                                                                                          del_row='False',
                                                                                          defaults={
                                                                                              'student_id':data.get('student_id'),
                                                                                              'subject_id':data.get('subject_id'),
                                                                                              'question_done_at':'practice',
                                                                                              'question_id':data.get('Qn'),
                                                                                              'entered_ans':data.get('Ans'),
                                                                                              'answered_time':timezone.now() + timedelta(hours=5, minutes=30),
                                                                                              'testcase_results':result,
                                                                                              'Attempts':1,
                                                                                              'score':score,
                                                                                              'del_row':'False'                                                                                          })
        response ={'message':'Submited','status':True}
        if created:
            response.update({'new':'True'})
        else:
            user.entered_ans    = data.get('Ans')
            user.answered_time  = timezone.now() + timedelta(hours=5, minutes=30)
            user.testcase_results = result
            user.score = score
            user.save()
            # return JsonResponse({'message':'Already Submited'},safe=False,status=200)
        # student_info = students_info.objects.get(student_id = student_id,del_row = False)
        old_score = student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')).get('week_'+str(data.get('week_number'))).get('day_'+str(data.get('day_number'))).get('coding_score').split('/')
        newscore = str(int(old_score[0]) + int(score)) + '/' + old_score[1]
        student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')
                                             ).get('week_'+str(data.get('week_number'))
                                                   ).get('day_'+str(data.get('day_number'))
                                                         ).get('coding_questions_status'
                                                               ).update({question_id:2})   
        student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')
                                             ).get('week_'+str(data.get('week_number'))
                                                   ).get('day_'+str(data.get('day_number'))
                                                         ).update({'coding_score':newscore})
        student.save()
        student_info.student_score = int(student_info.student_score) + int(score)
        student_info.student_total_score = int(student_info.student_total_score) + int(outoff)
        student_info.save()
        update_app_usage(student_id)
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        update_app_usage(json.loads(request.body).get('student_id'))
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
@api_view(['GET'])
def get_SQL_tables (request):
    try:
        return JsonResponse(get_all_tables(),safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
@api_view(['PUT']) 
def update_day_status(request):
    try:
        data = json.loads(request.body)
        student_info = students_info.objects.get(student_id = data.get('student_id'),del_row = False)
        student = students_details.objects.using('mongodb').get(student_id = data.get('student_id'),del_row = False)
        if student.student_question_details.get( student_info.course_id.course_id+'_'+data.get('subject_id')) == None:
            student.student_question_details.update({student_info.course_id.course_id+'_'+data.get('subject_id'):add_day_to_student(data.get('student_id'),data.get('subject_id'),data.get('subject'),data.get('week_number'),data.get('day_number')).get('data')})
        if student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')).get('week_'+data.get('week_number')) == None:
            student.student_question_details.update({student_info.course_id.course_id+'_'+data.get('subject_id'):add_day_to_student(data.get('student_id'),data.get('subject_id'),data.get('subject'),data.get('week_number'),data.get('day_number')).get('data')})
        if student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')).get('week_'+data.get('week_number')).get('day_'+data.get('day_number')) == None:
            student.student_question_details.update({student_info.course_id.course_id+'_'+data.get('subject_id'):add_day_to_student(data.get('student_id'),data.get('subject_id'),data.get('subject'),data.get('week_number'),data.get('day_number')).get('data')})
        current_status = student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')
                                                ).get('week_'+str(data.get('week_number'))
                                                      ).get('day_'+str(data.get('day_number'))
                                                            ).get('sub_topic_status').get(data.get('sub_topic'))
        list_of_sub_topics = [i for i in student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')
                                             ).get('week_'+str(data.get('week_number'))
                                                   ).get('day_'+str(data.get('day_number'))
                                                         ).get('sub_topic_status')]
        if current_status == 2 :
            update_app_usage(data.get('student_id'))
            if list_of_sub_topics != []:
                if list_of_sub_topics[-1] == data.get('sub_topic'):
                    return JsonResponse({'message':'Day Completed'},safe=False,status=200) 
            return JsonResponse({'message':'Already Completed'},safe=False,status=200)
        if current_status == 1 and data.get('status') == False:
            update_app_usage(data.get('student_id'))
            return JsonResponse({'message':'Already Started'},safe=False,status=200)
        message =''
        if data.get('status') == True:
            mcq_questions_ids = (student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')
                                                                  ).get('week_'+str(data.get('week_number'))
                                                                        ).get('day_'+str(data.get('day_number'))
                                                                              ).get('mcq_questions_status',[]))
            coding_questons = (student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')
                                                                  ).get('week_'+str(data.get('week_number'))
                                                                        ).get('day_'+str(data.get('day_number'))
                                                                              ).get('coding_questions_status',[]))

            status_of_qns = [{i:mcq_questions_ids.get(i)} for i in mcq_questions_ids if i[1:-5] == data.get('sub_topic')]
            status_of_qns.extend([{i:coding_questons.get(i)} for i in coding_questons if i[1:-5] == data.get('sub_topic')])
            if len(status_of_qns) == len([i for i in status_of_qns if i.get(list(i.keys())[0])  == 2]):
                student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')
                                             ).get('week_'+str(data.get('week_number'))
                                                   ).get('day_'+str(data.get('day_number'))
                                                         ).get('sub_topic_status').update({data.get('sub_topic'):2})
                message =   start_learning_activity(student.student_id,data.get('sub_topic'),data.get('week_number'),data.get('day_number'))
                student.save()
            else:
                update_app_usage(data.get('student_id'))
                return JsonResponse({'message':'Not Completed','message2':message},safe=False,status=200)
        else:
            if student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')
                                             ).get('week_'+str(data.get('week_number'))
                                                   ).get('day_'+str(data.get('day_number'))
                                                         ).get('sub_topic_status').get(data.get('sub_topic')) < 2 :
                student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')
                                             ).get('week_'+str(data.get('week_number'))
                                                   ).get('day_'+str(data.get('day_number'))
                                                         ).get('sub_topic_status').update({data.get('sub_topic'): 1})
                student.save()
        update_app_usage(data.get('student_id'))
        # list_of_sub_topics = [i for i in student.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject_id')
        #                                      ).get('week_'+str(data.get('week_number'))
        #                                            ).get('day_'+str(data.get('day_number'))
        #                                                  ).get('sub_topic_status')]
        # print(list_of_sub_topics)
        if list_of_sub_topics != []:
            if list_of_sub_topics[-1] == data.get('sub_topic'):
                return JsonResponse({'message':'Day Completed','message2':message},safe=False,status=200)    
        return JsonResponse({'message':'Updated','message2':message},safe=False,status=200)    
    except Exception as e:
        print(e)
        update_app_usage(json.loads(request.body).get('student_id'))
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)

def start_learning_activity(student_id,sub_topic_id,week_number,day_number):
    try :  
        # print(student_id)
        sub_topic = sub_topics.objects.get(sub_topic_id=sub_topic_id,del_row=False)
        student = students_info.objects.get(student_id=student_id,del_row=False)
        student,created = student_activities.objects.get_or_create(student_id=student,subject_id=sub_topic.topic_id.subject_id,activity_subtopic=sub_topic,del_row=False,
                                                           defaults={
                                                               'student_id':student,
                                                               'subject_id':sub_topic.topic_id.subject_id,
                                                               'activity_end_time':timezone.now().__add__(timedelta(hours=5,minutes=30)),
                                                               'activity_week': week_number,
                                                               'activity_day':day_number,
                                                               'activity_topic':sub_topic.topic_id,
                                                               'activity_subtopic':sub_topic,
                                                           })
        return 'Done'
    except Exception as e:
        print(e)
        return str(e)
