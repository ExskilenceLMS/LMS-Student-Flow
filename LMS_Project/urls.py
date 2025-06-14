from django.contrib import admin
from django.urls import path
from Student_Flow_App import views ,tests ,coding_validation as cv ,AppUsage,StudentProfile as profile
from Student_Flow_App import StudentDashBoard as dashboard ,StudentLiveSessions as live_session ,LearningModules as learning_modules
from Student_Flow_App import Student_Tickets as tickets , StudentRoadMap as roadmap , StudentTestDetails as test_details
from Student_Flow_App import Weekly_test as weekly_test,SQL_TESTING,ErrorLog as error_log #Student_Final_test as test_details
from Student_Flow_App import roadmaptesting as roadmaptesting
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home),
    path('api/clearcache/', AppUsage.clear_blob_ceche),
    # Login URLs
    path('api/login/<str:email>/', views.login),
    path('api/logout/<str:student_id>/', views.logout),
    # Dashboard URLs
    path('api/studentdashboard/mycourses/<str:student_id>/',       dashboard.fetch_enrolled_subjects),
    path('api/studentdashboard/upcomming/sessions/<str:student_id>/',      dashboard.fetch_live_session),
    path('api/studentdashboard/upcomming/events/<str:Course_id>/<str:batch_id>/',       dashboard.fetch_upcoming_events),
    path('api/studentdashboard/weeklyprogress/<str:student_id>/o',       dashboard.get_weekly_progress),
    path('api/studentdashboard/weeklyprogress/<str:student_id>/',       dashboard.get_weekly_progress01),
    path('api/studentdashboard/hourspent/<str:student_id>/<str:week>/',       dashboard.fetch_study_hours),
    path('api/studentdashboard/summary/<str:student_id>/',       dashboard.fetch_student_summary),
    path('api/studentdashboard/event/calender/<str:student_id>/',       dashboard.fetch_calendar),
    
    # top navigation and roadmap URLs
    path('api/notifications/<str:student_id>/',       roadmap.fetch_top_navigation),
    path('api/roadmap/<str:student_id>/<str:course_id>/<str:subject_id>/o',       roadmap.fetch_roadmap),
    path('api/roadmap/<str:student_id>/<str:course_id>/<str:subject_id>/',       roadmaptesting.fetch_roadmap0),

    # learning modules URLs
    path('api/student/learningmodules/<str:student_id>/<str:subject>/<str:subject_id>/<str:day_number>/<str:week_number>/',       learning_modules.fetch_learning_modules),
    path('api/student/lessonoverview/<str:student_id>/<str:subject>/<str:day_number>/',       learning_modules.fetch_overview_modules),
    path('api/student/practice<str:type>/<str:student_id>/<str:subject>/<str:subject_id>/<str:day_number>/<str:week_number>/<str:subTopic>/',       learning_modules.fetch_questions),
    path('api/student/add/days/', learning_modules.add_days_to_student),
    path('api/student/practicemcq/submit/', learning_modules.submit_MCQ_Question),
    path('api/student/practicecoding/tables/', learning_modules.get_SQL_tables),
    path('api/student/lessons/status/', learning_modules.update_day_status),
    
    # coding Validation URLs
    path('api/student/coding/py/',    cv.run_python),
    path('api/student/coding/ds/', cv.run_pythonDSA),
    path('api/student/coding/sql/', cv.sql_query),
    path('api/student/coding/', learning_modules.submition_coding_question),

    # Live Session URLs
    path('api/student/sessions/<str:student_id>/', live_session.fetch_all_live_session),

    # TEST Details URLs
    path('api/student/testdetails/<str:student_id>/', test_details.fetch_all_test_details),
            # Weekly Test URLs
    path('api/student/test/weekly/<str:student_id>/<str:week_number>/<str:subject_id>/', weekly_test.Automated_weekly_test),

            # Test URLs
    path('api/student/test/instuction/<str:student_id>/<str:test_id>/', test_details.test_instruction),
    path('api/student/test/section/<str:student_id>/<str:test_id>/', test_details.section_details),
#     path('api/student/test/start/<str:student_id>/<str:test_id>/', test_details.Start_TEST),
#     path('api/student/test/questions/status/<str:student_id>/<str:test_id>/', test_details.Qns_status_update),
    path('api/student/test/questions/<str:student_id>/<str:test_id>/<str:section_name>/', test_details.get_test_Qns),
    path('api/student/test/questions/submit/mcq/', test_details.submit_test_mcq_questions),
    path('api/student/test/questions/submit/coding/', test_details.submit_test_coding_questions),
    path('api/student/test/submit/<str:student_id>/<str:test_id>/', test_details.submit_test),
    path('api/student/duration/<str:student_id>/<str:test_id>/', test_details.Test_duration),
    #         # Final Test URLs
    # path('api/student/final/test/instuction/<str:student_id>/<str:test_id>/', final_test.final_test_insturction),
    # path('api/student/final/test/questions/<str:student_id>/<str:test_id>/<str:section_name>/', final_test.get_final_test_Qns),
    # path('api/student/final/test/questions/submit/mcq/', final_test.submit_final_test_mcq_questions),
    # path('api/student/final/test/questions/submit/coding/', final_test.submit_final_test_coding_questions),
    # path('api/student/final/test/submit/<str:student_id>/<str:test_id>/', final_test.submit_final_test),

            # Test report URLs
    path('api/student/test/report/<str:student_id>/<str:test_id>/', test_details.student_test_report),

    # Teckets URLs
    path('api/student/tickets/', tickets.submit_Tickets),
    path('api/student/tickets/<str:student_id>/', tickets.fetch_all_tickets),
    path('api/student/ticket/comments/', tickets.student_side_comments_for_tickets),

    # FAQ URLs
    path('api/student/faq/',views.fetch_FAQ),

    # Profile URLs
    path('api/student/profile/<str:student_id>/', profile.fetch_student_Profile),
    path('api/student/profile/', profile.update_profile),
    path('api/colleges/', profile.college_and_branch_list),

    # Media URLs
    path('media/', views.get_media),
    path('media/', views.generate_secure_blob_url),

    # Error_log URLs
    path('api/errorlog/', error_log.Upload_ErrorLog),

    # TESTING URLS
    # path('addstudent/',      tests.addStudent),
    # path('addstudentactivity/<str:day>/<str:week>/',      tests.addStudetsActivity),
    # path('addlivesession/',  tests.addLiveSession),
    # path('addappusage/',     tests.addstudent_app_usages),
    # path('addsubplan/',   tests.add_course_plane_details),
    # path('addnotification/',   tests.add_notification),
    # path('addstudentinfo/',   tests.update_student_info),
    # path('addparticipants/',   tests.add_participants),
    # path('addtestdetails/',   tests.add_test_sction),
    # path('ids/',   views.generate_ids),
    # path('upvideo/',   views    .upload_video),
    path('mcqtesting/<str:subject_id>/',   SQL_TESTING.get_mcqs),
    # path('testing/<str:student_id>/', student_final_test.fetch_all_test_details),

]

