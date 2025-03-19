FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV LOYVERSE_API_TOKEN=40ecae9d03fc4cdab46a005632af23db

EXPOSE 8000 