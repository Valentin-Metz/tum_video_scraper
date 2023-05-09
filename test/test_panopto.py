import argparse
import os

import pytest

import panopto


def test_login_pass():
    webdriver = panopto.login(os.environ['TUM_USERNAME'], os.environ['TUM_PASSWORD'])
    assert (webdriver.current_url == "https://tum.cloud.panopto.eu/Panopto/Pages/Home.aspx")
    assert ("UserMenuContent_loggedInControls" in webdriver.page_source)
    webdriver.close()


def test_login_none():
    with pytest.raises(argparse.ArgumentTypeError):
        panopto.login(None, None)


def test_login_fail():
    with pytest.raises(argparse.ArgumentTypeError):
        panopto.login("go42tum", "hunter2")


def test_get_folders_fast():
    panopto_folders = {
        'Introduction to Biological Imaging 950567672 (W21/22)': 'b87a3aa9-6f30-4fe3-9804-adcc00c7b486',
    }
    videos_for_subject: dict[str, [(str, str)]] = {}

    panopto.get_folders(panopto_folders, os.environ['TUM_USERNAME'], os.environ['TUM_PASSWORD'], videos_for_subject)

    assert (len(videos_for_subject['Introduction to Biological Imaging 950567672 (W21/22)']) == 19)

    assert (videos_for_subject['Introduction to Biological Imaging 950567672 (W21/22)'][0][0]
            == '000_Lecture 1: Introduction')
    assert (videos_for_subject['Introduction to Biological Imaging 950567672 (W21/22)'][2][0]
            == '002_Exercise 1: MATLAB Basics')
    assert (videos_for_subject['Introduction to Biological Imaging 950567672 (W21/22)'][13][0]
            == '013_Lecture 10: MRI (part 2)')
    assert (videos_for_subject['Introduction to Biological Imaging 950567672 (W21/22)'][18][0]
            == '018_Lecture 13: Case Study & Summary')


def test_get_folders_large():
    panopto_folders = {
        'Studentische Vollversammlung 950633228 (W22/23)': '81daaf4e-cbdd-42c6-8a37-af4c0100c518',
        'Introduction to Biological Imaging 950567672 (W21/22)': 'b87a3aa9-6f30-4fe3-9804-adcc00c7b486',
        'Maschinelles Lernen 950631887 (W22/23)': '37c7610b-63e6-46a2-b403-af2f0123f5c0',
    }
    videos_for_subject: dict[str, [(str, str)]] = {}

    panopto.get_folders(panopto_folders, os.environ['TUM_USERNAME'], os.environ['TUM_PASSWORD'], videos_for_subject)

    assert (len(videos_for_subject['Studentische Vollversammlung 950633228 (W22/23)']) == 1)
    assert (len(videos_for_subject['Introduction to Biological Imaging 950567672 (W21/22)']) == 19)
    assert (len(videos_for_subject['Maschinelles Lernen 950631887 (W22/23)']) == 55)
