import os
from dotenv import load_dotenv

load_dotenv('.env')

API_TOKEN = os.environ.get('API_TOKEN')
