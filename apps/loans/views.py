from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.users.models import User
from apps.users.permissions import IsLibrarian
from .models import Fines, Loans, Waitlists
from .serializers import (
    FineSerializer,
    LoanCreateSerializer,
    LoanListSerializer,
    LoanReturnSerializer,
    WaitlistSerializer,
)
from .services import approve_loan_request, pay_fine


@extend_schema(tags=["Loans"])
class LoanViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Loans.objects.all().select_related(
        "copy",
        "copy__book",
        "copy__book__author",
        "user",
        "issued_by",
        "returned_to",
    )

    def get_queryset(self):
        user = getattr(self.request, "user", None)
        qs = self.queryset

        if not user or not user.is_authenticated:
            return qs.none()

        if user.role in {User.Role.ADMIN, User.Role.SUPER_ADMIN}:
            return qs

        return qs.filter(user=user)

    def get_serializer_class(self):
        if self.action == "create":
            return LoanCreateSerializer
        if self.action == "return_book":
            return LoanReturnSerializer
        return LoanListSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated()]
        if self.action in ["approve", "return_book"]:
            return [IsLibrarian()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        loan = serializer.save()

        output = LoanListSerializer(loan, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        loan = self.get_object()
        loan = approve_loan_request(loan=loan, actor=request.user)

        loan = self.queryset.get(pk=loan.pk)
        serializer = LoanListSerializer(loan, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def return_book(self, request, pk=None):
        loan = self.get_object()
        serializer = self.get_serializer(
            loan,
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        loan = serializer.save()

        loan = self.queryset.get(pk=loan.pk)
        output = LoanListSerializer(loan, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_200_OK)


@extend_schema(tags=["Fines"])
class FineViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Fines.objects.all().select_related(
        "loan",
        "loan__user",
        "loan__copy",
        "loan__copy__book",
        "paid_by",
    )
    serializer_class = FineSerializer

    def get_queryset(self):
        user = getattr(self.request, "user", None)
        qs = self.queryset

        if not user or not user.is_authenticated:
            return qs.none()

        if user.role in {User.Role.ADMIN, User.Role.SUPER_ADMIN}:
            return qs

        return qs.filter(loan__user=user)

    def get_permissions(self):
        if self.action == "pay":
            return [IsLibrarian()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        fine = self.get_object()
        fine = pay_fine(fine=fine, actor=request.user)
        fine = self.queryset.get(pk=fine.pk)
        serializer = self.get_serializer(fine, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["Waitlists"])
class WaitlistViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Waitlists.objects.all().select_related("book", "book__author", "user")
    serializer_class = WaitlistSerializer

    def get_queryset(self):
        user = getattr(self.request, "user", None)
        qs = self.queryset

        if not user or not user.is_authenticated:
            return qs.none()

        if user.role in {User.Role.ADMIN, User.Role.SUPER_ADMIN}:
            return qs

        return qs.filter(user=user)

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        waitlist = serializer.save()

        output = self.get_serializer(waitlist, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_201_CREATED)