from django.db import models


class Location(models.Model):
    location_id = models.CharField(max_length=50, unique=True, primary_key=True)
    org_id = models.CharField(max_length=50)
    location_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'locations'

    def __str__(self):
        return f"{self.location_id} - {self.location_name}"


class SystemARecord(models.Model):
    record_id = models.CharField(max_length=50, unique=True, primary_key=True)
    location_id = models.ForeignKey(Location, on_delete=models.PROTECT, db_column='location_id')
    event_date = models.DateField()
    category_code = models.CharField(max_length=50, null=True, blank=True)
    actor_id = models.CharField(max_length=50, null=True, blank=True)
    base_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    adjustment = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    total_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    state = models.CharField(max_length=50)

    class Meta:
        db_table = 'system_a_records'

    def __str__(self):
        return f"{self.record_id} - {self.total_value}"


class SystemBEntry(models.Model):
    entry_id = models.CharField(max_length=50, unique=True, primary_key=True)
    record_ref = models.CharField(max_length=50, db_index=True)  # Can be dirty, not a foreign key
    location_id = models.ForeignKey(Location, on_delete=models.PROTECT, db_column='location_id')
    recorded_on = models.DateField()
    value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    label = models.CharField(max_length=255, null=True, blank=True)
    import_error = models.TextField(null=True, blank=True)  # Track import errors

    class Meta:
        db_table = 'system_b_entries'

    def __str__(self):
        return f"{self.entry_id} -> {self.record_ref}"


class Disagreement(models.Model):
    DISAGREEMENT_TYPES = [
        ('MISSING_IN_B', 'Record missing in System B'),
        ('ORPHAN_ENTRY', 'System B entry points to non-existent record'),
        ('DUPLICATE_ENTRY', 'Record has multiple System B entries'),
        ('VALUE_MISMATCH', 'Value mismatch between systems'),
    ]

    record_id = models.CharField(max_length=50, db_index=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    disagreement_type = models.CharField(max_length=50, choices=DISAGREEMENT_TYPES)
    system_a_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    system_b_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'disagreements'
        indexes = [
            models.Index(fields=['disagreement_type']),
            models.Index(fields=['system_a_value']),
            models.Index(fields=['system_b_value']),
        ]

    def __str__(self):
        return f"{self.record_id} - {self.disagreement_type}"
