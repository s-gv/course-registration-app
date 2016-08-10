from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, datetime
from coursereg import models
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import PermissionDenied
from django.utils.http import urlquote_plus, urlunquote_plus

def parse_datetime_str(date_str):
    naive_date_str = ' '.join(date_str.split(' ')[:5])
    offset_str = date_str.split(' ')[5][-5:]
    offset_name = str(date_str.split(' ')[5][:-5])
    naive_dt = datetime.strptime(naive_date_str, '%a %b %d %Y %H:%M:%S')
    offset = int(offset_str[-4:-2])*60 + int(offset_str[-2:])
    if offset_str[0] == "-":
        offset = -offset
    return naive_dt.replace(tzinfo=timezone.FixedOffset(offset, offset_name))


def datetime_to_str(datetime):
    return datetime.strftime('%a %b %d %Y %H:%M:%S %z (%Z)')

def get_state_desc(participant):
    if participant.is_drop:
        return 'Dropped this course'
    if not participant.is_adviser_approved:
        return 'Awaiting adviser review'
    if not participant.is_instructor_approved:
        return 'Adviser has approved. Awaiting instructor review'
    if participant.grade.id == models.get_default_grade():
        return 'Registered'
    else:
        return participant.grade
    return 'Unknown state'
