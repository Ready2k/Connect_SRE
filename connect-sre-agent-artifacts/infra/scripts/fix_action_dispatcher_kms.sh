#!/bin/bash
aws iam put-role-policy \
    --role-name dev-connect-sre-action-dispatcher-role \
    --policy-name KmsAccessPolicy \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "kms:Decrypt",
                    "kms:Encrypt",
                    "kms:GenerateDataKey",
                    "kms:DescribeKey"
                ],
                "Resource": "arn:aws:kms:us-west-2:388660028061:key/d6a7c296-0d56-43fa-99e5-068f6c47bb47"
            }
        ]
    }'
echo "KMS policy attached to Action Dispatcher Role."
