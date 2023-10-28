[![CI test](https://github.com/Valentin-Metz/tum_video_scraper/actions/workflows/tum_video_scraper_ci.yml/badge.svg)](https://github.com/Valentin-Metz/tum_video_scraper/actions/workflows/tum_video_scraper_ci.yml)
[![CodeQL](https://github.com/Valentin-Metz/tum_video_scraper/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/Valentin-Metz/tum_video_scraper/actions/workflows/codeql-analysis.yml)
[![TUM](https://custom-icon-badges.demolab.com/badge/TUM-exzellent-0065bd.svg?logo=tum_logo_2023)](https://www.tum.de/)
[![TUM-Live](https://custom-icon-badges.demolab.com/badge/TUM--Live-live-e5312b.svg?logo=tum_live_logo)](https://live.rbg.tum.de/)
[![TUM-Panopto](https://custom-icon-badges.demolab.com/badge/TUM--Panopto-online-11773d.svg?logo=panopto_icon_2015)](https://tum.cloud.panopto.eu/)

# Installation

Required system dependencies:

```
python  >= 3.9.9
ffmpeg  >= 4.4.1
chromium >= 96.0.4664.93
chromedriver >= 96.0.4664.93
```

Create a virtual environment (in the project folder) and install project-dependencies into it.

(This is only required if you run directly from the python source)

```bash
python3 -m venv venv
source ./venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -U -r requirements.txt
```

# Running

Activating your venv:

(This is only required if you run directly from the python source)

```
source ./venv/bin/activate
```

Usage:

```
The first argument supplied must be the output directory.
If you want to supply it at a different position, the argument must be marked with "output_folder".
    (Example: output_folder /home/feuermagier/videos/Lectures)


Optional arguments:

--help: Prints a help message

--tum_live: Download a subject from TUM-live (subject_name:subject_identifier:camera_type)
    subject_name: Will be used as the folder name. Freely choosable by you.
    subject_identifier: Can be found in the URL of your chosen subject. For now please make sure to use https://live.rbg.tum.de/old/
        (Example: https://live.rbg.tum.de/old/course/2021/W/it-sec - "2021/W/it-sec" is the subject_identifier for videos of this subject)
    camera_type: The camera-view to download
        COMB: Presentation slides fused with speaker-camera
        PRES: Presentation slides
        CAM:  Speaker camera
        
--panopto: Download a folder from TUM-Panopto. As Panopto is login-only you will have to supply your TUM-credentials.
    subject_name: Will be used as the folder name. Freely choosable by you.
    folder_id: Can be found in the URL of your Panopto folder
        (Example: https://tum.cloud.panopto.eu/Panopto/Pages/Sessions/List.aspx#folderID=a150c6d5-6cbe-40b0-8dc1-ad0a00967dfb - "a150c6d5-6cbe-40b0-8dc1-ad0a00967dfb" is the folder_id)

--username: Your TUM-Username (Example: go42tum)
--password: The password for your TUM-Username (Example: "hunter2")

--keep: Keep the original version of a downloaded video insted of only the jump-cutted ones. Defaults to true.
--jumpcut: Save a jump-cutted version of the video (fast-forwarding frames with silence). Defaults to true.

--temp_dir: Allows you to spcify a custom temp-directory. Usually the system-temp-folder will be used. You probably won't need this.
--maximum_parallel_downloads: Allows you to specify how many videos we download and convert at a time. Conversion uses a lot of RAM, so be careful with this. The default is 3.
```

# Automation

If you want to automatically download your lectures in the future, all you need to do is run the scraper periodically.

I suggest you use `systemd` for this task. Instructions on how to do this can be found in the `/systemd/README.md` of
this repository.
