# Description
Generate a match index for your Fighting Game videos. The match index includes:
* Timestamps for all matches
* Characters used
* Duration of each match
* Summary of character totals

Want an easy way to create timestamps for your YouTube videos? Just copy/paste the Match Indexer output into your video's description field, and away you go!

# Prerequisites
1. Download and install Python (https://python.org/downloads)
2. Install NumPy:
   * `pip install numpy`
3. Install OpenCV (ref: https://pypi.org/project/opencv-python/)
   * `pip install opencv-python`

# Installation
Download the `match-indexer.py` file and ensure there are subfolders named `templates` and `layouts` at the same level. These come prepared to detect Virtua Fighter 5 Final Showdown matches.

# Usage
From a terminal window:

    > python.exe match-indexer.py OPTIONS LAYOUT FILENAME

* OPTIONS: See the [Options](#Options) section for a list of the options.
* LAYOUT: 
* FILENAME: the filename of the video to process. See Filename Formats for more info.

# Options

    -h, --help  show this help message and exit
    -c          Output CSV format
    -n          Show match number sequentially in output
    -p          Preview while indexing
    -t DIR      Path to templates folder (default: "templates" in current folder)
    -z          Zoom preview window down to 50% (used with the -p option)

# Configuration
## Templates
For each character that exists in your Fighting Game, you need to create two "templates" to match against, one for Player 1 side and the other for Player 2.

To define your characters, create a `.jpg` with the following naming convention:

    {character name}-1p.jpg
    {character name}-2p.jpg

The `{character name}` label will be used in the match indexer's output.

> [!NOTE]
> This was deliberately designed this way, as opposed to using a single image and flipping it, since some games have non-mirrored 1P vs 2P character portraits.

## Layouts
Layout files (`{layout name}.py`) are placed in the `layouts` folder, and contain a single variable called `layout` which is a [Python Dictionary](https://docs.python.org/3/tutorial/datastructures.html#dictionaries) data type. This variable stores data in `key:value` pairs.

The layout file must define the following keys:
* scale
* originPlayer1
* originPlayer2
* originClock
* widthPortrait
* heightPortrait
* widthClock
* heightClock

This data is used to setup various Regions of Interest (ROIs) in which the templates will be compared to for a match. Since we know exactly where the character portraits will appear, we can narrow down our search area, rather than try to search across the entire frame, for optimal performance.

# Output
Print to screen, redirect to file, csv to spreadsheet

# FAQ

### Question
Answer 