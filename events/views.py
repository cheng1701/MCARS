from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Q
from django.http import HttpResponseForbidden

from units.models import Unit
from Members.models import Member
from .models import Event, EventAttendee
from .forms import EventForm
from .utils import can_manage_events, unit_descendant_ids, user_is_events_manager, user_can_view_event, event_audience_root


def calendar(request):
    """Public calendar view with filters and a true month-grid calendar.
    Query params:
      - scope: fleet|quadrant|sector|unit (default fleet)
      - unit: unit id for filtering (optional)
      - include_sub: 1/0 include subordinate units (default 1)
      - from/to: ISO date (YYYY-MM-DD) or datetime for range filtering (optional)
      - y/m: year and month for calendar grid navigation (defaults to today if absent)
    """
    from datetime import date as _date, time as _time
    from django.utils import timezone as _tz
    import calendar as _cal

    def _parse_dt(s: str, is_end=False):
        """Parse YYYY-MM-DD or ISO datetime; return timezone-aware datetime.
        If is_end=True and only a date is provided, return end-of-day; else start-of-day.
        """
        if not s:
            return None
        try:
            # Try full datetime first
            dt = datetime.fromisoformat(s)
        except Exception:
            try:
                d = _date.fromisoformat(s)
                dt = datetime.combine(d, _time.max if is_end else _time.min)
            except Exception:
                return None
        # Make aware if naive
        if _tz.is_naive(dt):
            try:
                dt = _tz.make_aware(dt, _tz.get_current_timezone())
            except Exception:
                # Fallback to UTC awareness
                dt = _tz.make_aware(dt)
        return dt

    scope = request.GET.get('scope', 'fleet').lower()
    unit_id = request.GET.get('unit')
    include_sub = request.GET.get('include_sub', '1') == '1'

    events = Event.objects.select_related('unit', 'host__user').all()

    selected_unit = None
    if unit_id:
        try:
            selected_unit = Unit.objects.get(pk=int(unit_id))
        except (ValueError, Unit.DoesNotExist):
            selected_unit = None

    if scope in {'unit', 'sector', 'quadrant'} and selected_unit:
        ids = {selected_unit.id}
        if include_sub:
            ids = unit_descendant_ids(selected_unit)
        events = events.filter(unit_id__in=ids)
    # fleet scope shows all

    # Date range
    frm_raw = request.GET.get('from')
    to_raw = request.GET.get('to')
    frm_dt = _parse_dt(frm_raw, is_end=False)
    to_dt = _parse_dt(to_raw, is_end=True)

    if frm_dt:
        events = events.filter(end_datetime__gte=frm_dt)
    if to_dt:
        events = events.filter(start_datetime__lte=to_dt)

    events = events.order_by('start_datetime')

    # Eligibility filter
    visible_events = [e for e in events if user_can_view_event(request.user, e)]

    # ---------------- Month grid computation ----------------
    # Determine which month to display
    now_local = _tz.localtime(_tz.now())
    try:
        y = int(request.GET.get('y', now_local.year))
    except (TypeError, ValueError):
        y = now_local.year
    try:
        m = int(request.GET.get('m', now_local.month))
    except (TypeError, ValueError):
        m = now_local.month
    # Clamp month/year to valid values
    if m < 1:
        m = 1
    if m > 12:
        m = 12

    # Build a matrix of weeks (each week is 7 day dicts with date and events)
    month_cal = _cal.Calendar(firstweekday=_cal.SUNDAY).monthdayscalendar(y, m)

    # Helper to get start/end of a given date in tz-aware datetimes
    def _day_bounds(d: _date):
        start = datetime.combine(d, _time.min)
        end = datetime.combine(d, _time.max)
        if _tz.is_naive(start):
            start = _tz.make_aware(start, _tz.get_current_timezone())
        if _tz.is_naive(end):
            end = _tz.make_aware(end, _tz.get_current_timezone())
        return start, end

    weeks = []
    for week in month_cal:
        week_cells = []
        for day_num in week:
            if day_num == 0:
                week_cells.append({'date': None, 'events': []})
                continue
            d = _date(y, m, day_num)
            ds, de = _day_bounds(d)
            day_events = [e for e in visible_events if e.start_datetime <= de and e.end_datetime >= ds]
            week_cells.append({'date': d, 'events': day_events})
        weeks.append(week_cells)

    # Month navigation (prev/next)
    import math as _math
    if m == 1:
        prev_y, prev_m = y - 1, 12
    else:
        prev_y, prev_m = y, m - 1
    if m == 12:
        next_y, next_m = y + 1, 1
    else:
        next_y, next_m = y, m + 1

    month_name = _cal.month_name[m]

    units = Unit.objects.all().order_by('name')

    return render(request, 'events/calendar.html', {
        'events': visible_events,
        'weeks': weeks,
        'month_name': month_name,
        'year': y,
        'prev_y': prev_y,
        'prev_m': prev_m,
        'next_y': next_y,
        'next_m': next_m,
        'units': units,
        'selected_scope': scope,
        'selected_unit': selected_unit,
        'include_sub': include_sub,
        'from_value': frm_raw or '',
        'to_value': to_raw or '',
        'title': 'Events Calendar',
    })


def event_detail(request, event_id):
    event = get_object_or_404(Event.objects.select_related('unit', 'host__user'), pk=event_id)
    if not user_can_view_event(request.user, event):
        return HttpResponseForbidden('You are not eligible to view this event.')
    attendees = event.attendees.select_related('member__user').all()
    my_attendance = None
    if request.user.is_authenticated:
        try:
            my_attendance = attendees.get(member__user=request.user)
        except EventAttendee.DoesNotExist:
            my_attendance = None
    return render(request, 'events/event_detail.html', {
        'event': event,
        'attendees': attendees,
        'my_attendance': my_attendance,
        'can_manage': request.user.is_authenticated and can_manage_events(request.user, event.unit),
    })


@login_required
def request_attendance(request, event_id):
    """Allow an authenticated user to request attendance for an eligible event.
    Creates or updates an EventAttendee record with status 'maybe'.
    """
    event = get_object_or_404(Event, pk=event_id)
    if not user_can_view_event(request.user, event):
        return HttpResponseForbidden('You are not eligible to request attendance for this event.')
    try:
        member = request.user.member
    except Member.DoesNotExist:
        messages.error(request, 'You must have a member profile to request attendance.')
        return redirect('events:event_detail', event_id=event.id)

    if request.method == 'POST':
        attendee, created = EventAttendee.objects.get_or_create(event=event, member=member, defaults={'status': EventAttendee.STATUS_MAYBE})
        if not created and attendee.status != EventAttendee.STATUS_GOING:
            attendee.status = EventAttendee.STATUS_MAYBE
            attendee.save(update_fields=['status'])
        messages.success(request, 'Your attendance request has been sent to the host/managers.')
        return redirect('events:event_detail', event_id=event.id)
    return redirect('events:event_detail', event_id=event.id)


@login_required
def event_create(request):
    # Optional pre-selected unit
    pre_unit_id = request.GET.get('unit')
    pre_unit = None
    if pre_unit_id:
        try:
            pre_unit = Unit.objects.get(pk=int(pre_unit_id))
        except (ValueError, Unit.DoesNotExist):
            pre_unit = None

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            unit = form.cleaned_data['unit']
            if not can_manage_events(request.user, unit):
                messages.error(request, 'You do not have permission to create events for this unit.')
                return redirect('events:calendar')
            event = form.save_with_attendees(request.user)
            event.notify_attendees('created')
            messages.success(request, 'Event created.')
            return redirect('events:event_detail', event_id=event.id)
    else:
        initial = {}
        if pre_unit:
            initial['unit'] = pre_unit
        form = EventForm(initial=initial)

    return render(request, 'events/event_form.html', {
        'form': form,
        'title': 'Create Event',
    })


@login_required
def event_edit(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if not can_manage_events(request.user, event.unit):
        messages.error(request, 'You do not have permission to edit this event.')
        return redirect('events:event_detail', event_id=event.id)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save_with_attendees(request.user)
            event.notify_attendees('updated')
            messages.success(request, 'Event updated.')
            return redirect('events:event_detail', event_id=event.id)
    else:
        # Pre-fill attendees
        form = EventForm(instance=event, initial={
            'attendees': [a.member_id for a in event.attendees.all()]
        })

    return render(request, 'events/event_form.html', {
        'form': form,
        'title': 'Edit Event',
        'event': event,
    })


@login_required
def event_delete(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if not can_manage_events(request.user, event.unit):
        messages.error(request, 'You do not have permission to delete this event.')
        return redirect('events:event_detail', event_id=event.id)

    if request.method == 'POST':
        # Notify before delete so attendees exist
        event.notify_attendees('deleted')
        event.delete()
        messages.success(request, 'Event deleted.')
        return redirect('events:calendar')

    return render(request, 'events/event_delete_confirm.html', {
        'event': event,
        'title': 'Delete Event',
    })
