# FTP M3U Maker

## Overview
FTP M3U Maker is a Python script designed to scrape video files from web-based directory listings (such as local BDIX FTP servers) and automatically generate an `.m3u` or M3U Plus playlist. It recursively scans directories, identifies video files, and organizes them properly based on natural sorting and season structures.

## File Structure
- `ftpserver-m3u-maker.py`: The core Python script that performs the crawling, parsing, and M3U playlist generation.
- `*.m3u`: Generated playlist files.

## Reason & Intention
The intention behind this project is to simplify the process of gathering media links from web directories and standardizing them into a single playlist file, automating a mostly manual and tedious process.

## Problem it Solves
Many local FTP networks (e.g., BDIX servers) host TV shows and movies in web-based directory indexes. Manually copying each video link to watch in media players like VLC or IPTV apps is time-consuming and inefficient. This tool crawls the provided URL, detects video extensions, and generates a structured playlist ready to be imported into any M3U-compatible media player.

## Tech Stack
- **Python 3**
- Modules: `requests`, `argparse`, `os`, `re`, `urllib.parse`
- **BeautifulSoup4** (`bs4`): Used for HTML parsing and extracting directory links.

## How it Works
1. **Input**: The script takes a base URL of the web directory as an argument (or prompts the user for it).
2. **Crawling**: It fetches the page using `requests` and parses the HTML with `BeautifulSoup`.
3. **Detection**: It identifies video links based on common video file extensions (`.mp4`, `.mkv`, etc.) and detects "Season" directories to recurse into them.
4. **Sorting**: Harvested video links are naturally sorted so episodes play in the correct sequential order (e.g., Ep1, Ep2... Ep10).
5. **Output**: Finally, it writes the formatted playlist to an standard `.m3u` file or an M3U Plus format (with group titles) based on user preference.
