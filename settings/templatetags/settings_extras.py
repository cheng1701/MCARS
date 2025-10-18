from django import template

register = template.Library()


@register.filter(name='friendly_group')
def friendly_group(name: str) -> str:
    """
    Render a human-friendly label for a Django Group name.
    Keeps internal names (like 'rank_manager') intact for logic elsewhere,
    but shows a prettified version in templates.
    """
    if not name:
        return name
    mapping = {
        'rank_manager': 'Rank Manager',
        'unit_manager': 'Unit Manager',
        'member_manager': 'Member Manager',
    }
    # If a direct mapping exists, use it; otherwise fallback to title-cased with spaces
    # (e.g., 'some_group' -> 'Some Group')
    return mapping.get(name, str(name).replace('_', ' ').title())
