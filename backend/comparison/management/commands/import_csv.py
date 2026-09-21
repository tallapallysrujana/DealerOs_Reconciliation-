import csv
import re
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from django.db import transaction
from comparison.models import Location, SystemARecord, SystemBEntry


class Command(BaseCommand):
    help = 'Import CSV data with dirty data handling'

    def add_arguments(self, parser):
        parser.add_argument('--locations', type=str, help='Path to locations.csv')
        parser.add_argument('--system-a', type=str, help='Path to system_a.csv')
        parser.add_argument('--system-b', type=str, help='Path to system_b.csv')

    def normalize_record_ref(self, record_ref):
        """Normalize dirty record_ref to match System A format (REC-XXXX)"""
        if not record_ref:
            return None
        
        # Strip whitespace
        record_ref = record_ref.strip()
        
        # If already in correct format, return as-is
        if re.match(r'^REC-\d+$', record_ref):
            return record_ref
        
        # Handle various dirty formats
        # Remove any non-alphanumeric characters except digits
        cleaned = re.sub(r'[^A-Za-z0-9]', '', record_ref)
        
        # Handle "rec1034" -> "REC-1034"
        if re.match(r'^rec\d+$', cleaned, re.IGNORECASE):
            number = re.sub(r'^rec', '', cleaned, flags=re.IGNORECASE)
            return f"REC-{number}"
        
        # Handle "1112" -> "REC-1112"
        if re.match(r'^\d+$', cleaned):
            return f"REC-{cleaned}"
        
        # Handle "REC1070" -> "REC-1070"
        if re.match(r'^REC\d+$', cleaned):
            number = re.sub(r'^REC', '', cleaned)
            return f"REC-{number}"
        
        # Return original if no pattern matches
        return record_ref

    def parse_decimal(self, value):
        """Parse decimal value from potentially dirty string"""
        if not value or value.strip() == '':
            return None
        
        try:
            # Remove commas and other formatting
            cleaned = value.replace(',', '').strip()
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None

    def handle(self, *args, **options):
        locations_path = options.get('locations', 'locations.csv')
        system_a_path = options.get('system_a', 'system_a.csv')
        system_b_path = options.get('system_b', 'system_b.csv')

        with transaction.atomic():
            # Import locations
            self.stdout.write('Importing locations...')
            self.import_locations(locations_path)
            
            # Import System A
            self.stdout.write('Importing System A records...')
            self.import_system_a(system_a_path)
            
            # Import System B
            self.stdout.write('Importing System B entries...')
            self.import_system_b(system_b_path)

        self.stdout.write(self.style.SUCCESS('Import completed successfully'))

    def import_locations(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                Location.objects.update_or_create(
                    location_id=row['location_id'],
                    defaults={
                        'org_id': row['org_id'],
                        'location_name': row['location_name']
                    }
                )
        self.stdout.write(f'  Imported {Location.objects.count()} locations')

    def import_system_a(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            imported = 0
            errors = 0
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    location = Location.objects.get(location_id=row['location_id'])
                    
                    SystemARecord.objects.update_or_create(
                        record_id=row['record_id'],
                        defaults={
                            'location_id': location,
                            'event_date': row['event_date'],
                            'category_code': row['category_code'] if row['category_code'] else None,
                            'actor_id': row['actor_id'] if row['actor_id'] else None,
                            'base_value': self.parse_decimal(row['base_value']),
                            'adjustment': self.parse_decimal(row['adjustment']),
                            'total_value': self.parse_decimal(row['total_value']),
                            'state': row['state']
                        }
                    )
                    imported += 1
                except Location.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Row {row_num}: Location {row["location_id"]} not found, skipping record {row["record_id"]}'
                        )
                    )
                    errors += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Row {row_num}: Error importing record {row.get("record_id", "unknown")}: {str(e)}'
                        )
                    )
                    errors += 1
            
            self.stdout.write(f'  Imported {imported} records, {errors} errors')

    def import_system_b(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            imported = 0
            errors = 0
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    location = Location.objects.get(location_id=row['location_id'])
                    
                    # Normalize the record_ref
                    normalized_ref = self.normalize_record_ref(row['record_ref'])
                    
                    # Parse value (handle dirty formats like "1,25,400.00")
                    value = self.parse_decimal(row['value'])
                    
                    error_msg = None
                    if value is None and row['value'] and row['value'].strip():
                        error_msg = f"Could not parse value: {row['value']}"
                    
                    SystemBEntry.objects.update_or_create(
                        entry_id=row['entry_id'],
                        defaults={
                            'record_ref': normalized_ref,
                            'location_id': location,
                            'recorded_on': row['recorded_on'],
                            'value': value,
                            'label': row['label'] if row['label'] else None,
                            'import_error': error_msg
                        }
                    )
                    imported += 1
                    
                    if error_msg:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  Row {row_num}: {error_msg} for entry {row["entry_id"]}'
                            )
                        )
                        
                except Location.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Row {row_num}: Location {row["location_id"]} not found, skipping entry {row["entry_id"]}'
                        )
                    )
                    errors += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Row {row_num}: Error importing entry {row.get("entry_id", "unknown")}: {str(e)}'
                        )
                    )
                    errors += 1
            
            self.stdout.write(f'  Imported {imported} entries, {errors} errors')