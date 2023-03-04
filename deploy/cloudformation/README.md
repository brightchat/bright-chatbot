# Cloudformation Template

The cloudformation template provided allows you to quickly start with the application by setting for you all the resoures that are required in your AWS account.

## Cloud Architecture

```mermaid
graph TB
    User -- "1. Send message" --> Entry[Whatsapp] -- "2. Pass message" --> Twilio -- "3. Send a request w/ message" --> API[API-Gateway]
    Lambda[Lambda Function Backend]
    SQS{{SQS Queue}}
    API -- "4. Store message" --> SQS
    Lambda -- "5. Poll the Queue" ---> SQS
    %% == Image Flow ==
    subgraph Backend
        Lambda -- "6. LogSession" --> X-Ray
        DallE["OpenAI API (Dall-E)"]
        DB2[(DynamoDB-Table)]
        S3[S3 Bucket]
        Lambda -- "7. Get Saved Images" --> DB2
        DB2 -- "8. Check requested image exists" --> ImgExists{Image saved?}
        ImgExists --> Yes
        Yes -- 9. Get Image from Bucket --> S3
        ImgExists --> No
        No --  "9. Generate Image" --> DallE
        DallE --> Img[Generated Image]
        Img -- "10. Save Image ID" --> DB2
        Img -- "11. Store Image in S3" --> S3
        S3 -- "10./12. Send Image Pre-Signed URL" --> Response2[\Response/]
    end
    click DallE "https://openai.com/dall-e-2/" _blank
```

## Pre-requisites

1. Install the [AWS SAM CLI](<https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html>)
2. Configure the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

## Instructions

1. Build the deployment packages using:

   ```sh
   sam build
   ```

2. Deploy the resources using the command:

    ```sh
    sam deploy --guided
    ```

    And follow the instructions, you'd be prompted to pass some parameters from the command line such
    as your Twilio Authentication Token, Account SID and phone number to use for sending messages.
    > For Stack Name you can use the name of your application or the repo name `openai-ws-bot`.

3. From the outputs, copy the URL of the development API to use in Twilio:

   ![Cloudformation Outputs](/docs/images/cloudformation-outputs.png?raw=true "Cloudformation Outputs")

4. Copy that url in the endpoint URL field of your Twilio Sandbox configuration

   ![Twilio Sandbox Console](/docs/images/twilio-sandbox.png?raw=true "Twilio Console WS Sandbox")

## Cleanup

You can easily remove all the deployed resources using the SAM CLI.

Delete the whole stack using the command:

```sh
sam delete
```
