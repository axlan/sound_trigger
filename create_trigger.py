from threading import Thread
import json

import pyaudio
import numpy as np

from detect_peaks import detect_peaks
from take_fft import take_fft

CHUNK = 1024
SAMP_FREQ = 44100
CLAP_POINTS = 5

def wait_for_done():
    raw_input("Press Enter to stop recording")


def get_number(msg, lim=None):
    while True:
        try:
            n = float(raw_input(msg + ' '))
            if lim is None or n in lim:
                return n
        except ValueError:
            print 'Invalid Number'


def main():
    p = pyaudio.PyAudio()
    raw_input("Press Enter to start recording")
    t = Thread(target=wait_for_done)
    t.start()
    data = np.array([], dtype=np.int16)
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=SAMP_FREQ,
                    input=True)
    while t.isAlive():
        block = stream.read(CHUNK)
        data = np.append(data, np.frombuffer(block, dtype='int16'))
    num_sounds = int(get_number('How many sounds were made?'))
    precision = get_number('How precise should the timing be (seconds)?')
    sound_type = get_number('What kind of sound (1:tone 2:clap 3:anything)?', [1, 2, 3])
    threshold = get_number('How loud should a sound be to count compared to this recording (ie. .5 for half as loud)?')
    min_seperation = precision * SAMP_FREQ
    peaks = detect_peaks(data, mpd=min_seperation, max_peaks=num_sounds)
    trigger = {'precision': precision}
    sounds = []
    start_sample = peaks[0]
    for peak in peaks:
        sound = {'time': (peak - start_sample) / float(SAMP_FREQ),
                 'type': sound_type}
        if sound_type == 3:
            sound['amplitude'] = data[peak] * threshold
        else:
            frq, Y = take_fft(data[peak - CHUNK/2 : peak + CHUNK/2], SAMP_FREQ)
            frq = frq[1:]
            Y = Y[1:]
            if sound_type == 1:
                idx = np.argmax(Y)
                sound['amplitude'] = (Y[idx] * threshold).tolist()
                sound['frequency'] = frq[idx].tolist()
            elif sound_type == 2:
                idxs = np.argsort(Y)[-1:-(CLAP_POINTS + 1):-1]
                sound['amplitude'] = (Y[idxs] * threshold).tolist()
                sound['frequency'] = frq[idxs].tolist()
            # import matplotlib.pyplot as plt
            # plt.plot(frq, abs(Y), 'r') # plotting the spectrum
            # plt.xlabel('Freq (Hz)')
            # plt.ylabel('|Y(freq)|')
            # plt.show()
        sounds.append(sound)
    trigger['sounds'] = sounds
    print json.dumps(trigger)


if __name__ == "__main__":
    main()