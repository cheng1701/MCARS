from typing import Iterable, Set
from django.contrib.auth.models import Group
from Members.models import Member
from units.models import Unit, UnitMembership


# Canonical Events Manager group name
EVENTS_MANAGER_GROUPS = {'Events Manager'}


def user_is_events_manager(user) -> bool:
    return user.is_superuser or user.groups.filter(name__in=EVENTS_MANAGER_GROUPS).exists()


def unit_descendant_ids(unit: Unit) -> Set[int]:
    """Return all descendant unit IDs including the unit itself."""
    ids = {unit.id}
    stack = [unit]
    while stack:
        u = stack.pop()
        for child in u.children.all():
            ids.add(child.id)
            stack.append(child)
    return ids


def can_manage_events(user, unit: Unit) -> bool:
    """Check if user can manage events for the given unit.

    Rules:
    - Events Managers (group) or superusers are allowed for any unit.
    - The unit's Commanding Officer (CO) may manage.
    - A CO may delegate to a unit member (active UnitMembership). If that member leaves (no active membership), CO retains control.
      We model this by checking for any active UnitMembership where member.user == user and membership.unit == unit.
    """
    if not user.is_authenticated:
        return False
    if user_is_events_manager(user):
        return True

    # CO can manage
    if unit.commanding_officer and unit.commanding_officer.user_id == user.id:
        return True

    # Delegate: any active unit membership the user holds in this unit grants manage rights per spec
    try:
        member = user.member
    except Member.DoesNotExist:
        return False

    return UnitMembership.objects.filter(unit=unit, member=member, is_active=True).exists()


# ---------------- Visibility Helpers ----------------

def _ancestor_of_type(unit: Unit, type_const: str) -> Unit | None:
    """Walk up the parent chain to find the first ancestor of a given type (including the unit itself)."""
    u = unit
    while u is not None:
        if u.type == type_const:
            return u
        u = u.parent
    return None


def event_audience_root(event) -> Unit | None:
    """Return the root Unit that defines the audience of the event based on its visibility_scope.
    For 'fleet' returns None, meaning everyone.
    """
    scope = getattr(event, 'visibility_scope', 'unit')
    unit = event.unit
    if scope == 'fleet':
        return None
    if scope == 'quadrant':
        from units.models import Unit as U
        return _ancestor_of_type(unit, U.TYPE_QUADRANT)
    if scope == 'sector':
        from units.models import Unit as U
        return _ancestor_of_type(unit, U.TYPE_SECTOR)
    # unit scope
    return unit


def user_can_view_event(user, event) -> bool:
    """Determine if a user is eligible to view an event.
    - Anonymous users: only fleet-wide events are visible.
    - Authenticated: Events Managers/superusers always see; otherwise must belong to the audience subtree.
    """
    scope = getattr(event, 'visibility_scope', 'unit')
    if not getattr(user, 'is_authenticated', False):
        return scope == 'fleet'
    # privileged users
    if user_is_events_manager(user):
        return True
    # members with units
    try:
        member = user.member
    except Member.DoesNotExist:
        # Non-member authenticated users: show fleet only
        return scope == 'fleet'

    if scope == 'fleet':
        return True

    root = event_audience_root(event)
    if not root:
        return True
    audience_ids = unit_descendant_ids(root)
    return member.unit_memberships.filter(unit_id__in=audience_ids, is_active=True).exists()
