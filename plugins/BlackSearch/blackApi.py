import json

import requests


def get_black_list(qq, api_key):
    url = f'https://yunhei.qimeng.fun/OpenAPI.php?id={qq}&key={api_key}'

    res = requests.get(url)

    res = json.loads(res.text)['info'][0]
    return res['yh'],res['note']

