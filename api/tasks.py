import csv
from celery import shared_task
from django.db import transaction
from .models import Debt, Invoice, EmailLog
import logging
from .constants import InvoiceStatusChoices

logger = logging.getLogger(__name__)


def log_and_check_invoice(debt):
    if Invoice.objects.filter(debt=debt).exists():
        logger.info(f"Boleto já gerado para {debt.name}")
        return True
    return False


def log_and_check_email(debt):
    if EmailLog.objects.filter(debt=debt).exists():
        logger.info(f"E-mail já enviado para {debt.email}")
        return True
    return False


@shared_task
def check_invoice(debt_id, new=None):
    if new:
        generate_invoice.delay(debt_id)
        return
    debt = Debt.objects.get(id=debt_id)
    if not log_and_check_invoice(debt):
        generate_invoice.delay(debt.id)

@shared_task
def check_email(debt_id, new=None):
    if new:
        send_email.delay(debt_id)
        return
    debt = Debt.objects.get(id=debt_id)
    if not log_and_check_email(debt):
        send_email.delay(debt.id)


@shared_task()
def generate_invoice(debt_id):
    debt = Debt.objects.get(id=debt_id)
    Invoice.objects.create(debt=debt, invoice_status=InvoiceStatusChoices.PROCESSED)
    logger.info(f"Boleto gerado para {debt.name}")


@shared_task()
def send_email(debt_id):
    debt = Debt.objects.filter(id=debt_id).first()
    EmailLog.objects.create(debt=debt, status='Sent')
    logger.info(f"E-mail enviado para {debt.email}")


@shared_task
def process_csv_file(csv_content):
    try:
        batch_size = 2000
        csv_reader = csv.DictReader(csv_content.splitlines())
        batch = []
        for row in csv_reader:
            process_csv_row(row, batch, batch_size)
        if batch:
            save_debts_in_batch(batch)
        logger.info(f"Processamento concluído para {len(batch)} débitos")
    except Exception as e:
        logger.error(f"Erro ao processar o CSV: {str(e)}", exc_info=True)


def process_csv_row(row, batch, batch_size):
    debt = Debt.objects.filter(debt_id=row['debtId']).first()
    if debt:
        logger.info(f"Duplicidade detectada para o debtId: {row['debtId']}")
        check_invoice.delay(debt.id)
        check_email.delay(debt.id)
        return
    debt = {
        'name': row['name'],
        'government_id': row['governmentId'],
        'email': row['email'],
        'debt_amount': row['debtAmount'],
        'debt_due_date': row['debtDueDate'],
        'debt_id': row['debtId']
    }
    batch.append(debt)
    if len(batch) == batch_size:
        save_debts_in_batch(batch)
        batch.clear()


def save_debts_in_batch(debts):
    try:
        with transaction.atomic():
            created_debts = Debt.objects.bulk_create([Debt(**debt) for debt in debts])
        for debt in created_debts:
            check_invoice.delay(debt.id, new=True)
            check_email.delay(debt.id, new=True)
    except Exception as e:
        logger.error(f"Erro ao salvar débitos em batch: {str(e)}", exc_info=True)
        raise e