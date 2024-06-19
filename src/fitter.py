import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import keras
import json
import numpy as np
import pickle


class Fitter:

    def __init__(self):
        pass


    def fit(self, name):
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

        self.save_model(model, tokenizer, name, max_sequence_len)


    def save_model(self, model, tokenizer, name, max_sequence_len):
        model.save(f'model_dumps/{name}_model.h5')
        print(f'SAVED MODEL TO {name}_model.h5')
            
        with open(f'tokenizer_dumps/{name}_tokenizer.pickle', 'wb') as handle:
            pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
            print(f'SAVED TOKENIZER TO {name}_tokenizer.pickle')

        with open(f'model_dumps/{name}_msl.txt', 'w', encoding='utf8') as f:
            f.write(str(max_sequence_len))
            print(f'SAVED MAX_SEQ_LEN TO model_dumps/{name}_msl.txt')