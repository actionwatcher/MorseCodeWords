import numpy as np
import queue
import json
from helpers import log
import helpers

def load_morse_table(filename):
    try:
        with open(filename, 'r') as file:
            morse_code_dict = json.load(file)
        return morse_code_dict
    except FileNotFoundError:
        log("error", f"Morse code mapping file <{filename}> not found.")
        exit() #FiXIT move exception handling up. This is not a correct place 
    except json.JSONDecodeError as e:
        log("error", f"Unable to decode {filename}: {e}")
        exit()


class MorseSoundSource:
    VolumeThreshold = helpers.dB2Amplitude(helpers.L_min) #determines if the source considered active or not
    def __init__(self, morse_mapping_filename, wpm=20, frequency=650, sample_rate=44100, rise_time=0.1, volume = 0.5, queue_sz = None):
        self.MORSE_CODE_DICT = load_morse_table(morse_mapping_filename)
        self._cur_msg = ''
        self.signal_dict={}
        self.sample_rate = sample_rate  # Standard audio sample rate in Hz
        self.frequency = frequency
        self.rise_time = rise_time  # Default rise time
        self._volume = volume
        self.signal = np.array([]) # last sent signal
        if self.volume <= self.VolumeThreshold:
            self.active = False
        else:
            self.active = True
        self.set_speed(wpm)
        self.signals =[]
        self.data_queue = queue.Queue()
        if queue_sz:
            self.data_queue.maxsize = queue_sz

    def reset(self):
        while(not self.data_queue.empty()):
            self.data_queue.get()
        self.signal = np.array([])
    
    def set_speed(self, wpm, slowdown=0):
        # Calculate durations based on WPM
        if hasattr(self, 'wpm') and self.wpm == wpm:
            return
        self.wpm = wpm
        self.dit_duration = 1.2 / self.wpm
        self.dah_duration = 3 * self.dit_duration
        self.element_gap = self.dit_duration
        self.symbol_gap = self.dah_duration + slowdown * self.dit_duration
        self.word_gap = 7 * self.dit_duration
        
        # Generate the arrays with the current frequency and volume
        self._generate_arrays()
    
    def set_frequency(self, frequency):
        self.frequency = frequency
        # Regenerate the arrays with the new frequency
        self._generate_arrays()

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, in_volume):
        if hasattr(self, '_volume') and in_volume == self._volume:
            return
        self._volume = in_volume
        if self._volume <= self.VolumeThreshold:
            self.deactivate()
            return
        self.activate()
        # Regenerate the arrays with the new volume
        self._generate_arrays()

    def set_rise(self, rise_time):
        self.rise_time = rise_time
        # Regenerate the arrays with the new rise time
        self._generate_arrays()

    def get_rise(self):
        return self.rise_time

    def _generate_arrays(self):
        # Generate time vectors for each element
        t_dit = np.linspace(0, self.dit_duration, int(self.dit_duration * self.sample_rate), endpoint=False)
        t_dah = np.linspace(0, self.dah_duration, int(self.dah_duration * self.sample_rate), endpoint=False)
        
        # Generate the sine wave for each element
        dit_wave = np.sin(2 * np.pi * self.frequency * t_dit)
        dah_wave = np.sin(2 * np.pi * self.frequency * t_dah)
        
        # Apply rise time using a cosine function
        rise_samples = int(self.rise_time * len(t_dit))  # Corrected rise samples calculation

        if rise_samples > 0:
            window_dit = np.ones(len(t_dit))
            window_dah = np.ones(len(t_dah))
            # Apply rise and fall for dit
            window_dit[:rise_samples] = 0.5 * (1 - np.cos(np.pi * np.arange(rise_samples) / rise_samples))
            window_dit[-rise_samples:] = 0.5 * (1 - np.cos(np.pi * np.arange(rise_samples, 0, -1) / rise_samples))
            dit_wave *= window_dit
            # Apply rise and fall for dah
            window_dah[:rise_samples] = 0.5 * (1 - np.cos(np.pi * np.arange(rise_samples) / rise_samples))
            window_dah[-rise_samples:] = 0.5 * (1 - np.cos(np.pi * np.arange(rise_samples, 0, -1) / rise_samples))
            dah_wave *= window_dah

        self.dit_array = self._volume * dit_wave
        self.dah_array = self._volume * dah_wave
        
        # Generate silence arrays for gaps
        self.element_gap_array = np.zeros(int(self.element_gap * self.sample_rate))
        self.symbol_gap_array = np.zeros(int(self.symbol_gap * self.sample_rate))
        self.word_gap_array = np.zeros(int(self.word_gap * self.sample_rate))
        self._build_signal_dict()
        self.signal = self._convert_to_signal(self._cur_msg)
    
    def get_speed(self):
        return self.wpm

    def get_frequency(self):
        return self.frequency

    def get_durations(self):
        return {
            "dit_duration": self.dit_duration,
            "dah_duration": self.dah_duration,
            "element_gap": self.element_gap,
            "symbol_gap": self.symbol_gap,
            "word_gap": self.word_gap
        }

    def get_arrays(self):
        return {
            "dit_array": self.dit_array,
            "dah_array": self.dah_array,
            "element_gap_array": self.element_gap_array,
            "symbol_gap_array": self.symbol_gap_array,
            "word_gap_array": self.word_gap_array
        }

    def play_string(self, message = None):
        """ will repeat previously sent message if no new message provided """
        if not self.active:
            if message:
                self._cur_msg = message.upper()
            return 0
        if message:
            self._cur_msg = message.upper()
            self.signal = self._convert_to_signal(self._cur_msg)
        if self.signal.any():
            self.data_queue.put(self.signal)
            return float(len(self.signal))/self.sample_rate
        else:
            return 0
    
    def get_audio_segment(self, size):
        result = np.zeros(size, dtype=np.float32)
        filled = 0

        while filled < size and not self.data_queue.empty():
            data = self.data_queue.queue[0]  # Peek at the first array in the queue
            available = len(data)
            to_copy = min(size - filled, available)
            result[filled:filled + to_copy] = data[:to_copy]
            filled += to_copy

            if to_copy < available:
                self.data_queue.queue[0] = data[to_copy:]  # Update the front array
            else:
                self.data_queue.get()  # Remove the front array from the queue

        return result

    def _generate_signal(self, morse_code_list):
        signal = np.array([])
        for symbol in morse_code_list:
            if symbol == ' ':
                signal = np.concatenate([signal, self.word_gap_array])
            else:
                for i, element in enumerate(symbol):
                    if element == '.':
                        signal = np.concatenate([signal, self.dit_array])
                    elif element == '-':
                        signal = np.concatenate([signal, self.dah_array])
                    if i < len(symbol) - 1:  # Add element gap if not the last element
                        signal = np.concatenate([signal, self.element_gap_array])
                signal = np.concatenate([signal, self.symbol_gap_array])
        if len(signal) == 0:
            return np.array([])  # Return an empty array if no valid Morse code is generated
        return signal  # Ensure signal is a list of arrays

    def deactivate(self):
        self.active = False
        self.reset()

    def activate(self):
        self.active = True

#Optimization
    def _build_signal_dict(self):
        for char, code in self.MORSE_CODE_DICT.items():
            self.signal_dict[char] = self._generate_signal([code])

    def _convert_to_signal(self, message):
        signal = np.array([])
        i = 0
        while i < len(message):
            if message[i] == '<':  # Detect start of a prosign
                end = message.find('>', i)
                if end != -1:
                    prosign = message[i+1:end]
                    if prosign in self.MORSE_CODE_DICT:
                        signal = np.concatenate([signal, self.signal_dict[prosign]])
                    i = end
            elif message[i] == ' ':
                signal = np.concatenate([signal, self.word_gap_array])
            else:
                char = message[i]
                signal = np.concatenate([signal, self.signal_dict[char]])
            i += 1
        return signal  # Return array of samples
