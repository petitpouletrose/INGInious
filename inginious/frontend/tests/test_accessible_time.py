# pylint: disable=redefined-outer-name
# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import pytest
import datetime

from inginious.frontend.accessible_time import parse_date, AccessibleTime


class TestAccessibleTime(object):
    def test_parse_date_correct(self):
        testing_date = "2022-01-01 01:01:01"
        date = parse_date(testing_date)
        assert type(date) == datetime.datetime
        assert date.year == 2022
        assert date.month == 1
        assert date.day == 1
        assert date.hour == 1
        assert date.minute == 1
        assert date.second == 1

    def test_parse_date_default_value(self):
        testing_date = ""
        now = datetime.datetime.now()
        date = parse_date(testing_date, default=now)
        assert type(date) == datetime.datetime
        assert date.year == now.year
        assert date.month == now.month
        assert date.day == now.day
        assert date.hour == now.hour
        assert date.minute == now.minute
        assert date.second == now.second

    def test_parse_date_wrong_values(self):
        testing_date = ""
        testing_default = None
        try:
            date = parse_date(testing_date, testing_default)
            assert False
        except Exception:
            assert True

    def test_parse_date_wrong_format(self):
        testing_date = "2022,01,01 01;01;01"
        try:
            date = parse_date(testing_date)
            assert False
        except Exception:
            assert True

    def test_accessible_time_init(self):
        try:
            ac_time = AccessibleTime(True)
            ac_time = AccessibleTime("2014-07-16 11:24:00")
            ac_time = AccessibleTime("2014-07-16")
            ac_time = AccessibleTime("/ 2014-07-16 11:24:00")
            ac_time = AccessibleTime("/ 2014-07-16")
            ac_time = AccessibleTime("2014-07-16 11:24:00 / 2014-07-20 11:24:00")
            ac_time = AccessibleTime("2014-07-16 / 2014-07-20 11:24:00")
            ac_time = AccessibleTime("2014-07-16 11:24:00 / 2014-07-20")
            ac_time = AccessibleTime("2014-07-16 / 2014-07-20")
            ac_time = AccessibleTime("2014-07-16 11:24:00 / 2014-07-20 11:24:00 / 2014-07-20 12:24:00")
            ac_time = AccessibleTime("2014-07-16 / 2014-07-20 11:24:00 / 2014-07-21")
            ac_time = AccessibleTime("2014-07-16 / 2014-07-20 / 2014-07-21")
            assert True
        except Exception:
            assert False
        try:
            ac_time = AccessibleTime("test")
            ac_time = AccessibleTime(object)
            assert False
        except Exception:
            assert True

    def test_accessible_time_before_start(self):
        ac_time = AccessibleTime(True)
        assert not ac_time.before_start()
        ac_time = AccessibleTime(False)
        assert ac_time.before_start()
        ac_time = AccessibleTime("2014-07-16 11:24:00")
        assert not ac_time.before_start()

    def test_accessible_time_after_start(self):
        ac_time = AccessibleTime(True)
        assert ac_time.after_start()
        ac_time = AccessibleTime(False)
        assert not ac_time.after_start()
        ac_time = AccessibleTime("2014-07-16 11:24:00")
        assert ac_time.after_start()

    def test_accessible_time_is_open(self):
        ac_time = AccessibleTime(True)
        assert ac_time.is_open()
        ac_time = AccessibleTime(False)
        assert not ac_time.is_open()
        ac_time = AccessibleTime("2014-07-16 11:24:00")
        assert ac_time.is_open()
        ac_time = AccessibleTime("2014-07-16 / 2014-07-20")
        assert not ac_time.is_open()
        assert ac_time.is_open(datetime.datetime(year=2014, month=7, day=17))

    def test_accessible_time_is_open_soft_deadline(self):
        ac_time = AccessibleTime(True)
        assert ac_time.is_open_with_soft_deadline()
        ac_time = AccessibleTime(False)
        assert not ac_time.is_open_with_soft_deadline()
        ac_time = AccessibleTime("2014-07-16 / 2014-07-20 11:24:00 / 2014-07-21")
        assert not ac_time.is_open_with_soft_deadline()
        assert ac_time.is_open_with_soft_deadline(datetime.datetime(year=2014, month=7, day=17))
        assert not ac_time.is_open_with_soft_deadline(datetime.datetime(year=2014, month=7, day=21))

    def test_accessible_time_is_always_accessible(self):
        ac_time = AccessibleTime(True)
        assert ac_time.is_always_accessible()
        ac_time = AccessibleTime(False)
        assert not ac_time.is_always_accessible()
        ac_time = AccessibleTime("2014-07-16 / 2014-07-20 11:24:00 / 2014-07-21")
        assert not ac_time.is_always_accessible()

    def test_accessible_time_is_never_accessible(self):
        ac_time = AccessibleTime(True)
        assert not ac_time.is_never_accessible()
        ac_time = AccessibleTime(False)
        assert ac_time.is_never_accessible()
        ac_time = AccessibleTime("2014-07-16 / 2014-07-20 11:24:00 / 2014-07-21")
        assert not ac_time.is_never_accessible()

    def test_accessible_time_get_std_start_date(self):
        ac_time = AccessibleTime(True)
        assert ac_time.get_std_start_date() == ""
        ac_time = AccessibleTime("2014-07-16 / 2014-07-20")
        assert ac_time.get_std_start_date() == "2014-07-16 00:00:00"

    def test_accessible_time_get_std_end_date(self):
        ac_time = AccessibleTime(True)
        assert ac_time.get_std_end_date() == ""
        ac_time = AccessibleTime("2014-07-16 / 2014-07-20")
        assert ac_time.get_std_end_date() == "2014-07-20 00:00:00"

    def test_accessible_time_get_std_soft_end_date(self):
        ac_time = AccessibleTime(True)
        assert ac_time.get_std_soft_end_date() == ""
        ac_time = AccessibleTime("2014-07-16 / 2014-07-20 / 2014-07-21")
        assert ac_time.get_std_soft_end_date() == "2014-07-20 00:00:00"

    def test_accessible_time_get_start_date(self):
        ac_time = AccessibleTime(True)
        assert type(ac_time.get_start_date()) is datetime.datetime
        assert ac_time.get_start_date() == datetime.datetime.min

    def test_accessible_time_get_end_date(self):
        ac_time = AccessibleTime(True)
        assert type(ac_time.get_end_date()) is datetime.datetime
        assert ac_time.get_end_date() == datetime.datetime.max

    def test_accessible_time_get_soft_end_date(self):
        ac_time = AccessibleTime(True)
        assert type(ac_time.get_soft_end_date()) is datetime.datetime
        assert ac_time.get_soft_end_date() == datetime.datetime.max

