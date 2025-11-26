from django import template
register = template.Library()

@register.simple_tag
def event_count(queryset):
    return queryset.count()

@register.simple_tag(takes_context=True)
def events_manage_eligible(context, event, user):
    """
    Return True if the given user is eligible to manage the event.
    """
    # Ensure we got actual objects
    if not hasattr(event, "created_by_id"):
        return False
    if not hasattr(user, "id"):
        return False

    if not user.is_authenticated:
        return False

    if event.created_by_id == user.id:
        return True
    if event.host and event.host.user_id == user.id:
        return True
    if hasattr(user, "is_unit_admin") and user.is_unit_admin(event.unit):
        return True

    return False