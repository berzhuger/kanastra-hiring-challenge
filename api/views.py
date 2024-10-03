from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
import logging
from .tasks import process_csv_file

logger = logging.getLogger(__name__)

class CSVUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        """
        Processa o arquivo CSV enviado pelo usuário de forma assíncrona.
        Cria débitos e dispara tarefas de geração de boletos e envio de e-mails em segundo plano.
        """
        # Verificar se um arquivo foi enviado
        if not request.FILES.get('file'):
            logger.error("Nenhum arquivo foi enviado")
            return JsonResponse({"error": "Nenhum arquivo foi enviado"}, status=400)

        try:
            # Verificar se o arquivo é CSV
            csv_file = request.FILES['file']
            if not csv_file.name.endswith('.csv'):
                logger.error(f"Formato de arquivo inválido: {csv_file.name}")
                return JsonResponse({"error": "Formato de arquivo inválido"}, status=400)

            # Disparar a task para processamento assíncrono do CSV
            process_csv_file.delay(csv_file.read().decode('utf-8'))

            logger.info(f"Processamento assíncrono iniciado para o arquivo: {csv_file.name}")
            return JsonResponse({'status': 'success', 'message': 'O arquivo CSV está sendo processado'}, status=202)

        except Exception as e:
            logger.error(f"Erro ao processar o CSV: {str(e)}", exc_info=True)
            return JsonResponse({"error": "Erro ao processar arquivo"}, status=500)
