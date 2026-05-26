import boto3
import os

session = boto3.Session(profile_name='connect-sre-runtime', region_name='us-west-2')
dynamo = session.client('dynamodb')
s3 = session.client('s3')

print("DynamoDB Tables:")
for table in dynamo.list_tables()['TableNames']:
    if 'connect-sre' in table.lower():
        print(f" - {table}")

print("\nS3 Buckets:")
for bucket in s3.list_buckets()['Buckets']:
    if 'connect-sre' in bucket['Name'].lower():
        print(f" - {bucket['Name']}")
