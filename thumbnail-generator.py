"""
AWS Lambda function that listens for S3 put events for a specified S3 bucket, retrieves the uploaded image file, creates the thumbnail, and puts them back to the specified S3 bucket's 'thumbnails' folder with the same key structure.
"""
from __future__ import print_function

import boto3
import json
import urllib
import datetime
import httplib
import time
import uuid
from PIL import Image
from PIL.ExifTags import TAGS
from io import BytesIO

s3 = boto3.client('s3')

"""
Generate the thumbnails for the files uploaded to the specified S3 bucket
"""
def generate_thumbnail(instance_id, response):
    # This is to by-pass the image size DecompressionBombWarning DOS attack warning by PIL
    Image.MAX_IMAGE_PIXELS = None
    thumbnail_size = 128, 128

    # Save the thumbnail to bytes array to stream it to S3 bucket
    bytes_array = BytesIO()

    image = Image.open(response['Body'])
    try:
        image.thumbnail(thumbnail_size, Image.ANTIALIAS)
        image.save(bytes_array, 'JPEG')
        bytes_array.seek(0)

        return bytes_array
    except IOError as ioe:
        return None

"""
Event handler for S3 uploads. Called automagically by AWS when an S3 put event occurs
"""
def lambda_handler(event, context):
    instance_id = str(uuid.uuid4())

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key']).decode('utf8')

    try:
        print ('Instance={}, bucket={}, key={}'.format(instance_id, bucket, key))
        thumbnails_folder = 'thumbnails'
        
        # Retrieve the uploaded file from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        thumbnail_image_file = generate_thumbnail(instance_id, response)

        # Put the thumbnail image to 'thumbnails' folder
        if thumbnail_image_file != None:
            thumbnails_key = 'thumbnails' + key[key.index("/"):]
            s3.put_object(Bucket=bucket, Key=thumbnails_key, Body=thumbnail_image_file)
            
            print ('Successfully created the thumbnail. Instance={}, bucket={}, key={}'.format(instance_id, bucket, key))            
    except:
        print ('Failed to create the thumbnail. Instance={}, bucket={}, key={}'.format(instance_id, bucket, key))