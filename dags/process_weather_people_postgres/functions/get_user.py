import logging
import json
import requests
from pandas import json_normalize

def get_user(id, endpoint):    
    url = endpoint    
    response = requests.get(url=url)
    user = json.loads(response.text)["results"][0]

    processed_user = json_normalize(
        {
            "user_id": id,
            "first_name": user['name']['first'],
            "last_name": user['name']['last'],
            "email": user['email'],
            "gender": 'F' if user['gender'] == 'female' else 'M',
            "age": user['dob']['age'],
            "city": user['location']['city'],
            "lat": user['location']['coordinates']['latitude'],
            "lon": user['location']['coordinates']['longitude'],
        }
    )   
    processed_user.to_csv(f"/tmp/user_inputttt_{id}.csv", sep='\t', index=False, header=False)
    logging.info(f"The file user_inputt_{id}.csv was generated successfully.")