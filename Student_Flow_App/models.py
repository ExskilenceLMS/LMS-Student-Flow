from django.db import models

# 1
class tracks(models.Model):
    track_id                = models.CharField(max_length=20, unique=True)
    track_name              = models.CharField(max_length=50)
    track_name_searchable   = models.CharField(max_length=50)
    track_description       = models.TextField()
    created_by              = models.CharField(max_length=100)
    created_at              = models.DateTimeField()
    modified_by             = models.CharField(max_length=100, null=True, blank=True)
    modified_at             = models.DateTimeField()
    action                  = models.CharField(max_length=100, null=True, blank=True)
    del_row                 = models.BooleanField(default=False)
    def __str__(self):
        return self.track_name
    class Meta:
        db_table = 'tracks'
# 2
class subjects(models.Model):
    subject_id              = models.CharField(max_length=20, unique=True)
    track_id                = models.ForeignKey(tracks, on_delete=models.CASCADE)
    subject_name            = models.TextField()
    subject_alt_name        = models.TextField()
    subject_description     = models.TextField()
    created_by              = models.CharField(max_length=100)
    created_at              = models.DateTimeField()
    modified_by             = models.CharField(max_length=100, null=True, blank=True)
    modified_at             = models.DateTimeField()
    action                  = models.CharField(max_length=100, null=True, blank=True)
    del_row                 = models.BooleanField(default=False)


    def __str__(self):
        return self.subject_name

    class Meta:
        db_table = 'subjects'
# 3
class topics(models.Model):
    topic_id                = models.CharField(max_length=20, unique=True)
    subject_id              = models.ForeignKey(subjects, on_delete=models.CASCADE)
    topic_name              = models.CharField(max_length=50)
    topic_alt_name          = models.CharField(max_length=50, null=True, blank=True)
    topic_description       = models.TextField()
    created_by              = models.CharField(max_length=100)
    created_at              = models.DateTimeField()
    modified_by             = models.CharField(max_length=100, null=True, blank=True)
    modified_at             = models.DateTimeField()
    action                  = models.CharField(max_length=100, null=True, blank=True)
    del_row                 = models.BooleanField(default=False)

    def __str__(self):
        return self.topic_name
    class Meta:
        db_table = 'topics'
# 4
class sub_topics(models.Model):
    sub_topic_id            = models.CharField(max_length=20, unique=True)
    topic_id                = models.ForeignKey(topics, on_delete=models.CASCADE)
    sub_topic_name          = models.CharField(max_length=100)
    sub_topic_description   = models.TextField()
    sub_topic_alt_name      = models.CharField(max_length=50, null=True, blank=True)
    notes                   = models.IntegerField(null=True, blank=True)
    videos                  = models.IntegerField(null=True, blank=True)
    mcq                     = models.IntegerField(null=True, blank=True)
    coding                  = models.IntegerField(null=True, blank=True)
    created_by              = models.CharField(max_length=100)
    created_at              = models.DateTimeField()
    modified_by             = models.CharField(max_length=100, null=True, blank=True)
    modified_at             = models.DateTimeField()
    action                  = models.CharField(max_length=100, null=True, blank=True)
    del_row                 = models.BooleanField(default=False)

    def __str__(self):
        return self.sub_topic_name

    class Meta:
        db_table = 'sub_topics'

# 5
class courses(models.Model):
    course_id               = models.CharField(max_length=20, unique=True)
    course_name             = models.CharField(max_length=50)
    course_description      = models.TextField()
    course_level            = models.CharField(max_length=20)
    Existing_Subjects       = models.CharField(max_length=100,null=True,blank=True)
    created_by              = models.CharField(max_length=100)
    created_at              = models.DateTimeField()
    modified_by             = models.CharField(max_length=100, null=True, blank=True)
    modified_at             = models.DateTimeField()
    action                  = models.CharField(max_length=100, null=True, blank=True)
    tracks                  = models.TextField(default=None, blank=True, null=True)
    del_row                 = models.BooleanField(default=False)

    def __str__(self):
        return self.course_name

    class Meta:
        db_table = 'courses'

# 7 
class batches(models.Model):
    batch_id                = models.CharField(max_length=20, primary_key=True)
    course_id               = models.ForeignKey(courses, on_delete=models.CASCADE)
    batch_name              = models.CharField(max_length=50)
    delivery_type           = models.CharField(max_length=50, choices=[("Online", "Online"), ("In-person", "In-person"), ("Hybrid", "Hybrid")])
    max_no_of_students      = models.IntegerField()
    start_date              = models.DateTimeField()
    indicative_date         = models.DateTimeField()
    saturday_holiday        = models.BooleanField(default=False, blank=True)
    sunday_holiday          = models.BooleanField(default=False, blank=True)
    hours_per_day           = models.IntegerField(default=0)
    del_row                 = models.BooleanField(default=False)

    def __str__(self):
        return self.batch_name
    class Meta:
        db_table = 'batches'

# 6
class course_subjects(models.Model):
    course_id               = models.ForeignKey(courses, on_delete=models.CASCADE)
    subject_id              = models.ForeignKey(subjects, on_delete=models.CASCADE)
    duration_in_days        = models.CharField(max_length=20)
    start_date              = models.DateTimeField(default=None )
    end_date                = models.DateTimeField(default=None)
    is_mandatory            = models.BooleanField()
    path                    = models.CharField(max_length=250)
    batch_id                = models.ForeignKey(batches,  on_delete=models.SET_NULL, null=True,default=None)
    del_row                 = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.course_id.course_name} - {self.subject_id.subject_name}"
    class Meta:
        db_table = 'course_subjects'
# 8
class course_plan_details(models.Model):
    course_id               = models.ForeignKey(courses, on_delete=models.CASCADE)
    subject_id              = models.ForeignKey(subjects, on_delete=models.CASCADE)
    day                     = models.IntegerField()
    content_type            = models.CharField(max_length=20)
    week                    = models.IntegerField()
    day_date                = models.DateTimeField()
    duration_in_hours       = models.IntegerField()
    batch_id                = models.ForeignKey(batches,  on_delete=models.SET_NULL, null=True,default=None)
    del_row                 = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.course_id.course_name} - {self.subject_id.subject_name}"
    class Meta:
        db_table = 'course_plan_details'

# 9
class students_info(models.Model):
    student_id              = models.CharField(max_length=20, primary_key=True)
    course_id               = models.ForeignKey(courses,  on_delete=models.SET_NULL, null=True)
    student_firstname       = models.CharField(max_length=100)
    student_lastname        = models.CharField(max_length=100)
    student_email           = models.EmailField(unique=True)
    student_country         = models.CharField(max_length=100)
    student_state           = models.CharField(max_length=100)
    student_city            = models.CharField(max_length=100)
    student_gender          = models.CharField(max_length=10)
    student_course_starttime= models.DateTimeField(null=True)
    student_pincode         = models.CharField(max_length=20)
    student_alt_phone       = models.CharField(max_length=20,blank=True,null=True)
    isActive                = models.BooleanField(default=True)
    student_dob             = models.DateField(default=None, null=True)
    student_qualification   = models.CharField(max_length=100)
    batch_id                = models.ForeignKey(batches,  on_delete=models.SET_NULL, null=True,default=None)
    college                 = models.CharField(max_length=50)
    branch                  = models.CharField(max_length=50)
    address                 = models.CharField(max_length=100,blank=True,null=True)
    phone                   = models.CharField(max_length=20)
    student_score           = models.CharField(max_length=20, default=0)
    student_total_score     = models.CharField(max_length=20, default=0)
    student_catogory        = models.CharField(max_length=20, choices=[("SUN", "SUN"), ("MOON", "MOON"), ("STAR", "STAR")],default="--")
    student_college_rank    = models.IntegerField(default=-1)
    student_overall_rank    = models.IntegerField(default=-1)
    student_type            = models.CharField(max_length=20)
    linkedin                = models.CharField(max_length=100, blank=True, null=True)
    leetcode                = models.CharField(max_length=100, blank=True, null=True)
    hackerrank              = models.CharField(max_length=100, blank=True, null=True)
    allocate                = models.BooleanField(default=False)
    del_row                 = models.BooleanField(default=False)
    student_CGPA            = models.FloatField(default=0.0)
    class Meta:
        db_table = 'students_info'
# 10
class trainers(models.Model):
    trainer_id              = models.CharField(max_length=20, primary_key=True)
    trainer_name            = models.CharField(max_length=100)
    trainer_email           = models.EmailField()
    gender                  = models.CharField(max_length=10)
    # trainer_college       = models.CharField(max_length=50)
    # trainer_branch        = models.CharField(max_length=50)
    address                 = models.CharField(max_length=100)
    phone                   = models.CharField(max_length=20)
    # trainer_score         = models.CharField(max_length=20)
    trainer_type            = models.CharField(max_length=20)
    linkedin                = models.CharField(max_length=100, blank=True, null=True)
    leetcode                = models.CharField(max_length=100, blank=True, null=True)
    hackerrank              = models.CharField(max_length=100, blank=True, null=True)
    del_row                 = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.trainer_name}"
    class Meta:
        db_table = 'trainers'
# 11
class trainer_review_comments(models.Model):
    comment_id              = models.CharField(max_length=20, primary_key=True)
    student_id              = models.ForeignKey(students_info,  on_delete=models.SET_NULL, null=True)
    trainer_id              = models.ForeignKey(trainers, on_delete=models.SET_NULL, null=True)
    review_type             = models.CharField(max_length=20)
    reason                  = models.CharField(max_length=20)
    comment                 = models.CharField(max_length=20)
    date_time               = models.DateTimeField()
    del_row                 = models.BooleanField(default=False)

    class Meta:
        db_table = 'trainer_review_comments'

# 12
class test_details(models.Model):
    test_id                 = models.CharField(max_length=20, primary_key=True)
    test_name               = models.CharField(max_length=50)
    test_duration           = models.CharField(max_length=20)
    test_marks              = models.IntegerField()
    test_type               = models.CharField(max_length=20)
    test_description        = models.CharField(max_length=250)
    test_created_by         = models.EmailField(default=None, null=True)
    track_id                = models.ForeignKey(tracks, on_delete=models.SET_NULL, null=True)
    course_id               = models.ForeignKey(courses, on_delete=models.SET_NULL, null=True)
    subject_id              = models.ForeignKey(subjects, on_delete=models.SET_NULL, null=True)
    batch_id                = models.ForeignKey(batches,  on_delete=models.SET_NULL, null=True,default=None)
    topic_id                = models.JSONField(default=list, blank=True)
    level                   = models.CharField(max_length=20)
    tags                    = models.JSONField(default=list, blank=True)
    test_date_and_time      = models.DateTimeField(default=None, null=True)
    test_created_date_time  = models.DateTimeField(default=None, null=True)
    del_row                 = models.BooleanField(default=False)

    def __str__(self):
        return self.test_name

    class Meta:
        db_table = 'test_details'
# 13
class questions(models.Model):
    question_id             = models.CharField(max_length=20, primary_key=True)
    question_type           = models.CharField(max_length=20)
    level                   = models.CharField(max_length=20)
    created_by              = models.CharField(max_length=100)
    creation_time           = models.DateTimeField()
    last_updated_time       = models.DateTimeField()
    last_updated_by         = models.CharField(max_length=100,null=True, blank=True)
    reviewed_by             = models.CharField(max_length=20, null=True, blank=True)
    tags                    = models.JSONField(default=list, blank=True)
    sub_topic_id            = models.ForeignKey(sub_topics, on_delete=models.SET_NULL, null=True)
    del_row                 = models.BooleanField(default=False)

    class Meta:
        db_table = 'questions'
# 14
class test_sections(models.Model):
    test_id                 = models.ForeignKey(test_details, on_delete=models.CASCADE, db_column="Test_id")
    section_number          = models.IntegerField()
    section_name            = models.CharField(max_length=20)
    topic_id                = models.ForeignKey(topics, on_delete=models.SET_NULL, null=True)
    sub_topic_id            = models.ForeignKey(sub_topics, on_delete=models.SET_NULL, null=True)
    question_id             = models.ForeignKey(questions, on_delete=models.SET_NULL, null=True)
    del_row                 = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('test_id', 'question_id')
        db_table = 'test_sections'
# 15
class students_assessments(models.Model):
    student_id                  = models.ForeignKey(students_info,  on_delete=models.SET_NULL, null=True)
    course_id                   = models.ForeignKey(courses, on_delete=models.SET_NULL, null=True)
    subject_id                  = models.ForeignKey(subjects, on_delete=models.SET_NULL, null=True)
    assessment_type             = models.CharField(max_length=20)
    test_id                     = models.ForeignKey(test_details, on_delete=models.CASCADE, db_column="Test_id")
    assessment_status           = models.CharField(max_length=20,choices=[('Pending','Pending'),('Started','Started'),('Completed','Completed')])
    assessment_score_secured    = models.FloatField()
    assessment_max_score        = models.FloatField()
    assessment_week_number      = models.IntegerField(default=None, null=True)
    assessment_completion_time  = models.DateTimeField(default=None, null=True)
    assessment_rank             = models.IntegerField(default=None, null=True)
    assessment_overall_rank     = models.IntegerField(default=None, null=True)
    student_duration            = models.FloatField(default=0)
    student_test_completion_time= models.DateTimeField(default=None, null=True)
    student_test_start_time     = models.DateTimeField(default=None, null=True)
    del_row                     = models.BooleanField(default=False)

    class Meta:
        db_table = 'students_assessments'
# 16 
class student_activities(models.Model):
    student_id              = models.ForeignKey(students_info,  on_delete=models.SET_NULL, null=True)
    subject_id              = models.ForeignKey(subjects,  on_delete=models.SET_NULL, null=True)
    activity_end_time       = models.DateTimeField()
    activity_week           = models.IntegerField()
    activity_day            = models.IntegerField()
    activity_topic          = models.ForeignKey(topics, on_delete=models.SET_NULL, null=True)
    activity_subtopic       = models.ForeignKey(sub_topics, on_delete=models.SET_NULL, null=True)
    del_row                 = models.BooleanField(default=False)

    class Meta:
        db_table = 'student_activities'

# 17 
class student_app_usage(models.Model):
    student_id              = models.ForeignKey(students_info,  on_delete=models.SET_NULL, null=True)
    logged_in               = models.DateTimeField()
    logged_out              = models.DateTimeField()
    del_row                 = models.BooleanField(default=False)

    class Meta:
        db_table = 'student_app_usage'
# 18    
class college_details(models.Model):
    college_id              = models.CharField(max_length=20, primary_key=True)
    college_name            = models.CharField(max_length=50)
    center_name             = models.CharField(max_length=20)
    college_code            = models.CharField(max_length=20)
    # college_type          = models.CharField(max_length=20) # 10th or 12th or diploma or degree or 10th#12th/diploma#BE
    del_row                 = models.BooleanField(default=False)

    class Meta:
        db_table = 'college_details'
# 19
class branch_details(models.Model):
    college_id              = models.ForeignKey(college_details, on_delete=models.SET_NULL, null=True)
    branch_id               = models.CharField(max_length=20)
    branch                  = models.CharField(max_length=20)
    del_row                 = models.BooleanField(default=False)

    class Meta:
        db_table = 'branch_details'

# class ranks(models.Model):
#20
class suite_login_details(models.Model):
    user_id                 = models.CharField(max_length=20, primary_key=True)
    user_first_name         = models.CharField(max_length=100)
    user_last_name          = models.CharField(max_length=100)
    user_email              = models.EmailField()
    phone                   = models.CharField(max_length=20)
    activity_status         = models.CharField(max_length=20)
    category                = models.JSONField(default=list, blank=True)
    reg_date                = models.DateTimeField()
    exp_date                = models.DateTimeField(null=True, blank=True)
    access                  = models.JSONField(default=list, blank=True)
    del_row                 = models.BooleanField(default=False)
 
    class Meta:
        db_table = 'suite_login_details'
#21
class student_test_questions_details(models.Model):
    student_id                  = models.ForeignKey(students_info,  on_delete=models.SET_NULL, null=True)
    subject_id                  = models.ForeignKey(subjects,  on_delete=models.SET_NULL, null=True)
    question_type               = models.CharField(max_length=20)
    test_id                     = models.ForeignKey(test_details, on_delete=models.SET_NULL, null=True)
    score_secured               = models.FloatField(default=0)
    question_status             = models.CharField(max_length=20,choices=[('Attempted','Attempted'),('Pending','Pending'),('Submitted','Submitted')])
    max_score                   = models.FloatField(default=0)
    week_number                 = models.IntegerField(default=0, null=True)
    completion_time             = models.DateTimeField(default=None, null=True) 
    question_id                 = models.ForeignKey(questions, on_delete=models.SET_NULL, null=True)
    student_answer              = models.TextField(default=None, null=True)
    del_row                     = models.BooleanField(default=False)

    class Meta:
        db_table = 'student_test_questions_details'

# MONGO DB Models +================================================================

from djongo import models as djongo_models
from django.utils import timezone
from datetime import datetime, timedelta

# 1
class live_sessions(djongo_models.Model):

    # student_id = models.ForeignKey(Students,  on_delete=models.SET_NULL, null=True)
    session_id                  = djongo_models.AutoField(primary_key=True)
    session_title               = djongo_models.TextField()
    session_starttime           = djongo_models.DateTimeField()
    session_author              = djongo_models.TextField()
    session_subject             = djongo_models.TextField()
    session_meetlink            = djongo_models.TextField()
    session_endtime             = djongo_models.DateTimeField()
    session_video_link          = djongo_models.TextField()
    session_status              = djongo_models.TextField()
    student_ids                 = djongo_models.JSONField(default=list)
    del_row                     = djongo_models.CharField(default='False',max_length=5)

    class Meta:
        db_table = 'live_sessions'
# 4
class student_practiceMCQ_answers(djongo_models.Model):
    student_id                  = djongo_models.CharField(max_length=20)
    question_id                 = djongo_models.CharField(max_length=20)
    question_done_at            = djongo_models.CharField(max_length=20)
    correct_ans                 = djongo_models.CharField(max_length=20)
    entered_ans                 = djongo_models.CharField(max_length=20)
    subject_id                  = djongo_models.CharField(max_length=20)
    score                       = djongo_models.FloatField(default=0)
    answered_time               = djongo_models.DateTimeField()
    del_row                     = djongo_models.CharField(default='False',max_length=5)

    class Meta:
        db_table = 'student_practiceMCQ_answers'
# 5
class student_practice_coding_answers(djongo_models.Model):
    student_id                  = djongo_models.CharField(max_length=20)
    question_id                 = djongo_models.CharField(max_length=25)
    question_done_at            = djongo_models.CharField(max_length=20)
    entered_ans                 = djongo_models.TextField()
    subject_id                  = djongo_models.CharField(max_length=20)
    answered_time               = djongo_models.DateTimeField()
    testcase_results            = djongo_models.JSONField(default=dict)
    Attempts                    = djongo_models.IntegerField()
    score                       = djongo_models.FloatField(default=0)
    del_row                     = djongo_models.CharField(default='False',max_length=5)

    class Meta:
        db_table = 'student_practice_coding_answers'
# 6
class student_online_session(djongo_models.Model):
    session_id                  = djongo_models.CharField(max_length=20)
    student_id                  = djongo_models.CharField(max_length=20)
    attended_duration           = djongo_models.FloatField()
    display_name                = djongo_models.CharField(max_length=20)
    del_row                     = djongo_models.CharField(default='False',max_length=5)

    def __str__(self):
        return self.session_id
    class Meta:
        db_table = 'student_online_session'
# 7
class student_attendance_session_details(djongo_models.Model):
    session_id                  = djongo_models.CharField(max_length=20)    
    student_id                  = djongo_models.CharField(max_length=20)
    session_in                  = djongo_models.DateTimeField()
    session_out                 = djongo_models.DateTimeField()
    attended_time               = djongo_models.FloatField()
    del_row                     = djongo_models.CharField(default='False',max_length=5)

    class Meta:
        db_table = 'student_attendance_session_details'
# 8
class group_announcement(djongo_models.Model):
    group_id                    = djongo_models.CharField(max_length=20, primary_key=True)
    group_name                  = djongo_models.TextField()
    student_ids                 = djongo_models.JSONField()
    del_row                     = djongo_models.CharField(default='False',max_length=5)

    class Meta:
        db_table = 'group_announcement'
# 9
class notification(djongo_models.Model):
    notification_id             = djongo_models.AutoField(primary_key=True)
    notification_title          = djongo_models.TextField()
    notification_message        = djongo_models.TextField()
    notification_timestamp      = djongo_models.DateTimeField()
    status                      = djongo_models.CharField(max_length=1)
    student_id                  = djongo_models.CharField(max_length=20)
    del_row                     = djongo_models.CharField(default='False',max_length=5)

    class Meta:
        db_table = 'notification'
# 10
class announcements(djongo_models.Model):
    announcement_id             = djongo_models.CharField(max_length=20)
    announcement_title          = djongo_models.TextField()
    announcement_message        = djongo_models.TextField()
    announcement_timestamp      = djongo_models.DateTimeField()
    origin                      = djongo_models.CharField(max_length=20)
    attachments                 = djongo_models.JSONField()
    group_id                    = djongo_models.CharField(max_length=20)
    announcement_type           = djongo_models.CharField(max_length=20)
    del_row                     = djongo_models.CharField(default='False',max_length=5)

    class Meta:
        db_table = 'announcements'
# 11
class students_details(djongo_models.Model):
    student_id                  = djongo_models.CharField(max_length=20, primary_key=True)
    student_question_details    = djongo_models.JSONField(default=dict)
    student_group_ids           = djongo_models.JSONField(default=dict)
    student_notification        = djongo_models.JSONField(default=dict)
    student_announcements       = djongo_models.JSONField(default=dict)
    student_education_details   = djongo_models.JSONField(default=list)
    student_score_details       = djongo_models.JSONField(default=dict)
    del_row                     = djongo_models.CharField(default='False',max_length=5)
    
    class Meta:
        db_table = 'students_details'
# 12
class participant(djongo_models.Model):
    session_id                  = djongo_models.CharField(max_length=20)
    student_id                  = djongo_models.CharField(max_length=20)
    display_name                = djongo_models.CharField(max_length=20)
    attended_time               = djongo_models.FloatField()
    del_row                     = djongo_models.CharField(default='False',max_length=5)

    class Meta:
        db_table = 'participant'
# 13
class logs(djongo_models.Model):
    session_id                  = djongo_models.CharField(max_length=20)
    student_id                  = djongo_models.CharField(max_length=20)
    session_start_time          = djongo_models.DateTimeField()
    session_end_time            = djongo_models.DateTimeField()
    del_row                     = djongo_models.CharField(default='False',max_length=5)

    class Meta:
        db_table = 'logs'

class trainers_details(djongo_models.Model):
    trainer_id                  = djongo_models.CharField(max_length=20, primary_key=True)
    batch_ids                   = djongo_models.JSONField(default=dict)
    trainer_education_details   = djongo_models.JSONField(default=list)
    del_row                     = djongo_models.CharField(default='False',max_length=5)
    class Meta:
        db_table = 'trainers_details'
      
class issue_details(djongo_models.Model): 
    sl_id                       = djongo_models.AutoField(primary_key=True)
    student_id                  = djongo_models.CharField(max_length=20)
    image_path                  = djongo_models.TextField()
    issue_description           = djongo_models.TextField()
    issue_status                = djongo_models.CharField(max_length=20)
    issue_type                  = djongo_models.CharField(max_length=20)
    reported_time               = djongo_models.DateTimeField()
    resolved_time               = djongo_models.DateTimeField()
    comments                    = djongo_models.JSONField(default=dict)
    del_row                     = djongo_models.CharField(default='False',max_length=5)

    class Meta:
        db_table = 'issue_details'
    
class ErrorLogs(djongo_models.Model):
    Error_id        = djongo_models.AutoField(primary_key=True)
    student_id       = djongo_models.CharField(max_length=15)
    Email           = djongo_models.EmailField()
    Name            = djongo_models.CharField(max_length=25)
    Occurred_time = djongo_models.DateTimeField()
    URL_and_Body    = djongo_models.TextField()
    Error_msg       = djongo_models.TextField()
    Stack_trace     = djongo_models.TextField()
    User_agent      = djongo_models.TextField()
    Operating_sys   = djongo_models.TextField()

    class Meta:
        db_table = 'ErrorLogs'