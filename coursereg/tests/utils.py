from django.contrib import messages

def is_error_msg_present(response):
    for message in response.context['messages']:
        if message.level == messages.ERROR:
            return True
