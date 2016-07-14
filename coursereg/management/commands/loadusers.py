from django.core.management.base import BaseCommand, CommandError
from coursereg.models import User, Department, Degree
import csv

class Command(BaseCommand):
    help = 'Bulk load departments to the database from a JSON file.'

    def add_arguments(self, parser):
        parser.add_argument('--student_csv_file', default='coursereg/data/ece_students.csv', help='File to load the student data from (default: coursereg/data/ece_students.csv)')
        parser.add_argument('--faculty_csv_file', default='coursereg/data/ece_faculty.csv', help='File to load data from (default: coursereg/data/ece_faculty.csv)')

    def handle(self, *args, **options):
        #Fixing naming inconsistencies by defining a map.
        dept_map={'CDS'   : 'Department of Computational and Data Sciences (CDS)',
                    'DESE' : 'Department of Electronic Systems Engineering (DESE)',
                    'EE'   : 'Electrical Engineering (EE)',
                    'CSA'  : 'Computer Science and Automation (CSA)',
                    'ECE'  : 'Electrical Communication Engineering (ECE)'}

        degree_map = {  'Ph.D':'PhD',
                        'M.Sc':'MSc',
                        'M.Tech':'MTech',
                        'ME':'ME',
                        'M.E':'ME'}

        print 'Loading the faculty data'
        with open(options['faculty_csv_file']) as f:
            user_reader = csv.reader(f,delimiter=',')
            line = 0;            
            for user in user_reader:
                if(line==0):
                    line += 1                 
                    continue
                else:
                    user_full_name = user[0]
                    user_email     = user[1]
                    user_type      = user[2]
                    user_sr_no     = user[3]
                    user_degree    = user[4]
                    user_dept      = user[5]
                    user_adv_email = user[6]
                    user_doj       = user[7]
                    if(user_email==''):
                         print 'Warning: Email ID not found for: '+user_full_name+'.... Hence not adding him in the database!;'
                         continue

                    if(user_type == 'Faculty'):
                        dept = dept_map[user_dept]
                        user_department = Department.objects.filter(name = dept)
                        if(not user_department):
                            print 'Warning: Department not found for: '+user_email+'.... Hence not adding him in the database!;'
                        else:
                            if(not User.objects.filter(email=user_email)):                          
                                User.objects.create_user(full_name=user_full_name, email=user_email, password='initpwd1729', user_type=User.USER_TYPE_FACULTY, department=user_department[0] )
                    else:
                        print 'Data format error!!.. Non faculty user listed in faculty_csv_file'
                        print user
    

        print 'Loading the student data'
        with open(options['student_csv_file']) as f:
            user_reader = csv.reader(f,delimiter=',')
            line=0
            for user in user_reader:
                if(line==0):
                    line += 1                    
                    continue
                else:               
                    user_full_name = user[0]
                    user_email     = user[1]
                    user_type      = user[2]
                    user_sr_no     = user[3]
                    user_degree    = user[4]
                    user_dept      = user[5]
                    user_adv_email = user[6]
                    user_doj       = user[7]       
                    if(user_email==''):
                        print 'Warning: Email ID not found for: '+user_full_name+'.... Hence not adding him in the database!;'
                        continue                       
                    if(user_type == 'Student'):
                        dept = dept_map[user_dept]
                        user_department = Department.objects.filter(name = dept)
                        if(not user_department):
                            print 'Warning: Department not found for: '+user_email+'.... Hence not adding him in the database!;'
                        else:
                            user_adviser = faculty_list = User.objects.filter(email = user_adv_email)
                            if(not user_adviser):
                                print 'Warning: Adviser not found for: '+user_email+'.... Hence not adding him in the database!;'
                            else:
                                user_program = Degree.objects.filter(name =degree_map[user_degree])
                                if(not user_program):
                                    print 'Warning: enrolled degree not found for: '+user_email+'.... Hence not adding him in the database!;'
                                else:
                                    if(not User.objects.filter(email=user_email)):
                                        User.objects.create_user(full_name=user_full_name, email=user_email, password='initpwd1234', user_type=User.USER_TYPE_STUDENT, department=user_department[0], sr_no=user_sr_no, degree=user_program[0], adviser=user_adviser[0] )
                    else:
                        print 'Data format error!!.. Non Student user listed in student_csv_file'
                        print user
        print 'Done loading data.'


