#SDRP\wavefile.py V. 1.0
# Libreria funzioni di debug - Versione 1.0

import wave
import numpy as np

def load_wav(fname):
    with wave.open(fname, 'rb') as wav:
        if wav.getsampwidth() != 2 or wav.getnchannels() != 1:
            raise ValueError("Il file WAV deve essere PCM 16 bit mono")
        sample_rate = wav.getframerate()
        data = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
    return sample_rate, data

def save_wav(signal, fname, sample_rate):
    signal = np.clip(signal, -1, 1) #Segnale in range +1;-1
    int_signal = (signal * 32767).astype(np.int16) #Conversione a 16-bit PCM
    with wave.open(fname, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2) #16 bit
        wav.setframerate(sample_rate)
        wav.writeframes(int_signal.tobytes())