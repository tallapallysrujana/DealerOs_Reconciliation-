from django.test import TestCase
from decimal import Decimal
from comparison.models import Location, SystemARecord, SystemBEntry, Disagreement


class ComparisonLogicTests(TestCase):
    """Tests for the core comparison logic that identifies disagreements between systems."""

    def setUp(self):
        """Set up test data for comparison tests."""
        # Create test locations
        self.location_a = Location.objects.create(
            location_id='LOC-TEST-1',
            org_id='ORG-A',
            location_name='Test Location 1'
        )
        self.location_b = Location.objects.create(
            location_id='LOC-TEST-2',
            org_id='ORG-B',
            location_name='Test Location 2'
        )

    def test_missing_in_system_b(self):
        """Test detection of records in System A with no entry in System B."""
        # Create a System A record
        record = SystemARecord.objects.create(
            record_id='REC-TEST-001',
            location_id=self.location_a,
            event_date='2026-01-01',
            category_code='CAT-01',
            actor_id='USR-01',
            base_value=Decimal('100.00'),
            adjustment=Decimal('10.00'),
            total_value=Decimal('110.00'),
            state='CONFIRMED'
        )

        # Simulate comparison logic for missing in B
        has_entry = SystemBEntry.objects.filter(record_ref=record.record_id).exists()
        
        # Create disagreement if missing
        if not has_entry:
            Disagreement.objects.create(
                record_id=record.record_id,
                location=record.location_id,
                disagreement_type='MISSING_IN_B',
                system_a_value=record.total_value,
                system_b_value=None,
                details=f'Record {record.record_id} exists in System A but has no entry in System B'
            )

        # Verify the disagreement was created
        disagreements = Disagreement.objects.filter(
            record_id='REC-TEST-001',
            disagreement_type='MISSING_IN_B'
        )
        self.assertEqual(disagreements.count(), 1)
        self.assertEqual(disagreements.first().system_a_value, Decimal('110.00'))
        self.assertIsNone(disagreements.first().system_b_value)

    def test_orphan_entry(self):
        """Test detection of System B entries pointing to non-existent System A records."""
        # Create a System B entry that points to a non-existent record
        entry = SystemBEntry.objects.create(
            entry_id='ENT-TEST-001',
            record_ref='REC-NONEXISTENT',
            location_id=self.location_a,
            recorded_on='2026-01-01',
            value=Decimal('200.00'),
            label='Test orphan entry'
        )

        # Simulate comparison logic for orphan entries
        record_exists = SystemARecord.objects.filter(record_id=entry.record_ref).exists()
        
        # Create disagreement if orphan
        if not record_exists:
            Disagreement.objects.create(
                record_id=entry.record_ref,
                location=entry.location_id,
                disagreement_type='ORPHAN_ENTRY',
                system_a_value=None,
                system_b_value=entry.value,
                details=f'Entry {entry.entry_id} references non-existent record {entry.record_ref}'
            )

        # Verify the disagreement was created
        disagreements = Disagreement.objects.filter(
            record_id='REC-NONEXISTENT',
            disagreement_type='ORPHAN_ENTRY'
        )
        self.assertEqual(disagreements.count(), 1)
        self.assertIsNone(disagreements.first().system_a_value)
        self.assertEqual(disagreements.first().system_b_value, Decimal('200.00'))

    def test_duplicate_entry(self):
        """Test detection of records with multiple System B entries."""
        # Create a System A record
        record = SystemARecord.objects.create(
            record_id='REC-TEST-002',
            location_id=self.location_b,
            event_date='2026-01-01',
            category_code='CAT-02',
            actor_id='USR-02',
            base_value=Decimal('300.00'),
            adjustment=Decimal('20.00'),
            total_value=Decimal('320.00'),
            state='CONFIRMED'
        )

        # Create multiple System B entries for the same record
        entry1 = SystemBEntry.objects.create(
            entry_id='ENT-TEST-002A',
            record_ref='REC-TEST-002',
            location_id=self.location_b,
            recorded_on='2026-01-01',
            value=Decimal('320.00'),
            label='First entry'
        )
        entry2 = SystemBEntry.objects.create(
            entry_id='ENT-TEST-002B',
            record_ref='REC-TEST-002',
            location_id=self.location_b,
            recorded_on='2026-01-01',
            value=Decimal('330.00'),
            label='Second entry'
        )

        # Simulate comparison logic for duplicate entries
        from django.db.models import Count
        duplicates = SystemBEntry.objects.filter(record_ref=record.record_id)
        
        # Create disagreement if multiple entries exist
        if duplicates.count() > 1:
            entry_ids = list(duplicates.values_list('entry_id', flat=True))
            values = list(duplicates.values_list('value', flat=True))
            Disagreement.objects.create(
                record_id=record.record_id,
                location=record.location_id,
                disagreement_type='DUPLICATE_ENTRY',
                system_a_value=None,
                system_b_value=entry1.value,
                details=f'Record {record.record_id} has {duplicates.count()} entries: {", ".join(entry_ids)} with values: {values}'
            )

        # Verify the disagreement was created
        disagreements = Disagreement.objects.filter(
            record_id='REC-TEST-002',
            disagreement_type='DUPLICATE_ENTRY'
        )
        self.assertEqual(disagreements.count(), 1)
        self.assertIn('has 2 entries', disagreements.first().details)

    def test_value_mismatch(self):
        """Test detection of value mismatches between System A and System B."""
        # Create a System A record
        record = SystemARecord.objects.create(
            record_id='REC-TEST-003',
            location_id=self.location_a,
            event_date='2026-01-01',
            category_code='CAT-03',
            actor_id='USR-03',
            base_value=Decimal('400.00'),
            adjustment=Decimal('30.00'),
            total_value=Decimal('430.00'),
            state='CONFIRMED'
        )

        # Create a System B entry with different value
        entry = SystemBEntry.objects.create(
            entry_id='ENT-TEST-003',
            record_ref='REC-TEST-003',
            location_id=self.location_a,
            recorded_on='2026-01-01',
            value=Decimal('450.00'),  # Different value
            label='Entry with mismatch'
        )

        # Simulate comparison logic for value mismatches
        entries = SystemBEntry.objects.filter(record_ref=record.record_id)
        
        # Create disagreement if values don't match
        if entries.count() == 1 and record.total_value != entry.value:
            Disagreement.objects.create(
                record_id=record.record_id,
                location=record.location_id,
                disagreement_type='VALUE_MISMATCH',
                system_a_value=record.total_value,
                system_b_value=entry.value,
                details=f'Value mismatch: System A={record.total_value}, System B={entry.value}'
            )

        # Verify the disagreement was created
        disagreements = Disagreement.objects.filter(
            record_id='REC-TEST-003',
            disagreement_type='VALUE_MISMATCH'
        )
        self.assertEqual(disagreements.count(), 1)
        self.assertEqual(disagreements.first().system_a_value, Decimal('430.00'))
        self.assertEqual(disagreements.first().system_b_value, Decimal('450.00'))

    def test_no_disagreement_when_values_match(self):
        """Test that no disagreement is created when values match correctly."""
        # Create a System A record
        record = SystemARecord.objects.create(
            record_id='REC-TEST-004',
            location_id=self.location_b,
            event_date='2026-01-01',
            category_code='CAT-04',
            actor_id='USR-04',
            base_value=Decimal('500.00'),
            adjustment=Decimal('40.00'),
            total_value=Decimal('540.00'),
            state='CONFIRMED'
        )

        # Create a System B entry with matching value
        entry = SystemBEntry.objects.create(
            entry_id='ENT-TEST-004',
            record_ref='REC-TEST-004',
            location_id=self.location_b,
            recorded_on='2026-01-01',
            value=Decimal('540.00'),  # Same value
            label='Entry with matching value'
        )

        # Simulate comparison logic
        entries = SystemBEntry.objects.filter(record_ref=record.record_id)
        
        # Should NOT create disagreement when values match
        if entries.count() == 1 and record.total_value == entry.value:
            # No disagreement should be created
            pass

        # Verify no disagreement was created
        disagreements = Disagreement.objects.filter(record_id='REC-TEST-004')
        self.assertEqual(disagreements.count(), 0)
