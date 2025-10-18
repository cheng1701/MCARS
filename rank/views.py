from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.urls import reverse
from .models import Genre, Branch, Rank, Theme, RankImage, RankSettings, MemberRank, MemberRankHistory
from .forms import RankForm, ThemeForm, RankImageForm, GenreForm, BranchForm, RankSettingsForm, MemberRankForm
from Members.models import Member



def is_rank_manager(user):
    """Check if user is in rank_manager group"""
    return user.groups.filter(name='rank_manager').exists() or user.is_staff


@login_required
@user_passes_test(is_rank_manager)
def rank_dashboard(request):
    """Main dashboard for rank managers"""
    from Members.models import Member, Child

    rank_count = Rank.objects.count()
    theme_count = Theme.objects.count()
    branch_count = Branch.objects.count()
    genre_count = Genre.objects.count()

    # Member and child counts
    member_count = Member.objects.count()
    child_count = Child.objects.count()

    # Members and children with ranks
    members_with_ranks = MemberRank.objects.count()
    children_with_ranks = Child.objects.filter(child_rank_association__isnull=False).count()

    # Get themes with rank coverage stats
    themes_with_stats = Theme.objects.annotate(rank_count=Count('rank_images'))

    # Recent ranks (ordered by rank order rather than creation date)
    recent_ranks = Rank.objects.all().order_by('order')[:10]

    # Get current default settings
    settings = RankSettings.get_settings()

    context = {
        'rank_count': rank_count,
        'theme_count': theme_count,
        'branch_count': branch_count,
        'genre_count': genre_count,
        'member_count': member_count,
        'child_count': child_count,
        'members_with_ranks': members_with_ranks,
        'children_with_ranks': children_with_ranks,
        'themes_with_stats': themes_with_stats,
        'recent_ranks': recent_ranks,
        'active_menu': 'dashboard',
        'settings': settings,
    }
    return render(request, 'rank/dashboard.html', context)


# Rank Views
@login_required
@user_passes_test(is_rank_manager)
def rank_list(request):
    """List all ranks"""
    ranks = Rank.objects.all().order_by('order')
    return render(request, 'rank/rank_list.html', {'ranks': ranks})


@login_required
@user_passes_test(is_rank_manager)
def rank_create(request):
    """Create new rank"""
    if request.method == 'POST':
        form = RankForm(request.POST)
        if form.is_valid():
            rank = form.save(commit=False)
            # Get the highest order value and increment by 1
            highest_order = Rank.objects.aggregate(models.Max('order'))['order__max'] or 0
            rank.order = highest_order + 1
            rank.save()
            messages.success(request, 'Rank created successfully.')
            return redirect('rank:rank_list')
    else:
        form = RankForm()

    return render(request, 'rank/rank_form.html', {'form': form, 'title': 'Create Rank'})


@login_required
@user_passes_test(is_rank_manager)
def update_rank_order(request):
    """Update the order of ranks via AJAX"""
    if request.method == 'POST':
        try:
            import json
            from django.http import JsonResponse

            rank_orders = json.loads(request.POST.get('rank_orders'))

            # Update each rank's order
            for rank_data in rank_orders:
                rank = Rank.objects.get(id=rank_data['id'])
                rank.order = rank_data['order']
                rank.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Rank order updated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error updating rank order: {str(e)}'
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)


@login_required
@user_passes_test(is_rank_manager)
def rank_edit(request, pk):
    """Edit existing rank"""
    rank = get_object_or_404(Rank, pk=pk)

    if request.method == 'POST':
        form = RankForm(request.POST, instance=rank)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rank updated successfully.')
            return redirect('rank:rank_list')
    else:
        form = RankForm(instance=rank)

    return render(request, 'rank/rank_form.html', {'form': form, 'title': 'Edit Rank'})


@login_required
@user_passes_test(is_rank_manager)
def rank_delete(request, pk):
    """Delete a rank"""
    rank = get_object_or_404(Rank, pk=pk)

    if request.method == 'POST':
        rank.delete()
        messages.success(request, 'Rank deleted successfully.')
        return redirect('rank:rank_list')

    return render(request, 'rank/rank_confirm_delete.html', {'rank': rank})


# Theme Views
@login_required
@user_passes_test(is_rank_manager)
def theme_list(request):
    """List all themes"""
    themes = Theme.objects.all()
    return render(request, 'rank/theme_list.html', {'themes': themes})


@login_required
@user_passes_test(is_rank_manager)
def theme_create(request):
    """Create new theme"""
    if request.method == 'POST':
        form = ThemeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Theme created successfully.')
            return redirect('rank:theme_list')
    else:
        form = ThemeForm()

    return render(request, 'rank/theme_form.html', {'form': form, 'title': 'Create Theme'})


@login_required
@user_passes_test(is_rank_manager)
def theme_edit(request, pk):
    """Edit existing theme"""
    theme = get_object_or_404(Theme, pk=pk)

    if request.method == 'POST':
        form = ThemeForm(request.POST, instance=theme)
        if form.is_valid():
            form.save()
            messages.success(request, 'Theme updated successfully.')
            return redirect('rank:theme_list')
    else:
        form = ThemeForm(instance=theme)

    return render(request, 'rank/theme_form.html', {'form': form, 'title': 'Edit Theme'})


@login_required
@user_passes_test(is_rank_manager)
def theme_delete(request, pk):
    """Delete a theme"""
    theme = get_object_or_404(Theme, pk=pk)

    if request.method == 'POST':
        theme.delete()
        messages.success(request, 'Theme deleted successfully.')
        return redirect('rank:theme_list')

    return render(request, 'rank/theme_confirm_delete.html', {'theme': theme})


@login_required
@user_passes_test(is_rank_manager)
def theme_detail(request, pk):
    """View theme details and manage rank images"""
    theme = get_object_or_404(Theme, pk=pk)
    rank_images = RankImage.objects.filter(theme=theme)
    missing_ranks = Rank.objects.exclude(images__theme=theme)

    context = {
        'theme': theme,
        'rank_images': rank_images,
        'missing_ranks': missing_ranks,
    }
    return render(request, 'rank/theme_detail.html', context)


# Rank Image Management
@login_required
@user_passes_test(is_rank_manager)
def rank_image_create(request, theme_id):
    """Add a rank image to a theme"""
    theme = get_object_or_404(Theme, pk=theme_id)

    if request.method == 'POST':
        form = RankImageForm(request.POST, request.FILES)
        form.fields['rank'].queryset = Rank.objects.exclude(images__theme=theme)

        if form.is_valid():
            rank_image = form.save(commit=False)
            rank_image.theme = theme
            rank_image.save()
            messages.success(request, 'Rank image added successfully.')
            return redirect('rank:theme_detail', pk=theme.id)
    else:
        form = RankImageForm()
        form.fields['rank'].queryset = Rank.objects.exclude(images__theme=theme)

    return render(request, 'rank/rank_image_form.html', {
        'form': form, 
        'theme': theme,
        'title': 'Add Rank Image'
    })


@login_required
@user_passes_test(is_rank_manager)
def rank_image_edit(request, pk):
    """Edit a rank image"""
    rank_image = get_object_or_404(RankImage, pk=pk)

    if request.method == 'POST':
        form = RankImageForm(request.POST, request.FILES, instance=rank_image)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rank image updated successfully.')
            return redirect('rank:theme_detail', pk=rank_image.theme.id)
    else:
        form = RankImageForm(instance=rank_image)

    return render(request, 'rank/rank_image_form.html', {
        'form': form, 
        'theme': rank_image.theme,
        'title': 'Edit Rank Image'
    })


@login_required
@user_passes_test(is_rank_manager)
def rank_image_delete(request, pk):
    """Delete a rank image"""
    rank_image = get_object_or_404(RankImage, pk=pk)
    theme_id = rank_image.theme.id

    if request.method == 'POST':
        rank_image.delete()
        messages.success(request, 'Rank image deleted successfully.')
        return redirect('rank:theme_detail', pk=theme_id)

    return render(request, 'rank/rank_image_confirm_delete.html', {'rank_image': rank_image})


# Genre Views
@login_required
@user_passes_test(is_rank_manager)
def genre_list(request):
    """List all genres"""
    genres = Genre.objects.all()
    return render(request, 'rank/genre_list.html', {'genres': genres})


@login_required
@user_passes_test(is_rank_manager)
def genre_create(request):
    """Create new genre"""
    if request.method == 'POST':
        form = GenreForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Genre created successfully.')
            return redirect('rank:genre_list')
    else:
        form = GenreForm()

    return render(request, 'rank/genre_form.html', {'form': form, 'title': 'Create Genre'})


@login_required
@user_passes_test(is_rank_manager)
def genre_edit(request, pk):
    """Edit existing genre"""
    genre = get_object_or_404(Genre, pk=pk)

    if request.method == 'POST':
        form = GenreForm(request.POST, instance=genre)
        if form.is_valid():
            form.save()
            messages.success(request, 'Genre updated successfully.')
            return redirect('rank:genre_list')
    else:
        form = GenreForm(instance=genre)

    return render(request, 'rank/genre_form.html', {'form': form, 'title': 'Edit Genre'})


@login_required
@user_passes_test(is_rank_manager)
def genre_delete(request, pk):
    """Delete a genre"""
    genre = get_object_or_404(Genre, pk=pk)

    if request.method == 'POST':
        genre.delete()
        messages.success(request, 'Genre deleted successfully.')
        return redirect('rank:genre_list')

    return render(request, 'rank/genre_confirm_delete.html', {'genre': genre})


# Branch Views
@login_required
@user_passes_test(is_rank_manager)
def branch_list(request):
    """List all branches"""
    branches = Branch.objects.all()
    return render(request, 'rank/branch_list.html', {'branches': branches})


@login_required
@user_passes_test(is_rank_manager)
def branch_create(request):
    """Create new branch"""
    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Branch created successfully.')
            return redirect('rank:branch_list')
    else:
        form = BranchForm()

    return render(request, 'rank/branch_form.html', {'form': form, 'title': 'Create Branch'})


@login_required
@user_passes_test(is_rank_manager)
def branch_edit(request, pk):
    """Edit existing branch"""
    branch = get_object_or_404(Branch, pk=pk)

    if request.method == 'POST':
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            form.save()
            messages.success(request, 'Branch updated successfully.')
            return redirect('rank:branch_list')
    else:
        form = BranchForm(instance=branch)

    return render(request, 'rank/branch_form.html', {'form': form, 'title': 'Edit Branch'})


@login_required
@user_passes_test(is_rank_manager)
def branch_delete(request, pk):
    """Delete a branch"""
    branch = get_object_or_404(Branch, pk=pk)

    if request.method == 'POST':
        branch.delete()
        messages.success(request, 'Branch deleted successfully.')
        return redirect('rank:branch_list')

    return render(request, 'rank/branch_confirm_delete.html', {'branch': branch})


# Rank Settings Views
@login_required
@user_passes_test(is_rank_manager)
def settings_edit(request):
    """Edit rank system default settings"""
    settings = RankSettings.get_settings()

    if request.method == 'POST':
        form = RankSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Default settings updated successfully.')
            return redirect('rank:dashboard')
    else:
        form = RankSettingsForm(instance=settings)

    return render(request, 'rank/settings_form.html', {
        'form': form,
        'title': 'Edit Default Settings'
    })


@login_required
@user_passes_test(is_rank_manager)
def get_themes_for_selection(request):
    """AJAX view to get themes based on selected genre and branch"""
    genre_id = request.GET.get('genre_id')
    branch_id = request.GET.get('branch_id')

    themes = Theme.objects.all()

    if genre_id:
        themes = themes.filter(genre_id=genre_id)

    if branch_id:
        themes = themes.filter(branch_id=branch_id)

    return JsonResponse({
        'themes': [
            {'id': theme.id, 'name': str(theme)} 
            for theme in themes
        ]
    })


@login_required
@user_passes_test(is_rank_manager)
def people_list(request):
    """Unified view to list both members and children for rank management"""
    from Members.models import Child

    query = request.GET.get('q', '')
    person_type = request.GET.get('type', 'all')

    people = []

    # Get members
    if person_type in ['all', 'members']:
        if query:
            members = Member.objects.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(user__email__icontains=query) |
                Q(user__username__icontains=query)
            ).select_related('user')
        else:
            members = Member.objects.all().select_related('user')

        for member in members:
            try:
                member.current_rank = member.rank_association
            except:
                member.current_rank = None
            member.person_type = 'member'
            member.display_name = member.get_ranked_name()
            people.append(member)

    # Get children
    if person_type in ['all', 'children']:
        if query:
            children = Child.objects.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(parent__user__first_name__icontains=query) |
                Q(parent__user__last_name__icontains=query)
            ).select_related('parent__user')
        else:
            children = Child.objects.all().select_related('parent__user')

        for child in children:
            try:
                child.current_rank = child.child_rank_association
            except:
                child.current_rank = None
            child.person_type = 'child'
            child.display_name = child.get_ranked_name()
            people.append(child)

    # Sort by last name, then first name
    people.sort(key=lambda p: (
        p.user.last_name if hasattr(p, 'user') else p.last_name,
        p.user.first_name if hasattr(p, 'user') else p.first_name
    ))

    # Pagination
    paginator = Paginator(people, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'rank/people_list.html', {
        'page_obj': page_obj,
        'query': query,
        'person_type': person_type,
        'title': 'People Rank Management',
    })


@login_required
@user_passes_test(is_rank_manager)
def person_rank_assign(request, person_type, person_id):
    """Unified view to assign ranks to both members and children"""
    from Members.models import Child
    from .models import ChildRank
    from .forms import ChildRankForm

    if person_type == 'member':
        person = get_object_or_404(Member, id=person_id)
        try:
            rank_assignment = person.rank_association
        except MemberRank.DoesNotExist:
            rank_assignment = MemberRank(member=person)
        form_class = MemberRankForm
        template_field = 'member'
    elif person_type == 'child':
        person = get_object_or_404(Child, id=person_id)
        try:
            rank_assignment = person.child_rank_association
        except:
            rank_assignment = ChildRank(child=person)
        form_class = ChildRankForm
        template_field = 'child'
    else:
        messages.error(request, "Invalid person type.")
        return redirect('rank:people_list')

    if request.method == 'POST':
        form = form_class(request.POST, instance=rank_assignment)
        if form.is_valid():
            rank_assignment = form.save(commit=False)
            if person_type == 'member':
                rank_assignment.member = person
            else:
                rank_assignment.child = person
            rank_assignment.assigned_by = request.user
            rank_assignment.save()
            messages.success(request, f"Rank successfully assigned to {person.get_ranked_name()}")
            return redirect('rank:people_list')
    else:
        # If new person with no rank, use default rank from settings if available
        if not hasattr(person, 'rank_association' if person_type == 'member' else 'child_rank_association'):
            settings = RankSettings.objects.first()
            if settings and settings.default_paygrade:
                form = form_class(instance=rank_assignment, initial={'rank': settings.default_paygrade})
            else:
                form = form_class(instance=rank_assignment)
        else:
            form = form_class(instance=rank_assignment)

    context = {
        'form': form,
        'person': person,
        'person_type': person_type,
        'title': f"Assign Rank to {person.get_ranked_name()}",
    }
    context[template_field] = person  # For template compatibility

    return render(request, 'rank/person_rank_form.html', context)


@login_required
@user_passes_test(is_rank_manager)
def person_rank_history(request, person_type, person_id):
    """Unified view to show rank history for both members and children"""
    from Members.models import Child
    from .models import ChildRank, ChildRankHistory

    if person_type == 'member':
        person = get_object_or_404(Member, id=person_id)
        try:
            current_rank = person.rank_association
        except MemberRank.DoesNotExist:
            current_rank = None
        rank_history = MemberRankHistory.objects.filter(member=person).order_by('-effective_date', '-created_at')
        template_field = 'member'
    elif person_type == 'child':
        person = get_object_or_404(Child, id=person_id)
        try:
            current_rank = person.child_rank_association
        except:
            current_rank = None
        rank_history = ChildRankHistory.objects.filter(child=person).order_by('-effective_date', '-created_at')
        template_field = 'child'
    else:
        messages.error(request, "Invalid person type.")
        return redirect('rank:people_list')

    context = {
        'person': person,
        'person_type': person_type,
        'current_rank': current_rank,
        'rank_history': rank_history,
        'title': f"Rank History for {person.get_ranked_name()}",
        'active_menu': 'people_list',
    }
    context[template_field] = person  # For template compatibility

    return render(request, 'rank/person_rank_history.html', context)
