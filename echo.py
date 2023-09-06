import random
from common_words import common_english_words
import streamlit as st
import pyaudio
import websockets
import asyncio
import base64
import json
from nltk.corpus import cmudict
import nltk
# from config import auth_key


with open("word_last_syllables.json", "r") as f:
    word_last_syllables = json.load(f)


def download_nltk_resources():
    # check if cmudict is already downloaded
    if not nltk.data.find("corpora/cmudict"):
        nltk.download("cmudict")


download_nltk_resources()
d = cmudict.dict()


def get_last_syllables(word):
    if word in d:
        phonemes = d[word][0]
        return phonemes[-2:]
    else:
        # word not found
        return None


if 'score' not in st.session_state:
    st.session_state.score = 0  # initial score

if 'feedback' not in st.session_state:
    st.session_state.feedback = False

if 'run' not in st.session_state:
    st.session_state.run = False

if 'heard_message_displayed' not in st.session_state:
    st.session_state.heard_message_displayed = False

# pyaudio setup
FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
p = pyaudio.PyAudio()

stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER
)


def check_rhyme(target_word_syllables, user_word):
    user_word_syllables = get_last_syllables(user_word)

    if target_word_syllables is None or user_word_syllables is None:
        return False

    if len(target_word_syllables[1]) > 1:
        return user_word_syllables[1] == target_word_syllables[1]

    return user_word_syllables == target_word_syllables


def start_listening():
    st.session_state.run = True


def stop_listening():
    st.session_state.run = False


def update_score(new_score):
    st.session_state.score = new_score
    scorebox.markdown(
        f'<p style="font-size: 2em; text-align: right"> Score: {st.session_state.score} </p>',  # noqa
        unsafe_allow_html=True
    )


word_list = common_english_words

target_word = random.choice(word_list)
target_word_syllables = word_last_syllables[target_word]


header = st.container()
scorebox = st.empty()
target = st.container()
messages = st.empty()
userbox = st.container()

with header:
    st.title('EchoMecho')
    st.text('Say a word that rhymes with the word you see')
    st.button('go', on_click=start_listening)


with target:
    if st.session_state.run:
        st.markdown(
            f'<h1 style="font-size: 8em; text-align: center;">"{target_word}"</h1>', unsafe_allow_html=True)  # noqa


# the AssemblyAI endpoint
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

update_score(st.session_state.score)


async def send_receive():
    print(f'Connecting websocket to url ${URL}')
    async with websockets.connect(
        URL,
        extra_headers=(("Authorization", st.secrets.auth_key),
                       ),  # for local use import auth_key from config; for delopy I'm using streamlit sercrets managament # noqa
        ping_interval=5,
        ping_timeout=20
    ) as _ws:
        await asyncio.sleep(0.1)
        print("Receiving SessionBegins ...")
        session_begins = await _ws.recv()
        print(session_begins)
        print("Sending messages ...")

        async def send():
            while st.session_state.run:

                try:
                    data = stream.read(FRAMES_PER_BUFFER)
                    data = base64.b64encode(data).decode("utf-8")
                    json_data = json.dumps({"audio_data": str(data)})
                    r = await _ws.send(json_data)
                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    assert e.code == 4008
                    break
                except Exception as e:
                    print("Unexpected exception:", e)
                r = await asyncio.sleep(0.01)  # noqa

            return True

        async def receive():
            while st.session_state.run:

                try:
                    result_str = await _ws.recv()
                    detect = json.loads(result_str)['confidence']

                    if detect > 0.0 and not st.session_state.heard_message_displayed:  # noqa
                        messages.markdown(
                            '<p style="font-size: 1em; text-align: center; color: gray;">I hear you...</h1>', unsafe_allow_html=True)  # noqa
                        st.session_state.heard_message_displayed = True

                    done = json.loads(result_str)[
                        'message_type'] == 'FinalTranscript'
                    if done and len(json.loads(result_str)['words']) > 0:  # noqa
                        user_word = json.loads(result_str)[
                            'words'][0]['text'].lower().rstrip('.')
                        phonemes1 = get_last_syllables(user_word)
                        phonemes2 = target_word_syllables
                        is_same = user_word == target_word
                        is_rhyme = check_rhyme(
                            target_word_syllables, user_word) and not is_same
                        verdict = 'Correct' if is_rhyme else (
                            'Self-rhyme' if is_same else 'Incorrect')
                        html_good = f'''
                                    <h1 style="font-size: 2em; text-align: center; color: green;">Yes!</h1>
                                    <h2 style="font-size: 2em; text-align: center;">'{user_word}' rhymes with '{target_word}'!</h2>
                                    '''  # noqa
                        html_bad = f'''
                                    <h1 style="font-size: 2em; text-align: center; color: red;">No.</h1>
                                    <h2 style="font-size: 2em; text-align: center;">'{user_word}' doesn't rhyme with '{target_word}'!</h2>
                                    '''  # noqa
                        html_blah = f'''
                                    <h1 style="font-size: 2em; text-align: center; color: yellow;">hmm.</h1>
                                    <h2 style="font-size: 1em; text-align: center;">Strictly speaking, yes. But that's not the game!</h2>
                                    '''  # noqa
                        combined_message = (
                            f'Word detected: \'{user_word}\'\n'f'Phonetic transcription: {phonemes1} ≈ {phonemes2} \n\n\n'f'{verdict}')  # noqa
                        messages.code(combined_message, language='plaintext')

                        st.markdown(html_good if is_rhyme else (
                            html_blah if is_same else html_bad), unsafe_allow_html=True)  # noqa

                        if is_rhyme:  # noqa
                            new_score_value = st.session_state.score + 1
                            update_score(new_score_value)

                        st.session_state.run = False

                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    assert e.code == 4008
                    break
                except Exception as e:
                    print("Unexpected exception:", e)
        st.session_state.run = True
        scorebox.markdown(
            f'<p style="font-size: 2em; text-align: right"> Score: {st.session_state.score} </p>', unsafe_allow_html=True)  # noqa

        send_result, receive_result = await asyncio.gather(send(), receive())


if st.session_state.run:
    received_data = asyncio.run(send_receive())
