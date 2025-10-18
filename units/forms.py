from django import forms
from django.core.exceptions import ValidationError

from Members.models import Member
from .models import Unit, UnitMembership, Position, Department, DepartmentMembership


class ChangeCommanderForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['commanding_officer']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit dropdown to active members (if Member has is_active) or all members
        # Ensure select has bootstrap styling
        self.fields['commanding_officer'].widget.attrs.update({'class': 'form-select'})


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = [
            'name', 'hull', 'type', 'parent',
            'street_address', 'city', 'state', 'zip_code', 'country',
            'phone_number', 'email',
            'commanding_officer', 'image',
        ]
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Basic Bootstrap classes for nicer defaults
        for name, field in self.fields.items():
            if not getattr(field.widget, 'attrs', None):
                field.widget.attrs = {}
            css = field.widget.attrs.get('class', '')
            base = 'form-control'
            if name in ('type', 'parent', 'commanding_officer'):
                base = 'form-select'
            field.widget.attrs['class'] = (css + ' ' + base).strip()


class AddMemberForm(forms.ModelForm):
    class Meta:
        model = UnitMembership
        fields = ['member']

    def __init__(self, *args, **kwargs):
        unit: Unit = kwargs.pop('unit')
        super().__init__(*args, **kwargs)
        self.unit = unit
        # Ensure the model instance has unit set before validation runs (ModelForm calls model.clean)
        # This prevents RelatedObjectDoesNotExist when UnitMembership.clean accesses self.unit
        if self.instance is not None:
            self.instance.unit = unit
            # default to Crewmember (no position) on creation
            if not getattr(self.instance, 'pk', None):
                self.instance.position = None
        # Only members not already active in this unit
        existing_ids = unit.memberships.filter(is_active=True).values_list('member_id', flat=True)
        self.fields['member'].queryset = Member.objects.exclude(id__in=existing_ids)
        # Nice default styling
        self.fields['member'].widget.attrs.update({'class': 'form-select'})

    def save(self, commit=True):
        obj: UnitMembership = super().save(commit=False)
        obj.unit = self.unit
        obj.position = None
        if commit:
            obj.save()
        return obj


class AssignPositionForm(forms.Form):
    position = forms.ModelChoiceField(queryset=Position.objects.none(), required=False, empty_label='Crewmember (no position)')

    def __init__(self, *args, **kwargs):
        unit: Unit = kwargs.pop('unit')
        membership: UnitMembership = kwargs.pop('membership')
        is_co: bool = membership.member_id == unit.commanding_officer_id
        super().__init__(*args, **kwargs)
        self.unit = unit
        self.membership = membership
        qs = unit.positions.all()
        if is_co:
            qs = qs.none()
        else:
            if unit.type == Unit.TYPE_FLEET_COMMANDER:
                qs = qs.filter(is_special_staff=True)
            else:
                qs = qs.filter(is_special_staff=False)
        self.fields['position'].queryset = qs

    def clean(self):
        cleaned = super().clean()
        position = cleaned.get('position')
        unit = self.unit
        if self.membership.member_id == unit.commanding_officer_id and position is not None:
            raise ValidationError('CO cannot be assigned to another position.')
        if position and position.get_available_slots() <= 0 and (not self.membership.position or self.membership.position_id != position.id):
            raise ValidationError('Selected position has no available slots.')
        return cleaned

    def save(self):
        self.membership.position = self.cleaned_data.get('position')
        self.membership.save()
        return self.membership


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['name', 'description', 'order', 'max_members', 'is_special_staff']

    def __init__(self, *args, **kwargs):
        self.unit: Unit = kwargs.pop('unit')
        super().__init__(*args, **kwargs)
        # Only show the is_special_staff field for Fleet Commander; hide otherwise
        if self.unit.type != Unit.TYPE_FLEET_COMMANDER:
            self.fields['is_special_staff'].widget = forms.HiddenInput()
            self.fields['is_special_staff'].initial = False
        else:
            # Default to Special Staff for Fleet Commander positions
            self.fields['is_special_staff'].initial = True
        # Basic Bootstrap classes
        for name, field in self.fields.items():
            if not getattr(field.widget, 'attrs', None):
                field.widget.attrs = {}
            css = field.widget.attrs.get('class', '')
            base = 'form-control'
            field.widget.attrs['class'] = (css + ' ' + base).strip()

    def clean(self):
        cleaned = super().clean()
        is_special = cleaned.get('is_special_staff') or False
        if self.unit.type == Unit.TYPE_FLEET_COMMANDER and not is_special:
            raise ValidationError({'is_special_staff': 'Positions under Fleet Commander must be marked as Special Staff.'})
        if self.unit.type != Unit.TYPE_FLEET_COMMANDER and is_special:
            raise ValidationError({'is_special_staff': 'Special Staff positions may only be created under the Fleet Commander unit.'})
        return cleaned

    def save(self, commit=True):
        obj: Position = super().save(commit=False)
        obj.unit = self.unit
        if commit:
            obj.save()
        return obj



class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'order', 'leader']

    def __init__(self, *args, **kwargs):
        self.unit: Unit = kwargs.pop('unit')
        super().__init__(*args, **kwargs)
        # Ensure model instance has unit set prior to validation so Department.clean can access it safely
        if self.instance is not None:
            self.instance.unit = self.unit
        # Leader is optional and must be a member within the organization; no further restriction
        # Bootstrap classes
        for name, field in self.fields.items():
            if not getattr(field.widget, 'attrs', None):
                field.widget.attrs = {}
            css = field.widget.attrs.get('class', '')
            base = 'form-control'
            if name == 'leader':
                base = 'form-select'
            field.widget.attrs['class'] = (css + ' ' + base).strip()

    def save(self, commit=True):
        obj: Department = super().save(commit=False)
        obj.unit = self.unit
        if commit:
            obj.save()
        return obj


class AddDepartmentStaffForm(forms.ModelForm):
    class Meta:
        model = DepartmentMembership
        fields = ['member']

    def __init__(self, *args, **kwargs):
        self.department: Department = kwargs.pop('department')
        super().__init__(*args, **kwargs)
        # Only members not already active in this department
        existing_ids = self.department.memberships.filter(is_active=True).values_list('member_id', flat=True)
        self.fields['member'].queryset = Member.objects.exclude(id__in=list(existing_ids))
        # Bootstrap
        self.fields['member'].widget.attrs.update({'class': 'form-select'})

    def save(self, commit=True):
        obj: DepartmentMembership = super().save(commit=False)
        obj.department = self.department
        obj.is_active = True
        if commit:
            obj.save()
        return obj
