# bdix-m3u

A Python script that turns any FTP/HTTP directory listing into an M3U playlist — built for Bangladesh BDIX FTP servers.

## What it does

BDIX FTP sites host thousands of movies and TV series through web-based directory indexes (H5AI, Apache autoindex, etc.). Opening these in a browser and copying links one by one is tedious. This script scrapes a given URL, finds all video files, and builds a ready-to-use `.m3u` playlist you can open directly in VLC, MX Player, Kodi, or any IPTV app.

- Works on any HTTP directory listing — H5AI, Apache, Nginx autoindex
- Detects Season folders automatically and recurses into them
- When multiple seasons are found, lets you pick one, several, or all
- Sorts episodes in the correct order (Episode 1, 2 ... 10, not 1, 10, 2)
- Auto-names the output file based on the show name and season(s)
- Supports standard M3U and M3U Plus format (with group titles for IPTV apps)

## Requirements

- Python 3.7+
- `requests`
- `beautifulsoup4`

```bash
pip install -r requirements.txt
```

## Usage

### Interactive mode

Just run the script and follow the prompts:

```bash
python bdix-m3u.py
```

It will ask for the URL and whether you want M3U Plus format.

### Command line

```bash
python bdix-m3u.py <URL> [OPTIONS]
```

| Option | Description |
|---|---|
| `<URL>` | URL of the FTP directory to scrape |
| `-o FILE` | Output filename (auto-generated if omitted) |
| `--plus` | M3U Plus format — adds group titles, better for IPTV apps |

### Examples

**Scrape a full TV series (all seasons):**
```bash
python bdix-m3u.py http://ftp.bdix.net/Movies/Breaking-Bad/
```

**Scrape a single season directly:**
```bash
python bdix-m3u.py http://ftp.bdix.net/Movies/Breaking-Bad/Season-3/
```

**M3U Plus format (recommended for Kodi / IPTV players):**
```bash
python bdix-m3u.py http://ftp.bdix.net/Movies/Breaking-Bad/ --plus
```

**Custom output filename:**
```bash
python bdix-m3u.py http://ftp.bdix.net/Movies/Breaking-Bad/ -o breaking-bad.m3u
```

### Season selection

When a URL has multiple seasons, the script will ask which ones to include:

```
Multiple seasons found: Season 1, Season 2, Season 3, Season 4, Season 5
Enter season number(s) to include (comma-separated), or press Enter for ALL seasons:
Season(s): 2,3
```

Press Enter to keep all seasons, or type season numbers separated by commas.

## Output format

**Standard M3U:**
```
#EXTM3U
#EXTINF:-1,Breaking.Bad.S01E01.mkv
http://ftp.bdix.net/.../Breaking.Bad.S01E01.mkv
```

**M3U Plus (with `--plus`):**
```
#EXTM3U
#EXTINF:-1 group-title="Season-1",Breaking.Bad.S01E01.mkv
http://ftp.bdix.net/.../Breaking.Bad.S01E01.mkv
```

## Supported video formats

`.mp4` `.mkv` `.avi` `.mov` `.flv` `.wmv` `.webm` `.m3u8` `.ts` `.3gp` `.m4v` `.mpg` `.mpeg`
