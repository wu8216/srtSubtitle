# srtSubtitle

# Generate SRT subtitle file for MP4 videos.
Create video subtitle file for videos in MP4 format.

# Requirements
* Python 3.9 or above

## Features
- Generate subtitle srt file for videos with mp4 format, such as youtube videos.
- The output files are SRT file (.srt), JSON file (.json).

## Installation
pip install -r requirements.txt



Step 1: Download Python 3.9 or below. [Link](https://www.python.org/downloads/release/python-3912/)

Step 2: Edit credentials.json to enter your Google-Cloud account information. If you don't have Google Clound account yet, please create free one with $300 free credit from Google.

Step 3: Add Google speech-to-text api to you Google Cloud project. If you don't have project yet, please create one.

Step 4: Add a Google sotrage bucket to your project. If you don't have project yet, please create one.

Step 5: Run this command "python main.py myVideoName.mp4 zh_CN", if you use english then the command is ""python main.py myVideoName.mp4 zh_CN"

Step 6: Check the output in "./output" folder for the new generated files with Timestamp as part of file name.


## Usage
```
usage: main.py [VIDEO_NAME.mp4] [LANGUAGE_CODE]
Example:
python main.py myVideoName.mp4 zh_CN
python main.py myVideoName.mp4 en_US

```

# FAQ

- Q: The format is the srt file does not have punctuation, how to fix it?
- A: Need to run another Java program to parse and add punctions. This step can be done in Python, but no time to implement in Pyton. Let me know if anyone needs me to do so.

- Q: Any sample vidoes with subtitles?
- A: Two Youtube channels with many videos:
-- Technology QA Channel: https://www.youtube.com/@TechnologyQA
-- Daily Journal Note Channel: https://www.youtube.com/@DailyJournalNote
