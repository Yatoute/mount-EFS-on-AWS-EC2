#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput, Token
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.data_aws_caller_identity import DataAwsCallerIdentity
from cdktf_cdktf_provider_aws.default_vpc import DefaultVpc
from cdktf_cdktf_provider_aws.default_subnet import DefaultSubnet
from cdktf_cdktf_provider_aws.security_group import (
    SecurityGroup, SecurityGroupIngress, SecurityGroupEgress
)
from cdktf_cdktf_provider_aws.launch_template import LaunchTemplate
from cdktf_cdktf_provider_aws.lb import Lb
from cdktf_cdktf_provider_aws.lb_target_group import LbTargetGroup
from cdktf_cdktf_provider_aws.lb_listener import LbListener, LbListenerDefaultAction
from cdktf_cdktf_provider_aws.autoscaling_group import AutoscalingGroup
from cdktf_cdktf_provider_aws.efs_file_system import EfsFileSystem
from cdktf_cdktf_provider_aws.efs_mount_target import EfsMountTarget

import os
from dotenv import load_dotenv
import base64

load_dotenv()

git_repo=os.getenv("GIT_REPO")
ami_id= "ami-0c34cd1ee08bce942"

class MyStack(TerraformStack):                                         
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
      
        # Infrastructure de base
        account_id, sg_ec2, sg_efs, default_vpc, subnets = self.infra_base()
        
        ####################################################################
        ### Elastic File System Storage
        ####################################################################
        efs= EfsFileSystem(
            self, "efs",
            performance_mode="generalPurpose",
            tags={"Name": "shared-processing-efs"}
        )
        efs_mount_targets = []
        for i, subnet in enumerate(subnets):
            efs_mount_target= EfsMountTarget(
                self, f"target_{i}",
                file_system_id= Token.as_string(efs.id),
                subnet_id= subnet,
                security_groups=[sg_efs.id]
            )
            efs_mount_targets.append(efs_mount_target)
        
        
        ####################################################################
        ### Templace EC2 + Load Balancer + Target Group + Auto Scaling Group
        ####################################################################
        # Templace d'instance EC2
        launch_template = LaunchTemplate(
            self, "launch_template",
            image_id=ami_id,
            instance_type="t2.micro",
            vpc_security_group_ids=[sg_ec2.id],
            key_name="data-skills-hub-key",
            user_data=self.get_user_data(efs.id),
            tags={"Name": "TP-EC2-EFS"},
            iam_instance_profile={"arn": f"arn:aws:iam::{account_id}:instance-profile/RoleEC2"},
            depends_on=efs_mount_targets
        )
        
        # Load Balancer
        lb= Lb(
            self, "lb",
            load_balancer_type="application",
            security_groups=[sg_ec2.id],
            subnets=subnets
        )
        
        # Target group
        target_group= LbTargetGroup(
            self, "tg_group",
            port=8080,
            protocol="HTTP",
            vpc_id=default_vpc.id,
            target_type="instance"
        )
        
        # LB Listener
        lb_listener= LbListener(
            self, "lb_listener",
            load_balancer_arn=lb.arn,
            port=8080,
            protocol="HTTP",
            default_action=[
                LbListenerDefaultAction(
                    type="forward", target_group_arn=target_group.arn
                )
            ]
        )
        
        # Auto scaling group
        asg= AutoscalingGroup(
            self, "asg",
            min_size=1,
            max_size=5,
            desired_capacity=1,
            launch_template={"id": launch_template.id},
            vpc_zone_identifier= subnets,
            target_group_arns=[target_group.arn]
        )
        
        
        # Adress du load balancer
        TerraformOutput(
            self, "lb_address",
            value=lb.dns_name
        )
        # ID du launch template
        TerraformOutput(
            self, "launch_template_id",
            value=launch_template.id
        )
        # Nom de l'ASG
        TerraformOutput(
            self, "asg_name",
            value=asg.name
        )
        

    def infra_base(self):
        """
        Définir une infrastructure de base avec une config minim de 
        réseau privé, sous réseau et de security group pour contrôler
        les trafic entrant et sortant

        Returns:
            account_id, sg_ec2, sg_efs, default_vpc, subnets
        """
        AwsProvider(self, "aws", region="us-east-1")
        
        account_id = DataAwsCallerIdentity(self, "account_id").account_id
       
        # Définir le réseau privé virtuel par défaut de aws
        default_vpc = DefaultVpc(self, "default_vpc")
        
        # Définir les sous réseaux dans chaque AZ de la région "us-east-1"
        az_ids= [f"us-east-1{i}" for i in "abcdef"] # la liste des AZ de la région
        subnets= []
        for i, az_id in enumerate(az_ids):
            subnets.append(
                DefaultSubnet(
                    self, f"subnet_{i}",
                    availability_zone=az_id
                ).id
            )
        # Security group pour EC2
        sg_ec2 = SecurityGroup(
            self, "sg-ec2",
            ingress=[
                SecurityGroupIngress(
                    from_port=22,
                    to_port=22,
                    cidr_blocks=["0.0.0.0/0"],
                    protocol="TCP"
                ),
                SecurityGroupIngress(
                    from_port=80,
                    to_port=80,
                    cidr_blocks=["0.0.0.0/0"],
                    protocol="TCP"
                ),
                SecurityGroupIngress(
                    from_port=8080,
                    to_port=8080,
                    cidr_blocks=["0.0.0.0/0"],
                    protocol="TCP"
                )
            ],
            egress=[
                SecurityGroupEgress(
                    from_port=0,
                    to_port=0,
                    cidr_blocks=["0.0.0.0/0"],
                    protocol="-1"
                )
            ]
        )
        
        # Security group pour EFS
        sg_efs = SecurityGroup(
            self, "sg-efs",
            ingress=[
                SecurityGroupIngress(
                    from_port=2049,
                    to_port=2049,
                    protocol="TCP",
                    security_groups=[sg_ec2.id]
                )
            ]
        )
        return account_id, sg_ec2, sg_efs, default_vpc, subnets
    
    def get_user_data(self, efs_id:str):
        
        """GET USER DATA FOR EC2"""
        
        return base64.b64encode(f"""#!/bin/bash
echo "userdata-start"
# Creation du point de montage
mkdir -p /mnt/efs
# Monter le systeme de fichiers EFS
mount -t nfs4 -o nfsvers=4.1 "{efs_id}.efs.us-east-1.amazonaws.com:/" /mnt/efs
# Ajouter le montage au fichier /etc/fstab pour le rendre persistant apres reboot
echo '{efs_id}.efs.us-east-1.amazonaws.com:/ /mnt/efs nfs4 defaults,_netdev 0 0' >> /etc/fstab
# Verifier que le montage a reussi
if mountpoint -q /mnt/efs; then
    echo "[OK] EFS monte avec succes sur /mnt/efs" >> /var/log/efs-check.log
else
    echo "[ERREUR] Le montage EFS a echoue" >> /var/log/efs-check.log
fi

[ ! -d /mnt/efs/uploads ] && mkdir -p /mnt/efs/uploads
[ ! -d /mnt/efs/results ] && mkdir -p /mnt/efs/results

# Donner les droits a utilisateur ubuntu (qui execute le service)
chown -R ubuntu:ubuntu /mnt/efs/uploads /mnt/efs/results

# Activer et demarrer le service
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable webservice
systemctl start webservice
echo "userdata-end"
""".encode("ascii")).decode("ascii")

        
app = App()
MyStack(app, "EFS-on-EC2")

app.synth()