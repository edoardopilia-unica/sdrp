# SDRP\tx_wav.py V. 1.0
# Eseguibile per decodifica file wav - Versione 1.0


import modem
import packer
import rdb
import wavefile
import packer
import sys
from collections import defaultdict
import itertools
import operator


FILENAME = '.\\wav\\burst.wav'


def rx_file(fname):
    wav_load = wavefile.load_wav(fname)
    decoded_signal=modem.fsk_dem_signal(wav_load[1])
    return decoded_signal


def print_decoded(decoded_packet):
    print(f'Pacchetti ricevuti: {len(decoded_packet)}')

    packet_burst_source = []
    decoded_packet.sort(key=lambda tup: tup.indice)
    source_list=[]
    for packet in decoded_packet:

        sorgente = packet.source
        payload = packet.payload

        if not (sorgente in source_list):
            packet_burst_source.append([sorgente, ''])
            source_list.append(sorgente)
        source_index = source_list.index(sorgente)
        old_payload = packet_burst_source[source_index][1]
        packet_burst_source[source_index] = (sorgente, f'{old_payload}{payload}')

    for source_packet in packet_burst_source:
        print(f'Sorgente: {source_packet[0]} - Messaggio: {source_packet[1]}')


def rx():
    try:
        decoded = rx_file(FILENAME)
    except FileNotFoundError as e:
        print(f'File non trovato - {e}')
    else:
        print_decoded(decoded)

if __name__ == '__main__':
    print('Simple Data Radio Protocol V. 2.0')
    print('rx-wav standalone module')

    if len(sys.argv) > 1: FILENAME = f'{sys.argv[1]}'

    if len(sys.argv) > 2:
        if sys.argv[2] == '-d':
            rdb.set_debug(True)
        else:
            rdb.set_DEBUG(False)


    print(f"Status Debug: {rdb.get_debug()}")
    rx()