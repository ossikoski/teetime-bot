import json
import requests


with open('backend/wisegolf_headers.json') as f:
    headers = json.load(f)

res = requests.get('https://api.tammer-golf.fi/api/1.0/reservations/?productid=424&date=2025-06-13&golf=1', headers=headers)
# keys: 'success', 'errors', 'resourceComments', 'reservationsGolfPlayers', 'reservationsAdditionalResources', 'rows', 'fromStartup', 'duration'
# reservationsAdditionalResources: golf carts
# 
data = res.json()

print(data.keys())
# print(data['reservationsGolfPlayers'])
# for obj in data['reservationsGolfPlayers']:
#     if obj['reservationTimeId'] == 224136:
#         print(obj)

# print(data['reservationsAdditionalResources'])

# print(data['rows'])
# for obj in data['rows']:
#     if obj['start'] == '2025-06-11 20:00:00':
#         print(obj)

# print(data['fromStartup'])
# print(data['duration'])

# print(data['resourceComments'])


# res = requests.get('https://app.wisegolf.fi/#/golf/reservation/424')
# print(res)
# print(res.content)

res = requests.get('https://api.tammer-golf.fi/api/1.0/reservations/calendarsettings/?productid=424&date=2025-06-12', headers=headers)
# print(res.json())
rules = res.json()['resourceRules']
for rule in rules:
    try:
        if rule['ruleValue']['hide'] == True:
            print(rule)
            print()
    except:
        pass
    # print(rule['ruleName'])
    # print(rule['ruleValue'])
    # print(rule['ruleId'])
    # print()

