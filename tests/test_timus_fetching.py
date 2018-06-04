import pytest
from datetime import datetime

import lib.timus_fetching as timus_fetching

@pytest.mark.parametrize(
    'time,date,expected',
    (
        ('23:04:16', '18 Feb 2018', datetime(2018, 2, 18, 23, 4, 16)),
        ('23:10:08', '4 Feb 2018', datetime(2018, 2, 4, 23, 10, 8)),
        ('08:35:33', '18 Feb 2018', datetime(2018, 2, 18, 8, 35, 33)),
    )
)
def test_parsing_date(time, date, expected):
    actual = timus_fetching.parse_timus_time(time, date)
    assert actual == expected


def test_ce_submit_parsing():
    html = open('tests/data/ce.html').read()
    actual = timus_fetching.parse_submit_records(html)
    expected = [
        timus_fetching.SubmitRecord(
            7764902,
            datetime(2018, 2, 18, 3, 10, 45),
            243756,
            1104,
            'Visual C++ 2017',
            'Compilation error',
            0,
            0,
            0
        )
    ]
    assert actual == expected


def test_ac_submit_parsing():
    html = open('tests/data/ac.html').read()
    actual = timus_fetching.parse_submit_records(html)
    expected = [
        timus_fetching.SubmitRecord(
            7764900,
            datetime(2018, 2, 18, 3, 6, 17),
            243756,
            1104,
            'Visual C++ 2017',
            'Accepted',
            0,
            0.187,
            260
        )
    ]
    assert actual == expected


def test_wa_submit_parsing():
    html = open('tests/data/wa.html').read()
    actual = timus_fetching.parse_submit_records(html)
    expected = [
        timus_fetching.SubmitRecord(
            7764901,
            datetime(2018, 2, 18, 3, 9, 7),
            243756,
            1104,
            'Visual C++ 2017',
            'Wrong answer',
            16,
            0.187,
            264
        )
    ]
    assert actual == expected


def test_1000_submits():
    html = open('tests/data/1000_submits.html').read()
    actual = timus_fetching.parse_submit_records(html)
    assert len(actual) == 1000

    
def test_difficulty_parsing():
    html = open('tests/data/1303.html').read()
    difficulty = timus_fetching.parse_problem_difficulty(html)
    assert difficulty == 231
    
    
def test_difficulty_fetching():
    difficulty = timus_fetching.fetch_problem_difficulty(1000)
    assert type(difficulty) is int
    assert 10 <= difficulty <= 50
