# AWS-Image-Recognition-App-Backend
This project demonstrates an image recognition application using AWS services. The application allows users to upload images, which are then processed using AWS Rekognition to extract labels, text, faces, and celebrity recognition. The results are stored in a DynamoDB table.

## Architecture

- **S3 Bucket**: Stores the uploaded images.
- **API Gateway**: Provides a REST API for uploading images.
- **Lambda Function**: Processes the uploaded images, calls AWS Rekognition, and stores the results in DynamoDB.
- **DynamoDB**: Stores the metadata and analysis results of the processed images.


## Setup

### Step 1: Create S3 Bucket

Create an S3 bucket to store the uploaded images. Ensure the bucket name is unique.

### Step 2: Configure Bucket Policy

Configure your Bucket Policy with the concept of least privilege in mind.

### Step 3: Create DynamoDB Table

Create a DynamoDB table with primary key imageId (String).

### Step 4: Create Lambda Function

Create a Lambda function (code attached and make sure to change the right values for you DynamoDB table)

### Step 5: Configure Lambda Trigger

Set up an S3 trigger for the Lambda function to invoke it whenever an image is uploaded to the S3 bucket.

### Step 6: Create and Configure API Gateway

Create a new REST API in API Gateway.
Create a POST method for the /upload resource.
Integrate the POST method with the UploadImageLambdaNew Lambda function.
Enable CORS for the /upload resource.

### Step 7: Configure IAM Roles and Permissions

Ensure the Lambda function execution role has the following permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectAcl",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR_BUCKET_NAME",
        "arn:aws:s3:::YOUR_BUCKET_NAME/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "rekognition:DetectLabels",
        "rekognition:DetectText",
        "rekognition:DetectFaces",
        "rekognition:RecognizeCelebrities",
        "rekognition:DetectModerationLabels"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "dynamodb:PutItem",
      "Resource": "arn:aws:dynamodb:us-east-1:YOUR_ACCOUNT_ID:table/ImageMetadata"
    }
  ]
}


