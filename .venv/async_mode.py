import threading
import queue

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

BIT_DURATION = 0.01 #S - durata in secondi per bit

def get_bit_duration():
    return BIT_DURATION

def set_bit_duration(bit_duration):
    global BIT_DURATION
    BIT_DURATION = bit_duration

# SDRP\packer.py V. 1.0
# Libreria Gestione Pacchetti - Versione 1.0

import alphabet
import rdb

CHAR_EOB = '00011011' #end of block #
CHAR_EOP = '00000011' #end of payload '
CHAR_EOF = '00011000' #end of file °
CHAR_START = '00001010' #start $
MAX_PAYLOAD_SIZE = 65472

class Packet:
    source = 0
    mode = 0
    indice = 0
    payload = 0
    def __init__(self, source, mode, indice, payload):
        self.source = source
        self.mode = mode
        self.indice = indice
        self.payload = payload
    def __str__(self):
        return f'Sorgente: {self.source} - Indice: {self.indice} - Payload: {self.payload}'


def fsk_dem_signal(wave_received, queue):  # funzione demodulatrice in frequenza
    wave_received = bandpass(wave_received, FREQ_0, FREQ_1, SAMPLE_RATE)
    bit_duration_samples = int(SAMPLE_RATE * BIT_DURATION)

    for i in range(0, len(wave_received), bit_duration_samples):
        chunk = wave_received[i:i + bit_duration_samples]  # crea chunk
        windowed_chunk = chunk * np.hamming(len(chunk))
        fft_result = np.abs(fft(windowed_chunk))  # Calcola la FFT
        freqs = np.fft.fftfreq(len(fft_result), d=1 / SAMPLE_RATE)
        peak_freq = abs(freqs[np.argmax(fft_result)])  # Trova la frequenza dominante
        rdb.log(f'Frequenza dominante: {peak_freq} Hz')
        # Decodifica in base alla frequenza dominante rilevata
        if abs(peak_freq - FREQ_1) < abs(peak_freq - FREQ_0):
            queue.put('1')
        else:
            queue.put('0')
    queue.put(None)  # Segnale di fine


def rtty_decode_packets(queue, current_station=0):
    burst = ""
    decoded_packets = []

    while True:
        bit = queue.get()
        if bit is None:
            break
        burst += bit

        if len(burst) >= 8 and burst[-8:] == CHAR_START:
            rdb.log('Start trovato')
            while len(burst) < 56:
                bit = queue.get()
                if bit is None:
                    break
                burst += bit

            if len(burst) >= 56:
                packet_base = burst[:36]
                packet_info = burst[36:56]
                burst = burst[56:]

                packet_source = int(packet_base[8:18], 2)
                rdb.log(f'Sorgente: {packet_source}')
                packet_destination = int(packet_base[18:28], 2)
                rdb.log(f'Destinazione: {packet_destination}')

                if current_station != packet_destination:
                    rdb.log('Destinazione non coerente')
                    continue  # discard the packet

                mode = int(packet_info[:2], 2)  # not implemented yet
                rdb.log(f'Modalita\': {mode}')
                index = int(packet_info[2:12], 2)
                rdb.log(f'Index: {index}')

                coded_payload = ""
                while True:
                    byte = burst[:8]
                    burst = burst[8:]
                    if byte == CHAR_EOF or len(byte) < 8:
                        break
                    coded_payload += byte

                decoded_payload = alphabet.decode_message(coded_payload)
                current_packet = Packet(packet_source, mode, index, payload=decoded_payload)
                decoded_packets.append(current_packet)
                rdb.log(current_packet.payload)

    rdb.log(decoded_packets)
    return decoded_packets

# Creazione della coda
queue = queue.Queue()

# Creazione dei thread
thread_fsk = threading.Thread(target=fsk_dem_signal, args=(wave_received, queue))
thread_rtty = threading.Thread(target=rtty_decode_packets, args=(queue,))

# Avvio dei thread
thread_fsk.start()
thread_rtty.start()

# Attesa della fine dei thread
thread_fsk.join()
thread_rtty.join()
