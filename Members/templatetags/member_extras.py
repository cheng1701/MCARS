from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def get_ranked_name(member):
    """
    Returns the member's name with rank (if applicable)
    """
    if hasattr(member, 'rank_association') and member.rank_association:
        return f"{member.rank_association.rank.short_name} {member.user.first_name} {member.user.last_name}"
    return f"{member.user.first_name} {member.user.last_name}"

@register.filter
def get_rank_image(member):
    """
    Returns the member's rank image URL (if applicable)
    """
    if hasattr(member, 'rank_association') and member.rank_association and member.rank_association.preferred_theme:
        # Try to get the image for the preferred theme
        rank = member.rank_association.rank
        theme = member.rank_association.preferred_theme
        try:
            from rank.models import RankImage
            rank_image = RankImage.objects.filter(rank=rank, theme=theme).first()
            if rank_image and rank_image.image:
                return rank_image.image.url
        except:
            pass
    return None

    @register.filter
    def is_manager(user):
        """Check if user has manager privileges"""
        return user.groups.filter(name__in=['member_manager', 'Member Manager']).exists() or user.is_staff

    @register.simple_tag
    def parent_link(parent, user):
        """Generate parent name as link if user has manager privileges, otherwise plain text"""
        if user.groups.filter(name__in=['member_manager', 'Member Manager']).exists() or user.is_staff:
            from django.urls import reverse
            url = reverse('members:member_detail', args=[parent.id])
            return format_html('<a href="{}" class="text-decoration-none">{}</a>', url, parent.get_ranked_name())
        else:
            return parent.get_ranked_name()
