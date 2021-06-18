import argparse
import re
from pathlib import Path
from time import sleep

from selenium import webdriver

import downloader


def login(tum_username: str, tum_password: str) -> webdriver:
    driver_options = webdriver.FirefoxOptions()
    driver_options.add_argument("--headless")
    driver = webdriver.Firefox(options=driver_options)
    driver.get("https://live.mm.rbg.tum.de/login")
    driver.find_element_by_id("username").send_keys(tum_username)
    driver.find_element_by_id("password").send_keys(tum_password)
    driver.find_element_by_id("username").submit()
    sleep(5)
    if "Couldn't log in. Please double check your credentials." in driver.page_source:
        driver.close()
        raise argparse.ArgumentTypeError("Username or password incorrect")
    return driver


def get_video_links_of_subject(driver: webdriver, subjects_identifier, camera_type) -> [(str, str)]:
    subject_url = "https://live.mm.rbg.tum.de/course/" + subjects_identifier
    driver.get(subject_url)
    links_on_page = driver.find_elements_by_xpath(".//a")
    video_urls: set[str] = set()
    for link in links_on_page:
        link_url = link.get_attribute("href")
        if link_url and "https://live.mm.rbg.tum.de/w/" in link_url:
            video_urls.add(link_url)
    video_playlists: set[(str, str)] = set()
    for video_url in video_urls:
        driver.get(video_url + "/" + camera_type)
        sleep(1)
        title = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[2]/h1").text.replace(' ', '_') + ".mp4"
        playlist_url = get_playlist_url(driver.page_source)
        video_playlists.add((title, playlist_url))
    return video_playlists


def get_playlist_url(source: str) -> str:
    prefix = 'https://stream.lrz.de/vod/_definst_/mp4:tum/RBG/'
    postfix = '.mp4/playlist.m3u8'
    playlist_extracted_url = re.search(prefix + '(.+?)' + postfix, source).group(1)
    playlist_url = prefix + playlist_extracted_url + postfix
    return playlist_url


def get_subjects(subjects: (str, str, str), destination_folder_path: Path, tmp_directory: Path,
                 tum_username: str, tum_password: str):
    driver = login(tum_username, tum_password)
    for subject_name, subjects_identifier, camera_type in subjects:
        m3u8_playlists = get_video_links_of_subject(driver, subjects_identifier, camera_type)
        subject_folder = Path(destination_folder_path, subject_name)
        subject_folder.mkdir(exist_ok=True)
        downloader.download_list_of_videos(m3u8_playlists, subject_folder, tmp_directory)
