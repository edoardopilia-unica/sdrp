# SDRP\tx_wav.py V. 2.0
# Eseguibile per generazione file wav codificati - Versione 1.0

import modem
import packer
import rdb
import wavefile
import sys



message = 'ABCabc0123456789[]{}'
FILENAME = '.\\wav\\burst.wav'

def tx(message_to_send, fname):
    data = modem.fsk_mod_signal(packer.rtty_encode_packets(message_to_send))
    wavefile.save_wav(data, fname, modem.get_sample_rate())

if __name__ == '__main__':
    print('Simple Data Radio Protocol V. 2.0')
    print('tx-wav standalone module')
    if len(sys.argv) > 1: message = sys.argv[1]

    if len(sys.argv) > 2: FILENAME = f'.\\wav\\{sys.argv[2]}'

    if len(sys.argv) > 3:
        if sys.argv[3] == '-d': rdb.set_debug(True)
        else: rdb.set_DEBUG(False)


    print(f"Status Debug: {rdb.get_debug()}")
    print(f'Messaggio da codificare: {message}')

    tx(message, FILENAME)


