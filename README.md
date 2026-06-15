# teetime-bot

- Find your authorization headers after logging in to the wisegolf app and save in backend/wisegolf_headers.json
  - Also add "x-session-type": "wisegolf"
  ```json
    {
        "Authorization": "token <token here>",
        "x-session-type": "wisegolf"
    }
  ```
- Add the bot token to bot/tolkien.py as tolkien = '...'