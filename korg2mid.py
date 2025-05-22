import struct
import re
import sys
import os
import argparse
from midiutil import MIDIFile
from collections import defaultdict

# Constants from korg_m01_extractor
SONG_MARKER = b'\x73\x6F\x6E\x67'
INSERT_DATA = b'\x73\x6F\x6E\x67\x00\x00\x00\x00\x00\x00\x00\x00'
MARKER_OFFSET = 0x1F0
FIRST_SONG_OFFSET = 0x1000
SONG_SPACING = 0xC000
ORIG_DIR = "songs"
NEW_DIR = "M01Dn_00000000"

# Constants from korg_m01_extractor
SONG_MARKER = b'\x73\x6F\x6E\x67'
INSERT_DATA = b'\x73\x6F\x6E\x67\x00\x00\x00\x00\x00\x00\x00\x00'
MARKER_OFFSET = 0x1F0
FIRST_SONG_OFFSET = 0x1000
SONG_SPACING = 0xC000
ORIG_DIR = "songs"
NEW_DIR = "M01Dn_00000000"

INSTRUMENT_MAP = {
    # Keyboards
    (0x00, 0x00, 0x00): {'name': 'Piano', 'program': 0},
    (0x00, 0x00, 0x01): {'name': 'Electric Piano 1', 'program': 4},
    (0x00, 0x00, 0x02): {'name': 'Electric Piano 2', 'program': 5},
    (0x00, 0x00, 0x03): {'name': 'Electric Piano 3', 'program': 6},
    (0x00, 0x00, 0x04): {'name': 'Clavinet', 'program': 7},
    (0x00, 0x00, 0x05): {'name': 'Harpsicord', 'program': 6},
    (0x00, 0x00, 0x06): {'name': 'Organ 1', 'program': 16},
    (0x00, 0x00, 0x07): {'name': 'Organ 2', 'program': 17},
    (0x00, 0x00, 0x08): {'name': 'Magic Organ', 'program': 19},
    (0x00, 0x00, 0x09): {'name': 'DW-Piano', 'program': 0},
    (0x00, 0x00, 0x0A): {'name': 'DW-Electric Piano 1', 'program': 4},
    (0x00, 0x00, 0x0B): {'name': 'DW-Electric Piano 2', 'program': 5},
    (0x00, 0x00, 0x0C): {'name': 'DW-Electric Piano 3', 'program': 6},
    (0x00, 0x00, 0x0D): {'name': 'DW-Clavinet', 'program': 7},
    (0x00, 0x00, 0x0E): {'name': 'DW-Organ 1', 'program': 16},
    (0x00, 0x00, 0x0F): {'name': 'DW-Organ 2', 'program': 17},
    (0x01, 0x00, 0x00): {'name': 'Analog Piano', 'program': 0},
    (0x01, 0x00, 0x01): {'name': 'Soft Electric Piano', 'program': 5},
    (0x01, 0x00, 0x02): {'name': 'Electric Piano', 'program': 4},
    (0x01, 0x00, 0x03): {'name': 'Piano Pad 1', 'program': 88},
    (0x01, 0x00, 0x04): {'name': 'Piano Pad 2', 'program': 89},
    (0x01, 0x00, 0x05): {'name': 'SynPiano', 'program': 90},
    (0x01, 0x00, 0x06): {'name': 'Clavinet', 'program': 7},
    (0x01, 0x00, 0x07): {'name': 'Harpsicord', 'program': 6},
    (0x01, 0x00, 0x08): {'name': 'Percussion Organ', 'program': 16},
    (0x01, 0x00, 0x09): {'name': 'Organ 1', 'program': 16},
    (0x01, 0x00, 0x0A): {'name': 'Organ 2', 'program': 17},
    (0x01, 0x00, 0x0B): {'name': 'Rotary Organ', 'program': 18},
    (0x01, 0x00, 0x0C): {'name': 'Gospel Organ', 'program': 19},
    (0x01, 0x00, 0x0D): {'name': 'Pipe Organ 1', 'program': 20},
    (0x01, 0x00, 0x0E): {'name': 'Pipe Organ 2', 'program': 21},
    (0x01, 0x00, 0x0F): {'name': 'Accordion', 'program': 23},
    (0x02, 0x00, 0x00): {'name': 'Electric Grand Piano', 'program': 2},
    (0x02, 0x00, 0x01): {'name': 'Electric Piano 1', 'program': 4},
    (0x02, 0x00, 0x02): {'name': 'Electric Piano 2', 'program': 5},
    (0x02, 0x00, 0x03): {'name': 'Toy Piano', 'program': 8},
    (0x02, 0x00, 0x04): {'name': 'Organ', 'program': 16},
    (0x02, 0x00, 0x05): {'name': 'Vox Organ', 'program': 17},

    # Guitar/Mallet
    (0x00, 0x01, 0x00): {'name': 'Guitar 1', 'program': 24},
    (0x00, 0x01, 0x01): {'name': 'Guitar 2', 'program': 25},
    (0x00, 0x01, 0x02): {'name': 'Electric Guitar', 'program': 26},
    (0x00, 0x01, 0x03): {'name': 'Sitar 1', 'program': 104},
    (0x00, 0x01, 0x04): {'name': 'Sitar 2', 'program': 104},
    (0x00, 0x01, 0x05): {'name': 'Vibes', 'program': 11},
    (0x00, 0x01, 0x06): {'name': 'Bell', 'program': 13},
    (0x00, 0x01, 0x07): {'name': 'Tubular', 'program': 14},
    (0x00, 0x01, 0x08): {'name': 'BellRing', 'program': 13},
    (0x00, 0x01, 0x09): {'name': 'Karimba', 'program': 107},
    (0x00, 0x01, 0x0A): {'name': 'SynMallet', 'program': 112},
    (0x00, 0x01, 0x0B): {'name': 'DW-Vibe', 'program': 11},
    (0x00, 0x01, 0x0C): {'name': 'DW-Bell', 'program': 13},
    (0x01, 0x01, 0x00): {'name': 'G. Guitar', 'program': 24},
    (0x01, 0x01, 0x01): {'name': 'Fretless Guitar', 'program': 33},
    (0x01, 0x01, 0x02): {'name': 'HardPick', 'program': 29},
    (0x01, 0x01, 0x03): {'name': 'Electric Guitar', 'program': 26},
    (0x01, 0x01, 0x04): {'name': 'Muted Guitar', 'program': 28},
    (0x01, 0x01, 0x05): {'name': 'Distortion Guitar', 'program': 29},
    (0x01, 0x01, 0x06): {'name': 'Feedbacker (overdriven guitar)', 'program': 30},
    (0x01, 0x01, 0x07): {'name': 'Banjo', 'program': 106},
    (0x01, 0x01, 0x08): {'name': 'Harp', 'program': 46},
    (0x01, 0x01, 0x09): {'name': 'Marimba', 'program': 12},
    (0x01, 0x01, 0x0A): {'name': 'Vibe', 'program': 11},
    (0x01, 0x01, 0x0B): {'name': 'MusicBox', 'program': 10},
    (0x01, 0x01, 0x0C): {'name': 'Gamelan', 'program': 109},
    (0x01, 0x01, 0x0D): {'name': 'Digital Bell', 'program': 13},
    (0x01, 0x01, 0x0E): {'name': 'Metal Bell', 'program': 13},
    (0x01, 0x01, 0x0F): {'name': 'VS Bell', 'program': 13},
    (0x02, 0x01, 0x00): {'name': 'Chorus Guitar', 'program': 27},
    (0x02, 0x01, 0x01): {'name': 'Jazz Guitar', 'program': 26},
    (0x02, 0x01, 0x02): {'name': 'Distorted Guitar', 'program': 29},
    (0x02, 0x01, 0x03): {'name': 'Sitar', 'program': 104},
    (0x02, 0x01, 0x04): {'name': 'Shamisen', 'program': 108},
    (0x02, 0x01, 0x05): {'name': 'Koto', 'program': 105},
    (0x02, 0x01, 0x06): {'name': 'Glockenspiel', 'program': 9},
    (0x02, 0x01, 0x07): {'name': 'SteelDrum', 'program': 114},
    (0x02, 0x01, 0x08): {'name': 'BottlePop', 'program': 117},

    # Bass
    (0x00, 0x02, 0x00): {'name': 'Analog Bass', 'program': 32},
    (0x00, 0x02, 0x01): {'name': 'Pick Bass', 'program': 33},
    (0x00, 0x02, 0x02): {'name': 'Electric Bass', 'program': 33},
    (0x00, 0x02, 0x03): {'name': 'Fretless Bass', 'program': 34},
    (0x00, 0x02, 0x04): {'name': 'SynthBass 1', 'program': 38},
    (0x00, 0x02, 0x05): {'name': 'SynthBass 2', 'program': 39},
    (0x00, 0x02, 0x06): {'name': 'SynthBass 3', 'program': 40},
    (0x00, 0x02, 0x07): {'name': 'DW-Bass1', 'program': 32},
    (0x00, 0x02, 0x08): {'name': 'DW-Bass2', 'program': 33},
    (0x01, 0x02, 0x00): {'name': 'Analog Bass 1', 'program': 32},
    (0x01, 0x02, 0x01): {'name': 'Analog Bass 2', 'program': 32},
    (0x01, 0x02, 0x02): {'name': 'Fretless Bass', 'program': 34},
    (0x01, 0x02, 0x03): {'name': 'Electric Bass 1', 'program': 33},
    (0x01, 0x02, 0x04): {'name': 'Electric Bass 2', 'program': 33},
    (0x01, 0x02, 0x05): {'name': 'Electric Bass 3', 'program': 33},
    (0x01, 0x02, 0x06): {'name': 'Slap Bass', 'program': 35},
    (0x01, 0x02, 0x07): {'name': 'SynthBass 1', 'program': 38},
    (0x01, 0x02, 0x08): {'name': 'SynthBass 2', 'program': 39},
    (0x01, 0x02, 0x09): {'name': 'TechBass', 'program': 40},
    (0x01, 0x02, 0x0A): {'name': 'BowBowBass', 'program': 36},
    (0x01, 0x02, 0x0B): {'name': 'RezzzzBass', 'program': 41},
    (0x01, 0x02, 0x0C): {'name': 'Residrops', 'program': 42},
    (0x02, 0x02, 0x00): {'name': 'Electric Bass', 'program': 33},
    (0x02, 0x02, 0x01): {'name': 'Slap Bass', 'program': 35},
    (0x02, 0x02, 0x02): {'name': 'BoostSaw', 'program': 38},
    (0x02, 0x02, 0x03): {'name': 'ElectroBass', 'program': 39},
    (0x02, 0x02, 0x04): {'name': 'DarkBass', 'program': 40},
    (0x02, 0x02, 0x05): {'name': 'FilterBass', 'program': 41},
    (0x02, 0x02, 0x06): {'name': 'FatBass', 'program': 42},
    (0x02, 0x02, 0x07): {'name': 'SawRezBass', 'program': 38},
    (0x02, 0x02, 0x08): {'name': 'SquareRezBass', 'program': 39},
    (0x02, 0x02, 0x09): {'name': 'DiscoBass', 'program': 40},
    (0x02, 0x02, 0x0A): {'name': 'VPMBass1', 'program': 41},
    (0x02, 0x02, 0x0B): {'name': 'VPMBass2', 'program': 42},
    (0x02, 0x02, 0x0C): {'name': 'AttackBass', 'program': 38},
    (0x02, 0x02, 0x0D): {'name': 'AcidDistortionBass', 'program': 39},
    (0x02, 0x02, 0x0E): {'name': 'DetuneBass', 'program': 40},
    (0x02, 0x02, 0x0F): {'name': 'WobbleBass', 'program': 41},

    # Strings/Pad
    (0x00, 0x03, 0x00): {'name': 'Strings', 'program': 48},
    (0x00, 0x03, 0x01): {'name': 'Voices', 'program': 52},
    (0x00, 0x03, 0x02): {'name': 'Choir', 'program': 52},
    (0x01, 0x03, 0x00): {'name': 'Violin', 'program': 40},
    (0x01, 0x03, 0x01): {'name': 'Cello', 'program': 42},
    (0x01, 0x03, 0x02): {'name': 'Pizzicato', 'program': 44},
    (0x01, 0x03, 0x03): {'name': 'StringEnsemble', 'program': 48},
    (0x01, 0x03, 0x04): {'name': 'AnalogStrings', 'program': 50},
    (0x01, 0x03, 0x05): {'name': 'Choir', 'program': 52},
    (0x01, 0x03, 0x06): {'name': 'SoftChoir', 'program': 53},
    (0x01, 0x03, 0x07): {'name': 'Ahhs', 'program': 52},
    (0x01, 0x03, 0x08): {'name': 'AirVox', 'program': 53},
    (0x01, 0x03, 0x09): {'name': 'SynVox', 'program': 54},
    (0x02, 0x03, 0x00): {'name': 'String', 'program': 48},
    (0x02, 0x03, 0x01): {'name': 'StringsQuartet', 'program': 49},
    (0x02, 0x03, 0x02): {'name': 'TapeString', 'program': 50},
    (0x02, 0x03, 0x03): {'name': 'AahChoir', 'program': 52},
    (0x02, 0x03, 0x04): {'name': 'OohChoir', 'program': 53},
    (0x02, 0x03, 0x05): {'name': 'VocoderPad', 'program': 54},
    (0x02, 0x03, 0x06): {'name': 'AnalogStrings1', 'program': 50},
    (0x02, 0x03, 0x07): {'name': 'AnalogStrings2', 'program': 51},
    (0x02, 0x03, 0x08): {'name': 'DarkPad', 'program': 50},
    (0x02, 0x03, 0x09): {'name': 'NoisePad', 'program': 55},
    (0x02, 0x03, 0x0A): {'name': 'AnalogPad', 'program': 50},
    (0x02, 0x03, 0x0B): {'name': 'SquarePad', 'program': 51},
    (0x02, 0x03, 0x0C): {'name': 'Fifths Pad', 'program': 52},
    (0x02, 0x03, 0x0D): {'name': 'OctavePad', 'program': 53},

    # Brass/Reed
    (0x00, 0x04, 0x00): {'name': 'Flute', 'program': 73},
    (0x00, 0x04, 0x01): {'name': 'PanFlute', 'program': 75},
    (0x00, 0x04, 0x02): {'name': 'Bottles', 'program': 74},
    (0x00, 0x04, 0x03): {'name': 'TenorSax', 'program': 66},
    (0x00, 0x04, 0x04): {'name': 'Trumpet', 'program': 56},
    (0x00, 0x04, 0x05): {'name': 'Muted Trumpet', 'program': 58},
    (0x00, 0x04, 0x06): {'name': 'TubaFlugel', 'program': 57},
    (0x00, 0x04, 0x07): {'name': 'DoubleReed', 'program': 70},
    (0x00, 0x04, 0x08): {'name': 'Brass1', 'program': 60},
    (0x00, 0x04, 0x09): {'name': 'Brass2', 'program': 61},
    (0x01, 0x04, 0x00): {'name': 'Trumpet', 'program': 56},
    (0x01, 0x04, 0x01): {'name': 'Trombone', 'program': 57},
    (0x01, 0x04, 0x02): {'name': 'MutedTrombone', 'program': 58},
    (0x01, 0x04, 0x03): {'name': 'HardFlute', 'program': 73},
    (0x01, 0x04, 0x04): {'name': 'TinFlute', 'program': 74},
    (0x01, 0x04, 0x05): {'name': 'BassonOboe', 'program': 69},
    (0x01, 0x04, 0x06): {'name': 'Clarinet', 'program': 71},
    (0x01, 0x04, 0x07): {'name': 'SopranoSax', 'program': 64},
    (0x01, 0x04, 0x08): {'name': 'AltoSax', 'program': 65},
    (0x01, 0x04, 0x09): {'name': 'Baritone Sax', 'program': 67},
    (0x01, 0x04, 0x0A): {'name': 'Tuba/FrH', 'program': 59},
    (0x01, 0x04, 0x0B): {'name': 'Harmonica', 'program': 21},
    (0x01, 0x04, 0x0C): {'name': 'BrassEnsemble1', 'program': 60},
    (0x01, 0x04, 0x0D): {'name': 'BrassEnsemble2', 'program': 61},
    (0x02, 0x04, 0x00): {'name': 'Trumpet', 'program': 56},
    (0x02, 0x04, 0x01): {'name': 'TinWhistle', 'program': 74},
    (0x02, 0x04, 0x02): {'name': 'TapeFlute', 'program': 75},
    (0x02, 0x04, 0x03): {'name': 'Shakuhachi', 'program': 77},
    (0x02, 0x04, 0x04): {'name': 'AltoSax', 'program': 65},
    (0x02, 0x04, 0x05): {'name': 'TenorSax', 'program': 66},
    (0x02, 0x04, 0x06): {'name': 'Bagpipe', 'program': 109},
    (0x02, 0x04, 0x07): {'name': 'BrassEnsemble', 'program': 60},

    # Lead Synth
    (0x00, 0x05, 0x00): {'name': 'Wire', 'program': 80},
    (0x00, 0x05, 0x01): {'name': 'SawWave', 'program': 81},
    (0x00, 0x05, 0x02): {'name': 'SquareWave', 'program': 80},
    (0x00, 0x05, 0x03): {'name': '25% Pulse', 'program': 81},
    (0x00, 0x05, 0x04): {'name': '10% Pulse', 'program': 81},
    (0x00, 0x05, 0x05): {'name': 'DW-Triangle Wave', 'program': 82},
    (0x00, 0x05, 0x06): {'name': 'DW-Sinewave', 'program': 88},
    (0x00, 0x05, 0x07): {'name': 'VoiceWave', 'program': 85},
    (0x00, 0x05, 0x08): {'name': 'DW-Voice', 'program': 85},
    (0x01, 0x05, 0x00): {'name': 'MonoLead', 'program': 80},
    (0x01, 0x05, 0x01): {'name': 'MiniLead', 'program': 81},
    (0x01, 0x05, 0x02): {'name': 'VS 89', 'program': 88},
    (0x01, 0x05, 0x03): {'name': '4% Pulse', 'program': 81},
    (0x01, 0x05, 0x04): {'name': 'SynSine', 'program': 88},
    (0x01, 0x05, 0x05): {'name': 'Sine', 'program': 88},
    (0x02, 0x05, 0x00): {'name': 'SoftLead', 'program': 88},
    (0x02, 0x05, 0x01): {'name': 'UrbanLead', 'program': 85},
    (0x02, 0x05, 0x02): {'name': 'HiResoLead', 'program': 82},
    (0x02, 0x05, 0x03): {'name': 'MS20Lead', 'program': 83},
    (0x02, 0x05, 0x04): {'name': 'OctaveLead', 'program': 84},
    (0x02, 0x05, 0x05): {'name': 'DriveLead', 'program': 85},
    (0x02, 0x05, 0x06): {'name': 'RaveLead', 'program': 86},
    (0x02, 0x05, 0x07): {'name': 'DualSquare', 'program': 81},
    (0x02, 0x05, 0x08): {'name': 'SynWire1', 'program': 80},
    (0x02, 0x05, 0x09): {'name': 'SynWire2', 'program': 80},
    (0x02, 0x05, 0x0A): {'name': 'SyncLoop', 'program': 87},
    (0x02, 0x05, 0x0B): {'name': 'Fifths Sine', 'program': 88},
    (0x02, 0x05, 0x0C): {'name': 'Fifths Saw', 'program': 81},
    (0x02, 0x05, 0x0D): {'name': 'Fifths Square', 'program': 80},
    (0x02, 0x05, 0x0E): {'name': 'ShortArp', 'program': 89},

    # PolySynth
    (0x00, 0x06, 0x00): {'name': 'Universe', 'program': 88},
    (0x00, 0x06, 0x01): {'name': 'SoftHorn', 'program': 64},
    (0x00, 0x06, 0x02): {'name': 'SynBrass', 'program': 64},
    (0x00, 0x06, 0x03): {'name': 'FvWave', 'program': 89},
    (0x00, 0x06, 0x04): {'name': 'MvWave', 'program': 90},
    (0x00, 0x06, 0x05): {'name': 'PanWave', 'program': 91},
    (0x00, 0x06, 0x06): {'name': 'PingWave', 'program': 92},
    (0x00, 0x06, 0x07): {'name': 'Digital1 (like brass)', 'program': 64},
    (0x00, 0x06, 0x08): {'name': 'Digital2 (like steel guitar)', 'program': 27},
    (0x00, 0x06, 0x09): {'name': 'Digital3 (like violin)', 'program': 40},
    (0x00, 0x06, 0x0A): {'name': 'Digital4 (like guitar)', 'program': 24},
    (0x00, 0x06, 0x0B): {'name': 'Digital5 (like bell)', 'program': 13},
    (0x00, 0x06, 0x0C): {'name': 'Digital6 (like strings)', 'program': 48},
    (0x01, 0x06, 0x00): {'name': 'RawDeal', 'program': 88},
    (0x01, 0x06, 0x01): {'name': 'Detune', 'program': 89},
    (0x01, 0x06, 0x02): {'name': 'EtherBell', 'program': 13},
    (0x01, 0x06, 0x03): {'name': 'FreshAir', 'program': 90},
    (0x01, 0x06, 0x04): {'name': 'Ghostly', 'program': 91},
    (0x01, 0x06, 0x05): {'name': 'Ephemerals', 'program': 92},
    (0x01, 0x06, 0x06): {'name': 'AliaBass', 'program': 38},
    (0x01, 0x06, 0x07): {'name': 'UnderWater', 'program': 93},
    (0x01, 0x06, 0x08): {'name': 'Spectrum1', 'program': 94},
    (0x01, 0x06, 0x09): {'name': 'Spectrum2', 'program': 95},
    (0x01, 0x06, 0x0A): {'name': 'Spectrum3', 'program': 95},
    (0x02, 0x06, 0x00): {'name': 'DetuneStab', 'program': 89},
    (0x02, 0x06, 0x01): {'name': 'UnisonStab', 'program': 88},
    (0x02, 0x06, 0x02): {'name': '5thStab', 'program': 90},
    (0x02, 0x06, 0x03): {'name': 'PolyComp', 'program': 91},
    (0x02, 0x06, 0x04): {'name': 'Square Detune', 'program': 81},
    (0x02, 0x06, 0x05): {'name': 'VPM Brass', 'program': 64},
    (0x02, 0x06, 0x06): {'name': 'SynthHorn', 'program': 64},
    (0x02, 0x06, 0x07): {'name': 'DarkSynth', 'program': 92},
    (0x02, 0x06, 0x08): {'name': 'NoisyComp', 'program': 93},
    (0x02, 0x06, 0x09): {'name': 'RisingPad', 'program': 88},       # Pad 1 (New Age)
    (0x02, 0x06, 0x0A): {'name': 'TremoloSine', 'program': 89},    # Pad 2 (Warm)
    (0x02, 0x06, 0x0B): {'name': 'TrillPad', 'program': 90},        # Pad 3 (Polysynth)
    (0x02, 0x06, 0x0C): {'name': 'LPF Sweep', 'program': 91},       # Pad 4 (Choir)
    (0x02, 0x06, 0x0D): {'name': 'HPF Sweep', 'program': 92},       # Pad 5 (Bowed)
    (0x02, 0x06, 0x0E): {'name': 'WaveSweep', 'program': 93},       # Pad 6 (Metallic)
    (0x02, 0x06, 0x0F): {'name': 'Palawan', 'program': 107},        # Koto (Ethnic approximation)

    # SE/Other
    (0x00, 0x07, 0x00): {'name': 'KotoTrem', 'program': 105},       # Koto
    (0x00, 0x07, 0x01): {'name': 'BambooTrem', 'program': 75},      # Pan Flute
    (0x00, 0x07, 0x02): {'name': 'Rhythm', 'program': 0},           # Default to Piano (placeholder)
    (0x00, 0x07, 0x03): {'name': 'Lore', 'program': 95},            # Spectrum 2 (approximation)
    (0x00, 0x07, 0x04): {'name': 'FlexaTone', 'program': 117},      # Agogo
    (0x00, 0x07, 0x05): {'name': 'WindBells', 'program': 14},       # Tubular Bells
    (0x01, 0x07, 0x00): {'name': 'Stadium', 'program': 48},         # String Ensemble 1
    (0x01, 0x07, 0x01): {'name': 'Thing', 'program': 95},           # Spectrum 2 (approximation)
    (0x01, 0x07, 0x02): {'name': 'TriangleRoll', 'program': 81},    # Square Wave
    (0x01, 0x07, 0x03): {'name': 'Clicker', 'program': 115},        # Steel Drums
    (0x01, 0x07, 0x04): {'name': 'Crickets1', 'program': 121},      # Bird Tweet (Sound FX)
    (0x01, 0x07, 0x05): {'name': 'Crickets2', 'program': 121},      # Bird Tweet (Sound FX)
    (0x01, 0x07, 0x06): {'name': 'MagicBell', 'program': 13},       # Celesta
    (0x01, 0x07, 0x07): {'name': 'TronUp', 'program': 94},          # Echo Drops (Sound FX)
    (0x01, 0x07, 0x08): {'name': 'Tooter', 'program': 80},          # Lead 1 (Square)
    (0x01, 0x07, 0x09): {'name': 'FluteFX', 'program': 73},         # Flute
    (0x01, 0x07, 0x0A): {'name': 'Flutter', 'program': 74},         # Recorder
    (0x02, 0x07, 0x00): {'name': 'Applause', 'program': 126},       # Gunshot (Sound FX)
    (0x02, 0x07, 0x01): {'name': 'HeartBeat', 'program': 118},      # Telephone Ring (Sound FX)
    (0x02, 0x07, 0x02): {'name': 'GunShot', 'program': 126},        # Gunshot (Sound FX)
    (0x02, 0x07, 0x03): {'name': 'CarSFX', 'program': 125},         # Car Horn (Sound FX)
    (0x02, 0x07, 0x04): {'name': 'Stream', 'program': 122},         # Telephone Ring (approximation)
    (0x02, 0x07, 0x05): {'name': 'Forest', 'program': 124},         # Bird Tweet (approximation)
    (0x02, 0x07, 0x06): {'name': 'ShakerLoop', 'program': 111},     # Castanets
    (0x02, 0x07, 0x07): {'name': 'Noise', 'program': 120},          # Bank Select (Sound FX)
    (0x02, 0x07, 0x08): {'name': '8bitNoise', 'program': 83},       # Lead 3 (Calliope)
    (0x02, 0x07, 0x09): {'name': 'NoiseShot', 'program': 120},      # Bank Select (Sound FX)
    (0x02, 0x07, 0x0A): {'name': 'NoiseSplit', 'program': 120},     # Bank Select (Sound FX)
    (0x02, 0x07, 0x0B): {'name': 'SweepSplit', 'program': 123},     # Helicopter (Sound FX)
    (0x02, 0x07, 0x0C): {'name': 'SirenUp', 'program': 123},        # Helicopter (approximation)
    (0x02, 0x07, 0x0D): {'name': 'SirenDown', 'program': 123},      # Helicopter (approximation)
    (0x02, 0x07, 0x0E): {'name': 'Modulation', 'program': 94},      # Echo Drops (Sound FX)
    (0x02, 0x07, 0x0F): {'name': 'Signal', 'program': 127},         # Undefined (Sound FX)

    # Hit/Chord
    (0x00, 0x08, 0x00): {'name': 'Pole', 'program': 56},            # Trumpet
    (0x00, 0x08, 0x01): {'name': 'Pop', 'program': 58},             # Muted Trumpet
    (0x00, 0x08, 0x02): {'name': 'MetalHit', 'program': 14},        # Tubular Bells
    (0x01, 0x08, 0x00): {'name': 'OrchestraHit', 'program': 48},    # String Ensemble 1
    (0x01, 0x08, 0x01): {'name': 'VibeHit', 'program': 11},         # Vibes
    (0x01, 0x08, 0x02): {'name': 'Gong', 'program': 114},           # Steel Drums
    (0x01, 0x08, 0x03): {'name': 'Timpani', 'program': 47},         # Timpani
    (0x01, 0x08, 0x04): {'name': 'OrchestraBell', 'program': 13},   # Celesta
    (0x01, 0x08, 0x05): {'name': 'SynClaves', 'program': 75},       # Pan Flute
    (0x01, 0x08, 0x06): {'name': 'SynTom1', 'program': 11},         # Vibes
    (0x01, 0x08, 0x07): {'name': 'SynTom2', 'program': 11},         # Vibes
    (0x01, 0x08, 0x08): {'name': 'Zap1', 'program': 85},           # Lead 5 (Charang)
    (0x01, 0x08, 0x09): {'name': 'Zap2', 'program': 85},           # Lead 5 (Charang)
    (0x01, 0x08, 0x0A): {'name': 'Industry1', 'program': 125},      # Car Horn (Sound FX)
    (0x01, 0x08, 0x0B): {'name': 'Industry2', 'program': 125},      # Car Horn (Sound FX)
    (0x01, 0x08, 0x0C): {'name': 'ReverseThing', 'program': 94},    # Echo Drops (Sound FX)
    (0x02, 0x08, 0x00): {'name': 'M1PfChord', 'program': 0},        # Piano
    (0x02, 0x08, 0x01): {'name': 'EPChord', 'program': 4},          # Electric Piano 1
    (0x02, 0x08, 0x02): {'name': 'min7Organ', 'program': 16},       # Organ 1
    (0x02, 0x08, 0x03): {'name': 'GtrChord1', 'program': 24},       # Acoustic Guitar (nylon)
    (0x02, 0x08, 0x04): {'name': 'GtrChord2', 'program': 25},       # Acoustic Guitar (steel)
    (0x02, 0x08, 0x05): {'name': 'PowerChord', 'program': 29},      # Distortion Guitar
    (0x02, 0x08, 0x06): {'name': 'StrChord', 'program': 48},        # String Ensemble 1
    (0x02, 0x08, 0x07): {'name': 'Maj7Pad', 'program': 88},         # Pad 1 (New Age)
    (0x02, 0x08, 0x08): {'name': 'SynChord1', 'program': 88},       # Pad 1 (New Age)
    (0x02, 0x08, 0x09): {'name': 'SynChord2', 'program': 89},       # Pad 2 (Warm)
    (0x02, 0x08, 0x0A): {'name': 'SynChord3', 'program': 90},       # Pad 3 (Polysynth)
    (0x02, 0x08, 0x0B): {'name': 'SynChord4', 'program': 91},       # Pad 4 (Choir)
    (0x02, 0x08, 0x0C): {'name': 'Glissando', 'program': 81},       # Square Wave
    (0x02, 0x08, 0x0D): {'name': 'OrchestraHit', 'program': 48},    # String Ensemble 1
    (0x02, 0x08, 0x0E): {'name': 'DanceHits', 'program': 118},      # Telephone Ring (approximation)
}

# Default drum map (M1 DrumKit1)
DRUM_MAP = {
    (0x00, 0x09, 0x00): {  # M1 DrumKit1
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 40, 0x40: 42, 0x41: 46,
        0x42: 45, 0x43: 48, 0x44: 50, 0x45: 56, 0x46: 49, 0x47: 51
    },
    (0x00, 0x09, 0x01): {  # M1 DrumKit2
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 40, 0x40: 42, 0x41: 46,
        0x42: 45, 0x43: 50, 0x44: 60, 0x45: 61, 0x46: 49, 0x47: 51
    },
    (0x00, 0x09, 0x02): {  # M1 DrumKit3
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 39, 0x40: 42, 0x41: 46,
        0x42: 45, 0x43: 50, 0x44: 70, 0x45: 54, 0x46: 55, 0x47: 59
    },
    (0x00, 0x09, 0x03): {  # M1 PercKit
        0x3C: 60, 0x3D: 61, 0x3E: 65, 0x3F: 66, 0x40: 67, 0x41: 69,
        0x42: 73, 0x43: 74, 0x44: 78, 0x45: 80, 0x46: 81, 0x47: 79
    },
    (0x00, 0x09, 0x04): {  # M1 NoiseKit
        0x3C: 58, 0x3D: 72, 0x3E: 71, 0x3F: 57, 0x40: 58, 0x41: 68,
        0x42: 75, 0x43: 77, 0x44: 63, 0x45: 86, 0x46: 87, 0x47: 85
    },
    (0x01, 0x09, 0x00): {  # 01/W TotalKit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 40, 0x40: 42, 0x41: 46,
        0x42: 45, 0x43: 50, 0x44: 60, 0x45: 61, 0x46: 49, 0x47: 51
    },
    (0x01, 0x09, 0x01): {  # 01/W RockKit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 40, 0x40: 42, 0x41: 46,
        0x42: 45, 0x43: 47, 0x44: 50, 0x45: 56, 0x46: 49, 0x47: 51
    },
    (0x01, 0x09, 0x02): {  # 01/W DanceKit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 40, 0x40: 42, 0x41: 46,
        0x42: 45, 0x43: 47, 0x44: 70, 0x45: 49, 0x46: 53, 0x47: 41
    },
    (0x01, 0x09, 0x03): {  # 01/W AnalogKit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 39, 0x40: 42, 0x41: 46,
        0x42: 45, 0x43: 50, 0x44: 75, 0x45: 84, 0x46: 85, 0x47: 86
    },
    (0x01, 0x09, 0x04): {  # 01/W HipHopKit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 40, 0x40: 42, 0x41: 43,
        0x42: 44, 0x43: 45, 0x44: 46, 0x45: 35, 0x46: 52, 0x47: 82
    },
    (0x01, 0x09, 0x05): {  # 01/W R&BKit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 39, 0x40: 42, 0x41: 46,
        0x42: 71, 0x43: 54, 0x44: 76, 0x45: 77, 0x46: 83, 0x47: 47
    },
    (0x01, 0x09, 0x06): {  # 01/W BD&SDKit1
        0x3C: 36, 0x3D: 37, 0x3E: 36, 0x3F: 37, 0x40: 38, 0x41: 40,
        0x42: 38, 0x43: 40, 0x44: 38, 0x45: 40, 0x46: 40, 0x47: 40
    },
    (0x01, 0x09, 0x07): {  # 01/W BD&SDKit2
        0x3C: 36, 0x3D: 37, 0x3E: 36, 0x3F: 86, 0x40: 39, 0x41: 38,
        0x42: 40, 0x43: 38, 0x44: 40, 0x45: 38, 0x46: 40, 0x47: 41
    },
    (0x01, 0x09, 0x08): {  # 01/W TomKit
        0x3C: 45, 0x3D: 47, 0x3E: 48, 0x3F: 50, 0x40: 41, 0x41: 43,
        0x42: 44, 0x43: 46, 0x44: 45, 0x45: 47, 0x46: 48, 0x47: 50
    },
    (0x01, 0x09, 0x09): {  # 01/W CymbalKit
        0x3C: 42, 0x3D: 42, 0x3E: 44, 0x3F: 46, 0x40: 42, 0x41: 46,
        0x42: 49, 0x43: 55, 0x44: 51, 0x45: 59, 0x46: 49, 0x47: 52
    },
    (0x01, 0x09, 0x0A): {  # 01/W PercKit1
        0x3C: 60, 0x3D: 61, 0x3E: 62, 0x3F: 63, 0x40: 70, 0x41: 71,
        0x42: 64, 0x43: 65, 0x44: 63, 0x45: 55, 0x46: 81, 0x47: 80
    },
    (0x01, 0x09, 0x0B): {  # 01/W PercKit2
        0x3C: 65, 0x3D: 66, 0x3E: 67, 0x3F: 56, 0x40: 68, 0x41: 69,
        0x42: 72, 0x43: 73, 0x44: 74, 0x45: 75, 0x46: 79, 0x47: 80
    },
    (0x01, 0x09, 0x0C): {  # 01/W SEKit
        0x3C: 52, 0x3D: 82, 0x3E: 73, 0x3F: 87, 0x40: 70, 0x41: 71,
        0x42: 75, 0x43: 85, 0x44: 86, 0x45: 84, 0x46: 88, 0x47: 83
    },
    (0x02, 0x09, 0x00): {  # EX DDD1Kit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 40, 0x40: 42, 0x41: 46,
        0x42: 45, 0x43: 48, 0x44: 56, 0x45: 49, 0x46: 51, 0x47: 51
    },
    (0x02, 0x09, 0x01): {  # EX DDD110Kit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 39, 0x40: 42, 0x41: 46,
        0x42: 45, 0x43: 50, 0x44: 60, 0x45: 61, 0x46: 49, 0x47: 54
    },
    (0x02, 0x09, 0x02): {  # EX S3Kit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 40, 0x40: 42, 0x41: 46,
        0x42: 45, 0x43: 48, 0x44: 37, 0x45: 49, 0x46: 51, 0x47: 51
    },
    (0x02, 0x09, 0x03): {  # EX LynKit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 39, 0x40: 42, 0x41: 46,
        0x42: 45, 0x43: 50, 0x44: 60, 0x45: 61, 0x46: 49, 0x47: 51
    },
    (0x02, 0x09, 0x04): {  # EX StandardKit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 40, 0x40: 42, 0x41: 46,
        0x42: 45, 0x43: 48, 0x44: 39, 0x45: 49, 0x46: 51, 0x47: 51
    },
    (0x02, 0x09, 0x05): {  # EX HouseKit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 40, 0x40: 42, 0x41: 46,
        0x42: 60, 0x43: 61, 0x44: 62, 0x45: 39, 0x46: 49, 0x47: 41
    },
    (0x02, 0x09, 0x06): {  # EX StandardKit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 40, 0x40: 42, 0x41: 46,
        0x42: 45, 0x43: 48, 0x44: 39, 0x45: 49, 0x46: 51, 0x47: 41
    },
    (0x02, 0x09, 0x07): {  # EX MinimalKit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 40, 0x40: 42, 0x41: 46,
        0x42: 70, 0x43: 71, 0x44: 73, 0x45: 39, 0x46: 84, 0x47: 85
    },
    (0x02, 0x09, 0x08): {  # EX TronicaKit
        0x3C: 36, 0x3D: 37, 0x3E: 84, 0x3F: 85, 0x40: 86, 0x41: 87,
        0x42: 73, 0x43: 74, 0x44: 75, 0x45: 88, 0x46: 89, 0x47: 90
    },
    (0x02, 0x09, 0x09): {  # EX D&BKit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 40, 0x40: 42, 0x41: 46,
        0x42: 36, 0x43: 38, 0x44: 73, 0x45: 54, 0x46: 51, 0x47: 51
    },
    (0x02, 0x09, 0x0A): {  # EX R&BKit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 40, 0x40: 42, 0x41: 46,
        0x42: 45, 0x43: 50, 0x44: 39, 0x45: 39, 0x46: 49, 0x47: 81
    },
    (0x02, 0x09, 0x0B): {  # EX HipHopKit
        0x3C: 36, 0x3D: 37, 0x3E: 38, 0x3F: 40, 0x40: 42, 0x41: 46,
        0x42: 45, 0x43: 50, 0x44: 56, 0x45: 39, 0x46: 70, 0x47: 51
    },
    (0x02, 0x09, 0x0C): {  # EX EthnicKit
        0x3C: 66, 0x3D: 68, 0x3E: 67, 0x3F: 69, 0x40: 70, 0x41: 71,
        0x42: 72, 0x43: 73, 0x44: 74, 0x45: 75, 0x46: 76, 0x47: 77
    },
    (0x02, 0x09, 0x0D): {  # EX SEKit
        0x3C: 49, 0x3D: 84, 0x3E: 82, 0x3F: 87, 0x40: 68, 0x41: 70,
        0x42: 73, 0x43: 88, 0x44: 89, 0x45: 83, 0x46: 52, 0x47: 47
    },
    (0x02, 0x09, 0x0E): {  # EX CartoonKit
        0x3C: 78, 0x3D: 78, 0x3E: 72, 0x3F: 79, 0x40: 71, 0x41: 80,
        0x42: 74, 0x43: 75, 0x44: 76, 0x45: 77, 0x46: 78, 0x47: 79
    },
    (0x02, 0x09, 0x0F): {  # EX GuitarElement
        0x3C: 89, 0x3D: 90, 0x3E: 91, 0x3F: 92, 0x40: 93, 0x41: 94,
        0x42: 95, 0x43: 96, 0x44: 97, 0x45: 98, 0x46: 99, 0x47: 100
    }
}

def sanitize_filename(name):
    cleaned = re.sub(r'[^\x20-\x7E]', '', name)
    cleaned = re.sub(r'[\\/*?:"<>|]', '', cleaned)
    return cleaned.strip() or "Untitled"

def read_binary_file(filename):
    with open(filename, 'rb') as f:
        return f.read()

def parse_song_list(data):
    header = data[4:8]
    if header != b'M01W':
        raise ValueError("Invalid header, expected M01W")
    
    max_songs = 10
    song_entries = []
    current_offset = 13
    
    for original_idx in range(max_songs):
        if current_offset + 40 > len(data):
            break
            
        title = data[current_offset:current_offset+8]
        length_offset = current_offset + 27
        length = struct.unpack('<I', data[length_offset:length_offset+4])[0]
        song_id_bytes = data[length_offset-4:length_offset]
        
        song_entries.append({
            'original_idx': original_idx,
            'title': title,
            'length': length,
            'song_id_bytes': song_id_bytes,
            'valid': length > 0
        })
        current_offset += 40
    
    return song_entries

def validate_and_process(song_data):
    if len(song_data) < MARKER_OFFSET + 4:
        return None
    if song_data[MARKER_OFFSET:MARKER_OFFSET+4] != SONG_MARKER:
        return None
    
    modified = bytearray(song_data)
    if len(modified) >= 5:
        modified[4] = 0x05
    
    insert_pos = MARKER_OFFSET
    modified = modified[:insert_pos] + INSERT_DATA + modified[insert_pos:]
    
    checksum = sum(modified[4:]) & 0xFFFFFFFF
    return struct.pack('<I', checksum) + modified[4:]

def process_songs(data, song_entries):
    os.makedirs(ORIG_DIR, exist_ok=True)
    os.makedirs(NEW_DIR, exist_ok=True)
    
    valid_entries = [entry for entry in song_entries if entry['valid']]
    list_file_data = generate_list_file(valid_entries)
    with open(os.path.join(NEW_DIR, "M01Dn_00000000"), 'wb') as f:
        f.write(list_file_data)
    
    valid_count = 0

    for entry in song_entries:
        if not entry['valid']:
            continue
        
        original_idx = entry['original_idx']
        title_bytes = entry['title']
        length = entry['length']
        
        current_start = FIRST_SONG_OFFSET + (original_idx * SONG_SPACING)
        
        if current_start + length > len(data):
            print(f"Song {original_idx+1} [0x{current_start:X}]: Exceeds file size, skipping")
            continue
            
        marker_pos = current_start + MARKER_OFFSET
        if marker_pos + 4 > len(data):
            print(f"Song {original_idx+1} [0x{current_start:X}]: Marker out of bounds, skipping")
            continue
        if data[marker_pos:marker_pos+4] != SONG_MARKER:
            print(f"Song {original_idx+1} [0x{current_start:X}]: Missing marker, skipping")
            continue

        song_data = data[current_start:current_start+length]
        processed = validate_and_process(song_data)
        
        if not processed:
            print(f"Song {original_idx+1} [0x{current_start:X}]: Failed validation, skipping")
            continue

        try:
            raw_title = title_bytes.decode('ascii', errors='replace').rstrip('\x00')
        except UnicodeDecodeError:
            raw_title = f"Song_{original_idx+1}"
        
        orig_filename = os.path.join(ORIG_DIR, f"{sanitize_filename(raw_title)}.m01")
        song_id_int = 0x00100000 + original_idx
        new_filename = f"M01Dn_{song_id_int:08X}"
        
        with open(orig_filename, 'wb') as f:
            f.write(processed)
        with open(os.path.join(NEW_DIR, new_filename), 'wb') as f:
            f.write(processed)
        
        valid_count += 1
        print(f"Extracted: Song {original_idx+1} at 0x{current_start:X} ({raw_title})")

    return valid_count

def generate_list_file(valid_entries):
    list_data = bytearray()
    list_data += bytes.fromhex("200100004D30315707")
    list_data += bytes(0xB)
    list_data += b'\x0A'
    list_data += bytes(0x24)
    list_data += b'\x0A'
    list_data += bytes(0x13)
    
    for original_idx in range(10):
        entry = next((e for e in valid_entries if e['original_idx'] == original_idx), None)
        if entry:
            title = entry['title']
            length = entry['length']
            new_length = length + 0xC
        else:
            title = b'\x00' * 9
            new_length = 0
        
        generated_id = 0x00100000 + original_idx
        id_bytes = struct.pack('<I', generated_id)
        
        entry_data = bytearray()
        entry_data += title.ljust(9, b'\x00')
        entry_data += bytes(15)
        entry_data += id_bytes
        entry_data += struct.pack('<I', new_length)
        entry_data += bytes(8)
        list_data += entry_data
    
    list_data += bytes(0x200 - len(list_data))
    return list_data

def convert_to_midi(input_file, output_file):
    # Read input file
    with open(input_file, 'rb') as f:
        data = f.read()
    
    # Global settings
    global_tempo = data[0x212] if 0x212 < len(data) and data[0x212] > 0 else 120
    master_steps = data[0x215] if 0x215 < len(data) and data[0x215] > 0 else 16
    
    # Channel configuration
    CHANNEL_OFFSETS = [0x08, 0x40, 0x78, 0xB0, 0xE8, 0x120, 0x158, 0x190]
    
    pan_map = {
        0xFB: 0, 0xFC: 13, 0xFD: 25, 0xFE: 38,
        0xFF: 51, 0x00: 64, 0x01: 77, 0x02: 89,
        0x03: 102, 0x04: 115, 0x05: 127
    }
    
    channels = []
    used_instruments = set()
    
    for ch_num, offset in enumerate(CHANNEL_OFFSETS):
        if offset + 9 >= len(data):
            bank = 0x00
            inst_type = 0x00
            inst_id = 0x00
            vol = 0x7F
            pan = 0x00
            attack = 0x00
            release = 0x00
        else:
            bank = data[offset]
            inst_type = data[offset + 1]
            inst_id = data[offset + 2]
            vol = data[offset + 7]
            pan = data[offset + 8]
            attack = data[offset + 5]
            release = data[offset + 6]
        
        is_drum = inst_type == 0x09
        key = (bank, inst_type, inst_id)
        instr_info = INSTRUMENT_MAP.get(key, {'name': 'Unknown', 'program': 0})
        name = instr_info['name']
        program = instr_info['program']
        
        midi_chan = 9 if is_drum else ch_num
        if not is_drum:
            used_instruments.add((name, program))
        
        channels.append({
            'name': name,
            'type': inst_type,
            'midi_chan': midi_chan,
            'program': program,
            'vol': min(vol, 0x7F),
            'pan': pan_map.get(pan, 64),
            'attack': attack,
            'release': release,
            'bank': bank if is_drum else None,
            'inst_id': inst_id if is_drum else None
        })
    
    # Pattern processing
    pattern_db = defaultdict(list)
    tempo_map = {}
    
    # Build tempo map
    for pattern_idx in range(99):
        offset = 0x21C + pattern_idx * 8
        if offset + 3 < len(data):
            tempo = data[offset] or global_tempo
            steps = data[offset+2] or master_steps
            tempo_map[pattern_idx] = {
                'tempo': max(tempo, 1),
                'steps': max(steps, 1),
                'duration': steps * 120
            }
    
    # Process patterns
    pos = 0x538
    processed_patterns = set()
    
    while pos < len(data):
        if pos + 4 > len(data):
            break
        pattern_idx = data[pos]
        channel_idx = data[pos+1]
        num_notes = data[pos+2]
        pos += 4
        
        if pattern_idx >= 99 or channel_idx >= 8:
            pos += num_notes * 4 + 4
            continue
        
        processed_patterns.add(pattern_idx)
        pattern_info = tempo_map.get(pattern_idx, {
            'tempo': global_tempo,
            'steps': master_steps,
            'duration': master_steps * 120
        })
        channel_info = channels[channel_idx]
        is_drum = channel_info['type'] == 0x09
        
        for _ in range(num_notes):
            if pos + 4 > len(data):
                break
            length, velocity, note_value, pos_steps = data[pos:pos+4]
            pos += 4
            
            if any([length == 0, velocity == 0, pos_steps >= pattern_info['steps'],
                   note_value < 0x8C, note_value > 0xF0]):
                continue
            
            std_midi_note = (note_value - 0x8C) + 12
            
            if is_drum:
                key = (channel_info['bank'], 0x09, channel_info['inst_id'])
                mapping = DRUM_MAP.get(key, None)
                if mapping and std_midi_note in mapping:
                    gm_note = mapping[std_midi_note]
                else:
                    continue
            else:
                gm_note = std_midi_note
                if gm_note < 0 or gm_note > 127:
                    continue
            
            max_duration = (pattern_info['steps'] - pos_steps) * 120
            note_duration = max(min(length * 30, max_duration), 10)
            note_start = pos_steps * 120
            
            pattern_db[pattern_idx].append({
                'channel': channel_idx,
                'start': note_start,
                'duration': note_duration,
                'pitch': gm_note,
                'velocity': max(8, int((velocity / 0xF) * 127))
            })
        
        pos += 4
    
    # MIDI Generation
    midi = MIDIFile(
        numTracks=8,
        deinterleave=False,
        removeDuplicates=True,
        adjust_origin=False,
        file_format=1,
        ticks_per_quarternote=480
    )
    
    # Initialize tracks
    for track in range(8):
        if track < len(channels):
            chan = channels[track]
            midi.addTrackName(track, 0, f"{chan['name']} (Ch{track+1})")
            midi.addProgramChange(track, chan['midi_chan'], 0, chan['program'])
            midi.addControllerEvent(track, chan['midi_chan'], 0, 7, chan['vol'])
            midi.addControllerEvent(track, chan['midi_chan'], 0, 10, chan['pan'])
            
            # Add attack and release controllers
            attack_value = int((chan['attack'] / 0x0F) * 127)
            release_value = int((chan['release'] / 0x0F) * 127)
            midi.addControllerEvent(track, chan['midi_chan'], 0, 73, attack_value)
            midi.addControllerEvent(track, chan['midi_chan'], 0, 72, release_value)
        
        if track == 0:
            midi.addTempo(track, 0, global_tempo)
    
    # Process events
    all_events = []
    current_tempo = global_tempo
    absolute_time = 0
    
    for pattern_idx in sorted(pattern_db.keys()):
        pattern_info = tempo_map.get(pattern_idx, {
            'tempo': current_tempo,
            'duration': master_steps * 120
        })
        pattern_tempo = pattern_info['tempo']
        pattern_duration = pattern_info['duration']
        
        if pattern_tempo != current_tempo:
            all_events.append({
                'type': 'tempo',
                'time': absolute_time,
                'value': pattern_tempo
            })
            current_tempo = pattern_tempo
        
        for note in pattern_db[pattern_idx]:
            all_events.append({
                'type': 'note',
                'track': note['channel'],
                'channel': channels[note['channel']]['midi_chan'],
                'time': absolute_time + note['start'],
                'duration': note['duration'],
                'pitch': note['pitch'],
                'velocity': note['velocity']
            })
        
        absolute_time += pattern_duration
    
    all_events.sort(key=lambda x: x['time'])
    
    for event in all_events:
        if event['type'] == 'tempo':
            midi.addTempo(0, event['time']/480, event['value'])
        else:
            if event['duration'] > 0 and event['time'] >= 0:
                midi.addNote(
                    event['track'],
                    event['channel'],
                    event['pitch'],
                    event['time']/480,
                    event['duration']/480,
                    event['velocity']
                )
    
    # Write MIDI file
    with open(output_file, 'wb') as f:
        midi.writeFile(f)
    print(f"MIDI file written to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Process Korg M01 files.')
    parser.add_argument('input', help='Input file (.sav or .m01)')
    parser.add_argument('-o', '--output', help='Output file or directory')
    
    args = parser.parse_args()
    
    # Check if input is .bin (extract and convert) or .m01 (convert)
    if args.input.endswith('.sav'):
        # Extract songs first
        data = read_binary_file(args.input)
        songs = parse_song_list(data)
        valid_count = process_songs(data, songs)
        print(f"Extracted {valid_count} songs")
        
        # Determine output directory
        output_dir = args.output if args.output else 'midi_output'
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert all .m01 files in ORIG_DIR and NEW_DIR
        for dir_name in [ORIG_DIR, NEW_DIR]:
            for root, dirs, files in os.walk(dir_name):
                for file in files:
                    if file.endswith('.m01'):
                        input_path = os.path.join(root, file)
                        output_path = os.path.join(output_dir, os.path.splitext(file)[0] + '.mid')
                        convert_to_midi(input_path, output_path)
        print(f"MIDI files saved to {output_dir}")
    else:
        # Single file conversion
        if not args.output:
            print("Output file must be specified for single file conversion")
            return
        convert_to_midi(args.input, args.output)

   
import tkinter as tk
from tkinter import filedialog, messagebox


import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import shutil

def run_gui():
    def select_input_file():
        file_path = filedialog.askopenfilename(filetypes=[("M01/SAV files", "*.m01 *.sav")])
        if file_path:
            input_entry.delete(0, tk.END)
            input_entry.insert(0, file_path)
            if file_path.lower().endswith(".sav"):
                load_sav_songs(file_path)
            else:
                song_listbox.delete(0, tk.END)

    def load_sav_songs(filepath):
        song_listbox.delete(0, tk.END)
        try:
            data = read_binary_file(filepath)
            songs = parse_song_list(data)
            valid_songs.clear()
            for entry in songs:
                if entry["valid"]:
                    try:
                        title = entry["title"].decode("ascii", errors="replace").rstrip("\x00")
                    except:
                        title = f"Song_{entry['original_idx'] + 1}"
                    song_listbox.insert(tk.END, f"{entry['original_idx']+1:02d}: {title}")
                    valid_songs.append(entry)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read .sav file:\n{e}")

    def select_output_folder():
        folder = filedialog.askdirectory()
        if folder:
            output_entry.delete(0, tk.END)
            output_entry.insert(0, folder)

    def convert():
        input_file = input_entry.get()
        output_dir = output_entry.get()
        if not input_file:
            messagebox.showwarning("Missing Input", "Please select a .m01 or .sav file.")
            return
        if not output_dir:
            messagebox.showwarning("Missing Output", "Please select an output folder.")
            return

        try:
            os.makedirs(output_dir, exist_ok=True)

            if input_file.lower().endswith(".m01"):
                output_file = filedialog.asksaveasfilename(defaultextension=".mid", filetypes=[("MIDI files", "*.mid")])
                if not output_file:
                    return
                convert_to_midi(input_file, output_file)
                messagebox.showinfo("Success", f"Converted to MIDI:\n{output_file}")

            elif input_file.lower().endswith(".sav"):
                data = read_binary_file(input_file)
                selected_indices = song_listbox.curselection()
                if not selected_indices:
                    messagebox.showwarning("No Selection", "Select at least one song to extract.")
                    return

                extracted = 0
                for idx in selected_indices:
                    entry = valid_songs[idx]
                    original_idx = entry["original_idx"]
                    length = entry["length"]
                    title_bytes = entry["title"]

                    current_start = FIRST_SONG_OFFSET + (original_idx * SONG_SPACING)
                    if current_start + length > len(data):
                        continue
                    song_data = data[current_start:current_start + length]
                    processed = validate_and_process(song_data)
                    if not processed:
                        continue

                    try:
                        raw_title = title_bytes.decode('ascii', errors='replace').rstrip('\x00')
                    except:
                        raw_title = f"Song_{original_idx + 1}"

                    clean_name = sanitize_filename(raw_title)
                    m01_path = os.path.join(output_dir, clean_name + ".m01")
                    with open(m01_path, "wb") as f:
                        f.write(processed)
                    extracted += 1

                    if midi_var.get():
                        midi_path = os.path.join(output_dir, clean_name + ".mid")
                        convert_to_midi(m01_path, midi_path)

                messagebox.showinfo("Done", f"Extracted {extracted} song(s) to:\n{output_dir}")

            else:
                messagebox.showerror("Unsupported", "Unsupported file type. Use .m01 or .sav.")
        except Exception as e:
            messagebox.showerror("Error", f"Operation failed:\n{e}")

    # GUI layout
    root = tk.Tk()
    root.title("Korg M01 to MIDI / Extractor")

    tk.Label(root, text="Input .m01 or .sav File:").pack(anchor="w", padx=10, pady=(10, 0))
    input_frame = tk.Frame(root)
    input_frame.pack(fill=tk.X, padx=10)
    input_entry = tk.Entry(input_frame, width=50)
    input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    tk.Button(input_frame, text="Browse", command=select_input_file).pack(side=tk.RIGHT)

    tk.Label(root, text="Output Folder:").pack(anchor="w", padx=10, pady=(10, 0))
    output_frame = tk.Frame(root)
    output_frame.pack(fill=tk.X, padx=10)
    output_entry = tk.Entry(output_frame, width=50)
    output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    tk.Button(output_frame, text="Browse", command=select_output_folder).pack(side=tk.RIGHT)

    song_frame = tk.LabelFrame(root, text="Available Songs (from .sav)")
    song_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
    song_listbox = tk.Listbox(song_frame, selectmode=tk.MULTIPLE, height=8)
    song_listbox.pack(fill=tk.BOTH, expand=True)

    midi_var = tk.IntVar()
    midi_check = tk.Checkbutton(root, text="Also convert extracted songs to MIDI", variable=midi_var)
    midi_check.pack(pady=(5, 0))

    tk.Button(root, text="Process", command=convert).pack(pady=10)

    valid_songs = []

    root.mainloop()

def main_cli(input_file, output_file):
    try:
        convert_to_midi(input_file, output_file)
        print(f"Converted to MIDI: {output_file}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys

    # Check for exactly two arguments (excluding script name)
    if len(sys.argv) == 3 and sys.argv[1].lower().endswith(".m01") and sys.argv[2].lower().endswith(".mid"):
        main_cli(sys.argv[1], sys.argv[2])
    else:
        run_gui()



