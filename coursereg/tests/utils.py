from coursereg.models import User
from django.contrib import messages

def is_error_msg_present(response):
    for message in response.context['messages']:
        if message.level == messages.ERROR:
            return True

def create_user(email, password, user_type, adviser):
    u = User.objects.create(email=email, user_type=user_type, adviser=adviser)
    u.set_password(password)
    u.save()
    return u
