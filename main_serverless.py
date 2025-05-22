#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack, TerraformAsset, AssetType
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.data_aws_caller_identity import DataAwsCallerIdentity

from cdktf_cdktf_provider_aws.s3_bucket import (
    S3Bucket
)
from cdktf_cdktf_provider_aws.s3_bucket_public_access_block import (
    S3BucketPublicAccessBlock
)
from cdktf_cdktf_provider_aws.s3_bucket_policy import S3BucketPolicy
from cdktf_cdktf_provider_aws.s3_bucket_object import S3BucketObject
from cdktf_cdktf_provider_aws.s3_bucket_lifecycle_configuration import (
    S3BucketLifecycleConfiguration, S3BucketLifecycleConfigurationRule,
    S3BucketLifecycleConfigurationRuleFilter,
    S3BucketLifecycleConfigurationRuleTransition,
    S3BucketLifecycleConfigurationRuleExpiration
)
from cdktf_cdktf_provider_aws.s3_bucket_server_side_encryption_configuration import (
    S3BucketServerSideEncryptionConfigurationA,
    S3BucketServerSideEncryptionConfigurationRuleA,
    S3BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultA
)

import json

class S3StorageStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        
        # Provier
        AwsProvider(self, "aws", region="us-east-1")
        account_id= DataAwsCallerIdentity(self, "account_id").account_id
        
        #Bucket S3
        bucket = S3Bucket(
            self, "S3_bucket",
            bucket_prefix="clients-articles",
            force_destroy= True
        )
        
        # Désactiver le blocage d'accès public
        S3BucketPublicAccessBlock(self, "PublicAccessBlock",
            bucket=bucket.id,
            # block_public_acls=False, # Les valeurs par défaut c'est False
            # block_public_policy=False,
            # ignore_public_acls=False,
            # restrict_public_buckets=False
        )

        # Attacher une politique au bucket
        bucket_policy = S3BucketPolicy(self, "BucketPolicy",
            bucket=bucket.id,
            policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Id": "Policy1747486071739",
                    "Statement": [
                        {
                            "Sid": "Stmt1747485999494",
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": [
                                "s3:GetObject",
                                "s3:GetObjectVersion"
                            ],
                            "Resource": f"arn:aws:s3:::{bucket.bucket}/*"
                        }
                    ]
                }
            )
        )
        bucket_policy.add_override("depends_on", ["aws_s3_bucket_public_access_block.PublicAccessBlock"]) # Pour garantir l'orde de création des resources
        
        
        # Configuration du chiffrement SSE-KMS + Bucket Key
        S3BucketServerSideEncryptionConfigurationA(self, "Encryption",
            bucket=bucket.id,
            rule=[S3BucketServerSideEncryptionConfigurationRuleA(
                bucket_key_enabled=True,
                apply_server_side_encryption_by_default=S3BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultA(
                    sse_algorithm="aws:kms",
                    kms_master_key_id=f"arn:aws:kms:us-east-1:{account_id}:key/32a2c3ad-7d50-4d96-a1db-e2ca5d423417"
                )
            )]
        )
              
        # Bucket Life cycle config : 
        # transition vers Standard-IA après 35 jours et vers Glacier après 90 jours
        ## suppression de l'objet après 365 jours
        lifecycle_rule = S3BucketLifecycleConfiguration(
            self, "lifecycle_config",
            bucket= bucket.id,
            rule=[S3BucketLifecycleConfigurationRule(
                filter=[S3BucketLifecycleConfigurationRuleFilter(
                            prefix="processed-articles/"
                        )
                ],
                id = "lifecycle_rule",
                status = "Enabled",
                transition= [
                    S3BucketLifecycleConfigurationRuleTransition(
                        days=35,
                        storage_class="STANDARD_IA"
                    ),
                    S3BucketLifecycleConfigurationRuleTransition(
                        days=90,
                        storage_class="GLACIER"
                    )
                             
                ],
                
                expiration=[S3BucketLifecycleConfigurationRuleExpiration(
                    days=365
                )
                ]

                )
            ]
        )

app = App()
S3StorageStack(app, "s3-object-storage")

app.synth()