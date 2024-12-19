# SDRP\packer.py V. 2.0
# Libreria Gestione Pacchetti - Versione 2.0

import alphabet
import rdb

CHAR_EOB = '00011011' #end of block #
CHAR_EOP = '00000011' #end of payload '
CHAR_EOF = '00011000' #end of file °
CHAR_START = '00001010' #start §
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


def rtty_encode_packets(message, source=0, destination=0):
    packets = []
    packet_base = CHAR_START
    packet_base += bin(source)[2:].zfill(10)
    packet_base += bin(destination)[2:].zfill(10)
    packet_base += CHAR_EOB
    packet_base += '00'  # RTTY Mode

    coded_message = alphabet.encode_message(message)
    packet_index = 0

    if len(coded_message) < MAX_PAYLOAD_SIZE:
        packet_base += bin(packet_index)[2:].zfill(10)
        packet_base += CHAR_EOB
        packet_base += coded_message
        packet_base += CHAR_EOF
        packets.append(packet_base)
    else:
        n = 0
        while n < len(coded_message):
            current_packet = packet_base
            current_packet += bin(packet_index)[2:].zfill(10)
            current_packet += CHAR_EOB
            current_packet += coded_message[n:n+MAX_PAYLOAD_SIZE]
            current_packet += CHAR_EOF
            n += MAX_PAYLOAD_SIZE
            packet_index += 1
            packets.append(current_packet)
    return packets


def rtty_decode_packets(burst, current_station=0):
    decoded_packets = []
    #suspended_packets = []
    n = 0
    while n < len(burst)-56:
        packet_base = burst[n:n+36]
        packet_info = burst[n+36:n+56]

        if packet_base[0:8] != CHAR_START:
            rdb.log('Start non trovato')
            n += 1
        else:
            rdb.log(f'{n}/{len(burst)}')
            packet_source = int(packet_base[8:18], 2)
            rdb.log(f'Sorgente: {packet_source}')
            packet_destination = int(packet_base[18:28], 2)
            rdb.log(f'Destinazione: {packet_destination}')
            if current_station != packet_destination:
                rdb.log('Destinazione non coerente')
                n+=1
                continue  # discard the packet
            mode = int(packet_info[:2], 2)  # not implemented yet
            rdb.log(f'Modalita\': {mode}')
            index = int(packet_info[2:12], 2)
            rdb.log(f'Index: {index}')
            eight_counter = 0
            flag_eof = False
            coded_payload = ''
            while not flag_eof:
                start_index = n + 56 + eight_counter
                rdb.log(f'{start_index}/{len(burst)}')
                byte = burst[start_index:start_index + 8]
                if byte != CHAR_EOF and start_index+8 < len(burst):
                    coded_payload += byte
                    eight_counter += 8
                else:
                    eight_counter += 8
                    flag_eof = True

            decoded_payload = alphabet.decode_message(coded_payload)
            current_packet = Packet(packet_source, mode, index, payload=decoded_payload)

            decoded_packets.append(current_packet)
            n = n + 56 + eight_counter
            rdb.log(current_packet.payload)

    rdb.log(decoded_packets)
    return decoded_packets

