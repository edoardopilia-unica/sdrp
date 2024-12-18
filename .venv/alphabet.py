# SDRP\alphabet.py V. 1.0
# Liberia per codifica 8P per l'utilizzo di SDRP in modalità rtty - Versione 1.0


__name__ = 'alphabet'
import itertools
import operator
from textwrap import wrap

import rdb

CHAR_MAP = {
    # Numeri
    '01100000': '0', '01000001': '1', '01000010': '2', '01100011': '3', '01000100': '4',
    '01100101': '5', '01100110': '6', '01000111': '7', '01001000': '8', '01101001': '9',

    # Lettere
    '10010000': 'a', '10001000': 'b', '10000100': 'c', '10000010': 'd', '10000001': 'e',
    '10011111': 'f', '10101111': 'g', '10001110': 'h', '10110111': 'i', '10111011': 'j',
    '10111000': 'k', '10110100': 'l', '10110010': 'm', '10110001': 'n', '10101100': 'o',
    '10101010': 'p', '10101001': 'q', '10100110': 'r', '10100101': 's', '10100011': 't',
    '10111110': 'u', '10011100': 'v', '10011010': 'w', '10011001': 'x', '10010110': 'y',
    '10010101': 'z',
    '11110000': 'A', '11101000': 'B', '11100100': 'C', '11100010': 'D', '11100001': 'E',
    '11111111': 'F', '11101111': 'G', '11101110': 'H', '11010111': 'I', '11011011': 'J',
    '11011000': 'K', '11010100': 'L', '11010010': 'M', '11010001': 'N', '11001100': 'O',
    '11001010': 'P', '11001001': 'Q', '11000110': 'R', '11000101': 'S', '11000011': 'T',
    '11011110': 'U', '11111100': 'V', '11111010': 'W', '11111001': 'X', '11110110': 'Y',
    '11110101': 'Z',

    #Simboli speciali:
    '00100001': '[', '00100010': ']', '00100100': '{', '00101000': '}','00110000': ':',
    '00010001': ' ', '00010010': '/', '00111111': '.',


    # Simboli riservati
    '00000011': '\'', '00011000': '°', '00011011': '#','00001010': '§'

    # ' => end of payload
    # ° => end of file
    # # => end of block
    # § => start
    # ? => non valido
}
ENCODE_MAP = {v: k for k,v in CHAR_MAP.items()}

NUMBER_MAP = {
    '00000': '0', '00001': '1', '00010': '2', '00011': '3', '00100': '4',
    '00101': '5', '00110': '6', '00111': '7', '01000': '8', '01001': '9'
}

LETTER_MAP = {
    '10000': 'a', '01000': 'b', '00100': 'c', '00010': 'd', '00001': 'e',
    '11111': 'f', '01111': 'g', '01110': 'h', '10111': 'i', '11011': 'j',
    '11000': 'k', '10100': 'l', '10010': 'm', '10001': 'n', '01100': 'o',
    '01010': 'p', '01001': 'q', '00110': 'r', '00101': 's', '00011': 't',
    '11110': 'u', '11100': 'v', '11010': 'w', '11001': 'x', '10110': 'y',
    '10101': 'z',
}

SPECIAL_MAP = {
    '00100001': '[', '00100010': ']', '00100100': '{', '00101000': '}','00110000': ':',
    '00010001': ' ', '00110010': '/', '00111111': '.',
}

RESERVED_MAP = {
    '00000011': '\'', '00011000': '°', '00011011': '#','00001010': '§'
}

IDENT_NUMBER = '01'
IDENT_LETTER = ['10', '11']
IDENT_SPECIAL = '00'

PARITY_INDEX = 2
CHAR_EOB = '00011011' #end of block #
CHAR_EOP = '00000011' #end of payload '
CHAR_EOF = '00011000' #end of file °
CHAR_START = '00001010' #start $
CHAR_UNKNOWN = '00000000' #simbolo sconosciuto
LIT_UNKNOWN = '?'
BURST_NUMBER = 3


def check_parity(bits):
    parity = 0
    for bit in bits:
        parity += eval(bit)
    return parity%2 == 0

def commute(bits, index):
    if bits[index] == '1': bits[index] = '0'
    elif bits[index] == '0': bits[index] = '1'
    return bits

def extract_map(bits):
    if bits in CHAR_MAP: return CHAR_MAP[bits]
    return LIT_UNKNOWN

def get_type(bits):
    if bits[:2] == IDENT_NUMBER: return 'number'
    if bits[:2] == IDENT_LETTER: return 'letter'
    if bits[:2] == IDENT_SPECIAL: return 'special'
    if bits is None: return None
    return 'unknown'

def se_solver(bits):
    """
    Single Error Solver
    se_solver restituisce una lista di tuple contenente la permutazione di ciascun bit (se il carattere è contenuto in CHAR_MAP) e la tipologia di carattere
    Returns: 1st ParityCommute - 0
    :param bits: Iterabile
    :return solutions: list:(solution, solution_type)
    """
    solutions = []
    i = 0
    while i<len(bits):
        possible_solution = commute(bits, i)
        if possible_solution in CHAR_MAP and check_parity(possible_solution):
            solutions.append([CHAR_MAP[possible_solution], get_type(possible_solution)])
        else:
            solutions.append(None)
    return solutions

def get_spec_solution(solutions, sol_type):
    retlist = []
    for solution in solutions:
        if solution[1] == sol_type: retlist.append(solution[0])
    return retlist

def decode(bits):
    if len(bits) != 8: raise ValueError(f'Lunghezza {len(bits)} diversa da 8 - {bits}')
    return extract_map(bits)

def encode(symbol):
    if symbol in ENCODE_MAP and not(symbol in RESERVED_MAP):
        return ENCODE_MAP[symbol]
    return CHAR_UNKNOWN

def encode_message(message):
    encoded = ''
    for char in message:
            encoded += encode(char)
    return encoded

def decode_message(bitstring):
    decoded = ''
    n = 0
    if (len(bitstring) % 8 ) != 0: raise ValueError(f'Lunghezza {len(bitstring)} non multiplo di 8')
    while n < len(bitstring):
        rdb.log(f'Valore indice: {n}')
        byte = bitstring[n:n+8]
        try:
            decoded += decode(byte)
        except ValueError:
            decoded += LIT_UNKNOWN
        finally:
            n += 8
    return decoded



























