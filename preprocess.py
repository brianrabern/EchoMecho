# this script preprocesses the word list
# and saves the last two syllables of each word to a JSON file

import json
from nltk.corpus import cmudict
import nltk
from common_words import common_english_words
nltk.download("cmudict")

# get phonemes of last two syllables of a word


def get_last_syllables(word, num_syllables=2):
    d = cmudict.dict()
    if word in d:
        phonemes = d[word][0]
        return phonemes[-num_syllables:]
    else:
        # word not found in lexicon
        print(f'Word "{word}" not found in lexicon')
        return None


# preprocess the word list
word_list = common_english_words
word_last_syllables = {word: get_last_syllables(word) for word in word_list}

# save the dictionary to a JSON file
with open("word_last_syllables.json", "w") as f:
    json.dump(word_last_syllables, f)
