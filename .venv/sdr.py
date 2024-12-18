import numpy as np
import scipy.signal as signal
import wave
from scipy.io.wavfile import read, write
from scipy.signal import stft, istft
import rtlsdr
import wavefile

def fm_demodulate(samples, sample_rate):
    # Unwrap the phase and smooth it
    phase = np.unwrap(np.angle(samples))
    smoothed_phase = signal.lfilter([1/3, 1/3, 1/3], 1, phase)  # Simple moving average filter
    demodulated = np.diff(smoothed_phase)

    # Remove DC offset from the demodulated signal
    demodulated -= np.mean(demodulated)

    # Decimate with anti-aliasing
    decimation_factor = 50
    audio = signal.decimate(demodulated, decimation_factor, n=8, ftype='fir')

    nyquist_rate = (sample_rate / decimation_factor) / 2

    # Lowpass Filter (15 kHz cutoff for FM audio bandwidth)
    cutoff_low = 15e3 / nyquist_rate
    b_low, a_low = signal.butter(5, cutoff_low, btype='low')
    audio_filtered = signal.lfilter(b_low, a_low, audio)

    # Bandpass Filter (300 Hz - 3.4 kHz for voice range)
    cutoff_band = [1900 / nyquist_rate, 6100 / nyquist_rate]
    b_band, a_band = signal.butter(6, cutoff_band, btype='band')
    audio_voice_filtered = signal.lfilter(b_band, a_band, audio_filtered)

    # Apply relaxed noise gate
    threshold = 0.02 * np.max(np.abs(audio_voice_filtered))
    audio_voice_filtered[np.abs(audio_voice_filtered) < threshold] = 0

    # Apply spectral subtraction for additional noise reduction
    freq_audio = np.fft.rfft(audio_voice_filtered)
    freq_magnitude = np.abs(freq_audio)
    noise_estimate = np.percentile(freq_magnitude, 20)  # Estimate noise floor
    freq_audio = np.where(freq_magnitude > noise_estimate, freq_audio, 0)
    audio_voice_filtered = np.fft.irfft(freq_audio)

    # Normalize only if the signal is non-zero
    max_val = np.max(np.abs(audio_voice_filtered))
    if max_val > 0:
        audio_normalized = np.int16(audio_voice_filtered / max_val * 32767)
    else:
        audio_normalized = np.zeros_like(audio_voice_filtered, dtype=np.int16)

    return audio_normalized, sample_rate / decimation_factor

def apply_notch_filter(audio, sample_rate, freq_to_remove, quality_factor=30):
    b, a = signal.iirnotch(freq_to_remove, quality_factor, sample_rate)
    filtered_audio = signal.lfilter(b, a, audio)
    return filtered_audio

def spectral_subtraction(audio, sample_rate):
    f, t, Zxx = stft(audio, fs=sample_rate, nperseg=1024)
    magnitude = np.abs(Zxx)
    phase = np.angle(Zxx)

    # Estimate noise floor as the median of the quiet parts
    noise_estimate = np.median(magnitude, axis=1, keepdims=True)
    magnitude_denoised = np.maximum(magnitude - noise_estimate, 0)

    # Reconstruct the signal
    Zxx_denoised = magnitude_denoised * np.exp(1j * phase)
    _, audio_denoised = istft(Zxx_denoised, fs=sample_rate)

    # Normalize the output
    audio_denoised = np.clip(audio_denoised / np.max(np.abs(audio_denoised)), -1, 1)
    return audio_denoised

def process_wav_file(input_file, output_file):
    # Read the WAV file
    sample_rate, audio = read(input_file)

    # Normalize the audio
    audio = audio / 32767.0

    # Apply spectral subtraction
    audio_denoised = spectral_subtraction(audio, sample_rate)

    # Apply notch filters for specific noise frequencies
    for freq in [50, 60]:  # Example: Remove 50 Hz and 60 Hz hum
        audio_denoised = apply_notch_filter(audio_denoised, sample_rate, freq)

    # Save the processed file
    audio_denoised = (audio_denoised * 32767).astype(np.int16)
    write(output_file, sample_rate, audio_denoised)
    print(f"Processed file saved as {output_file}")

Fs = 3.2e6
frequency = 90e6
bandwidth = 200e3
gain = 'auto'

def record_fm_to_wav(filename, duration=10):
    sdr = rtlsdr.RtlSdr()
    sdr.sample_rate = Fs
    sdr.center_freq = frequency
    sdr.gain = gain
    sdr.bandwidth = bandwidth

    try:
        print(f"Sintonizzazione su {frequency / 1e6} MHz per {duration} secondi...")

        chunk_duration = 0.5  # Durata di ogni chunk in secondi
        chunk_samples = int(Fs * chunk_duration)
        num_chunks = int(duration / chunk_duration)

        all_audio = []
        output_sample_rate = None

        for _ in range(num_chunks):
            samples = sdr.read_samples(chunk_samples)
            audio, output_sample_rate = fm_demodulate(samples, Fs)
            all_audio.append(audio)

        all_audio = np.concatenate(all_audio)
        wavefile.save_wav(all_audio, filename, output_sample_rate)
        print(f"File WAV salvato come {filename}")

    finally:
        sdr.close()

input_filename = "fm_recording.wav"
output_filename = "fm_recording_denoised.wav"
record_fm_to_wav(input_filename, duration=5)
process_wav_file(input_filename, output_filename)

