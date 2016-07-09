from coursereg.models import User

def create_user(email, password, user_type, adviser):
    u = User.objects.create(email=email, user_type=user_type, adviser=adviser)
    u.set_password(password)
    u.save()
    return u
