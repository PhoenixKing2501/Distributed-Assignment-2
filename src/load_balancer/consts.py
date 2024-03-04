import os

# if debug mode is enabled
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

# which hash function to use
HASH_NUM = int(os.environ.get('HASH_NUM', 0))

# max number of consecutive heartbeat fails
MAX_FAIL_COUNT = 5

# interval between heartbeat checks in seconds
HEARTBEAT_INTERVAL = 10

# timeout for stopping a container in seconds
STOP_TIMEOUT = 5

# timeout for requests in seconds
REQUEST_TIMEOUT = 1

# number of requests to send in a batch
REQUEST_BATCH_SIZE = 10

# number of docker tasks to perform in a batch
DOCKER_TASK_BATCH_SIZE = 10

# Database constants
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 5432))
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')
DB_NAME = os.environ.get('DB_NAME', 'postgres')
