FROM python:3.10

COPY . /app

COPY ./requirements.txt /app/requirements.txt

WORKDIR app

EXPOSE 8000

RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]