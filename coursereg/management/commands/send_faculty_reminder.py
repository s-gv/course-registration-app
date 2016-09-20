from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
import random, string
from coursereg import models
from bheemboy import settings
from django.db.models import Q, Count
import csv

class Command(BaseCommand):
    help = 'Looks up current semester registrations and sends an e-mail reminder to the Faculty for the pending actions if any.'

    def handle(self, *args, **options):
        adviser_pending = models.Participant.objects.filter(
            participant_type=models.Participant.PARTICIPANT_STUDENT,
            is_adviser_approved=False,
        ).values('user__adviser').annotate(num_pending=Count('user__adviser'))
    
        courses_pending = models.Participant.objects.filter(
            participant_type=models.Participant.PARTICIPANT_STUDENT,
            is_adviser_approved=True,
            is_instructor_approved=False
        ).values_list('course', flat=True)
    
        instructor_pending = models.Participant.objects.filter(
            participant_type=models.Participant.PARTICIPANT_INSTRUCTOR,
            course__in=courses_pending
        ).values('user').annotate(num_courses=Count('user'))
    
        faculty_pending = set([p['user__adviser'] for p in adviser_pending] + [p['user'] for p in instructor_pending])
        msg = 'Please review pending approvals in the Coursereg website.'
        mail_send_failed = False
        for faculty_id in faculty_pending:
            faculty = models.User.objects.get(id=faculty_id)
            try:
                send_mail('Coursereg notification', msg, settings.DEFAULT_FROM_EMAIL, [faculty.email])
            except:
                mail_send_failed = True
                print 'Could not send the mail to' + str([faculty.email])
                break
    
