
import numpy as np


def take_fft(data, fs):
    fs = float(fs)
    nfft = len(data)
    k = np.arange(nfft)
    T = nfft/fs
    frq = k/T # two sides frequency range
    frq = frq[range(nfft/2)] # one side frequency range
    Y = np.fft.fft(data)/nfft # fft computing and normalization
    Y = Y[range(nfft/2)]
    return frq, abs(Y)
