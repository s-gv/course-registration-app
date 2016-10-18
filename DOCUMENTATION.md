# Coursereg
- [Overview](#overview)
- [Features](#features)
- [Dependencies](#dependencies)
- [How to deploy](#how-to-deploy)
- [Management commands](#management-commands)
- [Settings](#settings)
- [DB Schema](#db-schema)
- [Misc](#misc)

## Overview
Coursereg is a webapp for managing course registrations at academic institutions. Students can register for courses on the Coursereg website. The registrations can be reviewed by the student's adviser, the relevant course instructor, and department admins. After the registration is complete, students can opt to change the registration type (Credit, Audit, etc.) or drop the course within the specified date. On completion of the course, instructors can assign grades.

There are four types of users in this webapp: (1) Student (2) Faculty (3) Department admin (4) Superuser. Faculty have two roles: (1) Adviser (2) Instructor. They can review courses taken by their advisees and have access to a list of students who have applied for a course they are instructing. A department admin has access to every course taken by a student in a department and can generate reports for the entire department. The superuser has full database access and can login as any other user in the system.

TODO: A YouTube screencast.

## Features
- E-mail notification is sent when a course is dropped.
- Bulk upload users, courses from a CSV file.
- Superuser can login as any user.
- Department-wise report in CSV/PDF.
- Faculty can export registered students to PDF/CSV.
- Layout is mobile friendly.

## Dependencies
- Python 2.7
- django 1.9

## How to deploy
- Obtain a stable [release](https://github.com/s-gv/bheemboy/releases).
- We recommend [PostgreSQL](http://www.postgresql.org/) for production use. Install it, create a database and a user. For the user, set the client encoding to utf-8, default transaction isolation to read committed, timezone to UTC, and grant the user all privileges for the DB.
- Edit `<proj_root>/bheemboy/settings.py` and give a value to `SECRET_KEY`, add auth details to `DATABASES`, set `DEBUG` to False, SMTP server in `EMAIL_HOST`, admin email in `DEFAULT_FROM_EMAIL`, and add the hostname (such as `coursereg.iisc.ac.in`) to `ALLOWED_HOSTS`. The [django documentation](https://docs.djangoproject.com/en/1.9/ref/settings/) has more details about the various settings.
- In `<proj_root>/`, run `python manage.py collectstatic` to collect all static files in `<proj_root>/static`.
- In `<proj_root>/`, run `python manage.py migrate` to update the database.
- Create a superuser with `python manage.py createsuperuser`.
- Set-up a production-grade webserver such as `gunicorn` to run on start-up and configure a reverse proxy like `nginx` to proxy requests to it.
- Set-up the server to serve static files at `/static/*` from `<proj_root>/bheemboy/coursereg/static/*`.

## Management commands
- To bulk load FAQs in `<project_root>/coursereg/data/faqs.json`, run `python manage.py loadfaqs --datafile coursereg/data/faqs.json`.
- To bulk load departments in `<project_root>/coursereg/data/depts.json`, run `python manage.py loaddepts --datafile coursereg/data/depts.json`.
- To bulk load degree programs in `<project_root>/coursereg/data/degrees.json`, run `python manage.py loaddegrees --datafile coursereg/data/degrees.json`.
- To bulk load grades in `<project_root>/coursereg/data/grades.json`, run `python manage.py loadgrades --datafile coursereg/data/grades.json`.
- To bulk load academic terms in `<project_root>/coursereg/data/terms.json`, run `python manage.py loadterms --datafile coursereg/data/terms.json`.
- To bulk load registration types in `<project_root>/coursereg/data/registration_types.json`, run `python manage.py loadregtypes --datafile coursereg/data/registration_types.json`. Note that you must have at least one registration type for the application to operate properly.

## Settings
These options can be configured in `bheemboy/settings.py`

- Key: `CAN_FACULTY_CREATE_COURSES`
  - Value: `True` to permit course creation by faculty
  - Value: `False` to disable course creation by faculty
- Key: `CAN_ADVISER_ADD_COURSES_FOR_STUDENTS`
  - Value: `True` to permit faculty to add courses on behalf of their advisees
  - Value: `False` to not allow faculty to add courses for their advisees
- Key: `CONTACT_EMAIL`
  - Value: the e-mail address to be displayed on the login page (ex: `admin@example.com`).
- Key: `MANUAL_FACULTY_REVIEW`
  - Value: `True` to have faculty manually click on course applications to mark them as reviewed.
  - Value: `False` to automatically mark as reviewed once faculty views a course application.

## DB Schema
Tables with sample rows:

### Course
|   Num   |            Title           |         Created_at         |         Updated_at         | Department_id |    Timings     | Term_id | Should_count_towards_cgpa |  credits |
|---------|:---------------------------|:---------------------------|:---------------------------|:--------------|:--------|:--------|:--------------------------|:-----|
|  E0-284 | Math for Graduate Students | 2016-07-15 15:52:05.924628 | 2016-10-18 07:37:43.506123 |       1       | M & W, 8:30 to 10:00 |     1      |         True       |  3:0 |
|  E0-232 |      Digital Circuits      | 2016-07-15 15:52:29.914621 | 2016-10-18 07:37:43.507363 |       1       | T & Th, 2:30 to 04:00 |     1      |        True       |  3:0 |


### Department
|                Name                  | Abbreviation | is_active |
|--------------------------------------|:-------------|:----------|
| Electrical Communication Engineering |      ECE     |   True    |
| Center for Neuroscience              |      CNS     |   True    |

### Degree
| Name  | is_active |
|-------|:----------|
| PhD   |   True    |
| MTech |   True    |
| ME    |   False   |

### Grade
|  Name   | Points | should_count_towards_cgpa | is_active |
|---------|--------|---------------------------|-----------|
| S grade |  8.0   |        True               |  True     |
| A grade |  7.0   |        True               |  True     |

### RegistrationType
|   Name   | should_count_towards_cgpa | is_active |
|----------|---------------------------|-----------|
|  Credit  |          True             |   True    |
|  Audit   |          True             |   True    |

### Faq
|  faq_for  |          question        |          answer           |
|-----------|--------------------------|---------------------------|
|  STUDENT  | Question from student?   | Sample answer             |
|  FACULTY  | Question from faculty?   | Sample answer 2           |

### Notification
|      user       |  origin  |          message          | is_student_acknowledged | is_adviser_acknowledged | is_dcc_acknowledged | created_at |
|-----------------|----------|---------------------------|-------------------------|-------------------------|---------------------|------------|
|  user1@abc.com  | ADVISER  | Enrolled for Course X     |           False         |          False          |        False        |  8/7/2016  |
|  user2@abc.com  | DCC      | Too few courses           |           False         |          False          |        False        |  8/9/2016  |

### Participant 
| Participant_type | Is_adviser_reviewed | Is_instructor_reviewed | Course_id | User_id | Lock_from_student | Is_Drop | Should_count_towards_cgpa | registration_type_id | grade_id | created_at | updated_at |
|------------------|:-------------------|:----------------------|:----------|:--------|:------------------|:--------|:----------------|:---------------|:-------|:-------|:-------|
|         1        |       False        |          False        |    1      |    2    |       False       |  False  |   True               |    1    |   NULL  |   2016-10-18 07:37:43.510979    |   2016-10-18 07:37:43.511042  |
|         1        |       False        |          False        |    2      |    2    |       False       |  False  |   True               |    1    |   NULL  |   2016-10-18 07:37:43.512202    |   2016-10-18 07:37:43.512202  |

### Term
|     name    | year | start_reg_date | last_reg_date | last_adviser_approval_date | last_instructor_approval_date | last_cancellation_date | last_conversion_date | last_drop_date | last_grade_date | is_active |
|-------------|:-----|:---------------|:--------------|:---------------------------|:------------------------------|:------------------|:--------------------|:-------------|:-------------|:---------|
| Aug-Dec | 2016 | 2016-05-20 15:51:20 | 2016-08-18 15:51:20 | 2016-08-18 15:51:20 | 2016-08-18 15:51:20 | 2016-08-23 15:51:20 | 2016-09-01 15:51:20 | 2016-09-01 15:51:20 | 2017-01-15 15:51:20 | True |

### User
| password | last_login | is_superuser | email | full_name | user_type | date_joined | sr_no | is_dcc_review_pending | is_staff | is_active | degree_id | department_id | telephone | is_dcc_sent_notification | adviser_id |
|----------|:-----------|:-------------|:-----|:----------|:----------|:------------|:------|:----------------------|:--------|:----------|:----------|:--------------|:----------|:-------------------------|:-----------|
| pbkdf2_sha256$24000$x3iHzLjgxeYw$FrCkSKxIgm8bvCB8br3f4Hypvc812EemmDk4B+djo2s= | 2016-10-18 15:32:45.757052 | False | dcc@ece.iisc.ernet.in | DCC | 2 | 2016-07-15 06:39:10 | - | False | False | True | NULL | 1 | - | False | NULL |
| pbkdf2_sha256$24000$VOdb7wPGcURj$HMlm8c8Q00TTJeEyXesnDyR8LTU3PsnCYLAkKxL+Ayo= | 2016-10-18 07:39:12.092271 | False | ben@ece.iisc.ernet.in | Ben Bitdiddle | 0 | 2016-07-15 06:38:16 | 04-02-01-10-41-2-12345 | False | False | True | 1 | 1 | 9912378901 | False | 2 | 
 
### User Groups
| User_id | Group_id |
|---------|:---------|

### User permissions
| User_id | Permission_id |
|---------|:--------------|

## Misc
- At least one registration type (ex: Credit, Audit) and Degree (ex: PhD, ME) must be added by the admin before students can login and register for courses.
- A fatal error occurs if a student with `adviser` NULL logs in. Always assign `adviser` when creating student users.
