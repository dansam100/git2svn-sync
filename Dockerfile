FROM python:3.6-slim-stretch
MAINTAINER Samuel Martey "dansam100@gmail.com"

RUN apt-get update -y
RUN apt-get install -y build-essential libopenblas-dev liblapack-dev cmake

COPY . /app
WORKDIR /app

RUN pip install -r requirements.d.txt

CMD ["python3", "./app.py"]