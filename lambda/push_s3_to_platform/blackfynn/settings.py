# -*- coding: utf-8 -*-

import os
import logging

# blackfynn api locations
api_host = os.environ.get('BLACKFYNN_API_LOC', 'https://api.blackfynn.io')
streaming_api_host = os.environ.get('BLACKFYNN_STREAMING_API_LOC', 'https://streaming.blackfynn.io')

# blackfynn user/pass
api_user = os.environ.get('BLACKFYNN_USER', None)
api_pass = os.environ.get('BLACKFYNN_PASS', None)

# streaming
stream_name = os.environ.get('BLACKFYNN_STREAM_NAME', 'prod-stream-blackfynn')
stream_aws_region = 'us-east-1'
stream_max_segment_size = 5000

# all requests
max_request_time = 120 # two minutes
max_request_timeout_retries = 2

#io
max_upload_workers = 10

# timeseries
max_points_per_chunk = 10000

# s3 (amazon/local)
s3_host = os.environ.get('S3_HOST', "")
s3_port = os.environ.get('S3_PORT', "")

# logging
log_level = logging.INFO
