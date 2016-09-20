from django.core.management.base import BaseCommand, CommandError
import random, string
from coursereg.models import User, Department, Degree, Participant, Course
import csv

class Command(BaseCommand):
    help = 'Fetch the list of courses taken by the students and print to a csv file.'

    def add_arguments(self, parser):
        parser.add_argument('--out_csv_file', default='coursereg/data/ece_coursereg_out.csv', help='File to dump the student course registration data from (default: coursereg/data/ece_coursereg_out.csv)')

    def handle(self, *args, **options):
        print 'This will read out the course plan of students in the prevous semster.'
	dcc_review_pending_list = []
	users_course_list = []
	for u in User.objects.filter(user_type=User.USER_TYPE_STUDENT).order_by('-is_active', '-date_joined'):
            if(u.is_dcc_review_pending):
		dcc_review_pending_list.append(u)
            else:
		user_obj = [u, u.full_name, u.degree, u.sr_no]
		credit_course_list = []
		audit_course_list  = []
                for p in Participant.objects.filter(user=u):
		    if(p.grade == Participant.GRADE_NA and p.state == Participant.STATE_CREDIT and p.is_adviser_approved and p.is_instructor_approved and (not p.course.is_last_grade_date_passed()) and p.course.term == Course.TERM_AUG and p.course.last_reg_date.year==2016):
                        credit_course_list.append([p, p.course.num, p.course.title])
                    elif(p.grade == Participant.GRADE_NA and p.state == Participant.STATE_AUDIT and p.is_adviser_approved and p.is_instructor_approved and (not p.course.is_last_grade_date_passed()) and p.course.term == Course.TERM_AUG and p.course.last_reg_date.year==2016):
                        audit_course_list.append([p, p.course.num, p.course.title])
		user_obj.append(credit_course_list)
		user_obj.append(audit_course_list)
                users_course_list.append(user_obj)
	
	print 'Following is the list of courses taken by students'
	print users_course_list

        print 'The following students still have DCC review pending  on their course plan!!!'
        print dcc_review_pending_list

	with open(options['out_csv_file'],'wb') as csvfile:
	    csvwriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
	    for user_obj in users_course_list:
                user_name   = user_obj[1]
                user_email  = user_obj[0]
                user_degree = user_obj[2]
                user_sr_no  = user_obj[3]
                user_credit_list    = ''
                num_credit_courses  = 0
                for course in user_obj[4]:
                    course_num  = course[1]
                    course_name = course[2]
                    course_str  = str(course_num) + '-' + str(course_name)
                    user_credit_list = user_credit_list+ course_str + ';'
                    num_credit_courses += 1
                user_audit_list    = ''
                num_audit_courses  = 0
                for course in user_obj[5]:
                    course_num  = course[1]
                    course_name = course[2]
                    course_str  = str(course_num) + '-' + str(course_name)
                    user_audit_list = user_audit_list+ course_str + ';'
                    num_audit_courses += 1
                csvwriter.writerow([user_name, user_email,user_degree, user_sr_no, str(num_credit_courses), user_credit_list, str(num_audit_courses) , user_audit_list])
                     
