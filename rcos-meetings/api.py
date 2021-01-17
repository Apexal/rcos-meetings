from typing import Dict, Optional
import requests
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = 'http://198.211.105.73:3000'
JWT_SECRET = os.environ['API_KEY']

encoded_jwt = jwt.encode({'role': 'api_user'}, JWT_SECRET,
                         algorithm='HS256')

api = requests.Session()
api.headers['Authorization'] = 'Bearer ' + encoded_jwt

meeting_types = {
    'large_group': 'Large Group',
    'small_group': 'Small Group',
    'mentors': 'Mentors',
    'coordinators': 'Coordinators'
}
meeting_type_urls = {
    'large_group': 'https://handbook.rcos.io/#/meetings/large_group_meetings',
    'small_group': 'https://handbook.rcos.io/#/meetings/small_group_meetings'
}


def get_meeting(meeting_id: int) -> Optional[Dict]:
    r = api.get(f'{API_BASE}/meetings?meeting_id=eq.{meeting_id}')
    results = r.json()
    if len(results) == 0:
        return None
    else:
        return results[0]
