from os import getenv
from pathlib import Path
from time import sleep, time

import deepl
import googletrans
import keyboard
import pyaudio
import requests
from dotenv import load_dotenv

from modules.tts import speak

load_dotenv()

USE_DEEPL = getenv('USE_DEEPL', 'False').lower() in ('true', '1', 't')
DEEPL_AUTH_KEY = getenv('DEEPL_AUTH_KEY')
TARGET_LANGUAGE = getenv('TARGET_LANGUAGE_CODE')
MIC_ID = int(getenv('MICROPHONE_ID'))
RECORD_KEY = getenv('MIC_RECORD_KEY')
LOGGING = getenv('LOGGING', 'False').lower() in ('true', '1', 't')
MIC_AUDIO_PATH = Path(__file__).resolve().parent / r'audio/mic.wav'
CHUNK = 1024
FORMAT = pyaudio.paInt16


def transcribe_stream():
    global recording, stream, start

    def generate():
        global start
        while True:
            if not keyboard.is_pressed(RECORD_KEY):
                break
            
            yield stream.read(CHUNK)
        
        yield b''

        start = time()

    def send():
        global start

        try:
            url = getenv('VOICEVOX_BASE_URL')
            req = requests.post(f'{url}/asr_stream?task=transcribe&language=en&output=json', data=generate())

            eng_speech = req.json()['text'].strip()
            if eng_speech == 'you':
                return None
            
            return eng_speech
        except requests.exceptions.JSONDecodeError:
            print('Too many requests to process at once')
            return

    # t = Thread(target=send)
    # t.start()
    # t.join()

    eng_speech = send()
    print(f'Took {time() - start} seconds to transcribe.')

    if eng_speech:
        translate_start = time()

        if USE_DEEPL:
            translated_speech = translator.translate_text(eng_speech, target_lang=TARGET_LANGUAGE)
        else:
            translated_speech = translator.translate(eng_speech, dest=TARGET_LANGUAGE).text

        print(f'Took {time() - translate_start} seconds to translate.')

        if LOGGING:
            print(f'English: {eng_speech}')
            print(f'Translated: {translated_speech}')

        speak(translated_speech, TARGET_LANGUAGE)

    else:
        print('No speech detected.')

    print(f'Everything took {time() - start} seconds.')
    print('')


def on_press_key(_):
    global frames, recording, stream, req
    if not recording:
        print('Recording...')
        frames = []
        recording = True
        stream = p.open(format=FORMAT,
                        channels=MIC_CHANNELS,
                        rate=MIC_SAMPLING_RATE,
                        input=True,
                        frames_per_buffer=CHUNK,
                        input_device_index=MIC_ID)
        
        transcribe_stream()

def on_release_key(_):
    global recording, stream
    recording = False
    stream.stop_stream()
    stream.close()
    stream = None

    # # if empty audio file
    # if not frames:
    #     print('No audio file to transcribe detected.')
    #     print('')
    #     return

    # # write microphone audio to file
    # wf = wave.open(str(MIC_AUDIO_PATH), 'wb')
    # wf.setnchannels(MIC_CHANNELS)
    # wf.setsampwidth(p.get_sample_size(FORMAT))
    # wf.setframerate(MIC_SAMPLING_RATE)
    # wf.writeframes(b''.join(frames))
    # wf.close()

    # start = time()

    # # transcribe audio
    # try:
    #     eng_speech = transcribe(MIC_AUDIO_PATH)
    # except requests.exceptions.JSONDecodeError:
    #     print('Too many requests to process at once')
    #     return

    # if eng_speech:

    #     if USE_DEEPL:
    #         translated_speech = translator.translate_text(eng_speech, target_lang=TARGET_LANGUAGE)
    #     else:
    #         translated_speech = translator.translate(eng_speech, dest=TARGET_LANGUAGE).text

    #     if LOGGING:
    #         print(f'English: {eng_speech}')
    #         print(f'Translated: {translated_speech}')

    #     speak(translated_speech, TARGET_LANGUAGE)

    # else:
    #     print('No speech detected.')

    # print(f'Everything took {time() - start} seconds.')
    # print('')


if __name__ == '__main__':
    # speak('むかしあるところに、ジャックという男の子がいました。ジャックはお母さんと一緒に住んでいました。', 'ja')

    p = pyaudio.PyAudio()

    # get channels and sampling rate of mic
    mic_info = p.get_device_info_by_index(MIC_ID)
    # MIC_CHANNELS = mic_info['maxInputChannels']
    MIC_CHANNELS = 1
    # MIC_SAMPLING_RATE = int(mic_info['defaultSampleRate'])
    MIC_SAMPLING_RATE = 16000

    frames = []
    recording = False
    stream = None
    req = None

    # Set DeepL or Google Translator
    if USE_DEEPL:
        translator = deepl.Translator(DEEPL_AUTH_KEY)
    else:
        translator = googletrans.Translator()

    keyboard.on_press_key(RECORD_KEY, on_press_key)
    keyboard.on_release_key(RECORD_KEY, on_release_key)

    try:
        while True:
            sleep(0.01)

    except KeyboardInterrupt:
        print('Closing voice translator.')
