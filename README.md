[![CI test](https://github.com/Valentin-Metz/tum_video_scraper/actions/workflows/tum_video_scraper_ci.yml/badge.svg)](https://github.com/Valentin-Metz/tum_video_scraper/actions/workflows/tum_video_scraper_ci.yml)
[![CodeQL](https://github.com/Valentin-Metz/tum_video_scraper/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/Valentin-Metz/tum_video_scraper/actions/workflows/codeql-analysis.yml)
[![TUM](https://custom-icon-badges.demolab.com/badge/TUM-exzellent-0065bd.svg?logo=tum_logo_2023)](https://www.tum.de/)
[![TUM-Live](https://custom-icon-badges.demolab.com/badge/TUM--Live-live-e5312b.svg?logo=tum_live_logo)](https://live.rbg.tum.de/)

# TUM Video Scraper

Download lecture recordings from [TUM-Live](https://live.rbg.tum.de/) and —
optionally — silence-cut them with [auto-editor](https://github.com/WyattBlue/auto-editor).

The scraper logs into TUM-Live with Selenium/Firefox, discovers the video
playlists of the courses you configure, downloads each video with `ffmpeg`
(`-c copy`, so it's fast and lossless), and runs `auto-editor` to produce a
jump-cut version that speeds up silent sections.

> **Note:** TUM has discontinued its Panopto offering, so Panopto support has
> been removed. Only TUM-Live is supported now.

## Quick start (Docker)

The suggested way to run this project is with [Docker](https://docs.docker.com/engine/reference/commandline/run/):

```bash
docker run -it -v ./config.yml:/app/config.yml -v target_location:/app/output ghcr.io/valentin-metz/tum_video_scraper:master
```

You'll need to link in a configuration file `config.yml`.
You can find an example in the root of this repository under `example_config.yml`.
The output folder you specify in the config file will be the target location *inside* the docker container,
so make sure to mount your target location to `/app/output`.

## How to find course identifiers

Course identifiers tell the scraper which TUM-Live course to download.

For a given course on [TUM-Live](https://live.rbg.tum.de/), the identifier is
derived from the URL query parameters.

Example:
`https://live.rbg.tum.de/?year=2024&term=W&slug=ws24PiSE`

In this case, the course identifier is `2024/W/ws24PiSE`, assembled from:

1. The `year` (`2024`)
2. The `term` (`W` for winter term, `S` for summer term)
3. The unique course `slug` (`ws24PiSE` — here for *Patterns in Software Engineering (IN2081)*)

You have to take these from the URL, as they are not consistent between courses and years.

You also specify the video stream you want to download.
TUM-Live usually offers three:

1. The combined view — `:COMB` (appended to the identifier)
2. The presentation view — `:PRES`
3. The presenter camera view — `:CAM`

## Configuration

### Config file

Run the scraper with a YAML config file. An example is provided in
`example_config.yml`:

```yaml
TUM-live:
  "IT-Sec": "2021/W/it-sec:COMB"
  "NumProg": "2021/W/NumProg:COMB"

Username: "go42tum"
Password: "hunter2"

Keep-Original-File: true
Jumpcut: true

Output-Folder: "/app/output"
Maximum-Parallel-Downloads: 3
```

| Key                        | Required | Default    | Description                                                                            |
| -------------------------- | -------- | ---------- | ------------------------------------------------------------------------------------- |
| `TUM-live`                 | no       | —          | Map of `"<folder name>": "<identifier>:<CAM\|PRES\|COMB>"`.                          |
| `Username`                 | no\*     | —          | TUM username (e.g. `go42tum`). Required only for non-public courses.                  |
| `Password`                 | no\*     | —          | TUM password. Prompted on stdin if `Username` is set but `Password` is omitted.       |
| `Keep-Original-File`       | no       | `true`     | Keep the unedited download alongside the jump-cut version.                           |
| `Jumpcut`                  | no       | `true`     | Run `auto-editor` to produce a silence-jump-cut version (`*_jc.mp4`).                 |
| `Output-Folder`            | yes      | —          | Where downloaded videos are stored.                                                   |
| `Temp-Dir`                 | no       | `/tmp/tum_video_scraper` | Working directory for intermediate files.                                  |
| `Maximum-Parallel-Downloads` | no     | `3`        | Cap on concurrent downloads/conversions to limit RAM usage.                           |

\* Public courses can be downloaded without credentials.

### Command-line arguments

Command-line arguments take priority over the config file.

```
python3 src/main.py -c config.yml -o ./output
```

| Flag                           | Description                                                                            |
| ------------------------------ | ------------------------------------------------------------------------------------- |
| `-c, --config_file`            | Path to a YAML config file.                                                             |
| `--tum_live`                   | One or more courses as `name:identifier:CAM\|PRES\|COMB`.                             |
| `-u, --username`               | TUM username.                                                                          |
| `-p, --password`               | TUM password (prompted on stdin if username is given without a password).             |
| `-k, --keep`                   | Keep the original file (`true`/`false`).                                               |
| `-j, --jump_cut`               | Produce a jump-cut version (`true`/`false`).                                           |
| `-o, --output_folder`          | Output directory.                                                                      |
| `-t, --temp_dir`               | Temporary working directory.                                                           |
| `-d, --maximum_parallel_downloads` | Maximum number of concurrent downloads/conversions.                                |

## Output files and `.lock` files

For each video the scraper may produce:

- `<index>_<title>.mp4` — the original, lossless download (if `Keep-Original-File` is on).
- `<index>_<title>_jc.mp4` — the silence-jump-cut version (if `Jumpcut` is on).

Each download is guarded by a `.lock` file (e.g. `<index>_<title>.mp4.lock`).
Locks are created at the start of a run and prevent the same video from being
downloaded twice — including across independent scraper instances. If a run is
interrupted, the `.lock` files are **not** removed; delete them manually to
re-download those videos.

You can exploit this for partial downloads: start the scraper, interrupt it
once the `.lock` files are created, then delete only the `.lock` files of the
videos you want.

---

## Installation from source

You only need this if you are not running via Docker.

### System dependencies

```
python  >= 3.11
ffmpeg  >= 6.1
firefox >= 120.0
geckodriver >= 0.33
auto-editor  (for jump-cutting)
```

`geckodriver` must be on your `PATH` and match your Firefox version.

### Python dependencies

Create a virtual environment (in the project folder) and install the dependencies into it:

```bash
python3 -m venv venv
source ./venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -U -r requirements.txt
```

### Run

```bash
python3 src/main.py -c config.yml -o ./output
```

In Docker the scraper runs headless by default. When running from source you
can toggle headless mode and sandboxing with the environment variables
`HEADLESS` (default `true`) and `NO-SANDBOX` (set to `1` to add `--no-sandbox`,
as required inside Docker).
