import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import keras
import json
import numpy as np
import pickle
import random

class AnswerGenerator:
    
    def __init__(self, random_word_probability = 0.25, char_limit = 50, shuffling = True, current_mode = 'fitting', ans_len_rate = 10, epochs = 50):
        self.epochs = epochs
        self.model = None
        self.tokenizer = None
        self.max_sequence_len = None
        self.current_mode = current_mode
        self.ans_len_arange = np.arange(1, ans_len_rate, 1)
        self.char_limit = char_limit
        self.shuffling = shuffling
        
        if random_word_probability <= 0: 
            self.random_word_arange = np.array([1]) 
        else: 
            self.random_word_arange = np.arange(0, int(1/random_word_probability), 1)
    

    def fit(self, name):
        if self.current_mode == 'fitting-predicting':

            templates = None
            with open(f'dialogs_dumps/{name}.json', encoding='utf8') as f:
                templates = json.load(f)

            messages = list(templates.keys())
            responses = list(templates.values())

            tokenizer = Tokenizer()
            tokenizer.fit_on_texts(messages + responses)
            total_words = len(tokenizer.word_index) + 1

            input_sequences = []
            for line in messages:
                token_list = tokenizer.texts_to_sequences([line])[0]
                for i in range(1, len(token_list)):
                    n_gram_sequence = token_list[:i+1]
                    input_sequences.append(n_gram_sequence)

            max_sequence_len = max([len(x) for x in input_sequences])
            input_sequences = pad_sequences(input_sequences, maxlen=max_sequence_len, padding='pre')
            xs, labels = input_sequences[:,:-1],input_sequences[:,-1]
            ys = tf.keras.utils.to_categorical(labels, num_classes=total_words)

            model = tf.keras.Sequential([
                tf.keras.layers.Embedding(total_words, 64, input_length=max_sequence_len-1),
                tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(20)),
                tf.keras.layers.Dense(total_words, activation='softmax')
            ])

            model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
            history = model.fit(xs, ys, epochs=self.epochs, verbose=0)

            model.save(f'model_dumps/{name}_model.h5')
            print(f'SAVED MODEL TO {name}_model.h5')
            
            with open(f'tokenizer_dumps/{name}_tokenizer.pickle', 'wb') as handle:
                pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
                print(f'SAVED TOKENIZER TO {name}_tokenizer.pickle')

            with open(f'model_dumps/{name}_msl.txt', 'w', encoding='utf8') as f:
                f.write(str(max_sequence_len))
                print(f'SAVED MAX_SEQ_LEN TO model_dumps/{name}_msl.txt')

            self.model = model
            self.tokenizer = tokenizer
            self.max_sequence_len = max_sequence_len

        if self.current_mode == 'predicting':

            with open(f'model_dumps/{name}_msl.txt', 'r', encoding='utf8') as f:
                self.max_sequence_len = int(f.read())
                print(f'OPENED model_dumps/{name}_msl.txt')

            with open(f'tokenizer_dumps/{name}_tokenizer.pickle', 'rb') as handle:
                self.tokenizer = pickle.load(handle)
                print(f'OPENED {name}_tokenizer.pickle')

            self.model = keras.models.load_model(f'model_dumps/{name}_model.h5')
            print(f'LOADED {name}_model.h5')
    

    def __random_value_gen(self) -> bool:
        return random.choice(self.random_word_arange) == 0


    def __word_crafter(self, ind) -> str:
        output_word = []
        sum_len = 0

        for word, index in self.tokenizer.word_index.items():
            if index in ind:
                sum_len += len(word)
                if sum_len > self.char_limit:
                    break
                output_word.append(word)

        if (self.shuffling):
            random.shuffle(output_word)

        return " ".join(output_word)


    def generate_response(self, message) -> str:
        token_list = self.tokenizer.texts_to_sequences([message])[0]
        token_list = pad_sequences([token_list], maxlen=self.max_sequence_len-1, padding='pre')
        pred = self.model.predict(token_list).tolist()
        all_predicts = pred[0]

        values = []
        ind = [] #indicies of classes
        ans_len = random.choice(self.ans_len_arange)

        for i in range(ans_len):
            if (i%2 == 1) and (self.__random_value_gen()):
                rand_pred = random.choice(all_predicts)
                values.append(rand_pred)
                all_predicts.remove(rand_pred)

            else:
                mx = max(all_predicts)
                values.append(mx)
                all_predicts.remove(mx)

        all_predicts = self.model.predict(token_list).tolist()[0]

        for i in range(len(all_predicts)):
            for value in values:
                if all_predicts[i] == value or abs(all_predicts[i] - value) < 1e-9:
                    ind.append(i)

        return self.__word_crafter(ind)

        

        
