from django import template
from django.utils import timezone
from events.models import Event
from events.utils import unit_descendant_ids, user_is_events_manager

register = template.Library()


@register.inclusion_tag('events/_unit_events_snippet.html')
def upcoming_events_for_unit(unit, include_subordinates=False, limit=5):
    if not unit:
        return {'events': [], 'unit': unit}
    ids = {unit.id}
    if include_subordinates:
        ids = unit_descendant_ids(unit)
    qs = (
        Event.objects.filter(unit_id__in=ids, end_datetime__gte=timezone.now())
        .order_by('start_datetime')[:limit]
    )
    return {'events': qs, 'unit': unit}


@register.simple_tag(takes_context=True)
def events_manage_eligible(context):
    """Return True if the current user is eligible to manage any events.
    Eligibility:
    - Superuser or in Events Manager groups; or
    - CO of any unit; or
    - Has any active UnitMembership (delegate) in any unit.
    """
    user = context.get('user')
    if not user or not user.is_authenticated:
        return False
    # Events Manager groups or superuser
    if user_is_events_manager(user):
        return True
    try:
        # Check if the user is a CO of any unit
        from units.models import Unit
        if Unit.objects.filter(commanding_officer__user_id=user.id).exists():
            return True
    except Exception:
        pass
    try:
        # Check if the user has any active unit membership (delegate)
        from Members.models import Member
        member = user.member
        if member.unit_memberships.filter(is_active=True).exists():
            return True
    except Exception:
        pass
    return False
