from django.db import models

# Create your models here.
# 1
class tracks(models.Model):
    track_id = models.CharField(max_length=20, unique=True)
    track_name = models.CharField(max_length=50)
    track_name_searchable = models.CharField(max_length=50)
    track_description = models.TextField()
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_by = models.CharField(max_length=100, null=True, blank=True)
    modified_at = models.DateTimeField(auto_now=True)
    action = models.CharField(max_length=100, null=True, blank=True)
    del_row = models.BooleanField(default=False)
    def __str__(self):
        return self.track_name
    class Meta:
        db_table = 'tracks'
# 2
class subjects(models.Model):
    subject_id = models.CharField(max_length=20, unique=True)
    track_id = models.ForeignKey(tracks, on_delete=models.CASCADE)
    subject_name = models.TextField()
    subject_alt_name = models.TextField()
    subject_description = models.TextField()
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_by = models.CharField(max_length=100, null=True, blank=True)
    modified_at = models.DateTimeField(auto_now=True)
    action = models.CharField(max_length=100, null=True, blank=True)
    del_row = models.BooleanField(default=False)


    def __str__(self):
        return self.subject_name

    class Meta:
        db_table = 'subjects'
# 3
class topics(models.Model):
    topic_id = models.CharField(max_length=20, unique=True)
    subject_id = models.ForeignKey(subjects, on_delete=models.CASCADE)
    topic_name = models.CharField(max_length=50)
    topic_alt_name = models.CharField(max_length=50, null=True, blank=True)
    topic_description = models.TextField()
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_by = models.CharField(max_length=100, null=True, blank=True)
    modified_at = models.DateTimeField(auto_now=True)
    action = models.CharField(max_length=100, null=True, blank=True)
    del_row = models.BooleanField(default=False)

    def __str__(self):
        return self.topic_name
    class Meta:
        db_table = 'topics'
# 4
class sub_topics(models.Model):
    sub_topic_id = models.CharField(max_length=20, unique=True)
    topic_id = models.ForeignKey(topics, on_delete=models.CASCADE)
    sub_topic_name = models.CharField(max_length=50)
    sub_topic_description = models.TextField()
    sub_topic_alt_name= models.CharField(max_length=50, null=True, blank=True)
    notes = models.IntegerField(null=True, blank=True)
    videos = models.IntegerField(null=True, blank=True)
    mcq = models.IntegerField(null=True, blank=True)
    coding = models.IntegerField(null=True, blank=True)
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_by = models.CharField(max_length=100, null=True, blank=True)
    modified_at = models.DateTimeField(auto_now=True)
    action = models.CharField(max_length=100, null=True, blank=True)
    del_row = models.BooleanField(default=False)

    def __str__(self):
        return self.sub_topic_name
    
    class Meta:
        db_table = 'sub_topics'

# 5
class courses(models.Model):
    course_id = models.CharField(max_length=20, unique=True)
    course_name = models.CharField(max_length=50)
    course_description = models.TextField()
    course_level = models.CharField(max_length=20)
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_by = models.CharField(max_length=100, null=True, blank=True)
    modified_at = models.DateTimeField(auto_now=True)
    action = models.CharField(max_length=100, null=True, blank=True)
    tracks= models.TextField(default=None, blank=True, null=True)
    del_row = models.BooleanField(default=False)

    def __str__(self):
        return self.course_name

    class Meta:
        db_table = 'courses'
# 6
class course_subjects(models.Model):
    course_id = models.ForeignKey(courses, on_delete=models.CASCADE)
    subject_id = models.ForeignKey(subjects, on_delete=models.CASCADE)
    duration_in_days = models.CharField(max_length=20)
    start_date = models.DateTimeField(default=None )
    end_date = models.DateTimeField(default=None)
    is_mandatory = models.BooleanField()
    path = models.CharField(max_length=250)
    del_row = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.course_id.course_name} - {self.subject_id.subject_name}"
    class Meta:
        db_table = 'course_subjects'
# 7 
class course_plan_details(models.Model):
    course_id = models.ForeignKey(courses, on_delete=models.CASCADE)
    subject_id = models.ForeignKey(subjects, on_delete=models.CASCADE)
    day = models.IntegerField()
    content_type = models.CharField(max_length=20)
    week = models.IntegerField()
    day_date = models.DateTimeField()
    duration_in_hours = models.IntegerField()
    del_row = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.course_id.course_name} - {self.subject_id.subject_name}"
    class Meta:
        db_table = 'course_plan_details'
# 8
class batches(models.Model):
    batch_id = models.CharField(max_length=20, primary_key=True)
    course_id = models.ForeignKey(courses, on_delete=models.CASCADE)
    batch_name = models.CharField(max_length=50)
    delivery_type = models.CharField(max_length=50, choices=[("Online", "Online"), ("In-person", "In-person"), ("Hybrid", "Hybrid")])
    max_no_of_students = models.IntegerField()
    start_date = models.DateTimeField()
    indicative_date = models.DateTimeField()
    del_row = models.BooleanField(default=False)

    def __str__(self):
        return self.batch_name
    class Meta:
        db_table = 'batches'
# 9
class students_info(models.Model):
    student_id = models.CharField(max_length=20, primary_key=True)
    course_id = models.ForeignKey(courses,  on_delete=models.SET_NULL, null=True)
    student_firstname = models.CharField(max_length=100)
    student_lastname = models.CharField(max_length=100)
    student_email = models.EmailField()
    student_country = models.CharField(max_length=100)
    student_state = models.CharField(max_length=100)
    student_city = models.CharField(max_length=100)
    student_gender = models.CharField(max_length=10)
    student_course_starttime = models.DateTimeField(null=True)
    student_pincode = models.CharField(max_length=20)
    student_alt_phone=models.CharField(max_length=20)
    isActive=models.BooleanField(default=True)
    student_dob=models.DateField(default=None, null=True)
    student_qualification=models.CharField(max_length=100)
    batch_id = models.ForeignKey(batches,  on_delete=models.SET_NULL, null=True,default=None)
    college = models.CharField(max_length=50)
    branch = models.CharField(max_length=50)
    address = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    student_score = models.CharField(max_length=20)
    student_catogory = models.CharField(max_length=20, choices=[("SUN", "SUN"), ("MOON", "MOON"), ("STAR", "STAR")],default="STAR")
    student_college_rank = models.IntegerField(default=-1)
    student_overall_rank = models.IntegerField(default=-1)
    student_type = models.CharField(max_length=20)
    linkedin = models.CharField(max_length=100, blank=True, null=True)
    leetcode = models.CharField(max_length=100, blank=True, null=True)
    hackerrank = models.CharField(max_length=100, blank=True, null=True)
    allocate=models.BooleanField(default=False)
    del_row = models.BooleanField(default=False)
    class Meta:
        db_table = 'students_info'
# 10
class trainers(models.Model):
    trainer_id = models.CharField(max_length=20, primary_key=True)
    trainer_name = models.CharField(max_length=100)
    trainer_email = models.EmailField()
    gender = models.CharField(max_length=10)
    # trainer_college = models.CharField(max_length=50)
    # trainer_branch = models.CharField(max_length=50)
    address = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    # trainer_score = models.CharField(max_length=20)
    trainer_type = models.CharField(max_length=20)
    linkedin = models.CharField(max_length=100, blank=True, null=True)
    leetcode = models.CharField(max_length=100, blank=True, null=True)
    hackerrank = models.CharField(max_length=100, blank=True, null=True)
    del_row = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.trainer_name}"
    class Meta:
        db_table = 'trainers'

# 11
class trainer_review_comments(models.Model):
    comment_id = models.CharField(max_length=20, primary_key=True)
    student_id = models.ForeignKey(students_info,  on_delete=models.SET_NULL, null=True)
    trainer_id = models.ForeignKey(trainers, on_delete=models.SET_NULL, null=True)
    review_type = models.CharField(max_length=20)
    reason = models.CharField(max_length=20)
    comment = models.CharField(max_length=20)
    date_time = models.DateTimeField()
    del_row = models.BooleanField(default=False)

    class Meta:
        db_table = 'trainer_review_comments'

# 12
class test_details(models.Model):
    test_id = models.CharField(max_length=20, primary_key=True)
    test_name = models.CharField(max_length=50)
    test_duration = models.CharField(max_length=20)
    test_marks = models.IntegerField()
    test_type = models.CharField(max_length=20)
    test_description = models.CharField(max_length=250)
    test_created_by = models.CharField(max_length=20)
    track_id =  models.ForeignKey(tracks, on_delete=models.SET_NULL, null=True)
    course_id = models.ForeignKey(courses, on_delete=models.SET_NULL, null=True)
    subject_id = models.ForeignKey(subjects, on_delete=models.SET_NULL, null=True)
    level = models.CharField(max_length=20)
    tags = models.CharField(max_length=20)
    test_date_and_time = models.DateTimeField()
    del_row = models.BooleanField(default=False)

    def __str__(self):
        return self.test_name

    class Meta:
        db_table = 'test_details'
# 13
class questions(models.Model):
    question_id = models.CharField(max_length=20, primary_key=True)
    question_type = models.CharField(max_length=20)
    level = models.CharField(max_length=20)
    created_by = models.CharField(max_length=100)
    creation_time = models.DateTimeField(auto_now_add=True)
    last_updated_time = models.DateTimeField(auto_now=True)
    last_updated_by = models.CharField(max_length=100,null=True, blank=True)
    reviewed_by = models.CharField(max_length=20, null=True, blank=True)
    tags = models.CharField(max_length=20, null=True, blank=True)
    sub_topic_id = models.ForeignKey(sub_topics, on_delete=models.SET_NULL, null=True)
    del_row = models.BooleanField(default=False)

    class Meta:
        db_table = 'questions'
# 14
class test_sections(models.Model):
    test_id = models.ForeignKey(test_details, on_delete=models.CASCADE, db_column="Test_id")
    section_name = models.CharField(max_length=20)
    topic_id = models.ForeignKey(topics, on_delete=models.SET_NULL, null=True)
    sub_topic_id = models.ForeignKey(sub_topics, on_delete=models.SET_NULL, null=True)
    question_id = models.ForeignKey(questions, on_delete=models.SET_NULL, null=True)
    del_row = models.BooleanField(default=False)

    class Meta:
        db_table = 'test_sections'

# 15 
class student_activities(models.Model):
    student_id = models.ForeignKey(students_info,  on_delete=models.SET_NULL, null=True)
    subject_id = models.ForeignKey(subjects,  on_delete=models.SET_NULL, null=True)
    activity_end_time = models.DateTimeField()
    activity_week = models.IntegerField()
    activity_day = models.IntegerField()
    activity_topic = models.ForeignKey(topics, on_delete=models.SET_NULL, null=True)
    activity_subtopic = models.ForeignKey(sub_topics, on_delete=models.SET_NULL, null=True)
    del_row = models.BooleanField(default=False)

    class Meta:
        db_table = 'student_activities'

# 16 
class student_app_usage(models.Model):
    student_id = models.CharField(max_length=20)
    logged_in = models.DateTimeField()
    logged_out = models.DateTimeField()
    del_row = models.BooleanField(default=False)

    class Meta:
        db_table = 'student_app_usage'
# 17    
class college_details(models.Model):
    college_id = models.CharField(max_length=20, primary_key=True)
    college_name = models.CharField(max_length=50)
    center_name = models.CharField(max_length=20)
    college_code = models.CharField(max_length=20)
    del_row = models.BooleanField(default=False)

    class Meta:
        db_table = 'college_details'
# 18
class branch_details(models.Model):
    college_id = models.CharField(max_length=20)
    branch_id = models.CharField(max_length=20)
    branch = models.CharField(max_length=20)
    del_row = models.BooleanField(default=False)

    class Meta:
        db_table = 'branch_details'

# class ranks(models.Model):
class admins(models.Model):
    admin_id = models.CharField(max_length=20, primary_key=True)
    admin_first_name = models.CharField(max_length=100)
    admin_last_name = models.CharField(max_length=100)
    admin_email = models.EmailField()
    phone = models.CharField(max_length=20)
    activity_status = models.CharField(max_length=20)
    category = models.CharField(max_length=20)
    reg_date = models.DateTimeField(auto_now_add=True)
    exp_date = models.DateTimeField(null=True, blank=True)
    del_row = models.BooleanField(default=False)
 
    class Meta:
        db_table = 'admins'