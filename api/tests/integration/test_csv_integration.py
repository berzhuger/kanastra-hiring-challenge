import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from io import BytesIO

from api.models import Debt
from api.tasks import save_debts_in_batch


@pytest.mark.django_db
def test_csv_upload_success(mocker):
    client = APIClient()
    mock_process_csv_file = mocker.patch('api.tasks.process_csv_file.delay')
    csv_content = b'name,governmentId,email,debtAmount,debtDueDate,debtId\nJohn Doe,12345678901,johndoe@test.com,1000.00,2023-01-01,1a1b6ccf-ff16-467f-bea7-5f05d494280f\n'
    csv_file = BytesIO(csv_content)
    csv_file.name = 'test.csv'
    url = reverse('csv-upload')
    response = client.post(url, {'file': csv_file}, format='multipart')
    assert response.status_code == 202
    assert response.json() == {
        'status': 'success',
        'message': 'O arquivo CSV está sendo processado'
    }
    mock_process_csv_file.assert_called_once()


@pytest.mark.django_db
def test_csv_upload_no_file():
    client = APIClient()
    url = reverse('csv-upload')
    response = client.post(url, {}, format='multipart')
    assert response.status_code == 400
    assert response.json() == {"error": "Nenhum arquivo foi enviado"}


@pytest.mark.django_db
def test_csv_upload_invalid_file_format():
    client = APIClient()
    txt_file = BytesIO(b'text file.')
    txt_file.name = 'test.txt'
    url = reverse('csv-upload')
    response = client.post(url, {'file': txt_file}, format='multipart')
    assert response.status_code == 400
    assert response.json() == {"error": "Formato de arquivo inválido"}


@pytest.mark.django_db
def test_process_csv_row_detect_duplicate(mocker):
    existing_debt = Debt.objects.create(
        name="John Doe",
        government_id="12345678901",
        email="johndoe@test.com",
        debt_amount=1000.00,
        debt_due_date="2023-01-01",
        debt_id="1a1b6ccf-ff16-467f-bea7-5f05d494280f"
    )
    row = {
        'name': 'John Doe',
        'governmentId': '12345678901',
        'email': 'johndoe@test.com',
        'debtAmount': '1000.00',
        'debtDueDate': '2023-01-01',
        'debtId': '1a1b6ccf-ff16-467f-bea7-5f05d494280f'
    }
    mock_check_invoice = mocker.patch('api.tasks.check_invoice.delay')
    mock_check_email = mocker.patch('api.tasks.check_email.delay')
    from api.tasks import process_csv_row
    batch = []
    process_csv_row(row, batch, 1)
    mock_check_invoice.assert_called_once_with(existing_debt.id)
    mock_check_email.assert_called_once_with(existing_debt.id)
    assert len(batch) == 0


@pytest.mark.django_db
def test_save_debts_in_batch(mocker):
    debts = [
        {'name': 'John Doe', 'government_id': '12345678901', 'email': 'johndoe@test.com', 'debt_amount': 1000.00, 'debt_due_date': '2023-01-01', 'debt_id': '1a1b6ccf-ff16-467f-bea7-5f05d494280f'},
        {'name': 'Jane Doe', 'government_id': '12345678902', 'email': 'janedoe@test.com', 'debt_amount': 2000.00, 'debt_due_date': '2023-02-01', 'debt_id': '2b2b6ccf-ff16-467f-bea7-5f05d494280f'}
    ]
    mock_check_invoice = mocker.patch('api.tasks.check_invoice.delay')
    mock_check_email = mocker.patch('api.tasks.check_email.delay')
    save_debts_in_batch(debts)
    assert Debt.objects.count() == 2
    assert mock_check_invoice.call_count == 2
    assert mock_check_email.call_count == 2
