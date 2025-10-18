from django import forms
from django.core.exceptions import ValidationError
from Members.models import Member
from units.models import Unit
from .models import Event, EventAttendee


class EventForm(forms.ModelForm):
    attendees = forms.ModelMultipleChoiceField(
        queryset=Member.objects.select_related('user').all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )

    include_subordinates = forms.BooleanField(
        required=False,
        initial=True,
        help_text='Show subordinate units on calendar view',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Event
        fields = [
            'title', 'description', 'unit', 'visibility_scope', 'host',
            'start_datetime', 'end_datetime', 'location', 'meeting_url', 'image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'visibility_scope': forms.Select(attrs={'class': 'form-select'}),
            'host': forms.Select(attrs={'class': 'form-select'}),
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'meeting_url': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_datetime')
        end = cleaned.get('end_datetime')
        if start and end and end < start:
            raise ValidationError({'end_datetime': 'End time must be after start time.'})
        return cleaned

    def save_with_attendees(self, user):
        event = self.save(commit=False)
        if not event.pk:
            event.created_by = user
        event.updated_by = user
        event.save()
        # Update attendees
        selected = set(self.cleaned_data.get('attendees', []))
        current = set(Member.objects.filter(event_attendances__event=event))
        to_add = selected - current
        to_remove = current - selected

        for member in to_add:
            EventAttendee.objects.get_or_create(event=event, member=member)
        # Ensure host is an attendee (role Host)
        host = getattr(event, 'host', None)
        if host and host not in selected:
            EventAttendee.objects.get_or_create(event=event, member=host, defaults={'status': EventAttendee.STATUS_GOING, 'role': 'Host'})
        else:
            # If host is in attendees, try to set their role to Host (non-destructive)
            if host:
                try:
                    ea = EventAttendee.objects.get(event=event, member=host)
                    if not ea.role:
                        ea.role = 'Host'
                        ea.save(update_fields=['role'])
                except EventAttendee.DoesNotExist:
                    pass
        # Remove obsolete attendees
        if to_remove:
            EventAttendee.objects.filter(event=event, member__in=list(to_remove)).delete()
        return event
