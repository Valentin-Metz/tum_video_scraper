# Installation

Required system dependencies:

```
python  >= 3.9
ffmpeg  >= 4.3.2
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
    subject_name: Will be used as the folder name. Freely choosable by you
    subject_identifier: Can be found in the URL of a video of your chosen subject
        (Example: https://live.rbg.tum.de/cgi-bin/streams/VOD/SoSe2021DWT/2021_04_16_12_15/COMB - "SoSe2021DWT" is the subject_identifier for videos of this subject)
    camera_type: The camera-view to download
        COMB: Presentation slides fused with speaker-camera
        PRES: Presentation slides
        CAM:  Speaker camera
        
--panopto: Download a folder from TUM-Panopto. As Panopto is login-only you will have to supply your TUM-credentials.
    subject_name: Will be used as the folder name. Freely choosable by you
    folder_id: Can be found in the URL of your Panopto folder
        (Example: https://tum.cloud.panopto.eu/Panopto/Pages/Sessions/List.aspx#folderID=a150c6d5-6cbe-40b0-8dc1-ad0a00967dfb - "a150c6d5-6cbe-40b0-8dc1-ad0a00967dfb" is the folder_id)

--username: Your TUM-Username (Example: ab12cde)
--password: The password for your TUM-Username (Example: "hunter2")

--temp_dir: Allows you to spcify a custom temp-directory. Usually the system-temp-folder will be used. You probably won't need this.
```