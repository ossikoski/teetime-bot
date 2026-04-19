## General
- When answering questions, prefer short answers over long answers if a long answer is not required. One word answers are fine when applicable.
- Don't use emojis in code. Use emojis in chat only when it's a good place to use one.
- Ask questions when you are unsure on something.
- Don't add any code unless you are asked specifically. Don't give examples or start doing long operations unless askes for.
- If you see some architectural aspects or other things that are done in a wrong way, you can always suggest changes on those.

## Project specific
- This is the teetime-bot project. It's purpose is to work in a telegram chat, providing teetimes to its users, to make schedule management easier and provide a single way to browse different .
- Uses the telegram bot api to send messages
  - Telegram bots respond to specific commands.
  - Commands and parameters can be defined manually with the botfather.
- The reserved teetimes or other blockers are fetched by scraping with selenium.
- The reserved teetimes need to be subtracted from all available teetimes to get free times.
- Currently, Wisegolf website is used for scraping but I plan to add other ones and simulators as well.
- You cannot see the data that is scraped during runtime, so when needed, you can ask for data snippets or I can even save them in the project folder.
- I use pandas dataframes to save and transform the data after loading it from the website
