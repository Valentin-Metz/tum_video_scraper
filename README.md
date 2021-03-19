# Installation

1. Install system dependencies

```
python  >= 3.9
ffmpeg  >= 4.3.2
```

2. Create virtual environment (in the project folder) and install project-dependencies into it

```bash
python3 -m venv venv
source ./venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

# Configuration
1. Set the `DESTINATION_FOLDER_PATH` in `main.py`.
2. Configure the subjects you want to download (at the bottom of `main.py`).
For this you need to choose a name for the subject and find the unique identifier in the URL of a video that belongs to the chosen subject on `live.rbg.tum.de`. Examples are provided in the file.


# Cronjob

This project can be run as a cronjob. The recommended configuration is:
```
0-59/5 7-21 * * 1-6 cd ABS_PATH_TO_PROJECT && ./tum_video_scraper_chronjob.bash
```
This is equivalent to: `At every 5th minute from 0 through 59 past every hour from 7 through 21 on every day-of-week from Monday through Saturday.`