import os
from dotenv import load_dotenv

load_dotenv()

config_var = {
    "token": os.environ.get('token'),
    "ipc_key": os.environ.get('ipc_key'),
    "ipc_host": os.environ.get('ipc_host'),
    "ipc_port": os.environ.get('ipc_port'),
    "postgres_host": os.environ.get('postgres_host'),
    "postgres_name": os.environ.get('postgres_name'),
    "postgres_port": os.environ.get("postgres_port"),
    "postgres_user": os.environ.get("postgres_user"),
    "postgres_pass": os.environ.get("postgres_pass")
}
