import argparse
import os
import tempfile
from pathlib import Path

import scraper


def parse_subject(s: str) -> (str, str):
    try:
        a, b = s.split(':')
        return a, b
    except ValueError:
        raise argparse.ArgumentTypeError("Subjects must be in the form: subject_name:subject_identifier")


if __name__ == '__main__':
    os.nice(15)  # set our nice value, so we can work in the background

    SOURCE_URL = 'https://live.rbg.tum.de/cgi-bin/streams'
    TMP_DIRECTORY = Path(tempfile.gettempdir(), "tum_video_scraper")  # default: (/tmp/tum_video_scraper/)

    parser = argparse.ArgumentParser(description="Download and jump-cut TUM-Lecture-Videos")
    parser.add_argument("output_folder", help="output folder path", type=Path)
    parser.add_argument("-t", "--temp_dir", help="path for temporary files")
    parser.add_argument("subjects", help="list of subjects in the form: subject_name:subject_identifier",
                        type=parse_subject, nargs='+')
    args = parser.parse_args()

    destination_folder_path = args.output_folder
    if args.temp_dir:
        TMP_DIRECTORY = args.temp_dir
        if not os.path.isdir(TMP_DIRECTORY):
            raise argparse.ArgumentTypeError("The supplied TEMP_DIR is invalid")
    subjects = args.subjects

    if not os.path.isdir(TMP_DIRECTORY):  # create temporary work-directory if it does not exist
        os.mkdir(TMP_DIRECTORY)

    all_urls: set[str] = scraper.get_all_website_links(SOURCE_URL)
    video_urls: set[str] = scraper.filter_urls(all_urls)

    scraper.get_videos(video_urls, subjects, destination_folder_path, TMP_DIRECTORY)
