# Installation

1. Install system dependencies

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

2. Install python-dependencies in an virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

#chronjob

This project is designed to be run as a cronjob. The Recomended configuration is:
```
0-59/5 7-21 * * 1-6 cd ABS_PATH_TO_PROJECT && ./download_chronjob.bash
```
This is equivalent to`At every 5th minute from 0 through 59 past every hour from 7 through 21 on every day-of-week from Monday through Saturday.`