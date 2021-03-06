from lib.audiohandle import divide, detect_peaks, generate_point_mesh, return_position, create_buffer, find_clips
from lib.database import insert_into_fingerprints, search_for_song_hash, insert_into_songs
from lib.hashtree import generate_tree, merge_trees, extract_values_from_tree
from lib.filehandle import walk_paths, open_audio, hash_file
from lib.constants import check_for_settings, DEFAULTS
from pydub.exceptions import CouldntDecodeError
from lib.fingerprint import hash_frequencies
from pathlib import Path
import matplotlib.mlab as mlab
import numpy as np
import logging
import sqlite3

conn = sqlite3.connect("fingerprint_database.db")

if not check_for_settings(conn, DEFAULTS):
    print("Database was created on other settings, next runs may not yield the same effects!")


for file in walk_paths():
    file_hash = hash_file(file)
    file_ext = file.name.split(".")[-1]
    if search_for_song_hash(conn, file_hash) is not None:
        print(f"File {file} already in database")
        logging.info("File %s already in database.", file)
        continue

    print(f"Parsing {file}")
    try:
        channel_count, Bps, sample_rate, audio_arr = open_audio(file)
    except CouldntDecodeError as e:
        print(f"Error while parsing {file}")
        print(e)
        exit(-1)
    audio_arr = create_buffer(audio_arr)
    start, end = find_clips(audio_arr)
    audio = divide(audio_arr[start:end], desired_length=1, sample_rate=sample_rate, overlap=0.5)
    hash_tree = {}
    for fragment in audio:
        # create spectrum and multiply it by 10*log10
        spectrum = mlab.specgram(fragment[0], NFFT=1024, Fs=sample_rate)
        with np.errstate(divide='ignore'):
            spectrum = 10*np.log10(spectrum[0])
        # now to detect the peaks inside
        peaks = detect_peaks(spectrum[:256])
        mesh = generate_point_mesh(return_position(peaks))
        merge_trees(hash_tree, generate_tree(mesh))

    id_ = insert_into_songs(conn, file.name, file_hash)
    insert_into_fingerprints(conn, id_,
                             hash_frequencies(extract_values_from_tree(hash_tree)))
    print(f"Succesfully parsed {file}")
    
    
    
    
        
