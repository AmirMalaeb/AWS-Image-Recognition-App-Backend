import json
import boto3
import urllib.parse

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ImageMetadata')

def convert_floats_to_strings(data):
    if isinstance(data, list):
        return [convert_floats_to_strings(i) for i in data]
    elif isinstance(data, dict):
        return {k: convert_floats_to_strings(v) for k, v in data.items()}
    elif isinstance(data, float):
        return str(data)
    else:
        return data

def remove_duplicate_texts(text_detections):
    seen_texts = set()
    unique_texts = []
    for text in text_detections:
        if text not in seen_texts:
            seen_texts.add(text)
            unique_texts.append(text)
    return unique_texts

def lambda_handler(event, context):
    try:
        print("Received event: " + json.dumps(event, indent=2))  # Log the entire event for debugging
        
        if 'Records' in event and event['Records'][0]['eventSource'] == 'aws:s3':
            bucket = event['Records'][0]['s3']['bucket']['name']
            key = event['Records'][0]['s3']['object']['key']
            print(f"Triggered by S3. Bucket: {bucket}, Key: {key}")
        else:
            body = json.loads(event['body'])
            bucket = 's3-imagerecognition-amirtest'
            key = body['image_key']
            print(f"Triggered by API Gateway. Bucket: {bucket}, Key: {key}")

        decoded_key = urllib.parse.unquote_plus(key)
        print(f"Decoded Key: {decoded_key}")
        
        response = s3.head_object(Bucket=bucket, Key=decoded_key)
        content_type = response['ContentType']
        print(f"Content type: {content_type}")
        
        supported_formats = ['image/jpeg', 'image/png', 'image/bmp', 'image/gif']
        if content_type not in supported_formats:
            print(f"Unsupported image format: {content_type}")
            return {
                'statusCode': 400,
                'body': json.dumps(f"Unsupported image format: {content_type}")
            }
        
        results = {
            'labels': [],
            'text': [],
            'faces': [],
            'celebrities': []
        }
        
        label_response = rekognition.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': decoded_key
                }
            },
            MaxLabels=10
        )
        results['labels'] = [label['Name'] for label in label_response['Labels']]
        print(f"Labels detected: {results['labels']}")
        
        text_response = rekognition.detect_text(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': decoded_key
                }
            }
        )
        detected_texts = [text['DetectedText'] for text in text_response['TextDetections']]
        results['text'] = remove_duplicate_texts(detected_texts)
        print(f"Text detected: {results['text']}")
        
        face_response = rekognition.detect_faces(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': decoded_key
                }
            },
            Attributes=['ALL']
        )
        for face in face_response['FaceDetails']:
            face_data = {
                'BoundingBox': convert_floats_to_strings(face['BoundingBox']),
                'Confidence': str(face['Confidence']),
                'Emotions': convert_floats_to_strings(face['Emotions'][:3])
            }
            results['faces'].append(face_data)
        print(f"Faces detected: {results['faces']}")
        
        celebrity_response = rekognition.recognize_celebrities(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': decoded_key
                }
            }
        )
        results['celebrities'] = [celebrity['Name'] for celebrity in celebrity_response['CelebrityFaces'][:3]]
        print(f"Celebrities recognized: {results['celebrities']}")
        
        results = convert_floats_to_strings(results)
        
        # Logging results before storing
        print(f"Storing results to DynamoDB: {results}")

        table.put_item(
            Item={
                'imageId': decoded_key,
                'bucket': bucket,
                'results': results
            }
        )
        print(f"Successfully stored metadata in DynamoDB for {decoded_key}")

        return {
            'statusCode': 200,
            'body': json.dumps('Image processed successfully!')
        }
    
    except rekognition.exceptions.InvalidImageFormatException as e:
        print(f"Invalid image format: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps(f"Invalid image format: {e}")
        }
    
    except Exception as e:
        print(f"Error processing image: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error processing image: {e}")
        }