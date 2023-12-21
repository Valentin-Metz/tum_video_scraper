import argparse
import os
import re
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from seleniumrequests import Firefox

import util


def login(tum_username: str | None, tum_password: str | None) -> webdriver:
    driver_options = webdriver.FirefoxOptions()
    driver_options.add_argument("--headless")
    if os.getenv('NO-SANDBOX') == '1':
        driver_options.add_argument("--no-sandbox")
    driver = Firefox(options=driver_options)

    if not tum_username or not tum_password:
        driver.close()
        raise argparse.ArgumentTypeError("You must provide a valid TUM username and password to use Panopto")

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

    links_on_page = driver.find_elements(By.XPATH, ".//a")
    video_urls: [str] = []
    for link in links_on_page:
        link_url = link.get_attribute("href")
        if link_url and "https://tum.cloud.panopto.eu/Panopto/Pages/Viewer.aspx" in link_url:
            video_urls.append(link_url)
    video_urls = list(dict.fromkeys(video_urls))  # deduplicate

    video_playlists: [(str, str)] = []
    for video_url in video_urls:
        video_id = video_url[-36:]
        video_playlists.append(get_m3u8_playlist(driver, video_id))
    video_playlists.reverse()

    return video_playlists


def get_m3u8_playlist(driver: webdriver, video_id: str) -> (str, str):
    video_url = "https://tum.cloud.panopto.eu/Panopto/Pages/Embed.aspx?id=" + video_id
    driver.get(video_url)
    request_url = "https://tum.cloud.panopto.eu/Panopto/Pages/Viewer/DeliveryInfo.aspx?deliveryId="
    post_response = driver.request('POST', request_url + video_id)

    prefix = "https://"
    postfix = "/master.m3u8"
    matches = re.search(prefix + '(.+?)' + postfix, post_response.text)
    if not matches:
        print("Error on URL " + video_url + " - " + driver.title)
        return
    playlist_extracted_url = matches.group(1)
    playlist_url = prefix + playlist_extracted_url.replace('\\', '') + postfix
    filename = driver.title.strip()
    return filename, playlist_url


def get_folders(panopto_folders: dict[str, str], tum_username: str | None, tum_password: str | None,
                queue: [str, [(str, str)]]):
    driver = login(tum_username, tum_password)
    for subject_name, folder_id in panopto_folders.items():
        m3u8_playlists = get_video_links_in_folder(driver, folder_id)
        m3u8_playlists = util.enumerate_list(m3u8_playlists)
        print(f'Found {len(m3u8_playlists)} videos for "{subject_name}"')
        queue[subject_name] = m3u8_playlists
    driver.close()
