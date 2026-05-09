from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Loans, Fines, Waitlists
from .serializers import LoanListSerializer, LoanCreateSerializer, LoanReturnSerializer, FineSerializer, \
    WaitlistSerializer
from drf_spectacular.utils import extend_schema

from rest_framework import permissions
from ..users.permissions import IsLibrarian


@extend_schema(tags=['Loans'])
class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loans.objects.all().select_related('copy__book', 'user', 'issued_by')

    def get_serializer_class(self):
        if self.action == 'create':
            return LoanCreateSerializer
        if self.action == 'return_book':
            return LoanReturnSerializer
        return LoanListSerializer

    def perform_create(self, serializer):
        serializer.save(issued_by=self.request.user)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        loan = self.get_object()
        serializer = LoanReturnSerializer(loan, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "Kitob topshirildi"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_permissions(self):
        # Kitobni ijaraga berish va tahrirlashni faqat kutubxonachi qila oladi
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'return_book']:
            return [IsLibrarian]
        return [permissions.IsAuthenticated()]

@extend_schema(tags=['Fines'])
class FineViewSet(viewsets.ModelViewSet):
    queryset = Fines.objects.all().select_related('loan__user', 'paid_by')
    serializer_class = FineSerializer

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        fine = self.get_object()
        if fine.is_paid:
            return Response({'detail': "Jarima allaqachon to'langan"}, status=400)

        fine.is_paid = True
        fine.paid_at = timezone.now()
        fine.paid_by = request.user
        fine.save()

        user = fine.loan.user
        user.balance -= fine.amount
        user.save()

        return Response({'status': "To'lov qabul qilindi"})


class WaitlistViewSet(viewsets.ModelViewSet):
    queryset = Waitlists.objects.all()
    serializer_class = WaitlistSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)