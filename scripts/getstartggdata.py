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
        identifier
        slots {
          entrant {
            name
            participants {
              player {
                gamerTag
              }
            }
          }
          standing {
            stats {
              score {
                displayValue
              }
            }
          }
        }
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

def reduceMatchData(data):
    # Initialize the result dictionary with fullRoundText as the key
    result = {
        data["identifier"]: {
            "roundText" : data["fullRoundText"],
            "a" : {},
            "b" : {}
        }
    }
    players = {}

    for game in data["games"]:
        for selection in game["selections"]:
            entrant_id = selection["entrant"]["id"]
            entrant_name = selection["entrant"]["name"]
            character_name = selection["character"]["name"]

            # Ensure the player exists in the players dictionary
            if entrant_id not in players:
                players[entrant_id] = {
                    "name": entrant_name,
                    "score": 0,
                    "characters": set(),  # Use a set to avoid duplicates
                }

            # Add the character to the player's character set
            players[entrant_id]["characters"].add(character_name)

        # Update the score of the winning player
        winner_id = game["winnerId"]
        if winner_id in players:
            players[winner_id]["score"] += 1

    # Assign players to 'a' and 'b' in the result structure
    player_entries = list(players.values())

    if len(player_entries) >= 2:
        result[data["identifier"]]["a"] = {
            "name": player_entries[0]["name"],
            "score": player_entries[0]["score"],
            "characters": list(player_entries[0]["characters"])
        }
        result[data["identifier"]]["b"] = {
            "name": player_entries[1]["name"],
            "score": player_entries[1]["score"],
            "characters": list(player_entries[1]["characters"])
        }
    
    return result



def getManipulatedInfo(data):
    matches = []
    for set in data["data"]["event"]["sets"]["nodes"]:
        if set.get("games"):
            matchInfo = reduceMatchData(set)
            print(matchInfo)
            matches.append(matchInfo)
    return matches


def getEventInfo(eventId):
  # Define any variables for the query
  variables = {
    "eventId": eventId
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

      #print('raw:',  json.dumps(data, indent=4))
      
      reduced = getManipulatedInfo(data)
      #print(reduced)

      return reduced
  else:
      print(f"Error: {response.status_code}, {response.text}")
      return {}
