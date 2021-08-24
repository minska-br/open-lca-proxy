FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt
RUN pip install git+https://github.com/minska-br/olca-ipc.py.git

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]