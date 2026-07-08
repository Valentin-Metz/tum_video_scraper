import argparse
import os
import re
import sys
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

import util


def login(tum_username: str | None, tum_password: str | None) -> webdriver:
    driver_options = webdriver.FirefoxOptions()
    if str(os.getenv('HEADLESS', 'true')) in ("1", "true", "yes", "on"):
        driver_options.add_argument("--headless")
    if os.getenv('NO-SANDBOX') == '1':
        driver_options.add_argument("--no-sandbox")
    driver = webdriver.Firefox(options=driver_options)

    if tum_username:
        driver.get("https://live.rbg.tum.de/login")
        driver.find_element(By.XPATH, "/html/body/main/section/article/div/button").click()
        driver.find_element(By.ID, "username").send_keys(tum_username)
        driver.find_element(By.ID, "password").send_keys(tum_password)
        driver.find_element(By.ID, "username").submit()
        sleep(2)
        if "Couldn't log in. Please double check your credentials." in driver.page_source:
            driver.close()
            raise argparse.ArgumentTypeError("Username or password incorrect")
    driver.get("https://live.rbg.tum.de/old/")
    return driver


def get_video_links_of_subject(driver: webdriver, subjects_identifier, camera_type) -> [(str, str)]:
    year, term, slug = subjects_identifier.split("/", 2)
    subject_url = f"https://live.rbg.tum.de/?year={year}&term={term}&slug={slug}&view=3"
    driver.get(subject_url)

    # The course page is rendered client-side, so we wait for the video list
    # to appear before scraping it. An empty list means an empty lecture series.
    video_urls = _collect_video_links(driver)
    if not video_urls:
        return []

    sort_ascending = _sort_is_ascending(driver)

    video_playlists: [(str, str)] = []
    for video_url in video_urls:
        driver.get(video_url + "/" + camera_type)
        sleep(2)
        filename = driver.find_element(By.XPATH, "//h1").text.strip()
        if not ("Starts in more than a day" or "Stream is due") in driver.page_source:
            playlist_url = get_playlist_url(driver)
            if playlist_url:
                video_playlists.append((filename, playlist_url))
            else:
                print(f'Warning: no playlist URL for "{filename}" ({video_url}) - skipping',
                      file=sys.stderr)

    if not sort_ascending:
        video_playlists.reverse()

    return video_playlists


def _collect_video_links(driver: webdriver) -> [str]:
    # The video list is rendered asynchronously; wait for at least one
    # watch link ("https://live.rbg.tum.de/w/...") to appear.
    def watch_links() -> [str]:
        urls: [str] = []
        for link in driver.find_elements(By.XPATH, ".//a"):
            link_url = link.get_attribute("href")
            if link_url and "https://live.rbg.tum.de/w/" in link_url:
                urls.append(link_url)
        urls = [url for url in urls if ("/CAM" not in url and "/PRES" not in url and "/chat" not in url)]
        return list(dict.fromkeys(urls))  # deduplicate, preserve order

    try:
        WebDriverWait(driver, 10).until(lambda _d: watch_links())
    except TimeoutException:
        pass
    return watch_links()


def _sort_is_ascending(driver: webdriver) -> bool:
    # The newer TUM-Live UI offers two toggle buttons, "Newest first" and
    # "Oldest first"; the one carrying the "active" class reflects the
    # current order. We consider the list ascending (oldest first) only when
    # "Oldest first" is the active button, defaulting to descending.
    newest = oldest = False
    for button in driver.find_elements(By.CSS_SELECTOR, "button"):
        label = (button.text or "").strip()
        if not label:
            continue
        classes = button.get_attribute("class") or ""
        if "active" not in classes:
            continue
        if label == "Oldest first":
            oldest = True
        elif label == "Newest first":
            newest = True
    return oldest and not newest


def get_playlist_url(driver: webdriver) -> str | None:
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script(
                "const s = document.querySelector('video source'); return s && s.src ? s.src : '';"
            )
        )
    except TimeoutException:
        pass

    src = driver.execute_script(
        "const s = document.querySelector('video source'); return s && s.src ? s.src : '';"
    )
    if src and ".m3u8" in src:
        return src

    match = re.search(r"(https://\S+?/playlist\.m3u8[^'\"\s]*)", driver.page_source)
    if match:
        return match.group(1)

    return None


def get_subjects(subjects: dict[str, (str, str)], tum_username: str | None, tum_password: str | None,
                 queue: dict[str, [(str, str)]]):
    driver = login(tum_username, tum_password)
    for subject_name, (subjects_identifier, camera_type) in subjects.items():
        m3u8_playlists = get_video_links_of_subject(driver, subjects_identifier, camera_type)
        m3u8_playlists = util.enumerate_list(m3u8_playlists)
        print(f'Found {len(m3u8_playlists)} videos for "{subject_name}"')
        queue[subject_name] = m3u8_playlists
    driver.close()
