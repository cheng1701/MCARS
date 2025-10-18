from django.db import models
from django.conf import settings
from django.utils import timezone


class Event(models.Model):
    """Calendar event visible across the organization and filterable by unit hierarchy."""
    SCOPE_FLEET = 'fleet'
    SCOPE_QUADRANT = 'quadrant'
    SCOPE_SECTOR = 'sector'
    SCOPE_UNIT = 'unit'

    SCOPE_CHOICES = [
        (SCOPE_UNIT, 'Unit only'),
        (SCOPE_SECTOR, 'Sector'),
        (SCOPE_QUADRANT, 'Quadrant'),
        (SCOPE_FLEET, 'Fleet-wide'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    location = models.CharField(max_length=255, blank=True)
    meeting_url = models.URLField(blank=True)
    image = models.ImageField(upload_to='event_images/', null=True, blank=True)

    # owning/hosting unit for filtering and permissions
    unit = models.ForeignKey('units.Unit', on_delete=models.CASCADE, related_name='events')
    visibility_scope = models.CharField(max_length=16, choices=SCOPE_CHOICES, default=SCOPE_UNIT)

    # host of the event (optional)
    host = models.ForeignKey('Members.Member', on_delete=models.SET_NULL, null=True, blank=True, related_name='events_hosting', help_text='Primary host of the event')

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='events_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='events_updated')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_datetime']

    def __str__(self):
        return f"{self.title} @ {self.start_datetime:%Y-%m-%d %H:%M}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_datetime and self.start_datetime and self.end_datetime < self.start_datetime:
            raise ValidationError({'end_datetime': 'End time must be after start time.'})

    def notify_attendees(self, action: str):
        """Email attendees about create/update/delete actions."""
        from django.core.mail import send_mail
        subject = f"Event {action}: {self.title}"
        lines = [
            f"Title: {self.title}",
            f"Starts: {timezone.localtime(self.start_datetime).strftime('%Y-%m-%d %H:%M')}",
            f"Ends: {timezone.localtime(self.end_datetime).strftime('%Y-%m-%d %H:%M')}",
        ]
        if self.location:
            lines.append(f"Location: {self.location}")
        if self.meeting_url:
            lines.append(f"Meeting: {self.meeting_url}")
        if self.host:
            try:
                lines.append(f"Host: {self.host.get_ranked_name()}")
            except Exception:
                lines.append(f"Host: {self.host.user.get_full_name()}")
        body = "\n".join(lines)
        recipients = [a.member.user.email for a in self.attendees.select_related('member__user').all() if a.member and a.member.user and a.member.user.email]
        if not recipients:
            return
        try:
            send_mail(subject, body, None, recipients, fail_silently=True)
        except Exception:
            # Avoid breaking core flow due to email issues
            pass


class EventAttendee(models.Model):
    STATUS_INVITED = 'invited'
    STATUS_GOING = 'going'
    STATUS_MAYBE = 'maybe'
    STATUS_DECLINED = 'declined'

    STATUS_CHOICES = [
        (STATUS_INVITED, 'Invited'),
        (STATUS_GOING, 'Going'),
        (STATUS_MAYBE, 'Maybe'),
        (STATUS_DECLINED, 'Declined'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendees')
    member = models.ForeignKey('Members.Member', on_delete=models.CASCADE, related_name='event_attendances')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_INVITED)
    role = models.CharField(max_length=100, blank=True, help_text='Optional role, e.g., Speaker, Host')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('event', 'member')]
        ordering = ['event__start_datetime', 'member__user__last_name']

    def __str__(self):
        return f"{self.member} -> {self.event} ({self.status})"
