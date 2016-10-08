# Coursereg
- [Overview](#overview)
- [Features](#features)
- [Dependencies](#dependencies)
- [How to deploy](#how-to-deploy)
- [Management commands](#management-commands)
- [DB Schema](#db-schema)
- [URLs](#urls)
- [Misc](#misc)

## Overview
Coursereg is a webapp for managing course registrations. 
TODO: description of how it works and a link to a YouTube screencast.

## Features
- E-mail notification is sent when a course is dropped.
- Admin can bulk upload users from a CSV file.
- Admin can login as any user.
- Department-wise report in CSV/PDF.
- Faculty can export registered students in CSV/PDF.

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
TODO

## Misc
- At least one registration type (ex: Credit, Audit) must be added by the admin before other users login.
- A fatal error occurs if a user with `user_type` NULL logs in. Always assign `user_type` when creating users.
