#SDRP\rdb.py V. 2.0
# Libreria funzioni di debug - Versione 1.0

__name__ = 'rdb'
import logging
import matplotlib.pyplot as plt

DEBUG = False

def set_debug(new_debug):
    global DEBUG
    DEBUG = new_debug

def get_debug():
    return DEBUG

def log(s):
    if DEBUG:
        print(s)

def plot_init(dim1, dim2):
    if DEBUG:
        plt.figure(figsize=(dim1, dim2))

def plot_add(signal, description, x,y,z):
    if DEBUG:
        plt.subplot(x,y,z)
        plt.title(description)
        plt.plot(signal)

def plot_show():
    if DEBUG:
        plt.tight_layout()
        plt.show()