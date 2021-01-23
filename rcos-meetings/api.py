from typing import Dict, Optional
import requests
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.environ['RCOS_API_URL']
JWT_SECRET = os.environ['POSTGREST_JWT_SECRET']

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
    r = api.get(f'{API_BASE}/meetings', params={
        'meeting_id': f'eq.{meeting_id}'
    })
    results = r.json()
    if len(results) == 0:
        return None
    else:
        return results[0]

def create_meeting(meeting_dict: Dict) -> Dict:
    r = api.post(f'{API_BASE}/meetings', json=meeting_dict, headers={
        'Prefer': 'return=representation'
    })
    r.raise_for_status()
    new_meeting = r.json()[0]
    return new_meeting

def update_meeting(meeting_id: int, updates: Dict) -> Dict:
    r = api.patch(f'{API_BASE}/meetings', params={
        'meeting_id': 'eq.' + str(meeting_id)
    }, json=updates, headers={
        'Prefer': 'return=representation'
    })
    r.raise_for_status()
    new_meeting = r.json()[0]
    return new_meeting