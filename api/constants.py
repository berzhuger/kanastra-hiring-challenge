from django.db import models


class InvoiceStatusChoices(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    PROCESSED = 'Processed', 'Processed'
