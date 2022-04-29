import argparse
import os
import re
from multiprocessing import Semaphore
from pathlib import Path
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import downloader
import util


def login(tum_username: str, tum_password: str) -> webdriver:
    capabilities = DesiredCapabilities.CHROME
    capabilities["goog:loggingPrefs"] = {"performance": "ALL"}  # chromedriver 75+

    driver_options = webdriver.ChromeOptions()
    driver_options.add_argument("--headless")
    if os.getenv('NO-SANDBOX') == '1':
        driver_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=driver_options, desired_capabilities=capabilities)

    driver.get("https://www.moodle.tum.de/login/index.php")
    driver.find_element(By.LINK_TEXT, "TUM LOGIN").click()

    driver.find_element(By.ID, "username").send_keys(tum_username)
    driver.find_element(By.ID, "password").send_keys(tum_password)
    driver.find_element(By.ID, "btnLogin").click()
    sleep(3)
    if "Username or password was incorrect" in driver.page_source:
        driver.close()
        raise argparse.ArgumentTypeError("Username or password incorrect")

    driver.get("https://tum.cloud.panopto.eu/")
    driver.find_element(By.LINK_TEXT, "Sign in").click()
    sleep(1)
    return driver


def get_video_links_in_folder(driver: webdriver, folder_id: str) -> [(str, str)]:
    folder_link = f"https://tum.cloud.panopto.eu/Panopto/Pages/Sessions/List.aspx#folderID=%22" \
                  f"{folder_id}" \
                  f"%22&maxResults=250"
    driver.get(folder_link)
    sleep(3)
    if "Failed to load folder" in driver.title:
        print("Folder-ID incorrect: " + folder_id)
        raise Exception

    links_on_page = driver.find_elements_by_xpath(".//a")
    video_urls: [str] = []
    for link in links_on_page:
        link_url = link.get_attribute("href")
        if link_url and "https://tum.cloud.panopto.eu/Panopto/Pages/Viewer.aspx" in link_url:
            video_urls.append(link_url)

    video_playlists: [(str, str)] = []
    for video_url in video_urls:
        video_id = video_url[-36:]
        video_playlists.append(get_m3u8_playlist(driver, video_id))

    video_playlists = util.dedup(video_playlists)
    video_playlists.reverse()

    return video_playlists


def get_m3u8_playlist(driver: webdriver, video_id: str) -> (str, str):
    video_url = "https://tum.cloud.panopto.eu/Panopto/Pages/Embed.aspx?id=" + video_id
    driver.get(video_url)

    playlist_url = None

    prefix = "\"VideoUrl\":\""
    postfix = "/master.m3u8"
    matches = re.search(prefix + '(.+?)' + postfix, driver.page_source)
    if matches:
        playlist_extracted_url = matches.group(1)
        playlist_url = playlist_extracted_url.replace('\\', '') + postfix

    if playlist_url is None:
        driver.get("https://tum.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=" + video_id)
        sleep(3)
        urls = util.filter_log(driver.get_log("performance"), lambda x: x.endswith("index.m3u8"))
        if len(urls) > 0:
            playlist_url = urls[0] # maybe we could do this interactively, or should we just abort if multuple m3u8 were found

    if playlist_url is None:
        print("Error on URL " + video_url + " - " + driver.title)
        return

    filename = driver.title.strip()
    return filename, playlist_url


def get_folders(panopto_folders: dict[str, str], tum_username: str, tum_password: str, queue: [str, (str, str)]):
    driver = login(tum_username, tum_password)
    for subject_name, folder_id in panopto_folders.items():
        m3u8_playlists = get_video_links_in_folder(driver, folder_id)
        m3u8_playlists = util.rename_duplicates(m3u8_playlists)
        print(f'Found {len(m3u8_playlists)} videos for "{subject_name}"')
        queue.append((subject_name, m3u8_playlists))
    driver.close()
