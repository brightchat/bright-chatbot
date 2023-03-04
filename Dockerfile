FROM python:3.9-slim-buster

# Install dependencies
RUN apt-get update
RUN pip install --upgrade pip setuptools wheel

# Add the source code
ADD . /openai_mobile

RUN pip install -e "/openai_mobile[twilio-provider,dynamodb-backend]"

WORKDIR /app
