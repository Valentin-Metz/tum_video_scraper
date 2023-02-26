import argparse
import os

import pytest

import tum_live


def test_login_pass():
    webdriver = tum_live.login(os.environ['TUM_USERNAME'], os.environ['TUM_PASSWORD'])
    assert (webdriver.current_url == "https://live.rbg.tum.de/")
    assert ("Login" not in webdriver.page_source)
    webdriver.close()


def test_login_none():
    webdriver = tum_live.login(None, None)
    assert (webdriver.current_url == "https://live.rbg.tum.de/")
    assert ("Login" in webdriver.page_source)
    webdriver.close()


def test_login_fail():
    with pytest.raises(argparse.ArgumentTypeError):
        tum_live.login("go42tum", "hunter2")


def test_get_subjects_fast():
    tum_live_subjects = {
        'FVV der NAT': ('2022/W/1', 'COMB'),
    }
    videos_for_subject: dict[str, [(str, str)]] = {}

    tum_live.get_subjects(tum_live_subjects, None, None, videos_for_subject)

    assert (len(videos_for_subject['FVV der NAT']) == 1)
    assert (videos_for_subject['FVV der NAT'][0][0] == '000_FVV')


def test_get_subjects_login():
    tum_live_subjects = {
        'Netzsicherheit (IN2101)': ('2022/W/NetSec', 'COMB'),
    }
    videos_for_subject: dict[str, [(str, str)]] = {}

    tum_live.get_subjects(tum_live_subjects, os.environ['TUM_USERNAME'], os.environ['TUM_PASSWORD'], videos_for_subject)

    assert (len(videos_for_subject['Netzsicherheit (IN2101)']) == 27)

    assert (videos_for_subject['Netzsicherheit (IN2101)'][0][0]
            == '000_00 Formalities (Carle, von Seck)')
    assert (videos_for_subject['Netzsicherheit (IN2101)'][5][0]
            == '005_03 Firewalls + Intrusion Detection Systems Pt. 3 (Kinkelin)')
    assert (videos_for_subject['Netzsicherheit (IN2101)'][10][0]
            == '010_08 Secure Channels Pt. 1 (Kinkelin, von Seck)')
    assert (videos_for_subject['Netzsicherheit (IN2101)'][26][0]
            == '026_NO LECTURE')


def test_get_subjects_large():
    tum_live_subjects = {
        'Introduction to Deep Learning (IN2346)': ('2022/W/i2dl', 'COMB'),
        'Einführung in Quantum Computing (IN2381)': ('2022/W/EiQC', 'COMB'),
        'Concepts of C++ programming (IN2377)': ('2022/W/cpp', 'COMB'),
        'FVV der NAT': ('2022/W/1', 'COMB'),
        'SET FSMPIC': ('2022/W/set', 'COMB'),
        'hackaTUM': ('2022/W/hackaTUM', 'COMB'),
        'Absolventenfest 2022': ('2022/W/Absfest', 'COMB'),
        'Functional Data Structures (IN2347)': ('2022/S/FDS', 'COMB'),
        'Einführung in Informatik für Games Engineering (IN0031)': ('2021/W/EIDIGames', 'COMB'),
        'Diskrete Wahrscheinlichkeitstheorie (IN0018)': ('2021/S/dwt', 'PRES'),
        'Funktionale Programmierung und Verifikation (IN0003)': ('2020/W/fpv', 'CAM'),
        'Grundlagen: Algorithmen und Datenstrukturen (IN0007)': ('2020/S/gad', 'COMB'),
        'Einführung in die Informatik 1 (IN0001)': ('2019/W/eidi', 'COMB'),
        'Einführung in die Theoretische Informatik (IN0011)': ('2019/S/theo', 'COMB'),
    }
    videos_for_subject: dict[str, [(str, str)]] = {}

    tum_live.get_subjects(tum_live_subjects, None, None, videos_for_subject)

    assert (len(videos_for_subject['Introduction to Deep Learning (IN2346)']) == 24)
    assert (len(videos_for_subject['Einführung in Quantum Computing (IN2381)']) == 15)
    assert (len(videos_for_subject['Concepts of C++ programming (IN2377)']) == 13)
    assert (len(videos_for_subject['FVV der NAT']) == 1)
    assert (len(videos_for_subject['SET FSMPIC']) == 6)
    assert (len(videos_for_subject['hackaTUM']) == 0)
    assert (len(videos_for_subject['Absolventenfest 2022']) == 0)
    assert (len(videos_for_subject['Functional Data Structures (IN2347)']) == 27)
    assert (len(videos_for_subject['Einführung in Informatik für Games Engineering (IN0031)']) == 23)
    assert (len(videos_for_subject['Diskrete Wahrscheinlichkeitstheorie (IN0018)']) == 13)
    assert (len(videos_for_subject['Funktionale Programmierung und Verifikation (IN0003)']) == 13)
    assert (len(videos_for_subject['Grundlagen: Algorithmen und Datenstrukturen (IN0007)']) == 24)
    assert (len(videos_for_subject['Einführung in die Informatik 1 (IN0001)']) == 27)
    assert (len(videos_for_subject['Einführung in die Theoretische Informatik (IN0011)']) == 20)
