## use this if i extend it and publicize so other people can sign in and access their brackets i guess?
## otherwise secret key easy enough.

# test bracket
# https://www.start.gg/tournament/wellington-fgc-meetup-tournament/event/street-fighter-6/brackets/1807323/2671485

import json
import requests
import webbrowser
from urllib.parse import urlencode, parse_qs

# Your API endpoint and authentication
#url = "https://api.start.gg/gql/alpha"  # Start.gg's GraphQL endpoint
#api_token = "7a5a301ef879a38df450f8add302266d"  # Replace with your actual token
# Replace with your Start.gg Client ID and Secret

##jb.gg
CLIENT_ID = "191"
CLIENT_SECRET = "478a22df6968bde4259841540d1758fbf62fc8433006e7f48e59b200eba0009a"
REDIRECT_URI = "http://localhost:8000/callback"
SCOPES = "tournament.manager"

# 1. Request authorization
# example auth?: 
# https://start.gg/oauth/authorize?response_type=code&client_id=0&scope=user.identity%20user.email&redirect_uri=http%3A%2F%2Fexampleurl.com%2Foauth

##this generated one looks wrong.
'''auth_url = "https://api.start.gg/oauth/authorize?" + urlencode({
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "scope": "tournament.manager" # Replace with desired scopes
})'''

auth_url = "https://start.gg/oauth/authorize?" + urlencode({
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "scope": SCOPES
})

webbrowser.open_new_tab(auth_url)

# 2. Handle authorization code callback
print("Please authorize the app and copy the callback URL from your browser.")
callback_url = input("Enter the callback URL: ")

# Extract authorization code
code = parse_qs(callback_url.split("?")[1])["code"][0]

# 3. Exchange code for access token
#generated code wrong again?
###token_url = "https://api.start.gg/oauth/token"
token_url = "https://api.start.gg/oauth/access_token"


token_data = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": code,
    "grant_type": "authorization_code",
    "redirect_uri": REDIRECT_URI
}

# Send the request
response = requests.post(token_url, data=token_data)


if response.status_code == 200:
    print(response)
    print(json.dumps(response.json()))

    access_token = response.json()["access_token"]
    print(access_token)

    # access_token = response.json()["access_token"]

    # # 4. Use access token for API requests
    # headers = {"Authorization": f"Bearer {access_token}"}

    # api_endpoint = "https://api.start.gg/..." # Replace with desired API endpoint

    # api_response = requests.get(api_endpoint, headers=headers)

    # # Process API response
    # print(api_response.json())

else:
    print("Error obtaining access token. Status code:", response.status_code)