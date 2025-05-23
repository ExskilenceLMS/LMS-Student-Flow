from django.http import HttpResponse, JsonResponse
import json
from datetime import datetime, timedelta
from django.utils import timezone
from LMS_Mongodb_App.models import *
from LMS_MSSQLdb_App.models import *
from rest_framework.decorators import api_view
import re
from LMS_Project.settings import *
from .sqlrun import *
from .ErrorLog import *
def addAttempt (studentId,Subject,Qn,user_ans,data):
    try :
        student_info = students_info.objects.get(student_id = studentId,del_row = False)
        mainuser  = students_details.objects.using('mongodb').get(student_id = studentId,
                                                                     del_row = 'False')
        stat = mainuser.student_question_details.get(student_info.course_id.course_id+'_'+data.get('subject')).get('week_'+str(data.get('week_number')),{}).get('day_'+str(data.get('day_number')),{}).get('coding_questions_status',{}).get(Qn,0)  
        if stat < 2 :
                print("stat",stat)
                user , created = student_practice_coding_answers.objects.using('mongodb').get_or_create(student_id=str( studentId),
                                                                                          subject_id=str( Subject ),
                                                                                          question_id=str( Qn ),
                                                                                          del_row='False',
                                                                                          defaults={
                                                                                              'student_id':str( studentId ),
                                                                                              'subject_id':str( Subject ),
                                                                                              'question_done_at':'practice',
                                                                                              'question_id':str( Qn ),
                                                                                              'entered_ans':user_ans,
                                                                                              'answered_time':timezone.now() + timedelta(hours=5, minutes=30),
                                                                                              'testcase_results':[],
                                                                                              'Attempts':1,
                                                                                              'score':0
                                                                                          })
                attempt = 1
                if not created :
                    user.Attempts=user.Attempts+1
                    user.answered_time=timezone.now() + timedelta(hours=5, minutes=30)
                    user.entered_ans=user_ans
                    user.save()
                    attempt = user.Attempts
                if stat == 0 :
                    mainuser.student_question_details.get( student_info.course_id.course_id+'_'+data.get('subject')
                                                          ).get('week_'+str(data.get('week_number')
                                                                            ),{}).get('day_'+str(data.get('day_number')),{}
                                                                                      ).get('coding_questions_status',{}
                                                                                      ).update({Qn:1})
                    mainuser.save()
                return attempt
        else:
                return 0
    except Exception as e:
        print(e)
        return 'False'
@api_view(['POST'])
def run_python(request):
    if request.method == 'POST':
        try:
            jsondata = json.loads(request.body)
            code=jsondata.get('Code')
            callfunc=jsondata.get('CallFunction')
            code_data=str(code+'\n'+callfunc).split('\n')
            result=jsondata.get('Result')
            TestCases=jsondata.get('TestCases')
            Attempt = jsondata.get('Attempt')
            Subject = jsondata.get ('subject_id')
            studentId = jsondata.get('studentId')
            Qn = jsondata.get('Qn')
            Day_no = jsondata.get('Day_no')
            bol=True
            main=[]
            i=0
            for tc in TestCases:
                if i==0:
                    tc=tc.get('Testcase')
                    boll=[]
                    for t in tc:
                        for c in code_data:
                            if str(c).replace(' ','').startswith('#') or str(c).replace(' ','').startswith('"""') or str(c).replace(' ','').startswith("'''"):
                                code_data.remove(c)
                                continue
                            if str(c).replace(' ','').startswith(str(t).replace(' ','')):
                                boll.append({t:code_data.index(c),"val": str(c)})
                                break 
                    unique_in_tc = [item for item in tc if item not in {key for d in boll for key in d.keys()}]
                    for u in unique_in_tc:
                        if str(code_data).__contains__(u):
                            boll.append({u:True,"val": str(u)})
                    if len(boll)==len(tc):
                        t={"TestCase"+str(i+1) :"Passed"}
                        main.append(t)
                    else:
                        t={"TestCase"+str(i+1) :"Failed"}
                        bol=False
                        main.append(t)
                if i>0:
                    tc=tc['Testcase']
                    Values=tc['Value']
                    Output=tc['Output']
                    def slashNreplace(string):
                        if string=='':
                            return string
                        if string[-1]=='\n':
                            string=slashNreplace(string[:-1])
                        return string
                    for val in Values:
                        for b in boll :
                            key=str(b.keys()).split("'")[1]
                            if str(val).replace(' ','').split('=')[0] in str(b.keys()): 
                                newvalue=str(b['val'])[0:str(b['val']).index(key[0])]+val
                                if str(val).startswith(key):
                                    if str(val).replace(' ','').split('=')[0]==code_data[b[key]].replace(' ','').split('=')[0]:
                                        code_data[b[key]]=newvalue
                                    else:
                                        for c in code_data:
                                            if str(c).replace(' ','').split('=')[0]==(str(val).replace(' ','').split('=')[0]):
                                                newvalue = str(c)[0:str(c).index(key[0])]+val
                                                code_data[code_data.index(c)]= newvalue
                                                break
                                                
                    newcode=""
                    for c in code_data:
                        newcode=newcode+str(c)+'\n' 

                    t = {'TestCase'+str(i+1) :
                    {'Code':newcode,'Output':str(Output)}}

                    main.append(t)
                i=i+1
            data={'Result' : {
                'Code':code+'\n'+callfunc,
                'Output':str(result)}}

            main.append(data)
            addAttempts = addAttempt(studentId,Subject,Qn,str(code+'\n'+callfunc),jsondata)
            Output={'TestCases':main,
                    'Attempt':addAttempts
                    }
            return JsonResponse(Output,safe=False,status=200)
        except Exception as e:
            print(e)
            return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)

@api_view(['POST'])
def run_pythonDSA(request):
        try:
            jsondata = json.loads(request.body)
            code=jsondata.get('Code')
            callfunc=jsondata.get('CallFunction')
            code_data=str(code+'\n'+callfunc).split('\n')
            result=jsondata.get('Result')
            TestCases=jsondata.get('TestCases')
            Subject = jsondata.get ('subject_id')
            studentId = jsondata.get('studentId')
            Qn = jsondata.get('Qn')
            bol=True
            main=[]
            i=0
            for tc in TestCases:
                if i==0:
                    tc=tc.get('Testcase')
                    boll=[]
                    for t in tc:
                        for c in code_data:
                            if str(c).replace(' ','').startswith('#') or str(c).replace(' ','').startswith('"""') or str(c).replace(' ','').startswith("'''"):
                                code_data.remove(c)
                                continue
                            if str(c).replace(' ','').startswith(str(t).replace(' ','')):
                                boll.append({t:code_data.index(c),"val": str(c)})
                                break 
                    unique_in_tc = [item for item in tc if item not in {key for d in boll for key in d.keys()}]
                    for u in unique_in_tc:
                        if str(code_data).__contains__(u):
                            boll.append({u:True,"val": str(u)})
                    if len(boll)==len(tc):
                        t={"TestCase"+str(i+1) :"Passed"}
                        main.append(t)
                    else:
                        t={"TestCase"+str(i+1) :"Failed"}
                        bol=False
                        main.append(t)
                if i>0:
                    tc=tc['Testcase']
                    Values=tc['Value']
                    Output=tc['Output']
                    if jsondata.get('ClassTypeValidation','False') == 'True':
                        t = {'TestCase'+str(i+1) :
                        {'Code':code+'\n'+Values[0],'Output':str(Output)}}

                        main.append(t)
                                            
                    else:
                        for val in Values:
                            for b in boll :
                                key=str(b.keys()).split("'")[1]
                                if str(val).replace(' ','').split('=')[0] in str(b.keys()): 
                                    newvalue=str(b['val'])[0:str(b['val']).index(key[0])]+val
                                    if str(val).startswith(key):
                                        if str(val).replace(' ','').split('=')[0]==code_data[b[key]].replace(' ','').split('=')[0]:
                                            code_data[b[key]]=newvalue
                                        else:
                                            for c in code_data:
                                                if str(c).replace(' ','').split('=')[0]==(str(val).replace(' ','').split('=')[0]):
                                                    newvalue = str(c)[0:str(c).index(key[0])]+val
                                                    code_data[code_data.index(c)]= newvalue
                                                    break
                                                    
                        newcode=""
                        for c in code_data:
                            newcode=newcode+str(c)+'\n' 

                        t = {'TestCase'+str(i+1) :
                        {'Code':newcode,'Output':str(Output)}}

                        main.append(t)
                i=i+1
            data={'Result' : {
                'Code':code+'\n'+callfunc,
                'Output':str(result)}}

            main.append(data)
            addAttempts = addAttempt(studentId,Subject,Qn,code,jsondata)
            Output={'TestCases':main,
                    'Attempt':addAttempts
                    }
            return JsonResponse(Output,safe=False,status=200)
        except Exception as e:
            print(e)
            return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)

@api_view(['POST'])
def sql_query(req):
    if req.method == 'POST':
        try:
            current_time=timezone.now() + timedelta(hours=5, minutes=30)
            data = json.loads(req.body)
            query = str(data.get('query')).strip()
            Subject = data.get ('subject_id')
            studentId = data.get('studentId')
            Qn = data.get('Qn')
            addAttempts = addAttempt(studentId,Subject,Qn,query,data)
            out = local(query)
            result= out
            ExpectedOutput=data.get('ExpectedOutput')
            TestCases=data.get('TestCases')
            main ={
                'TestCases':list(testcase_validation(query,result,ExpectedOutput,TestCases))
                ,'data':out
                ,'Time':[{"Execution_Time":str(((timezone.now() + timedelta(hours=5, minutes=30))-current_time).total_seconds())[0:-2]+" s"}],
                'Attempt':addAttempts
 
            }
            return JsonResponse(main,safe=False,status=200)
        except Exception as e:
            print(e)
            return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(req.build_absolute_uri())+'\nBody:-' + (str(json.loads(req.body)) if req.body else "{}")
                                    })))},safe=False,status=400)
        
def removespace(query_list):
    sl=re.compile(r'[*=,]')
    query=[]
    for s in query_list:
        if sl.search(s):
            equal_index = query_list.index(s)
            if s=='=' or s=='*':#sl.search(s):
                data=query_list[equal_index-1]+query_list[equal_index]+query_list[equal_index+1]
                query_list.remove(query_list[equal_index+1]) 
                query.pop()
                query.append(data)
            elif s.startswith('=') or s.startswith('*') :# or s.endswith('=' or'*'):
                data=query_list[equal_index-1]+query_list[equal_index]
                query.pop()
                query.append(data)
            elif s.endswith('=')or s.endswith('*') :
                data=query_list[equal_index]+query_list[equal_index+1]
                query_list.remove(query_list[equal_index+1]) 
                query.append(data)        
            elif s.endswith(','):
                query.append(query_list[equal_index][0:-1])        
            elif s.startswith(','):
                query.append(query_list[equal_index][1:]) 
            elif s.count(',')  :
                data=query_list[equal_index].split(',')
                query.append(data[0])
                query.append(data[1])       
            else:
                query.append(s)
        else:
            query.append(s)
    return query

def testcase_validation(query,result,ExpectedOutput,TestCases):
    try:
            bol=True
            main=[]
            i=0
            bol=True
            for t in TestCases:
                if i==1:
                    t=t["Testcase"].replace('##',' ').split()[0].split(',')
                    key=str(result[0].keys())

                    key = key.replace('dict_keys(', '')[0:-1]
                    t=str(key).lower()==str(t).lower()
                    if t:
                        t={"TestCase"+str(i) :"Passed"}
                    else:
                        t={"TestCase"+str(i) :"Failed"}
                        bol=False
                    main.append(t)
                if i==2:
                    t=t["Testcase"]
                    if str(result).lower().replace('.0','')==str(t).lower().replace('.0',''):#======================================
                        t={"TestCase"+str(i) :"Passed"}
                    else:
                        t={"TestCase"+str(i) :"Failed"}
                        bol=False
                    main.append(t)
                if i>=3:
                    t=t['Testcase']
                    q = str(re.sub(r"([^\w\s])", r" \1 ", query)).lower().split()
                    t2 = str(re.sub(r"([^\w\s])", r" \1 ", t)).lower().split()
                    if str(q).__contains__(str(t2)[1:-1]):#len(list(common))==len(t2):
                        t={"TestCase"+str(i) :"Passed"}
                    else:
                        t={"TestCase"+str(i) :"Failed"}
                        bol=False
                    main.append(t)
                i=i+1
            if bol:
                t={"TestCase"+str(i) :"Passed"}
                main.append(t)
                result_json = json.dumps(str(result).lower().replace('.0',''), sort_keys=True)
                result_json = json.loads(result_json)
            
                ExpectedOutput_json = json.dumps(str(ExpectedOutput).lower().replace('.0',''), sort_keys=True)
                ExpectedOutput_json = json.loads(ExpectedOutput_json)
                if result_json == ExpectedOutput_json:
                    data={"Result" :"True"}
                else:
                    data=   {"Result" :"False"}
            else:
                t=TestCases[0]["Testcase"]
                t=str(t).lower()
                queryt=str(query).lower()
                if queryt==t:
                    t={"TestCase"+str(i) :"Passed"}
                else:
                    t={"TestCase"+str(i) :"Failed"}
                    
                main.append(t)
                data={"Result" :"False"}
                bol=False

            main.append(data)
            return main
    except Exception as e:
        return False

