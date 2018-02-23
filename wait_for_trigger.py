import json
import sys

import pyaudio
import numpy as np

from take_fft import take_fft
from detect_peaks import detect_peaks

CHUNK = 1024
SAMP_FREQ = 44100
TONE_PRECISION = 500

def main():
    if len(sys.argv) < 2:
        print 'usage: %s TRIGGER_JSON_FILE' % (sys.argv[0])
    with open(sys.argv[1]) as f:
        conf = json.load(f)
    p = pyaudio.PyAudio()
    data = np.array([], dtype=np.int16)
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=SAMP_FREQ,
                    input=True)
    sounds = conf['sounds']
    num_sounds = len(sounds)
    sample_window = (sounds[-1]['time'] + num_sounds * conf['precision']) * SAMP_FREQ
    min_seperation = conf['precision'] * SAMP_FREQ
    while True:
        block = stream.read(CHUNK)
        data = np.append(data, np.frombuffer(block, dtype='int16'))
        if len(data) > sample_window:
            peaks = detect_peaks(data, mpd=min_seperation, max_peaks=num_sounds)
            triggered = True
            for i in range(num_sounds):
                if sounds[i]['type'] == 3 and data[peaks[i]] < sounds[i]['amplitude']:
                    triggered = False
                    break
                else:
                    if peaks[i] < CHUNK/2:
                        triggered = False
                        break
                    frq, Y = take_fft(data[peaks[i] - CHUNK/2 : peaks[i] + CHUNK/2], SAMP_FREQ)
                    frq = frq[1:]
                    Y = Y[1:]
                    if sounds[i]['type'] == 1:
                        idx = np.argmax(Y)
                        if abs(frq[idx] - sounds[i]['frequency']) > TONE_PRECISION or Y[idx] < sounds[i]['amplitude']:
                            triggered = False
                            break
                    elif sounds[i]['type'] == 2:
                        CLAP_POINTS = len(sounds[i]['frequency'])
                        idxs = np.argsort(Y)[-1:-(CLAP_POINTS + 1):-1]
                        for j in range(CLAP_POINTS):
                            if abs(frq[idxs[j]] - sounds[i]['frequency'][j]) > TONE_PRECISION or Y[idxs[j]] < sounds[i]['amplitude'][j]:
                                triggered = False
                                break
                if i > 0:
                    target_delta = sounds[i]['time'] - sounds[i - 1]['time']
                    delta = (peaks[i] - peaks[i - 1]) / float(SAMP_FREQ)
                    if abs(target_delta - delta) > conf['precision']:
                        triggered = False
                        break
            if triggered:
                exit(0)
            data = data[CHUNK:]


if __name__ == "__main__":
    main()