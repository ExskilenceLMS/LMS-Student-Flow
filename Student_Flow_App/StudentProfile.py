import json
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from LMS_MSSQLdb_App.models import *
from LMS_Mongodb_App.models import *
from datetime import datetime, timedelta
from django.core.serializers import serialize
from .AppUsage import update_app_usage
from .ErrorLog import *

@api_view(['GET'])
def fetch_student_Profile(request,student_id):
    try:
        student = students_info.objects.get(student_id =student_id , del_row = False)
        student_details = students_details.objects.using('mongodb').get(student_id = student_id ,del_row = 'False')
        subjects = list(course_subjects.objects.filter(course_id = student.course_id,del_row =False).values('subject_id__subject_name'))
        print(student.course_id)
        response = {
            'student_id' : student.student_id,
            'student_name' : student.student_firstname +' '+student.student_lastname,
            'course_name' : student.course_id.course_name,
            'batch_name' : student.batch_id.batch_name if student.batch_id is not None else student.batch_id,
            'subjects' : [sub.get("subject_id__subject_name") for sub in subjects],
            'profile_details' : {
                'college':student.college,
                'branch' : student.branch,
                'gender' : student.student_gender,
                'address' : student.address,
                'email': student.student_email,
                'phone': student.phone
            },
            'social_media':{
                'linkedin':student.linkedin,
                'leetcode':student.leetcode,
                'hackerrank':student.hackerrank,
                'resume':'',
                'video' : ''
            },
            'education_details':student_details.student_education_details

        }
        update_app_usage(student_id)
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        update_app_usage(student_id)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
@api_view(['PUT'])
def update_social_media(request):
    try:
        data =json.loads(request.body)
        student_details = students_info.objects.get(student_id = data.get('student_id'),del_row ='False')
        needtosave = False
        if data.get('linkedin')!=None or data.get('linkedin')!='':
            student_details.linkedin=data.get('linkedin')
            needtosave = True
        if data.get('leetcode')!=None or data.get('leetcode')!='':
            student_details.leetcode=data.get('leetcode')
            needtosave = True
        if data.get('hackerrank')!=None or data.get('hackerrank')!='':
            student_details.hackerrank=data.get('hackerrank')
            needtosave = True
        # if data.get('resume')!=None or data.get('resume')!='':
        #     student_details.linkedin=data.get('resume')
        #     needtosave = True
        # if data.get('video')!=None or data.get('video')!='':
        #     student_details.linkedin=data.get('video')
        #     needtosave = True
        if needtosave:
            student_details.save()
            response ={"message": "Updated"}
        else:
            response ={"message": "Not Updated"}
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
@api_view(['PUT'])
def update_profile(request):
    try:
        data =json.loads(request.body)
        student_details = students_info.objects.get(student_id = data.get('student_id'),del_row ='False')
        education_details = students_details.objects.using('mongodb').get(student_id = data.get('student_id'),del_row = 'False')
        student_details.college=data.get('college')
        student_details.branch=data.get('branch')
        student_details.student_gender=data.get('gender')
        student_details.address=data.get('address')
        # student_details.student_email=data.get('email')
        student_details.phone=data.get('phone')
        student_details.leetcode=data.get('leetcode')
        student_details.hackerrank=data.get('hackerrank')
        student_details.linkedin=data.get('linkedin')
        education_details.student_education_details =(data.get('education_details'))
        student_details.save()
        education_details.save()
        response ={"message": "Updated"}
        update_app_usage(data.get('student_id'))
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        update_app_usage(json.loads(request.body).get('student_id'))
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
    
@api_view(['GET'])
def college_and_branch_list(request):
    try:
        branches = branch_details.objects.filter(del_row =False)
        colleges = set(item.college_id.college_name for item in branches)
        # new_college_types = ['10th','12th','BE']
        response = {}
        # # for college_type in new_college_types:
        #     response.update({college_type if college_type != '12th' else '12th/diploma':{}})
        #     for college in colleges:
        #         response.get(college_type if college_type != '12th' else '12th/diploma'   ).update({
        #             college:[branch.branch for branch in branches if branch.college_id.college_name == college and branch.college_id.college_type.__contains__(college_type) ]
        #             })
        #         if response.get(college_type if college_type != '12th' else '12th/diploma').get (college) == []:
        #             response.get(college_type if college_type != '12th' else '12th/diploma').pop(college)
        for college in colleges:
             response.update({str(college):[branch.branch for branch in branches if branch.college_id.college_name == college  ]
             })
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed",
                             "error":str(encrypt_message(str({
                                    "Error_msg": str(e),
                                    "Stack_trace":str(traceback.format_exc())+'\nUrl:-'+str(request.build_absolute_uri())+'\nBody:-' + (str(json.loads(request.body)) if request.body else "{}")
                                    })))},safe=False,status=400)
    
