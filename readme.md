# LaunchBox Python Scripts

A collection of Python scripts and modules to speed up the never-ending tasks of keeping everything up to date. Maybe if I automake some of this stuff, I'll eventually have time to play some of these games before I die.

These are all written as personal scripts. While an attempt has been made to not hard-code values like file paths, there's no guarantee that they'll work with your setup.

## lb_cheevo_checker

**PRE-RELEASE VERSION**

A script that requests all game/hash data from the RetroAchievements API, then compares it against entries in LaunchBox platform data.

Designed to spot when you are missing files in your collection, when files you have may not be the right hash/region/version, or don't have a required patch applied.

LaunchBox data is loaded as read only, so does not edit or update any LaunchBox data files for you. Make all your fixes/changes from within LaunchBox itself, rescan for achievements, close LaunchBox, then run this script again to see updates.

### Setup and Usage

- Install Python 3 (if asked, make sure that PATH environment variable is set)

- Open `config_settings.ini` and set the following required values:

    - `[LAUNCHBOX]`
        - `directory` - Path to your LaunchBox directory (i.e. `C:\Emulation\LaunchBox`)
    - `[RETROACHIVEMENTS]`
        - `username` - Username for RetroAchievements website, required for API access
        - `api_key` - Web API key from [RetroAchievements Settings](https://retroachievements.org/settings) page

- Open `config_consoles.json` and set `should_scan` to `true` for each console/platform you would like to scan

- Run the Python script by opening `lb_cheevo_checker.bat` (or manually running `lb_cheevo_checker.py`)

    - The first run should install the 'requests-cache' module via Python package installer, which is required for caching of RetroAchievements API data

### Features

- Requests and caches all relevant game/hash from the RetroAchievements API for given platforms

- Generates and caches RetroAchievement hashes for all 'Additional Application' entries for a LaunchBox platform, something not currently done by LaunchBox itself

    - _Dev Note: This is because I keep all hacks and subsets as additional applications/versions under each main game entry, so we need to knows these hashes in order to compare_

- Compares all games for a RetroAchievements console to see if one of the compatible hashes matches the saved hash for any LaunchBox game entries

- Lists any RetroAchievements games that did not match any LaunchBox game entries, and requests/shows additional information about compatible hashes and files

## lb_cheevo_gc_rvz (coming soon)

A script for adding RetroAchievements hash data for .rvz files.

## lb_rename_game (coming soon)

A script for renaming files and updating LaunchBox data when a game file is updated, such as revisions in No-Intro and Redump databases.