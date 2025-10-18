from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from Members.models import Member


class Unit(models.Model):
    TYPE_FLEET_COMMANDER = 'FLEET_COMMANDER'
    TYPE_HQ = 'HEADQUARTERS'
    TYPE_QUADRANT = 'QUADRANT'
    TYPE_SECTOR = 'SECTOR'
    TYPE_SHIP = 'SHIP'
    TYPE_SHUTTLE = 'SHUTTLE'

    TYPE_CHOICES = [
        (TYPE_FLEET_COMMANDER, 'Fleet Commander'),
        (TYPE_HQ, 'Headquarters'),
        (TYPE_QUADRANT, 'Quadrant'),
        (TYPE_SECTOR, 'Sector'),
        (TYPE_SHIP, 'Ship'),
        (TYPE_SHUTTLE, 'Shuttle'),
    ]

    name = models.CharField(max_length=255)
    hull = models.CharField(max_length=50, blank=True, default='')
    type = models.CharField(max_length=32, choices=TYPE_CHOICES)

    # hierarchy
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')

    # contact/location
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default='')
    phone_number = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)

    # leadership
    commanding_officer = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL, related_name='units_commanded')

    # assets
    image = models.ImageField(upload_to='unit_images/', null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['type', 'name']

    def __str__(self):
        return self.get_display_name()

    def clean(self):
        """Enforce hierarchy business rules for allowed parents based on type."""
        if self.type == self.TYPE_FLEET_COMMANDER:
            if self.parent is not None:
                raise ValidationError({'parent': 'Fleet Commander cannot have a parent.'})
        elif self.type == self.TYPE_HQ:
            if self.parent is None or self.parent.type != self.TYPE_FLEET_COMMANDER:
                raise ValidationError({'parent': 'Headquarters must be subordinate to the Fleet Commander.'})
        elif self.type == self.TYPE_QUADRANT:
            if self.parent is None or self.parent.type != self.TYPE_HQ:
                raise ValidationError({'parent': 'Quadrant must be subordinate to Headquarters.'})
        elif self.type == self.TYPE_SECTOR:
            if self.parent is None or self.parent.type != self.TYPE_QUADRANT:
                raise ValidationError({'parent': 'Sector must be subordinate to a Quadrant.'})
        elif self.type == self.TYPE_SHIP:
            if self.parent is None or self.parent.type not in (self.TYPE_SECTOR, self.TYPE_QUADRANT, self.TYPE_HQ, self.TYPE_FLEET_COMMANDER):
                raise ValidationError({'parent': 'Ship must be subordinate to a Sector, Quadrant, Headquarters, or Fleet Commander.'})
        elif self.type == self.TYPE_SHUTTLE:
            if self.parent is None or self.parent.type not in (self.TYPE_SHIP, self.TYPE_SECTOR):
                raise ValidationError({'parent': 'Shuttle must be subordinate to a Ship or Sector.'})

        # Ensure Fleet Commander has exactly one Person (CO) and unique constraint overall
        if self.type == self.TYPE_FLEET_COMMANDER and not self.commanding_officer:
            raise ValidationError({'commanding_officer': 'Fleet Commander must have exactly one Person (CO).'})

    @property
    def co_membership(self):
        """Return a synthetic membership-like dict for the CO for display lists."""
        if not self.commanding_officer:
            return None
        return {
            'member': self.commanding_officer,
            'position_name': 'Commander' if self.type in {self.TYPE_HQ, self.TYPE_QUADRANT, self.TYPE_SECTOR, self.TYPE_SHIP, self.TYPE_SHUTTLE} else 'Fleet Commander',
        }

    def get_display_name(self):
        return f"{self.name} ({self.hull})" if self.hull else self.name


class Position(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='positions')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    max_members = models.PositiveIntegerField(default=1)
    is_special_staff = models.BooleanField(default=False, help_text='Special Staff positions work directly for the Fleet Commander')

    class Meta:
        ordering = ['order', 'name']
        unique_together = [('unit', 'name')]

    def __str__(self):
        return f"{self.name} @ {self.unit.get_display_name()}"

    def clean(self):
        # Enforce business rules for Special Staff
        if self.unit and self.unit.type == Unit.TYPE_FLEET_COMMANDER:
            # All positions under Fleet Commander must be Special Staff
            if not self.is_special_staff:
                from django.core.exceptions import ValidationError
                raise ValidationError({'is_special_staff': 'Positions under Fleet Commander must be marked as Special Staff.'})
        else:
            # Special Staff positions can only exist under Fleet Commander
            if self.is_special_staff:
                from django.core.exceptions import ValidationError
                raise ValidationError({'is_special_staff': 'Special Staff positions may only belong to the Fleet Commander unit.'})

    def get_available_slots(self):
        assigned = self.memberships.filter(is_active=True).count()
        return max(self.max_members - assigned, 0)


class UnitMembership(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='memberships')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='unit_memberships')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, related_name='memberships')
    joined_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('unit', 'member', 'is_active')]
        ordering = ['-joined_date']

    def __str__(self):
        return f"{self.member} in {self.unit} as {self.position.name if self.position else 'Crewmember'}"

    def clean(self):
        # CO cannot hold other positions in the same unit
        if self.unit.commanding_officer_id == self.member_id and self.position is not None:
            raise ValidationError({'position': 'The CO cannot hold another position. Leave as Crewmember.'})
        # Respect max members for position
        if self.position and self.position.get_available_slots() <= 0 and not self.pk:
            raise ValidationError({'position': 'This position has no available slots.'})



class Department(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    leader = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL, related_name='departments_led')

    class Meta:
        ordering = ['order', 'name']
        unique_together = [('unit', 'name')]

    def __str__(self):
        return f"{self.name} @ {self.unit.get_display_name()}"

    def clean(self):
        # Departments only allowed for Headquarters units
        if self.unit and self.unit.type != Unit.TYPE_HQ:
            from django.core.exceptions import ValidationError
            raise ValidationError({'unit': 'Departments can only be created for Headquarters units.'})

    def staff_count(self):
        return self.memberships.filter(is_active=True).count()


class DepartmentMembership(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='memberships')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='department_memberships')
    is_active = models.BooleanField(default=True)
    joined_date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = [('department', 'member', 'is_active')]
        ordering = ['-joined_date']

    def __str__(self):
        return f"{self.member} in {self.department}"
