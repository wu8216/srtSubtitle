import datetime
import os
import shutil
import subprocess
import sys
from datetime import datetime
from sys import argv

import srt
from dotenv import load_dotenv
from google.cloud import storage, speech_v1
from google.cloud.speech_v1 import *
from pydub.utils import mediainfo


def main():
    # Calculate media info from video
    channels, bit_rate, sample_rate = video_info(video_path)

    # Convert to audio
    # audio_filename = timestamp + "_audio.wav"
    audio_filename = timestamp + "_audio.mp3"
    audio_filename_flac = timestamp + "_audio.flac"
    blob_name = video_to_audio(video_path, audio_filename, channels, bit_rate, sample_rate, audio_filename_flac)

    # Upload to Google storage
    gcs_uri = f"gs://{BUCKET_NAME}/{blob_name}"
    # gcs_uri = f"gs://media_srt/20230111.flac"

    # Transcribe
    response = long_running_recognize(gcs_uri, channels, sample_rate)

    # Output to files
    write_srt(response)
    write_txt(response)

    move_files_to_output()


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )


def video_info(video_filepath):
    """Returns number of channels, bit rate, and sample rate of the video"""

    video_data = mediainfo(video_filepath)
    channels = video_data["channels"]
    bit_rate = video_data["bit_rate"]
    sample_rate = video_data["sample_rate"]

    return channels, bit_rate, sample_rate


def video_to_audio(video_filepath, audio_filename, video_channels, video_bit_rate, video_sample_rate,
                   audio_filename_flac):
    """Converts video into audio, and upload the audio to GS"""
    # ffmpeg -i video.mp4 -f mp3 -ab 192000 -vn music.mp3
    # command = f"ffmpeg -i {video_filepath} -b:a {video_bit_rate} -ac {video_channels} -ar {video_sample_rate} -vn {audio_filename} "
    command = f"ffmpeg -i {video_filepath}  -b:a {video_bit_rate} -ac {video_channels} -ar {video_sample_rate} -f mp3 -ab 192000 -vn {audio_filename} "
    subprocess.call(command, shell=True)
    # ffmpeg -i audio.xxx -c:a flac audio.flac
    # sleep(3)
    command = f"ffmpeg -i {audio_filename} -c:a flac {audio_filename_flac} "
    subprocess.call(command, shell=True)
    blob_name = f"{audio_filename_flac}"
    upload_blob(BUCKET_NAME, audio_filename_flac, audio_filename_flac)
    return blob_name


def long_running_recognize(storage_uri, channels, sample_rate):
    """Transcribes the audio"""

    client = speech_v1.SpeechClient()

    config = {
        "language_code": LANG,
        "sample_rate_hertz": int(sample_rate),
        # "encoding": RecognitionConfig.AudioEncoding.LINEAR16,
        "encoding": RecognitionConfig.AudioEncoding.FLAC,
        "audio_channel_count": int(channels),
        "enable_word_time_offsets": True,
        "model": "default",
        "enable_automatic_punctuation": True
    }
    audio = {"uri": storage_uri}

    print(f"Using the config: {config}")
    print(f"Audio file location: {audio}")

    operation = client.long_running_recognize(config=config, audio=audio)

    print(u"Waiting for operation to complete...")
    response = operation.result(timeout=1000000)
    # print(response)

    json_filename = timestamp + "subtitles.json"
    with open(json_filename, mode="w", encoding="utf-8") as f:
        f.write(str(response))

    subs = []
    for result in response.results:
        # First alternative is the most probable result
        subs = break_sentences(MAX_CHARS, subs, result.alternatives[0])

    print("Transcribing finished")
    return subs

def break_sentences(max_chars, subs, alternative):
    """Breaks sentences by punctuations and maximum sentence length"""

    firstword = True
    charcount = 0
    idx = len(subs) + 1
    content = ""

    for w in alternative.words:
        if firstword:
            # first word in sentence, record start time
            start = w.start_time  # .ToTimedelta()

        charcount += len(w.word)
        content += " " + w.word.strip()

        if ("。" in w.word or "." in w.word or "!" in w.word or "?" in w.word or
                charcount > max_chars or
                ("," in w.word and not firstword)):
            # break sentence at: . ! ? or line length exceeded
            # also break if , and not first word
            subs.append(srt.Subtitle(index=idx,
                                     start=start,
                                     end=w.end_time,  # .ToTimedelta(),
                                     content=srt.make_legal_content(content)))
            firstword = True
            idx += 1
            content = ""
            charcount = 0
        else:
            firstword = False
    return subs


def write_srt(subs):
    """Writes SRT file"""

    srt_file = timestamp + "subtitles.srt"
    # print("Writing {} subtitles to: {}".format(LANG, srt_file))
    f = open(srt_file, mode="w", encoding="utf-8")
    content = srt.compose(subs)
    f.writelines(str(content).replace(" ", "").replace("-->", " --> "))
    f.close()
    return


def write_txt(subs):
    """Writes TXT file"""

    txt_file = timestamp + "subtitles.txt"
    print(f"Writing text to: {txt_file}")
    f = open(txt_file, mode="w", encoding="utf-8")
    for s in subs:
        content = s.content.strip() + "\n"
        f.write(str(content))
    f.close()
    return

def move_files_to_output():
    source = 'C:/Users/Richard/PycharmProjects/srtSubtitle'
    dest = 'C:/Users/Richard/PycharmProjects/srtSubtitle/output'
    files = os.listdir(source)

    #.flac .mp3 .json .srt .txt
    for f in files:
        if (f.endswith(".flac") or f.endswith(".mp3") or f.endswith("subtitles.json") or f.endswith(".srt") or f.endswith(".txt")):
            shutil.move(f, dest)
    return

def timestamp():
    """Gets current date and time"""

    current_datetime = datetime.now()
    # print("Current date & time : ", current_datetime)
    # convert datetime obj to string
    str_current_datetime = str(current_datetime).replace(" ", "_").replace(":", "_")
    return str_current_datetime


# Load configuration from .env file
load_dotenv()
BUCKET_NAME = str(os.getenv('BUCKET_NAME'))
MAX_CHARS = int(os.getenv('MAX_CHARS'))
FFMPEG_LOCATION = str(os.getenv('FFMPEG_LOCATION'))
FFPROBE_LOCATION = str(os.getenv('FFPROBE_LOCATION'))

# Load ffmpeg location
mediainfo.converter = FFMPEG_LOCATION
mediainfo.ffmpeg = FFMPEG_LOCATION
mediainfo.ffprobe = FFPROBE_LOCATION

# Take CLI arguments
if len(argv) != 3:
    print("Missing command-line argument. Usage: python main.py example.wav en-US")
    exit(1)
video_path = sys.argv[1]
LANG = sys.argv[2]  # LANG = "en-US"

# Acess GCP credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

# Get timestamp for filenames
timestamp = timestamp()

# Call the main function
if __name__ == "__main__":
    main()

