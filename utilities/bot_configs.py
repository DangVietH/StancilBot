import os
from dotenv import load_dotenv

load_dotenv()

config_var = {
    "token": os.environ.get('token'),
    "postgres_host": os.environ.get('postgres_host'),
    "postgres_name": os.environ.get('postgres_name'),
    "postgres_port": os.environ.get("postgres_port"),
    "postgres_user": os.environ.get("postgres_user"),
    "postgres_pass": os.environ.get("postgres_pass")
}
