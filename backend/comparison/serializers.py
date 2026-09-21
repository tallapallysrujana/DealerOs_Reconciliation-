from rest_framework import serializers
from comparison.models import Disagreement, Location


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['location_id', 'org_id', 'location_name']


class DisagreementSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='location.location_name', read_only=True)
    org_id = serializers.CharField(source='location.org_id', read_only=True)
    
    class Meta:
        model = Disagreement
        fields = [
            'id', 'record_id', 'location_name', 'org_id', 
            'disagreement_type', 'system_a_value', 'system_b_value', 
            'details', 'created_at'
        ]