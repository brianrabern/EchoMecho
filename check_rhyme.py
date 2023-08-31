# testing out the the rhyme chking logic

from nltk.corpus import cmudict
import nltk
# import json


def download_nltk_resources():
    # check if cmudict is already downloaded
    if not nltk.data.find("corpora/cmudict"):
        nltk.download("cmudict")


def get_last_syllables(word):
    if word in d:
        phonemes = d[word][0]
        return phonemes[-2:]
    else:
        # word not found
        return None


def check_rhyme(target_word_syllables, user_word):
    user_word_syllables = get_last_syllables(user_word)

    if target_word_syllables is None or user_word_syllables is None:
        return False

    if len(target_word_syllables[1]) > 1:
        return user_word_syllables[1] == target_word_syllables[1]

    return user_word_syllables == target_word_syllables


download_nltk_resources()
d = cmudict.dict()


target_word = "them"

# this is preprocessed in the main app
target_word_syllables = get_last_syllables(target_word)

# with open("word_last_syllables.json", "r") as f:
#     word_last_syllables = json.load(f)
# target_word_syllables = word_last_syllables[target_word]

user_word = "time"
result = check_rhyme(target_word_syllables, user_word)

print(target_word_syllables, get_last_syllables(user_word))
print(result)
