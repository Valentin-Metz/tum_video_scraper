import re
from pathlib import Path
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

import downloader


def get_subjects(subjects: (str, str, str), destination_folder_path, tmp_directory):
    source_url = 'https://live.rbg.tum.de/cgi-bin/streams'
    all_urls: set[str] = get_all_website_links(source_url)

    for subject_name, subjects_identifier, camera_type in subjects:
        video_urls: set[str] = filter_urls(all_urls, camera_type)
        get_videos_of_subject(video_urls, subject_name, subjects_identifier, destination_folder_path, tmp_directory)


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


def filter_urls(urls: set[str], camera_type: str) -> set[str]:  # filters for combined view only
    return {url for url in urls if url.endswith("/" + camera_type)}


def get_videos_of_subject(urls: set[str], subject_name: str, url_identifier: str, destination_folder_path: Path,
                          tmp_directory: Path):
    """The URL-Identifier is found in the URL of every video of the target subject"""
    output_folder_path = Path(destination_folder_path, subject_name)
    output_folder_path.mkdir(exist_ok=True)
    urls = {url for url in urls if url_identifier in url}
    videos = []
    for url in urls:
        filename = get_name(url) + ".mp4"
        playlist_url = get_playlist_url(url)
        videos.append((filename, playlist_url))
    downloader.download_list_of_videos(videos, output_folder_path, tmp_directory)


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
