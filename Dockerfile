FROM python:3.7-slim-stretch
MAINTAINER Samuel Martey "dansam100@gmail.com"

RUN apt-get update -y
RUN apt-get install -y build-essential libopenblas-dev liblapack-dev cmake
RUN apt-get install -y gcc patch  wget curl nano

# Install Subversion 1.8 and Apache
RUN apt-get install -y subversion

# Install Git
RUN apt-get update && apt-get upgrade -y && apt-get install -y git

COPY . /app
WORKDIR /app

RUN pip install -r requirements.d.txt

CMD ["python3", "./app.py"]