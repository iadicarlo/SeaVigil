"""Tests for country + flag-emoji helpers."""

from __future__ import annotations

from seavigil import flags


def test_flag_emoji_basic():
    assert flags.flag_emoji("US") != ""
    assert flags.flag_emoji("us") == flags.flag_emoji("US")
    assert flags.flag_emoji("X") == ""
    assert flags.flag_emoji(None) == ""


def test_from_mmsi_mid():
    iso2, emoji = flags.from_mmsi(366123456)   # MID 366 -> United States
    assert iso2 == "US" and emoji != ""
    assert flags.from_mmsi(563999999)[0] == "SG"   # 563 -> Singapore
    assert flags.from_mmsi(None) == ("", "")
    assert flags.from_mmsi("garbage") == ("", "")


def test_from_iso3():
    assert flags.from_iso3("ECU")[0] == "EC"
    assert flags.from_iso3("AUS")[0] == "AU"
    assert flags.from_iso3(None) == ("", "")


def test_emoji_for_accepts_iso2_and_iso3():
    assert flags.emoji_for("US") == flags.emoji_for("USA") != ""
    assert flags.emoji_for("") == ""
