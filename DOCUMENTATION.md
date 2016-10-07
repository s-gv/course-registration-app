Coursereg
=========

- [Overview](#overview)
- [Dependencies](#dependencies)
- [How to deploy](#how-to-deploy)

Overview
--------

Coursereg is a webapp for managing course registrations. 

Dependencies
------------

- Python 2.7
- django 1.9

How to deploy
-------------

- Obtain a stable [release](https://github.com/s-gv/bheemboy/releases).
- We recommend [PostgreSQL](http://www.postgresql.org/) for production use.
Install it, create a database and a user. For the user, set the client encoding to utf-8, default transaction isolation to read committed, timezone to UTC, and grant the user all privileges for the DB.
- Edit `<proj_root>/bheemboy/settings.py` and give a value to `SECRET_KEY`, add auth details to `DATABASES`, set `DEBUG` to False, SMTP server in `EMAIL_HOST`, admin email in `DEFAULT_FROM_EMAIL`, and add the hostname (such as `coursereg.iisc.ac.in`) to `ALLOWED_HOSTS`. The [django documentation](https://docs.djangoproject.com/en/1.9/ref/settings/) has more details about the various settings.
- In `<proj_root>/`, run `python manage.py collectstatic` to collect all static files in `<proj_root>/static`.
- In `<proj_root>/`, run `python manage.py migrate` to update the database.
- Create a superuser with `python manage.py createsuperuser`.
- Set-up a production-grade webserver such as `gunicorn` to run on start-up and configure a reverse proxy like `nginx` to proxy requests to it.
- Set-up the server to serve static files at `/static/*` from `<proj_root>/bheemboy/coursereg/static/*`.
