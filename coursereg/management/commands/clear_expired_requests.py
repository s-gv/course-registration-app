from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from datetime import date
from coursereg.models import Participant, User, Notification
from django.core.mail import send_mail
from django.utils import timezone

def delete_participants(expired_participants):
    count = 0
    should_send_mail = True
    for participant in expired_participants:
        msg = 'Cancelled application for %s because the last registration date has passed.' % participant.course
        Notification.objects.create(
            user=participant.user,
            origin=Notification.ORIGIN_OTHER,
            message=msg,
        )
        if should_send_mail:
            try:
                send_mail('Coursereg notification', msg, settings.DEFAULT_FROM_EMAIL, [participant.user.email])
            except:
                should_send_mail = False
        participant.delete()
        count += 1
    return count

class Command(BaseCommand):
    help = '''Delete enrolment requests past the last registration date that are not approved by adviser/instructor.
    Also sends a notification upon deletion.'''

    def handle(self, *args, **options):
        expired_adviser_participants = Participant.objects.filter(
            is_adviser_approved=False,
            course__last_adviser_approval_date__lt=timezone.now(), participant_type=Participant.PARTICIPANT_STUDENT)
        count = delete_participants(expired_adviser_participants)

        expired_instructor_participants = Participant.objects.filter(
            is_instructor_approved=False,
            course__last_instructor_approval_date__lt=timezone.now(), participant_type=Participant.PARTICIPANT_STUDENT)
        count += delete_participants(expired_instructor_participants)

        self.stdout.write(self.style.SUCCESS(
            'Cleared %s expired enrolment applications.' % count
        ))
