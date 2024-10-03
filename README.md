# Kanastra Hiring Challenge

Projeto de teste para Soft. Engineers Backend na empresa Kanastra
Backend desenvolvido em Django Rest Framework, Celery e Postgres.

Adicionado Flower para monitoramento de tarefas do Celery.
Pode ser acessado em http://localhost:5555


## Requisitos

- Python 3.12.3
- Docker
- Docker Compose

## Instalação

1. Clone o repositório:
   ```sh
   git clone https://seu-repositorio-url.git
   cd nome-do-projeto
   ```

## Uso

1. Construa e inicie os containers do Docker:
   ```sh
   docker-compose up --build
   ```

2. Execute as migrações do banco de dados:
   ```sh
   docker-compose exec web poetry run python manage.py migrate
   ```

3. Para rodar os testes:
   ```sh
   docker-compose run tests
   ```

Exemplo de requisição para a API:

```sh
curl --request POST \
  --url http://127.0.0.1:8000/process-csv/ \
  --header 'Content-Type: multipart/form-data' \
  --form file=@/seu/arquivo/input.csv
```
Exemplo de arquivo CSV:

```csv
name,governmentId,email,debtAmount,debtDueDate,debtId
Elijah Santos,9558,janet95@example.com,7811,2024-01-19,ea23f2ca-663a-4266-a742-9da4c9f4fcb3
Samuel Orr,5486,linmichael@example.com,5662,2023-02-25,acc1794e-b264-4fab-8bb7-3400d4c4734d
Leslie Morgan,9611,russellwolfe@example.net,6177,2022-10-17,9f5a2b0c-967e-4443-a03d-9d7cdcb2216f
Joseph Rivera,1126,urangel@example.org,7409,2023-08-16,33bec852-beee-477f-ae65-1475c74e1966
```
