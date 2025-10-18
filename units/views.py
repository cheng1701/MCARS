from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
import json

from .models import Unit, UnitMembership, Position, Department, DepartmentMembership
from .forms import AddMemberForm, AssignPositionForm, PositionForm, UnitForm, ChangeCommanderForm, DepartmentForm, AddDepartmentStaffForm


def is_unit_manager(user):
    return user.is_staff or user.groups.filter(name='unit_manager').exists()


def can_manage_unit(user, unit: Unit):
    if not user.is_authenticated:
        return False
    if is_unit_manager(user):
        return True
    # CO can manage their own unit
    if unit.commanding_officer and unit.commanding_officer.user_id == user.id:
        return True
    return False


@login_required
def unit_list(request):
    units = Unit.objects.all().select_related('commanding_officer')
    return render(request, 'units/unit_list.html', {'units': units, 'title': 'Units'})


def unit_org_chart(request):
    """Read-only organizational chart with filtering/sorting and chain-of-command navigation."""
    # Roots are units without a parent (typically Fleet Commander)
    roots = (
        Unit.objects.filter(parent__isnull=True)
        .select_related('commanding_officer')
        .prefetch_related('children__commanding_officer', 'children__children__commanding_officer')
        .order_by('type', 'name')
    )

    # Build lightweight dicts for client-side chain-of-command and flat list rendering
    all_units = (
        Unit.objects.all()
        .select_related('commanding_officer', 'parent')
        .only(
            'id', 'name', 'hull', 'type', 'city', 'state', 'country', 'email', 'image', 'parent_id', 'commanding_officer__id'
        )
        .order_by('type', 'name')
    )

    def unit_to_dict(u: Unit):
        return {
            'id': u.id,
            'name': u.get_display_name(),
            'short_name': u.name,
            'hull': u.hull or '',
            'type': u.get_type_display(),
            'type_code': u.type,
            'city': u.city or '',
            'state': u.state or '',
            'country': u.country or '',
            'email': u.email or '',
            'parent_id': u.parent_id,
            'public_url': reverse('units:unit_public', args=[u.id]),
            'detail_url': reverse('units:unit_detail', args=[u.id]),
            'image_url': (u.image.url if u.image else ''),
            'co_id': (u.commanding_officer.id if u.commanding_officer else None),
            'co_name': (u.commanding_officer.get_ranked_name() if u.commanding_officer else ''),
            'co_url': (reverse('members:member_detail', args=[u.commanding_officer.id]) if u.commanding_officer else ''),
        }

    units_data = [unit_to_dict(u) for u in all_units]

    context = {
        'roots': roots,
        'units_json': json.dumps(units_data),
        'title': 'Organizational Chart',
    }
    return render(request, 'units/unit_org_chart.html', context)


@login_required
def unit_detail(request, pk):
    unit = get_object_or_404(
        Unit.objects.select_related('commanding_officer', 'parent').prefetch_related('children__commanding_officer'),
        pk=pk
    )
    positioned = UnitMembership.objects.filter(unit=unit, is_active=True, position__isnull=False).select_related('member', 'position')
    unpositioned = UnitMembership.objects.filter(unit=unit, is_active=True, position__isnull=True).select_related('member')
    context = {
        'unit': unit,
        'positioned_members': positioned,
        'unpositioned_members': unpositioned,
    }
    return render(request, 'units/unit_detail.html', context)


def unit_public(request, pk):
    """Public, read-only profile view for units."""
    unit = get_object_or_404(
        Unit.objects.select_related('commanding_officer', 'parent').prefetch_related('children__commanding_officer'),
        pk=pk
    )
    positioned = UnitMembership.objects.filter(unit=unit, is_active=True, position__isnull=False).select_related('member', 'position')
    # Public profile won't list unpositioned crewmembers to keep it concise
    context = {
        'unit': unit,
        'positioned_members': positioned,
    }
    return render(request, 'units/unit_public.html', context)


@login_required
def change_commander(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if not can_manage_unit(request.user, unit):
        messages.error(request, 'You do not have permission to manage this unit.')
        return redirect('units:unit_detail', pk=unit.pk)

    if unit.type != Unit.TYPE_FLEET_COMMANDER:
        # For now, only provide dedicated change commander UI for Fleet Commander
        messages.info(request, 'Commander changes for this unit type can be managed via unit editing workflow.')
        return redirect('units:unit_detail', pk=unit.pk)

    if request.method == 'POST':
        form = ChangeCommanderForm(request.POST, instance=unit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Commander updated successfully.')
            return redirect('units:unit_detail', pk=unit.pk)
    else:
        form = ChangeCommanderForm(instance=unit)

    return render(request, 'units/change_commander.html', {
        'unit': unit,
        'form': form,
        'title': 'Change Fleet Commander'
    })


@login_required
def add_member(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if not can_manage_unit(request.user, unit):
        messages.error(request, 'You do not have permission to manage this unit.')
        return redirect('units:unit_detail', pk=unit.pk)


    if request.method == 'POST':
        form = AddMemberForm(request.POST, unit=unit)
        if form.is_valid():
            membership = form.save()
            messages.success(request, f"Added {membership.member.user.get_full_name() or membership.member.user.username} as Crewmember.")
            return redirect('units:unit_detail', pk=unit.pk)
    else:
        form = AddMemberForm(unit=unit)

    return render(request, 'units/add_member.html', {'unit': unit, 'form': form, 'title': 'Add Member'})


@login_required
def assign_position(request, pk, membership_id):
    unit = get_object_or_404(Unit, pk=pk)
    membership = get_object_or_404(UnitMembership.objects.select_related('member', 'position'), pk=membership_id, unit=unit)

    if not can_manage_unit(request.user, unit):
        messages.error(request, 'You do not have permission to manage this unit.')
        return redirect('units:unit_detail', pk=unit.pk)

    if request.method == 'POST':
        form = AssignPositionForm(request.POST, unit=unit, membership=membership)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment updated.')
            return redirect('units:unit_detail', pk=unit.pk)
    else:
        form = AssignPositionForm(unit=unit, membership=membership, initial={'position': membership.position_id})

    return render(request, 'units/assign_position.html', {
        'unit': unit,
        'membership': membership,
        'form': form,
        'is_co': membership.member_id == unit.commanding_officer_id,
    })


@login_required
def manage_positions(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if not can_manage_unit(request.user, unit):
        messages.error(request, 'You do not have permission to manage this unit.')
        return redirect('units:unit_detail', pk=unit.pk)

    # Allow positions for Fleet Commander: these are Special Staff positions
    # Creation constraints are enforced in PositionForm/Position.clean

    if request.method == 'POST':
        form = PositionForm(request.POST, unit=unit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Position created.')
            return redirect('units:manage_positions', pk=unit.pk)
    else:
        form = PositionForm(unit=unit)

    positions = unit.positions.all()
    return render(request, 'units/position_manage.html', {
        'unit': unit,
        'form': form,
        'positions': positions,
    })


@login_required
def manage_departments(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if not can_manage_unit(request.user, unit):
        messages.error(request, 'You do not have permission to manage this unit.')
        return redirect('units:unit_detail', pk=unit.pk)
    if unit.type != Unit.TYPE_HQ:
        messages.info(request, 'Departments are only available for Headquarters units.')
        return redirect('units:unit_detail', pk=unit.pk)

    if request.method == 'POST':
        form = DepartmentForm(request.POST, unit=unit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department created.')
            return redirect('units:manage_departments', pk=unit.pk)
    else:
        form = DepartmentForm(unit=unit)

    departments = unit.departments.select_related('leader').all()
    return render(request, 'units/department_overview.html', {
        'unit': unit,
        'form': form,
        'departments': departments,
    })


@login_required
def manage_department(request, pk, dept_id):
    unit = get_object_or_404(Unit, pk=pk)
    if not can_manage_unit(request.user, unit):
        messages.error(request, 'You do not have permission to manage this unit.')
        return redirect('units:unit_detail', pk=unit.pk)
    department = get_object_or_404(Department.objects.select_related('unit', 'leader'), pk=dept_id, unit=unit)

    # Update department meta (leader, name/desc/order)
    if request.method == 'POST' and 'update_department' in request.POST:
        form = DepartmentForm(request.POST, instance=department, unit=unit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated.')
            return redirect('units:manage_department', pk=unit.pk, dept_id=department.pk)
    else:
        form = DepartmentForm(instance=department, unit=unit)

    # Add staff
    if request.method == 'POST' and 'add_staff' in request.POST:
        staff_form = AddDepartmentStaffForm(request.POST, department=department)
        if staff_form.is_valid():
            staff_form.save()
            messages.success(request, 'Staff member added to department.')
            return redirect('units:manage_department', pk=unit.pk, dept_id=department.pk)
    else:
        staff_form = AddDepartmentStaffForm(department=department)

    memberships = department.memberships.select_related('member').filter(is_active=True)

    return render(request, 'units/department_manage.html', {
        'unit': unit,
        'department': department,
        'form': form,
        'staff_form': staff_form,
        'memberships': memberships,
    })


@login_required
def unit_create(request):
    if not is_unit_manager(request.user):
        messages.error(request, 'You do not have permission to create units.')
        return redirect('units:unit_list')

    if request.method == 'POST':
        form = UnitForm(request.POST, request.FILES)
        if form.is_valid():
            unit = form.save()
            messages.success(request, f"Unit '{unit.get_display_name()}' created.")
            return redirect('units:unit_detail', pk=unit.pk)
    else:
        form = UnitForm()

    return render(request, 'units/unit_form.html', {
        'form': form,
        'title': 'Create Unit',
    })


@login_required
def unit_edit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if not can_manage_unit(request.user, unit):
        messages.error(request, 'You do not have permission to edit this unit.')
        return redirect('units:unit_detail', pk=unit.pk)

    if request.method == 'POST':
        form = UnitForm(request.POST, request.FILES, instance=unit)
        if form.is_valid():
            unit = form.save()
            messages.success(request, f"Unit '{unit.get_display_name()}' updated.")
            return redirect('units:unit_detail', pk=unit.pk)
    else:
        form = UnitForm(instance=unit)

    return render(request, 'units/unit_form.html', {
        'form': form,
        'title': 'Edit Unit',
    })
