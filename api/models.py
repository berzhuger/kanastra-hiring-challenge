from django.db import models
from .constants import InvoiceStatusChoices


class Debt(models.Model):
    name = models.CharField(max_length=255)
    government_id = models.CharField(max_length=20)
    email = models.EmailField()
    debt_amount = models.DecimalField(max_digits=10, decimal_places=2)
    debt_due_date = models.DateField()
    debt_id = models.UUIDField()


class Invoice(models.Model):
    debt = models.ForeignKey(Debt, on_delete=models.CASCADE)
    invoice_status = models.CharField(
        max_length=20,
        choices=InvoiceStatusChoices.choices,
        default=InvoiceStatusChoices.PENDING,
    )
    generated_at = models.DateTimeField(auto_now_add=True)


class EmailLog(models.Model):
    debt = models.ForeignKey(Debt, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10)
