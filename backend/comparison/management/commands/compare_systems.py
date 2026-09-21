from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from comparison.models import SystemARecord, SystemBEntry, Disagreement, Location


class Command(BaseCommand):
    help = 'Compare System A and System B data to identify disagreements'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Clear existing disagreements
            Disagreement.objects.all().delete()
            
            self.stdout.write('Comparing systems...')
            
            # 1. Find records in System A with no entry in System B
            self.find_missing_in_b()
            
            # 2. Find System B entries pointing to non-existent records
            self.find_orphan_entries()
            
            # 3. Find records with multiple System B entries
            self.find_duplicate_entries()
            
            # 4. Find value mismatches
            self.find_value_mismatches()
            
        total = Disagreement.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Found {total} disagreements'))

    def find_missing_in_b(self):
        """Find records in System A with no corresponding entry in System B"""
        system_a_records = SystemARecord.objects.all()
        
        for record in system_a_records:
            # Check if any System B entry references this record
            has_entry = SystemBEntry.objects.filter(record_ref=record.record_id).exists()
            
            if not has_entry:
                location = record.location_id
                Disagreement.objects.create(
                    record_id=record.record_id,
                    location=location,
                    disagreement_type='MISSING_IN_B',
                    system_a_value=record.total_value,
                    system_b_value=None,
                    details=f'Record {record.record_id} exists in System A but has no entry in System B'
                )
        
        count = Disagreement.objects.filter(disagreement_type='MISSING_IN_B').count()
        self.stdout.write(f'  Found {count} records missing in System B')

    def find_orphan_entries(self):
        """Find System B entries that point to non-existent System A records"""
        system_b_entries = SystemBEntry.objects.all()
        
        for entry in system_b_entries:
            # Check if the referenced record exists in System A
            record_exists = SystemARecord.objects.filter(record_id=entry.record_ref).exists()
            
            if not record_exists:
                location = entry.location_id
                Disagreement.objects.create(
                    record_id=entry.record_ref,
                    location=location,
                    disagreement_type='ORPHAN_ENTRY',
                    system_a_value=None,
                    system_b_value=entry.value,
                    details=f'Entry {entry.entry_id} references non-existent record {entry.record_ref}'
                )
        
        count = Disagreement.objects.filter(disagreement_type='ORPHAN_ENTRY').count()
        self.stdout.write(f'  Found {count} orphan entries')

    def find_duplicate_entries(self):
        """Find records that have multiple System B entries"""
        from django.db.models import Count
        
        # Find record_refs that appear more than once in System B
        duplicates = SystemBEntry.objects.values('record_ref').annotate(
            count=Count('record_ref')
        ).filter(count__gt=1)
        
        for dup in duplicates:
            record_ref = dup['record_ref']
            entries = SystemBEntry.objects.filter(record_ref=record_ref)
            
            # Use the first entry's location
            first_entry = entries.first()
            location = first_entry.location_id
            
            # Get all values for this record
            values = list(entries.values_list('value', flat=True))
            entry_ids = list(entries.values_list('entry_id', flat=True))
            
            Disagreement.objects.create(
                record_id=record_ref,
                location=location,
                disagreement_type='DUPLICATE_ENTRY',
                system_a_value=None,
                system_b_value=first_entry.value,
                details=f'Record {record_ref} has {len(entries)} entries: {", ".join(entry_ids)} with values: {values}'
            )
        
        count = Disagreement.objects.filter(disagreement_type='DUPLICATE_ENTRY').count()
        self.stdout.write(f'  Found {count} records with duplicate entries')

    def find_value_mismatches(self):
        """Find records where System A and System B report different values"""
        system_a_records = SystemARecord.objects.all()
        
        for record in system_a_records:
            # Get System B entries for this record
            entries = SystemBEntry.objects.filter(record_ref=record.record_id)
            
            # Skip if no entries or multiple entries (already handled)
            if entries.count() != 1:
                continue
            
            entry = entries.first()
            
            # Compare values
            # Handle None values
            if record.total_value is None and entry.value is None:
                continue
            
            if record.total_value is None or entry.value is None:
                location = record.location_id
                Disagreement.objects.create(
                    record_id=record.record_id,
                    location=location,
                    disagreement_type='VALUE_MISMATCH',
                    system_a_value=record.total_value,
                    system_b_value=entry.value,
                    details=f'Value mismatch: System A={record.total_value}, System B={entry.value}'
                )
                continue
            
            # Compare decimal values
            if record.total_value != entry.value:
                location = record.location_id
                Disagreement.objects.create(
                    record_id=record.record_id,
                    location=location,
                    disagreement_type='VALUE_MISMATCH',
                    system_a_value=record.total_value,
                    system_b_value=entry.value,
                    details=f'Value mismatch: System A={record.total_value}, System B={entry.value}'
                )
        
        count = Disagreement.objects.filter(disagreement_type='VALUE_MISMATCH').count()
        self.stdout.write(f'  Found {count} value mismatches')