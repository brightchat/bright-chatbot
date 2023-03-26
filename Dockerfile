FROM python:3.9-slim-buster

# Install dependencies
RUN apt-get update
RUN pip install --upgrade pip setuptools wheel

# Add the source code
ADD . /bright_chatbot

RUN pip install -e "/bright_chatbot[twilio-provider,dynamodb-backend]"

WORKDIR /app
