# vk_api_bot
 
Chatbot for a personal page vk.com to automatically generate replies to messages
***
## Opportunities
- Сhoosing profiles vk.com to start the process of scanning incoming messages and subsequent response
- The possibility of automatic labeling of reactions with a specified probability of their occurrence
- The ability to respond solely with reactions
- The ability to train a machine learning model based on a dialog to generate answers
***
## What is necessary to start using?
- Fill in the data/targets.json file (if missing, create) profiles of the right people in the format [name convenient for you: vk_id] (in the future it will be automated)
- Get a personal vk api access token and place it in the .env file (visit https://vkhost.github.io/, choose vk.com, follow instructions)
- Put your own vk id in the .env file (it is necessary to distinguish your messages from others')
