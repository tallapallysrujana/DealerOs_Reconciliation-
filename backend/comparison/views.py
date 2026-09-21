from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from comparison.models import Disagreement
from comparison.serializers import DisagreementSerializer


class DisagreementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Disagreement.objects.all()
    serializer_class = DisagreementSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['disagreement_type', 'location__org_id']
    ordering_fields = ['system_a_value', 'system_b_value', 'created_at', 'record_id']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by org_id if provided (for tenant isolation)
        org_id = self.request.query_params.get('org_id', None)
        if org_id:
            queryset = queryset.filter(location__org_id=org_id)
        
        return queryset