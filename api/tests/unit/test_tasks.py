import uuid
import pytest
from unittest.mock import MagicMock
from api.constants import InvoiceStatusChoices
from api.tasks import (
    log_and_check_invoice, log_and_check_email,
    check_invoice, check_email, generate_invoice,
    send_email, process_csv_file, process_csv_row, save_debts_in_batch
)


@pytest.fixture
def debt():
    return {
        'name': 'John',
        'governmentId': '1234',
        'email': 'john@email.com',
        'debtAmount': '5000',
        'debtDueDate': '2024-12-31',
        'debtId': uuid.uuid4()
    }


@pytest.mark.django_db
def test_process_csv_row_without_existing_debt(debt):
    batch = []
    process_csv_row(debt, batch, 10)
    assert len(batch) == 1


@pytest.mark.django_db
def test_process_csv_row_batches(mocker, debt):
    batch = []
    mock_check_invoice = mocker.patch('api.tasks.check_invoice.delay')
    mock_check_email = mocker.patch('api.tasks.check_email.delay')
    for i in range(9):
        process_csv_row(debt, batch, 10)
    assert len(batch) == 9
    process_csv_row(debt, batch, 10)
    assert len(batch) == 0


def test_log_and_check_invoice(mocker):
    debt = MagicMock()
    mock_invoice = mocker.patch('api.tasks.Invoice.objects.filter')
    mock_invoice.return_value.exists.return_value = True

    result = log_and_check_invoice(debt)

    mock_invoice.assert_called_once_with(debt=debt)
    assert result is True

    mock_invoice.return_value.exists.return_value = False
    result = log_and_check_invoice(debt)
    assert result is False


def test_log_and_check_email(mocker):
    debt = MagicMock()
    mock_email_log = mocker.patch('api.tasks.EmailLog.objects.filter')
    mock_email_log.return_value.exists.return_value = True

    result = log_and_check_email(debt)

    mock_email_log.assert_called_once_with(debt=debt)
    assert result is True

    mock_email_log.return_value.exists.return_value = False
    result = log_and_check_email(debt)
    assert result is False


@pytest.mark.django_db
def test_check_invoice(mocker):
    mocker.patch('api.tasks.Debt.objects.get', return_value=MagicMock(id=1))
    mock_log_and_check = mocker.patch('api.tasks.log_and_check_invoice', return_value=False)
    mock_generate_invoice = mocker.patch('api.tasks.generate_invoice.delay')

    check_invoice(1)

    mock_log_and_check.assert_called_once()
    mock_generate_invoice.assert_called_once_with(1)


@pytest.mark.django_db
def test_check_email(mocker):
    mocker.patch('api.tasks.Debt.objects.get', return_value=MagicMock(id=1))
    mock_log_and_check = mocker.patch('api.tasks.log_and_check_email', return_value=False)
    mock_send_email = mocker.patch('api.tasks.send_email.delay')

    check_email(1)

    mock_log_and_check.assert_called_once()
    mock_send_email.assert_called_once_with(1)


@pytest.mark.django_db
def test_generate_invoice(mocker):
    debt = MagicMock()
    mocker.patch('api.tasks.Debt.objects.get', return_value=debt)
    mock_invoice_create = mocker.patch('api.tasks.Invoice.objects.create')

    generate_invoice(debt.id)

    mock_invoice_create.assert_called_once_with(debt=debt, invoice_status=InvoiceStatusChoices.PROCESSED)


@pytest.mark.django_db
def test_send_email(mocker):
    debt = MagicMock()
    mock_debt_filter = mocker.patch('api.tasks.Debt.objects.filter')
    mock_debt_filter.return_value.first.return_value = debt
    mock_email_log_create = mocker.patch('api.tasks.EmailLog.objects.create')

    send_email(debt.id)

    mock_email_log_create.assert_called_once_with(debt=debt, status='Sent')


@pytest.mark.django_db
def test_save_debts_in_batch(mocker):
    debts = [{'name': 'John Doe', 'debt_id': uuid.uuid4()}]
    mock_bulk_create = mocker.patch('api.tasks.Debt.objects.bulk_create', return_value=[MagicMock(id=1)])
    mock_check_invoice = mocker.patch('api.tasks.check_invoice.delay')
    mock_check_email = mocker.patch('api.tasks.check_email.delay')

    save_debts_in_batch(debts)

    mock_bulk_create.assert_called_once()
    mock_check_invoice.assert_called_once_with(1, new=True)
    mock_check_email.assert_called_once_with(1, new=True)


def test_process_csv_file_with_batch_control(mocker):
    csv_content = f"""name,governmentId,email,debtAmount,debtDueDate,debtId
    John Doe,12345678901,johndoe@test.com,1000.00,2023-01-01,{uuid.uuid4()}
    Jane Doe,12345678902,janedoe@test.com,500.00,2023-02-01,{uuid.uuid4()}"""
    def mock_process_row(row, batch, batch_size):
        batch.append(row)
    mock_process_csv_row = mocker.patch('api.tasks.process_csv_row', side_effect=mock_process_row)
    mock_save_debts_in_batch = mocker.patch('api.tasks.save_debts_in_batch')
    process_csv_file(csv_content)
    assert mock_process_csv_row.call_count == 2
    mock_save_debts_in_batch.assert_called_once()
