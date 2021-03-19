import json
import os
import re
import tempfile
import time
from multiprocessing import Pool
from os.path import expanduser
from typing import Set, Dict
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

SOURCE_URL = 'https://live.rbg.tum.de/cgi-bin/streams'
CONFIG_FILE = "config.json"
DESTINATION_FOLDER_PATH = os.path.join(expanduser("~"), "Videos", "Lectures")
if not os.path.isdir(DESTINATION_FOLDER_PATH):  # create destinatnion-directory if it does not exist
    os.mkdir(DESTINATION_FOLDER_PATH)

# /tmp/tum_video_scraper or most likely C:\TEMP\tum_video_scraper\. Windows has a multitude of temp folders.
TMP_DIRECTORY = os.path.join(tempfile.gettempdir(), "tum_video_scraper")
if not os.path.isdir(TMP_DIRECTORY):  # create temporary work-directory if it does not exist
    os.mkdir(TMP_DIRECTORY)

PROCESS_COUNT = os.cpu_count()


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


# source: https://www.thepythoncode.com/article/extract-all-website-links-python
def get_all_website_links(url: str) -> Set[str]:
    urls_on_site = set()
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            # href empty tag
            continue
        # join the URL if it's relative (not absolute link)
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        # remove URL GET parameters, URL fragments, etc.
        href = f"{parsed_href.scheme}://{parsed_href.netloc}{parsed_href.path}"
        if not is_valid_url(href):
            # not a valid URL
            continue
        if href in urls_on_site:
            # already in the set
            continue
        urls_on_site.add(href)
    return urls_on_site


def filter_urls(urls: Set[str]) -> Set[str]:  # filters for combined view only
    return {url for url in urls if url.endswith("/COMB")}


def get_videos_of_subject(urls: Set[str], name: str, url_identifier: str):
    """The URL-Identifier is found in the URL of every video of the target subject"""

    output_folder_path = os.path.join(DESTINATION_FOLDER_PATH, name)
    if not os.path.isdir(output_folder_path):
        os.mkdir(output_folder_path)
    urls = {url for url in urls if url_identifier in url}
    args_list = []
    for url in urls:
        filename = f"{get_name(url)}.mp4"
        playlist_url = get_playlist_url(url)
        output_file_path = os.path.join(output_folder_path, filename)
        # We use locks to prevent processing the same video twice (for example if we run as a daemon)
        # Locks can also be created by the user to keep us from downloading a specific video"""
        if not os.path.isfile(f"{output_file_path}.lock") and not os.path.isfile(output_file_path):
            args_list.append((playlist_url, filename, output_file_path))
    # download_and_cut(playlist_url, filename, output_file_path)
    # We use one process of the Processpool for every video
    process_pool = Pool(PROCESS_COUNT)
    process_pool.starmap(download_and_cut, args_list)


def download_and_cut(playlist_url: str, filename: str, output_file_path: str):
    if not os.path.isfile(f"{output_file_path}.lock") and not os.path.isfile(output_file_path):
        open(os.path.join(f"{output_file_path}.lock"), 'a')  # create lock

        start_time = time.time()
        with tempfile.NamedTemporaryFile(delete=True, dir=TMP_DIRECTORY, suffix=".mp4") as temporary_path:
            print(f"Starting download of {filename}")
            os.system(f"ffmpeg -y -hide_banner -hwaccel auto -loglevel warning "
                      f"-i {playlist_url} "
                      f"-c copy "
                      f"{temporary_path.name}")
            print(f"Starting to convert {filename}")
            os.system(f"auto-editor {temporary_path.name} "
                      f"--silent_speed 8 --frame_margin 15 --video_codec libx264 --constant_rate_factor 30 "
                      f"--no_progress --no_open "
                      f"-o {output_file_path}")

        os.remove(f"{output_file_path}.lock")  # remove lock
        print(f"Done with {filename} in {str(time.time() - start_time)}s")


def get_name(p_url: str) -> str:
    return p_url.rsplit('/')[-2]


def get_playlist_url(p_url: str) -> str:
    text = requests.get(p_url).text
    prefix = 'https://stream.lrz.de/vod/_definst_/mp4:tum/RBG'
    postfix = '.mp4/playlist.m3u8'
    playlist_extracted_url = re.search(f'{prefix}(.+?){postfix}', text).group(1)
    return prefix + playlist_extracted_url + postfix


def map_to_identifiers(playlist_urls: Set[str]) -> Dict[str, Dict[str, bool]]:
    ids = {}
    for p_url in playlist_urls:
        long_id = p_url.rsplit('/')[-3]
        if long_id[8:] in ids:
            ids[long_id[8:]][long_id[:8]] = False
        else:
            ids[long_id[8:]] = {long_id[:8]: False}
    return ids


def merge_identifiers(ids, prev_ids):
    # merges previous identifiers and current identifiers.
    # invalid formating in the previous config is ignored
    if prev_ids and isinstance(prev_ids, dict):
        for p_name, p_choices in prev_ids.items():
            if isinstance(p_choices, dict):
                if p_name not in ids:
                    ids[p_name] = p_choices
                else:
                    for p_sub_option, p_is_selected in p_choices.items():
                        if p_sub_option not in ids[p_name]:
                            ids[p_name][p_sub_option] = p_is_selected
                        else:
                            ids[p_name][p_sub_option] |= p_is_selected
    return ids


def get_identifiers(playlist_urls):
    ids: Dict[str, Dict[str, bool]] = map_to_identifiers(playlist_urls)
    if not os.path.isfile(CONFIG_FILE):
        open(CONFIG_FILE, "x").close()
    with open(CONFIG_FILE, "r+") as config_file:
        if os.path.getsize("config.json") > 0:
            previous_identifieres = json.load(config_file)
            config_file.seek(0)
            ids = merge_identifiers(ids, previous_identifieres)
        json.dump(ids, config_file, sort_keys=True, indent=4)
    return ids


if __name__ == '__main__':
    os.nice(15)  # set our nice value, so we can work in the background
    all_urls: Set[str] = get_all_website_links(SOURCE_URL)
    video_urls: Set[str] = filter_urls(all_urls)
    identifieres: Dict[str, Dict[str, bool]] = get_identifiers(video_urls)

    for name, choices in identifieres.items():
        for sub_option, is_selected in choices.items():
            if is_selected:
                get_videos_of_subject(video_urls, name, f"{sub_option}{name}")
