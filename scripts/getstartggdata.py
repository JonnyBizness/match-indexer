# test bracket
# https://www.start.gg/tournament/wellington-fgc-meetup-tournament/event/street-fighter-6/brackets/1807323/2671485

import requests
import json

# Your API endpoint and authentication
url = "https://api.start.gg/gql/alpha"  # Start.gg's GraphQL endpoint
keyFile = open('startggbearer.txt', 'r')
api_token = keyFile.readline().rstrip()

# Define your GraphQL query
query = """
query getEventDetails($eventId: ID!) {
  event(id: $eventId) {
    id
    name
    startAt
    slug
    sets(
      page: 1
    	perPage: 100
    	sortType: STANDARD
    ) {
      nodes {
        id
        fullRoundText
        games{
          id
          winnerId
          selections{
            character{
              name
            }
            entrant{
              id
              name
            }
          }
        }
      }
    }
  }
}
"""

def getEventInfo(eventId):
  # Define any variables for the query
  variables = {
    "eventId": 1250662
  }

  # Set up headers, including authorization
  headers = {
      "Authorization": f"Bearer {api_token}",
      "Content-Type": "application/json"
  }

  print(url)
  print(query)
  print(variables)

  # Send the request
  response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)

  # Check for a successful response
  if response.status_code == 200:
      data = response.json()
      # print("Response data:", json.dumps(data, indent=4))
      return data
  else:
      print(f"Error: {response.status_code}, {response.text}")
      return {}
