import subprocess
import numpy as np
from moviepy.editor import AudioFileClip, CompositeAudioClip
from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.fx import resize
import os
import speech_recognition as sr
from difflib import SequenceMatcher
import soundfile
import shutil

from moviepy.video.io.VideoFileClip import VideoFileClip
from pydub import AudioSegment


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return "Speech Recognition could not understand audio"
        except sr.RequestError as e:
            return f"Could not request results from Google Speech Recognition service; {e}"

def compare_transcription(file_path, expected_text):
    transcribed_text = transcribe_audio(file_path)
    print("Transcribed text:", transcribed_text)
    print("Expected text:", expected_text)
    return similarity(transcribed_text, expected_text)


def byAccuracy(current_audio_files, audio_folder, text):
    inaccurate_folder = os.path.join(audio_folder, "Inaccurate")

    if not os.path.exists(inaccurate_folder):
        os.mkdir(inaccurate_folder)

    files_to_move = []  # Store files to move

    for file_path in current_audio_files:
        data, samplerate = soundfile.read(file_path)
        soundfile.write(file_path, data, samplerate, subtype='PCM_16')
        accuracy = compare_transcription(file_path, text)

        if accuracy < 0.88:
            files_to_move.append(file_path)

        print(f"Accuracy: {accuracy:.2f}, File: {file_path}")

        # Move identified files
    for curFile in files_to_move:
        shutil.move(curFile, inaccurate_folder)
        current_audio_files.remove(curFile)  # Update the list after moving the file


def byLength(current_audio_files, audio_folder):
    badLength_folder = os.path.join(audio_folder, "BadLength")

    if not os.path.exists(badLength_folder):
        os.mkdir(badLength_folder)

    durations = []
    for curFile in current_audio_files:
        with AudioFileClip(curFile) as clip:
            durations.append(clip.duration)
    print("Durations:", durations)
    avg_duration = sum(durations) / len(durations)
    lower_bound, upper_bound = avg_duration * 0.8, avg_duration * 1.15

    # Filter out files outside +-20% of average duration
    files_to_move = []  # Store files to move

    # Identify files outside +-20% of average duration
    for i, curFile in enumerate(current_audio_files):
        if not lower_bound <= durations[i] <= upper_bound:
            files_to_move.append(curFile)

    # Move identified files
    for curFile in files_to_move:
        shutil.move(curFile, badLength_folder)
        current_audio_files.remove(curFile)  # Update the list after moving the file


def byAveragePitch(current_audio_files, audio_folder):
    squekyBoi_folder = os.path.join(audio_folder, "SquekyBoi")

    if not os.path.exists(squekyBoi_folder):
        os.mkdir(squekyBoi_folder)

    pitches = []

    for curFile in current_audio_files:
        data, samplerate = soundfile.read(curFile)

        # Performing FFT and limiting the frequency range to 0 - 5000 Hz
        fft_data = np.abs(np.fft.rfft(data))
        freqs = np.fft.rfftfreq(len(data), 1 / samplerate)
        limited_freq_range = (freqs >= 60) & (freqs <= 500)
        freqs = freqs[limited_freq_range]
        fft_data = fft_data[limited_freq_range]

        # Plotting
        '''plt.figure(figsize=(10, 4))
        plt.plot(freqs, fft_data)
        plt.title(f"FFT of {os.path.basename(curFile)}")
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Magnitude")
        plt.grid(True)
        plt.tight_layout()
        plt.show()'''

        # Calculating weighted average frequency
        total_magnitude = np.sum(fft_data)
        if total_magnitude > 0:
            avg_freq = np.sum(freqs * fft_data) / total_magnitude
        else:
            avg_freq = 0
        pitches.append(avg_freq)

    avg_pitch = sum(pitches) / len(pitches)
    print("Average pitch:", avg_pitch)
    pitch_diff = [pitch - avg_pitch for pitch in pitches]
    print("Pitch difference:", pitch_diff)

    # Select the file with pitch closest to the average
    best_file_index = pitch_diff.index(min(pitch_diff))
    worst_file_index = pitch_diff.index(max(pitch_diff))

    best_file = current_audio_files[best_file_index]

    shutil.move(current_audio_files[worst_file_index], squekyBoi_folder)

    return best_file


def filterAudio(current_audio_files, audio_folder, text):
    print(current_audio_files)
    byAccuracy(current_audio_files, audio_folder, text)
    print(current_audio_files)
    if len(current_audio_files) == 0:
        return None
    byLength(current_audio_files, audio_folder)
    print(current_audio_files)
    if len(current_audio_files) == 0:
        return None
    best_file = byAveragePitch(current_audio_files, audio_folder)
    print(current_audio_files)
    if len(current_audio_files) == 0:
        return None
    return best_file


def makeReel(base_path, video_paths, texts, genAudio, video_duration):
    if os.path.exists(os.path.join(base_path, "final_video.mp4")):
        return

    texts = [text.lower() for text in texts]

    audio_folder = os.path.join(base_path, "Audio")

    # Step 1: Create the Audio folder
    if not os.path.exists(audio_folder):
        os.mkdir(audio_folder)

    # Step 2: Generate TTS Audio for each text
    selected_audio_files = []
    for i, text in enumerate(texts):
        output_audio_path = os.path.join(audio_folder, f"audio_{i + 1}")
        cmd = [
            r"C:\Users\chris\IdeaProjects\Instagram Image\venv\Scripts\python.exe",
            r"C:\Users\chris\IdeaProjects\Instagram Image\venv\Lib\site-packages\tortoise\do_tts.py",
            "--text", text,
            "--voice", "pat2",
            "--preset", "standard",  # ultra-fast, fast, standard, high_quality
            "--candidates", "8",
            "--output_path", output_audio_path
        ]
        if genAudio:
            subprocess.run(cmd)
        current_audio_files = [os.path.join(output_audio_path, f) for f in os.listdir(output_audio_path) if f.endswith(".wav")]
        goodAudioPath = filterAudio(current_audio_files, output_audio_path, text)
        if goodAudioPath is None:
            raise Exception("No good audio files found")
        selected_audio_files.append(goodAudioPath)

    # Step 3: Create the Video from Video Clips
    video_clips = [VideoFileClip(video_path) for video_path in video_paths]
    video_clip = concatenate_videoclips(video_clips, method="compose")

    # Step 4: Add Audio to Video
    audio_clips = []
    max_duration = 5.6  # Maximum duration in seconds

    for i, audio in enumerate(selected_audio_files):
        audio_clip = AudioFileClip(audio)

        # Speed up the audio if it's longer than max_duration
        if audio_clip.duration > max_duration:
            speed_factor = audio_clip.duration / max_duration

            if speed_factor > 1:
                # Load the audio file with pydub
                sound = AudioSegment.from_file(audio)
                # Speed change with pitch preservation
                sound = sound.speedup(playback_speed=speed_factor)
                # Export the processed audio to a temporary file
                temp_audio_path = audio.replace(".wav", "_temp.wav")
                sound.export(temp_audio_path, format="wav")

                # Use the new audio file with the moviepy AudioFileClip
                audio_clip = AudioFileClip(temp_audio_path)
            else:
                audio_clip = audio

        # Set start time for each audio clip
        audio_clip = audio_clip.set_start(i * video_duration)
        audio_clips.append(audio_clip)

    final_audio = CompositeAudioClip(audio_clips)
    final_clip = video_clip.set_audio(final_audio)
    final_clip.write_videofile(os.path.join(base_path, "final_video.mp4"), codec="libx264", fps=24)

useThis = False

if useThis:
    subdir_path = r'pics\Tall20231031_234918'

    texts_file_path = os.path.join(subdir_path, "captions.txt")

    with open(texts_file_path, 'r') as file:
        texts = [line.strip() for line in file.readlines()]
        for i in range(2):
            for i in range(len(texts)):
                if texts[i][-1] == "." or texts[i][-1] == ",":
                    texts[i] = texts[i][:-1]


    makeReel(subdir_path, texts, False, 9)