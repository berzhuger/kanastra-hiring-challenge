import json
import pytest
from api.views import CSVUploadView
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory
from unittest.mock import patch


@pytest.fixture
def api_factory():
    return APIRequestFactory()


@pytest.fixture
def csv_view():
    return CSVUploadView.as_view()


@pytest.fixture
def fake_csv_file():
    return SimpleUploadedFile("test.csv", b"name,governmentId,email,debtAmount,debtDueDate,debtId\nJohn Doe,11111111111,johndoe@kanastra.com.br,1000000.00,2022-10-12,1a1b6ccf-ff16-467f-bea7-5f05d494280f\n")



def test_csv_upload_view_post_success(api_factory, csv_view, fake_csv_file):
    with patch('api.views.process_csv_file.delay') as mock_process:
        mock_process.return_value = None
        request = api_factory.post('api/csv-upload', {'file': fake_csv_file}, format='multipart')
        response = csv_view(request)
        assert response.status_code == 202
        response_data = json.loads(response.content)
        assert response_data == {
            'status': 'success',
            'message': 'O arquivo CSV está sendo processado'
        }
        mock_process.assert_called_once()


def test_csv_upload_view_no_file(api_factory, csv_view):
    request = api_factory.post('api/csv-upload', {}, format='multipart')
    response = csv_view(request)
    assert response.status_code == 400
    response_data = json.loads(response.content)
    assert response_data == {
        "error": "Nenhum arquivo foi enviado"
    }


def test_csv_upload_view_not_csv_file(api_factory, csv_view):
    fake_text_file = SimpleUploadedFile("test.txt", b"nome,email\nTeste,teste@teste.com\n")
    request = api_factory.post('api/csv-upload', {'file': fake_text_file}, format='multipart')
    response = csv_view(request)
    assert response.status_code == 400
    response_data = json.loads(response.content)
    assert response_data == {
        "error": "Formato de arquivo inválido"
    }


def test_csv_upload_view_file_processing_error(api_factory, csv_view, fake_csv_file):
    with patch('api.views.process_csv_file.delay', side_effect=Exception):
        request = api_factory.post('api/csv-upload', {'file': fake_csv_file}, format='multipart')
        response = csv_view(request)
        assert response.status_code == 500
        response_data = json.loads(response.content)
        assert response_data == {
            "error": "Erro ao processar arquivo"
        }

def test_csv_upload_view_invalid_data(api_factory, csv_view):
    fake_text_file = SimpleUploadedFile("test.txt", b"nome,email\nTeste,teste@teste.com\n")
    request = api_factory.post('api/csv-upload', {'file': fake_text_file}, format='multipart')
    response = csv_view(request)
    assert response.status_code == 400
    response_data = json.loads(response.content)
    assert response_data == {
        "error": "Formato de arquivo inválido"
    }