import json
import os
import sys
import urllib.request

API_KEY = os.environ.get('OPENAI_API_KEY')
if not API_KEY:
    print('ERROR: OPENAI_API_KEY is not set in the environment.')
    sys.exit(2)

MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini-2024-07-18')

payload = {
    "model": MODEL,
    "input": [
        {"role": "user", "content": [{"type": "input_text", "text": "ping"}]}
    ]
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(
    'https://api.openai.com/v1/responses',
    data=data,
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}',
    },
    method='POST',
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode('utf-8')
        print('STATUS:', resp.status)
        print('BODY:', body)
except urllib.error.HTTPError as e:
    print('STATUS:', e.code)
    print('BODY:', e.read().decode('utf-8'))
    sys.exit(1)
except Exception as e:
    print('ERROR:', repr(e))
    sys.exit(1)
