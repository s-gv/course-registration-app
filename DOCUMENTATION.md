# Coursereg
- [Overview](#overview)
- [Features](#features)
- [Dependencies](#dependencies)
- [How to deploy](#how-to-deploy)
- [Management commands](#management-commands)
- [Config options](#config-options)
- [DB Schema](#db-schema)
- [URLs](#urls)
- [Misc](#misc)

## Overview
Coursereg is a webapp for managing course registrations at academic institutions. Students can register for courses on the Coursereg website. The registrations can be reviewed by the student's adviser, the relevant course instructor, and department admins. After the registration is complete, students can opt to change the registration type (Credit, Audit, etc.) or drop the course within the specified date. On completion of the course, instructors can assign grades.

There are four types of users in this webapp: (1) Student (2) Faculty (3) Department admin (4) Superuser. Faculty have two roles: (1) Adviser (2) Instructor. They can review courses taken by their advisees and have access to a list of students who have applied for a course they are instructing. A department admin has access to every course taken by a student in a department and can generate reports for the entire department. The superuser has full database access and can login as any other user in the system. 

TODO: A YouTube screencast.

## Features
- E-mail notification is sent when a course is dropped.
- Bulk upload users from a CSV file.
- Superuser can login as any user.
- Department-wise report in CSV/PDF.
- Faculty can export registered students in CSV/PDF.
- Layout is mobile friendly.

TODO: Rest of features worth mentioning.

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
- To bulk load configs in `<project_root>/coursereg/data/configs.json`, run `python manage.py loadconfigs --datafile coursereg/data/configs.json`.

## Config options
These options can be configured by the superuser in the admin interface.

- Key: `can_faculty_create_courses`
  - Value: `1` to permit course creation by faculty
  - Value: `0` to disable course creation by faculty
- Key: `can_adviser_add_courses_for_students`
  - Value: `1` to permit faculty to add courses on behalf of their advisees
  - Value: `0` to not allow faculty to add courses for their advisees
- Key: `contact_email`
  - Value: the e-mail address to be displayed on the login page (ex: `admin@example.com`).
- Key: `num_days_before_last_reg_date_course_registerable`
  - Value: An integer number of days before the last registration date that students can begin registering for courses (ex: `60`).

## DB Schema
Tables with sample rows:

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

TODO: Rest of the tables

## URLS
Note: These URLs may change in even minor revisions and are not to be used as a public API.

- `/participants/<participant_id>/delete`
  - Participant row with ID `<participant_id>` is deleted if the user signed in is authorized to perform the action.
  - POST only. 
  - Parameters: 
    - `next` (optional) - URL to re-direct to. Defaults to the index page.

TODO: Rest of URLs

## Misc
- At least one registration type (ex: Credit, Audit) must be added by the admin before other users login.
- A fatal error occurs if a student with `adviser` NULL logs in. Always assign `adviser` when creating student users.
