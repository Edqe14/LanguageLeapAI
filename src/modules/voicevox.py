from io import BytesIO
from os import getenv
from pathlib import Path
from threading import Thread
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
import time
import shutil

from modules.audio_to_device import play_voice

load_dotenv()

# Audio devices
SPEAKERS_INPUT_ID = int(getenv('VOICEMEETER_INPUT_ID'))
APP_INPUT_ID = int(getenv('CABLE_INPUT_ID'))

# Voicevox settings
BASE_URL = getenv('VOICEVOX_BASE_URL')
VOICE_ID = int(getenv('VOICE_ID'))
SPEED_SCALE = float(getenv('SPEED_SCALE'))
VOLUME_SCALE = float(getenv('VOLUME_SCALE'))
INTONATION_SCALE = float(getenv('INTONATION_SCALE'))
PRE_PHONEME_LENGTH = float(getenv('PRE_PHONEME_LENGTH'))
POST_PHONEME_LENGTH = float(getenv('POST_PHONEME_LENGTH'))

TTS_WAV_PATH = Path(__file__).resolve().parent.parent / r'audio\tts.wav'


def speak_jp(sentence):
    start = time.time()

    # generate initial query
    # params_encoded = urlencode({'text': sentence, 'speaker': VOICE_ID})
    # r = requests.post(f'{BASE_URL}/audio_query?{params_encoded}')

    # if r.status_code == 404:
    #     print('Unable to reach Voicevox, ensure that it is running, or the VOICEVOX_BASE_URL variable is set correctly')
    #     return
    
    # print(f'[VOICEVOX] Took {time.time() - start} seconds to query')

    # voicevox_query = r.json()
    # voicevox_query['speedScale'] = SPEED_SCALE
    # voicevox_query['volumeScale'] = VOLUME_SCALE
    # voicevox_query['intonationScale'] = INTONATION_SCALE
    # voicevox_query['prePhonemeLength'] = PRE_PHONEME_LENGTH
    # voicevox_query['postPhonemeLength'] = POST_PHONEME_LENGTH

    # synthesize voice as wav file
    params_encoded = urlencode({
        'speaker': VOICE_ID,
        'text': sentence,
        'speed_scale': SPEED_SCALE,
        'volume_scale': VOLUME_SCALE,
        'intonation_scale': INTONATION_SCALE,
        'pre_phoneme_length': PRE_PHONEME_LENGTH,
        'post_phoneme_length': POST_PHONEME_LENGTH,
    })
    # r = requests.post(f'{BASE_URL}/synthesis?{params_encoded}', json=voicevox_query, stream=True)
    r = requests.post(f'{BASE_URL}/tts?{params_encoded}', stream=True)

    print(f'[VOICEVOX] Took {time.time() - start} seconds to get synthesized')

    with open(TTS_WAV_PATH, 'wb') as outfile:
        shutil.copyfileobj(r.raw, outfile)
        # for chunk in r.iter_content(chunk_size=1024):
        #     if chunk:
        #         outfile.write(chunk)

    # play voice to app mic input and speakers/headphones
    threads = [Thread(target=play_voice, args=[APP_INPUT_ID]), Thread(target=play_voice, args=[SPEAKERS_INPUT_ID])]
    [t.start() for t in threads]
    [t.join() for t in threads]


if __name__ == '__main__':
    # test if voicevox is up and running
    print('Voicevox attempting to speak now...')
    speak_jp('むかしあるところに、ジャックという男の子がいました。ジャックはお母さんと一緒に住んでいました。')
