from moto.dynamodb import dynamodb_backend
from moto.ec2 import ec2_backend
from moto.elb import elb_backend
from moto.s3 import s3_backend
from moto.ses import ses_backend
from moto.sqs import sqs_backend
from moto.sts import sts_backend

BACKENDS = {
    'dynamodb': dynamodb_backend,
    'ec2': ec2_backend,
    'elb': elb_backend,
    's3': s3_backend,
    'ses': ses_backend,
    'sqs': sqs_backend,
    'sts': sts_backend,
}
