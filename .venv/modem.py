# SDRP\modem.py V. 1.0
# Libreria Modulazione-Demodulazione AFSK - Versione 1.0

from signal import signal
import wave
import numpy as np
from scipy.fft import fft
from scipy.signal import butter, filtfilt
from scipy.io.wavfile import write, read
import sys
import packer
import rdb
import wavefile

SAMPLE_RATE = 22050 #Hz - Frq campionamento

def get_sample_rate():
    return SAMPLE_RATE

def set_sample_rate(sample_rate):
    global SAMPLE_RATE
    SAMPLE_RATE = sample_rate

BIT_DURATION = 0.0008 #S - durata in secondi per bit --- 0.0001 limite di nyquist (20000 Hz => si degrada) => 1,250 kbps
#BIT_DURATION = 0.0003 #S => 3.33 kbps


def get_bit_duration():
    return BIT_DURATION

def set_bit_duration(bit_duration):
    global BIT_DURATION
    BIT_DURATION = bit_duration

T = np.linspace(0, BIT_DURATION, int(SAMPLE_RATE * BIT_DURATION), endpoint=False)
FREQ_0 = 2000 #Hz - Frq per bit = 0
TONE_0 = np.sin(2*np.pi*FREQ_0*T)
FREQ_1 = 6000 #Hz - Frq per bit = 1
TONE_1 = np.sin(2*np.pi*FREQ_1*T)
bandpass_par = 200 #Hz

def fsk_mod_signal(data): #funzione modulatrice in frequenza
    fsk_signal = np.array([])
    tone_seq = []
    packet_number=1
    for packet in data:
        bit_number = 0
        for bit in packet:
            rdb.log(f'{bit_number}/{len(packet)} : {packet_number}/{len(data)}')
            if bit == '1':
                tone_seq.append(TONE_1)
                #fsk_signal = np.append(fsk_signal, TONE_1)
            else:
                tone_seq.append(TONE_0)
                #fsk_signal = np.append(fsk_signal, TONE_0)
                bit_number += 1
        packet_number+=1
        fsk_signal = np.append(fsk_signal, np.array(tone_seq)) #incrementa velocita' (testo di 2k caratteri in circa 1s)
    return fsk_signal

def fsk_dem_signal(wave_received):  # funzione demodulante
    bytestr = ""
    wave_received = bandpass(wave_received, FREQ_0, FREQ_1, SAMPLE_RATE)
    bit_duration_samples = int(SAMPLE_RATE * BIT_DURATION)
    #hamming_window = np.hamming(bit_duration_samples)

    for i in range(0, len(wave_received), int(SAMPLE_RATE * BIT_DURATION)):
        chunk = wave_received[i:i + bit_duration_samples]  # crea chunk
        windowed_chunk = chunk * np.hamming(len(chunk))
        fft_result = np.abs(fft(windowed_chunk))  # Calcola la fft
        freqs = np.fft.fftfreq(len(fft_result), d=1 / SAMPLE_RATE)
        peak_freq = abs(freqs[np.argmax(fft_result)])  # Trova la frequenza dominante
        rdb.log(f'Frequenza dominante: {peak_freq}, Hz')
        # Converti frequenza dominante in bit
        if abs(peak_freq - FREQ_1) < abs(peak_freq - FREQ_0):
            bytestr += '1'
        else:
            bytestr += '0'

    return packer.rtty_decode_packets(bytestr)


def bandpass(signal_to_filter, lowfrq, highfrq, sample_rate):
    nyquist = 0.5 * sample_rate
    low = (lowfrq - bandpass_par) / nyquist
    high = (highfrq + bandpass_par) / nyquist
    b, a = butter(4, [low, high], btype='band')
    return filtfilt(b, a, signal_to_filter)


