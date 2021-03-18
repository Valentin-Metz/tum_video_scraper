import os
import re
import tempfile
import time
from multiprocessing import Process
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
from typing import Set

SOURCE_URL = 'https://live.rbg.tum.de/cgi-bin/streams'
DESTINATION_FOLDER_PATH = '/home/feuermagier/Videos/Lectures/'
TMP_DIRECTORY = os.path.join(tempfile.gettempdir(), "tum_video_scraper")

if not os.path.isdir(TMP_DIRECTORY):  # create temporary work-directory if it does not exist
    os.mkdir(TMP_DIRECTORY)


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


# source: https://www.thepythoncode.com/article/extract-all-website-links-python
def get_all_website_links(url: str) -> set[str]:
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


def filter_urls(urls: set[str]) -> set[str]:  # filters for combined view only
    return {url for url in urls if url.endswith("/COMB")}


def get_videos_of_subject(urls: set[str], name: str, url_identifier: str):
    """The URL-Identifier is found in the URL of every video of the target subject"""
    output_folder_path = os.path.join(DESTINATION_FOLDER_PATH, name)
    if not os.path.isdir(output_folder_path):
        os.mkdir(output_folder_path)
    urls = {url for url in urls if url_identifier in url}
    for url in urls:
        filename = get_name(url) + ".mp4"
        playlist_url = get_playlist_url(url)
        output_file_path = os.path.join(output_folder_path, filename)
        """We use locks to prevent processing the same video twice (for example if we run as a daemon)
        Locks can also be created by the user to keep us from downloading a specific video"""
        if not (os.path.isfile(output_file_path + ".lock")  # check if lock exists
                or os.path.isfile(output_file_path)):  # check if file exists
            open(os.path.join(output_file_path + ".lock"), 'a')  # create lock
            """We use one process for every video"""
            # download_and_cut(playlist_url, filename, output_file_path)
            Process(target=download_and_cut, args=(playlist_url, filename, output_file_path)).start()


def download_and_cut(playlist_url: str, filename: str, output_file_path: str):
    temporary_path = os.path.join(TMP_DIRECTORY, (filename + ".original"))
    download_command = "ffmpeg -y -hide_banner -hwaccel auto " + \
                       f"-i {playlist_url} -c copy -f mp4 {temporary_path}"
    print("Starting download of " + filename)
    download_start_time = time.time()
    os.system(download_command)
    print(f"Download completed after {str(time.time() - download_start_time)}s")
    cut_command = "auto-editor " + temporary_path + \
                  " --silent_speed 8 --frame_margin 15 --video_codec libx264 --constant_rate_factor 30 --no_open -o " \
                  + output_file_path
    print("Starting to convert " + filename)
    conversion_start_time = time.time()
    os.system(cut_command)
    print(f"Conversion completed after {str(time.time() - conversion_start_time)}s")
    os.remove(temporary_path)
    os.remove(output_file_path + ".lock")  # remove lock
    print(f"Done with {filename} after {str(time.time() - download_start_time)}s")


def get_name(url: str) -> str:
    name = url.rsplit('/')[-2]
    return name


def get_playlist_url(url: str) -> str:
    text = requests.get(url).text
    prefix = 'https://stream.lrz.de/vod/_definst_/mp4:tum/RBG'
    postfix = '.mp4/playlist.m3u8'
    playlist_extracted_url = re.search(prefix + '(.+?)' + postfix, text).group(1)
    playlist_url = prefix + playlist_extracted_url + postfix
    return playlist_url


if __name__ == '__main__':
    os.nice(15)  # set our nice value, so we can work in the background
    all_urls: set[str] = get_all_website_links(SOURCE_URL)
    video_urls: set[str] = filter_urls(all_urls)

    get_videos_of_subject(video_urls, 'GBS', 'WiSe2021GBS')
    get_videos_of_subject(video_urls, 'NumProg', 'WiSe2021NumProg')
