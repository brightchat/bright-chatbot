# Web backend API Endpoints

This section describes some of the API endpoints that are available in the web backend.

It uses API Gateway and Lambda to provide a RESTful API to the web backend and can be used to integrate the web backend with other applications.

## Deploy with CloudFormation

The resources for the web backend can be deployed with the CloudFormation stack.

Requires the AWS CLI and the AWS SAM CLI to be installed, follow the instructions [here](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) to install them.

Use the following command to deploy the stack and follow the instructions:

```sh
sam deploy --stack-name brightbot-web --guided
```
