import requests
import jwt
import os

API_BASE = 'http://198.211.105.73:3000'
JWT_SECRET = os.environ['API_KEY']

encoded_jwt = jwt.encode({'role': 'api_user'}, JWT_SECRET,
                         algorithm='HS256')

api = requests.Session()
api.headers['Authorization'] = 'Bearer ' + encoded_jwt
