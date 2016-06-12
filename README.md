bheemboy
========

bheemboy is a webapp for organizing course registrations at academic institutions.

Dependencies
------------

- Python 2.7
- django 1.9

How to deploy
-------------

- Obtain a stable release of bheemboy.
- We recommend [PostgreSQL](http://www.postgresql.org/) database for production use.
Install it, create a database and a user, and grant all permissions for the DB to the created user.
- Edit `<proj_root>/bheemboy/settings.py` and give a value to `SECRET_KEY`, add auth details to `DATABASES`, and set `DEBUG` to False.
- In `<proj_root>/`, run `python manage.py migrate`.
- To bulk load FAQs in `<project_root>/coursereg/data/faqs.json`, run `python manage.py loadfaqs`.
- To bulk load departments in `<project_root>/coursereg/data/depts.json`, run `python manage.py loaddepts`.
- Create a superuser with `python manage.py createsuperuser`.
- Test if the app is working by running `python manage.py runserver` and going to [localhost:8000/](http://localhost:8000/).
- Set-up a production-grade webserver such as `gunicorn` to run on start-up and configure a reverse proxy like `nginx` to proxy requests to it.
- Set-up the system to server static files at `/static/*` from `<proj_root>/bheemboy/coursereg/static/*`.

Notes for devs
--------------

- To test drive this app, run `python manage.py runserver` and goto
[localhost:8000/sudo](http://localhost:8000/sudo) to access the admin page.
- The email address of the super-user in the SQLite database shipped with this
repo is `admin@ece.iisc.ernet.in` and the password is `test12345`. Use the same
password for all accounts where possible.
- Currently simple verisons of Student, Facutly and Course(Instructor) pages have been setup through which:
    - Students can browse and  register for courses and track the approval process.
    - Advisors can view the enrolment requests from their Advisees
    - Course instructors can view all the enrolment requests in one page per course and approve them.
- You could create more user accounts(Faculty or Students) and Courses by logging in as admin (with credentials given above).
