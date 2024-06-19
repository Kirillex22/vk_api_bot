from tkinter.ttk import Combobox 
from src.account_manager import AccountManager
from src.answer_generator import AnswerGenerator
from src.fitter import Fitter

class Instance:
    def __init__(self, am : AccountManager, targets : list, ans_gen):
        self.am = am
        self.ftr = Fitter()
        self.targets = targets
        self.current_target = None
        self.combobox = None
        self.combobox1 = None
        self.ans_gen = ans_gen
        self.count_of_messages = 200


    def start(self):
        self.am.create_target_handler(self.current_target, delay_between_answers_seconds=5, delay_limit_seconds=500)
        

    def stop(self):
        self.am.terminate_handler([self.current_target])


    def dump_dialog(self):
        self.am.getDialogAsJson(self.current_target, self.count_of_messages)
        print(f'SUCCESFUL DUMPED {self.current_target} [{self.count_of_messages}] MESSAGES')

    
    def stop_all(self):
        self.am.terminate_handler(self.targets)


    def selected(self, event): 
        self.current_target = self.combobox.get()
        print(f'SELECTED {self.current_target}')


    def fit_model(self):
        self.fitter.fit(self.current_target)
        print(f'FITTED AND SAVED MODEL FOR {self.current_target}')


    def load_model(self):
        self.ans_gen.load_model(self.current_target)
        print(f'LOADED MODEL FOR {self.current_target}')


    def set_count_of_messages(self, event):
        self.count_of_messages = int(self.combobox1.get())
        print(f'SELECTED {self.count_of_messages} AS COUNT OF MESSAGES TO DUMP')

        