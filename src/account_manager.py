import vk_api
import time
import random
import threading
import pprint
import json


class AccountManager:

    def __init__(self, targets: dict, token: str, vk_id: str):
        self.targets = targets
        self.token = token
        self.vk_id = vk_id
        self.path_to_out = None
        self.api = None
        self.handlers = {}
        self.activities = ["typing", "audiomessage", "photo", "videomessage"]


    def logger(self):
        pprint.pp(f'CURRENT_HANDLERS {(self.handlers)}')


    def auth(self): self.api = vk_api.VkApi(token = self.token).get_api()


    def __getLastUnhandledMessages(self, user_name: str):
        messages = self.api.messages.getHistory(user_id = self.targets[user_name])
        corpus = []
        for msg in messages['items']:

            if(int(msg['from_id']) == int(self.vk_id)): break

            if random.randint(0, 2) == 0:
                self.sendReaction(user_name, msg['conversation_message_id'])

            corpus.append(msg["text"])

        corpus.reverse()
        return corpus


    def getDialogAsJson(self, user_name: str, count_of_messages : int = 200):
        dialog = {}
        current_msgs_line_from = []
        current_msgs_line = []
        is_pre_end = False
        current_offset = 0
        count_of_iters = int(count_of_messages/200)

        for i in range(count_of_iters):
            messages = self.api.messages.getHistory(user_id = self.targets[user_name], count = 200, offset = current_offset)

            for msg in messages['items']:

                if (is_pre_end and int(msg['from_id']) != int(self.vk_id)):
                    dialog[" ".join(current_msgs_line_from)] = " ".join(current_msgs_line)
                    is_pre_end = False
                    current_msgs_line_from = [] 
                    current_msgs_line = []

                if(int(msg['from_id']) != int(self.vk_id) and is_pre_end == False):
                    try:
                        current_msgs_line_from.append(msg['text'])
                    except:
                        continue
                else:
                    is_pre_end = True
                    current_msgs_line.append(msg['text'])

            current_offset += 200
                
        with open(f"dialogs_dumps/{user_name}.json", "w", encoding="utf-8") as target_json_file:
                json.dump(dialog, target_json_file, ensure_ascii=False, indent=4)

        return dialog


    def sendMessage(self, user_name: str, text:str,):
        self.api.messages.send(user_id = self.targets[user_name], random_id = '0', message = text)


    def conversation(self, target: str, delay_between_answers_seconds: int, delay_limit_seconds: int):
        current_delay_capacity = 0
        stop = False
        while(not stop):
            corpus = self.__getLastUnhandledMessages(target)
            if current_delay_capacity > delay_limit_seconds:
                break
            if corpus != []:
                self.setActivity(target, mode = 'typing')
                current_delay_capacity = 0
                msg = self.answer_generator(corpus)
                self.sendMessage(target, msg)
                print(f'SENDED MESSAGE [{msg}] TO {target} : {self.targets[target]}')  
            else:
                time.sleep(delay_between_answers_seconds)
                current_delay_capacity += delay_between_answers_seconds

            stop = self.handlers[target][0]

        self.handlers.pop(target)
        self.logger()


    def sendReaction(self, target: str, conv_msg_id: int):
        react_id = random.randint(1, 16)
        self.api.messages.sendReaction(peer_id = self.targets[target], cmid = conv_msg_id, reaction_id = react_id)


    def setActivity(self, target: str, mode = 'random'):
        if mode == 'random':
            self.api.messages.setActivity(user_id = self.targets[target], type = random.choice(self.activities))
        else:
            self.api.messages.setActivity(user_id = self.targets[target], type = mode)


    def create_target_handler(self, target: str, delay_between_answers_seconds = 10, delay_limit_seconds = 60) -> threading.Thread:
        thread = threading.Thread(target=self.conversation, args=(target, delay_between_answers_seconds, delay_limit_seconds,))
        self.handlers[target] = [False, thread]
        thread.start()
        print(f'ADDED AND STARTED HANDLER FOR {target} : {self.targets[target]}')  
        

    def terminate_handler(self, targets: list):
        for target in targets:
            if target not in list(self.handlers.keys()):
                continue
            self.handlers[target][0] = True
            print(f'START STOPPING HANDLER FOR {target} : {self.targets[target]}')  
        



