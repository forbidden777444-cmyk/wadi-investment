from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class AgentProfile(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    phone = models.CharField(max_length=30)
    agent_code = models.CharField(max_length=30, unique=True)
    status = models.CharField(
        max_length=10,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.status})"


class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    national_id = models.CharField(max_length=30, unique=True)
    address = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="customers_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Loan(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="loans"
    )
    principal = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("25.00")
    )
    term_days = models.PositiveIntegerField(default=30)
    issued_on = models.DateField(default=timezone.localdate)
    issued_at = models.DateTimeField(auto_now_add=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="loans_issued"
    )

    @property
    def total_due(self):
        interest = self.principal * self.interest_rate / Decimal("100")
        total = self.principal + interest
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def amount_paid(self):
        result = self.payments.aggregate(total=Sum("amount"))["total"]
        return result or Decimal("0.00")

    @property
    def balance(self):
        return max(self.total_due - self.amount_paid, Decimal("0.00"))

    @property
    def daily_installment(self):
        if not self.term_days:
            return Decimal("0.00")
        return (self.total_due / Decimal(self.term_days)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

    @property
    def next_payment_due(self):
        if self.balance <= 0:
            return Decimal("0.00")

        days_elapsed = (timezone.localdate() - self.issued_on).days + 1
        days_elapsed = max(0, min(days_elapsed, self.term_days))

        scheduled_amount = (
            self.total_due * Decimal(days_elapsed)
            / Decimal(self.term_days)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return min(
            max(scheduled_amount - self.amount_paid, Decimal("0.00")),
            self.balance
        )

    @property
    def is_overdue(self):
        return self.balance > 0 and self.next_payment_due > 0

    def __str__(self):
        return f"Loan #{self.pk} - {self.customer}"


class Payment(models.Model):
    loan = models.ForeignKey(
        Loan,
        on_delete=models.PROTECT,
        related_name="payments"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_on = models.DateField(default=timezone.localdate)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments_recorded"
    )
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of KSh {self.amount} for loan #{self.loan_id}"