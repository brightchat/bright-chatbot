# OpenAI (ChatGPT) Mobile Chatbot

Python package that uses the OpenAI API to carry out a conversation with OpenAI's incredible language models right from your phone, using WhatApp or SMS (By leveraging the Twilio Provider).

**Features:**

- Strike a conversation with an AI assistant, OpenAI's [ChatGPT](https://openai.com/blog/chatgpt)
- Generate an Image never seen before with OpenAI's [Dall-E](https://openai.com/blog/dall-e/) model

**Coming Soon!**

- Transcribe voice messages to text right from your mobile chat application.

![Image of ChatGPT Mobile Chatbot](docs/images/whatsapp-img-example.jpeg?raw=true "ChatGPT Mobile Chatbot")

## Supported Configurations

### Supported Comms Providers

- [Twillio](https://www.twilio.com/).
    The implemented Twilio Provider allows you to communicate with ChatGPT and generate images with Dall-E by using WhatsApp, or SMS.

### Supported Data Backends

- [AWS DynamoDB](https://aws.amazon.com/dynamodb/).
    See the [DynamoDB backend documentation](openai_mobile/backends/dynamodb/backend.py) to see
    how to setup the DynamoDB tables.
- [PostgreSQL](https://www.postgresql.org/). (Coming Soon)

## Quick Deployment

### Deploy to your Cloud Infrastructure in AWS

There is a handy CloudFormation script that you can use to easily deploy the Application on your own AWS account
with just a few commands. The deployed application will be ready to use with the Twilio Provider and the DynamoDB backend.
It will also be highly scalable and fault tolerant by using AWS' family of serverless resources.

The cloudformation stack handles the creation of the DynamoDB tables,
the creation of the Lambda functions, and an API Gateway endpoint
that can be used as the Callback URL of your Twilio messaging service.

**Just go to the `deploy/cloudformation` directory and follow [these instructions](deploy/cloudformation/README.md) to deploy the application.**

## Setup

Requirements:

- Python >= 3.8

Install the Client by running:

```sh
pip install -e .
```

Or install it with a supported provider or backend:

```sh
pip install -e ".[dynamodb-backend,twilio-provider]"
```

The following environment variables are required by the application:

Variable Name | Description
--- | ---
`OPENAI_API_KEY` | API Key for the OpenAI API. You can get one from [here](https://platform.openai.com/docs/api-reference/authentication)
`OPENAI_MOBILE_SECRET_KEY` | Secret key used to cryptographically sign sensitive data. You can generate one using the command: `openssl rand -hex 32`

If you are using the Twilio Provider, you'll also need to set the following variables to authenticate with the Twilio API:

Variable Name | Description
--- | ---
`TWILIO_AUTH_TOKEN` | Twilio Authentication Token used to communicate with the Twilio API
`TWILIO_ACCOUNT_SID` | Twilio Account SID
`TWILIO_PHONE_NUMBER` | Twilio Phone Number used to send messages to the user.

> See [Twilio Rest API Credentials Documentation](https://www.twilio.com/docs/iam/credentials/api) for more details.

If you use the DynamoDB backend, you'll also need to set the following variables to authenticate with the AWS API:

Variable Name | Description
--- | ---
`AWS_ACCESS_KEY_ID` | AWS Access Key ID used to communicate with the AWS API
`AWS_SECRET_ACCESS_KEY` | AWS Secret Access Key used to communicate with the AWS API
`AWS_DEFAULT_REGION` | AWS Region where the DynamoDB tables are located

> AWS credentials can also be set using the `~/.aws/credentials` file when the AWS CLI is installed or ignored when taking advantage of an [IAM Role for EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html) feature.
> See [AWS Credentials Documentation](https://docs.aws.amazon.com/general/latest/gr/aws-security-credentials.html) for more details.

## Usage

### Use locally with the Python Client

You can use the `OpenAIChatClient` class to have ChatGPT send messages to an user in response to a request coming
to your own application.

The following example shows how to use the `OpenAIChatClient` with the `TwilioProvider` and the `DynamodbBackend` to
respond to a request coming from Twilio. The class `TwilioProvider` can validate the requests coming from Twilio by checking the signature of the request.

> If you use the Twilio Provider, see the [Twilio Documentation](https://www.twilio.com/docs/messaging/twiml#twilios-request-to-your-application)
> for details on how to setup the Callback URL and check how the requests are sent to your application.

```python
from openai_mobile.client import OpenAIChatClient

from openai_mobile.providers import TwilioProvider
from openai_mobile.backends import DynamodbBackend

from openai_mobile.models import MessagePrompt, User

# Obtain the request object made to your application:
request = get_request()
params = request["params"]
headers = request["headers"]
signature  = headers["X-Twilio-Signature"]
callback_url = f"{request['scheme']}://{request['Host']}{request['path']}"

# Verify that the request is actually coming from Twilio:
TwilioProvider.verify_signature(
    callback_url=callback_url,
    request_params=params,
    signature=signature,
    raise_on_failure=True
)

# Create the client and reply to the user:
client = OpenAIChatClient(
    backend=DynamodbBackend(),
    provider=TwilioProvider(),
)
user = User(
    user_id=request["from"]
)
prompt = MessagePrompt(
    body=request["body"],
    from_user=user
)
client.reply(prompt)
```
