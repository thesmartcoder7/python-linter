from mido import Message, MidiFile, MidiTrack
import sys

# Create a new MIDI file and track
midi = MidiFile()
track = MidiTrack()
midi.tracks.append(track)

lyric = "forever be lifted high"
test = {}

# Define note mappings for C major chord progression (C - Am - F - G for verse, Am - F - C - G for chorus)
chords = {
    "C": [60, 64, 67],   # C major
    "Am": [57, 60, 64],  # A minor
    "F": [53, 57, 60],   # F major
    "G": [55, 59, 62]    # G major
}

# Define the song structure (progression for verse and chorus)
progression_verse = ["C", "Am", "F", "G"]
progression_chorus = ["Am", "F", "C", "G"]

# Set note duration
note_duration = 1920  # Length of a quarter note

# Function to add chords to MIDI track
def add_chord(chord_name, duration):
    for note in chords[chord_name]:
        track.append(Message('note_on', note=note, velocity=64, time=0))
    track.append(Message('note_off', note=chords[chord_name][0], velocity=64, time=duration))
    track.append(Message('note_off', note=chords[chord_name][1], velocity=64, time=0))
    track.append(Message('note_off', note=chords[chord_name][2], velocity=64, time=0))

# Add two verses
for _ in range(2):
    for chord in progression_verse:
        add_chord(chord, note_duration)

# Add the chorus twice
for _ in range(2):
    for chord in progression_chorus:
        add_chord(chord, note_duration)

# Save the MIDI file
midi.save("sample_song.mid")
print("MIDI file saved as sample_song.mid")
