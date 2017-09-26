import boto3
import os
import urllib

from blackfynn import Blackfynn
from blackfynn import Collection

organization_id = "N:organization:b2734f39-a106-4d41-bb9e-d8a234c9e486"
collection_id = "N:collection:176b2121-7043-4cf0-af86-9c08a55d4b43"

s3 = boto3.client('s3')

def push_to_blackfynn(event, context):

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))

    try:
        bf = Blackfynn()
        bf.set_context(organization_id)
        root_collection = bf.get(collection_id)

        package_name = key.split("/")[-2]
        package_collection = next((c for c in root_collection.items if c.name == package_name), None)
        if package_collection is None:
            package_collection = Collection(package_name)
            root_collection.add(package_collection)

        local_object = '/tmp/{}'.format(os.path.basename(key))
        s3.download_file(Bucket=bucket, Key=key, Filename=local_object)
        package_collection.upload_files(local_object)
        return 'Successfully pushed {} from bucket {} to Blackfynn.'.format(key, bucket)

    except Exception as e:
        print(e)
        print('Error pushing {} from bucket {} to Blackfynn.'.format(key, bucket))
        raise e
