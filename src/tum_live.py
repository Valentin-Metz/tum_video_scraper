import argparse
import os
import re
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By

import util


def login(tum_username: str, tum_password: str) -> webdriver:
    driver_options = webdriver.ChromeOptions()
    driver_options.add_argument("--headless")
    if os.getenv('NO-SANDBOX') == '1':
        driver_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=driver_options)

    driver.get("https://live.rbg.tum.de/login")
    driver.find_element(By.ID, "username").send_keys(tum_username)
    driver.find_element(By.ID, "password").send_keys(tum_password)
    driver.find_element(By.ID, "username").submit()
    sleep(2)
    if "Couldn't log in. Please double check your credentials." in driver.page_source:
        driver.close()
        raise argparse.ArgumentTypeError("Username or password incorrect")
    return driver


def get_video_links_of_subject(driver: webdriver, subjects_identifier, camera_type) -> [(str, str)]:
    subject_url = "https://live.rbg.tum.de/course/" + subjects_identifier
    driver.get(subject_url)

    links_on_page = driver.find_elements_by_xpath(".//a")
    video_urls: [str] = []
    for link in links_on_page:
        link_url = link.get_attribute("href")
        if link_url and "https://live.rbg.tum.de/w/" in link_url:
            video_urls.append(link_url)

    video_urls = [url for url in video_urls if ("/CAM" not in url and "/PRES" not in url)]

    video_playlists: [(str, str)] = []
    for video_url in video_urls:
        driver.get(video_url + "/" + camera_type)
        sleep(2)
        filename = driver.find_element_by_xpath("/html/body/div[2]/div/div/div[3]/h1").text.strip()
        playlist_url = get_playlist_url(driver.page_source)
        video_playlists.append((filename, playlist_url))

    video_playlists = util.dedup(video_playlists)

    return video_playlists


def get_playlist_url(source: str) -> str:
    prefix = 'https://stream.lrz.de/vod/_definst_/mp4:tum/RBG/'
    postfix = '.mp4/playlist.m3u8'
    playlist_extracted_url = re.search(prefix + '(.+?)' + postfix, source).group(1)
    playlist_url = prefix + playlist_extracted_url + postfix
    return playlist_url


def get_subjects(subjects: dict[str, (str, str)], tum_username: str, tum_password: str, queue: [str, (str, str)]):
    driver = login(tum_username, tum_password)
    for subject_name, (subjects_identifier, camera_type) in subjects.items():
        m3u8_playlists = get_video_links_of_subject(driver, subjects_identifier, camera_type)
        m3u8_playlists = util.rename_duplicates(m3u8_playlists)
        print(f'Found {len(m3u8_playlists)} videos for "{subject_name}"')
        queue.append((subject_name, m3u8_playlists))
    driver.close()
