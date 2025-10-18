from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.urls import reverse

from Members.models import Member
from .forms import MemberSelectForm, MemberRolesForm


def is_staff_or_superuser(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_staff_or_superuser)
def dashboard(request):
    """Settings Dashboard for staff and superusers.
    Central hub linking to all settings pages.
    """
    # Define available settings sections dynamically (extendable)
    sections = [
        {
            'title': 'Roles & Groups',
            'description': 'Manage user roles (staff/superuser) and group memberships.',
            'icon': 'fa-user-shield',
            'url': reverse('settings:manage_roles'),
        },
        {
            'title': 'Rank Defaults',
            'description': 'Configure default rank and theme used for new members and displays.',
            'icon': 'fa-sliders-h',
            'url': reverse('rank:settings_edit'),
        },
        {
            'title': 'Member FAQs',
            'description': 'Manage Frequently Asked Questions and categories for members.',
            'icon': 'fa-question-circle',
            'url': reverse('members:faq_management'),
        },
        {
            'title': 'Member Settings',
            'description': 'Update your personal site theme and preferred rank theme.',
            'icon': 'fa-user-cog',
            'url': reverse('members:member_settings'),
        },
    ]
    return render(request, 'settings/dashboard.html', {
        'title': 'Settings Dashboard',
        'sections': sections,
    })


@login_required
@user_passes_test(is_staff_or_superuser)
def manage_roles(request):
    # Determine selected member
    selected_member = None
    member_id = request.GET.get('member') or request.POST.get('member')
    if member_id:
        try:
            selected_member = Member.objects.select_related('user').get(pk=member_id)
        except Member.DoesNotExist:
            selected_member = None
            messages.error(request, 'Selected member does not exist.')

    select_form = MemberSelectForm(initial={'member': selected_member.id if selected_member else None})

    roles_form = None
    if selected_member:
        # Process role assignment
        if request.method == 'POST' and 'save_roles' in request.POST:
            roles_form = MemberRolesForm(request.POST, user_instance=selected_member.user)
            if roles_form.is_valid():
                roles_form.save()
                messages.success(request, f"Updated roles for {selected_member.user.get_full_name() or selected_member.user.username}.")
                return redirect(f"{reverse('settings:manage_roles')}?member={selected_member.id}")
        else:
            roles_form = MemberRolesForm(user_instance=selected_member.user)

    context = {
        'title': 'Manage Roles & Groups',
        'select_form': select_form,
        'selected_member': selected_member,
        'roles_form': roles_form,
    }
    return render(request, 'settings/manage_roles.html', context)
