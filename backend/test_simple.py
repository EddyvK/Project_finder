import requests

try:
    r = requests.get('http://localhost:8000/api/matches/1')
    data = r.json()
    matches = data.get('matches', [])
    print(f'Matches found: {len(matches)}')

    if matches:
        print(f'Top match: {matches[0]["project_title"]} - {matches[0]["match_percentage"]}%')
    else:
        print('No matches found - threshold is working!')

except Exception as e:
    print(f'Error: {e}')
