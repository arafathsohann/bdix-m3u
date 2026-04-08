import argparse
import requests
import sys
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote

# List of common video file extensions to look for
VIDEO_EXTENSIONS = (
    '.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', 
    '.webm', '.m3u8', '.ts', '.3gp', '.m4v', '.mpg', '.mpeg'
)

def is_video_link(url):
    """
    Checks if a URL ends with a video extension.
    Ignores query parameters when checking the extension.
    """
    parsed = urlparse(url)
    path = parsed.path.lower()
    return path.endswith(VIDEO_EXTENSIONS)

def get_filename_from_url(url):
    """Extracts a readable filename from the URL, decoding percent-encoding."""
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    return unquote(filename) if filename else "Unknown Video"

def get_season_name(url):
    """
    Extracts 'Season X' or 'Season-X' from the parent directory of the URL.
    Returns None if not found.
    """
    parsed = urlparse(url)
    path_segments = parsed.path.strip('/').split('/')
    if len(path_segments) >= 2:
        # Check the parent folder (second to last segment)
        parent = unquote(path_segments[-2])
        # Match Season-1, Season 01, Season_1 etc.
        if re.search(r'Season[-_\s]?\d+', parent, re.IGNORECASE):
            return parent
    return None

def natural_sort_key(item):
    """
    Key for natural sorting (e.g., Ep1, Ep2, Ep10 instead of Ep1, Ep10, Ep2).
    """
    url = item['url']
    filename = get_filename_from_url(url)
    # Split string by digits, converting digits to integers for numerical comparison
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', filename)]

def generate_m3u(video_items, output_file, is_m3u_plus=False):
    """
    Writes the list of video items to an M3U file.
    video_items: list of dicts {'url': str, 'filename': str, 'season': str}
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            
            for item in video_items:
                filename = item['filename']
                url = item['url']
                season = item.get('season')

                if is_m3u_plus and season:
                    # M3U Plus format with group-title
                    f.write(f'#EXTINF:-1 group-title="{season}",{filename}\n')
                else:
                    # Standard M3U
                    f.write(f"#EXTINF:-1,{filename}\n")
                
                f.write(f"{url}\n")
        
        print(f"\nSuccess! Playlist saved to: {output_file}")
        print(f"Found {len(video_items)} video link(s).")
        
    except IOError as e:
        print(f"Error writing file: {e}")

def get_links_from_page(url):
    """Fetches a page and returns a tuple (video_links, directory_links)."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"Scanning: {url}...")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return [], []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    video_links = set()
    directory_links = set()

    for link in soup.find_all('a', href=True):
        href = link['href']
        
        # Skip parent directory links
        if href in ['../', './', '/'] or href.startswith('?'):
            continue
            
        full_url = urljoin(url, href)
        
        if is_video_link(full_url):
            video_links.add(full_url)
        else:
            # It's a directory, check if it looks like a Season folder
            decoded_href = unquote(href).strip('/')
            last_segment = decoded_href.split('/')[-1]

            if re.match(r'Season[-_\s]?\d+', last_segment, re.IGNORECASE):
                directory_links.add(full_url)
            elif "Season" in last_segment or "Series" in last_segment:
                 # Fallback: strict match failed, but might be "Seasons/" or similar structure
                 directory_links.add(full_url)
                
    # Also check <video> and <source> tags for the current page
    for tag in soup.find_all(['video', 'source']):
        src = tag.get('src')
        if src:
            full_url = urljoin(url, src)
            if is_video_link(full_url):
                video_links.add(full_url)

    return list(video_links), list(directory_links)


def get_clean_show_name(url):
    """
    Extracts a cleaner show name from the URL.
    Example: .../Modern-Family-(TV-Series-2009-2020)-1080p/ -> Modern-Family
    If the URL ends with a Season folder, uses the parent segment as the show name.
    """
    parsed = urlparse(url)
    path = unquote(parsed.path).strip('/')
    segments = [s for s in path.split('/') if s]
    folder_name = segments[-1] if segments else path

    # If last segment is a Season folder, step up to the show folder
    if re.match(r'Season[-_\s]?\d+', folder_name, re.IGNORECASE) and len(segments) >= 2:
        folder_name = segments[-2]

    # Common patterns to strip
    # Remove (TV Series ...) or similar parentheticals
    clean_name = re.sub(r'\s*\(.*?\)', '', folder_name)
    # Remove quality tags like 1080p, 720p
    clean_name = re.sub(r'[-_\s]?(1080p|720p|480p|2160p|4k).*', '', clean_name, flags=re.IGNORECASE)
    # Remove year patterns if at the end e.g. -2009
    clean_name = re.sub(r'[-_\s]?\d{4}([-_\u2013\u2014]\d{4})?', '', clean_name)
    
    # Final cleanup of extra separators
    clean_name = re.sub(r'[-_\s]+', '-', clean_name).strip('-')
    
    return clean_name if clean_name else "TV_Show"

def crawl_recursive(base_url):
    """
    Crawls the base URL.
    Returns (all_videos, season_numbers)
    """
    all_videos = []
    season_numbers = set()
    
    # scan root
    videos, dirs = get_links_from_page(base_url)
    
    # Process videos in the root (files mixed with season folders, or single season)
    for v_url in videos:
        seas_str = get_season_name(v_url)
        all_videos.append({
            'url': v_url,
            'filename': get_filename_from_url(v_url),
            'season': seas_str
        })
        if seas_str:
            # Extract number from "Season-1" -> 1
            match = re.search(r'\d+', seas_str)
            if match:
                season_numbers.add(int(match.group(0)))
    
    # Process Season directories
    for d_url in dirs:
        # Check if directory name implies a season number
        decoded_href = unquote(urlparse(d_url).path).strip('/')
        last_segment = decoded_href.split('/')[-1]
        
        match = re.search(r'Season[-_\s]?(\d+)', last_segment, re.IGNORECASE)
        if match:
             # Add to set even before scanning, though scanning confirms content
             season_numbers.add(int(match.group(1)))

        # Recurse into season directory
        season_videos, _ = get_links_from_page(d_url)
        # We don't recurse deeper than one level of Season folders typically
        for v_url in season_videos:
            seas_str = get_season_name(v_url)
            all_videos.append({
                'url': v_url,
                'filename': get_filename_from_url(v_url),
                'season': seas_str 
            })
            
    return all_videos, season_numbers

def main():
    parser = argparse.ArgumentParser(description="Scrape video links from a URL and create an M3U playlist.")
    parser.add_argument("url", nargs='?', help="The URL of the website to scrape")
    parser.add_argument("-o", "--output", help="Output .m3u filename (optional)", default=None)
    parser.add_argument("--plus", action="store_true", help="Generate M3U Plus format with group titles")

    args = parser.parse_args()
    
    target_url = args.url
    is_m3u_plus = args.plus
    
    # Hybrid input mode
    if not target_url:
        try:
            target_url = input("Enter URL: ").strip()
            if not target_url:
                print("Error: No URL provided.")
                sys.exit(1)
            
            if not is_m3u_plus:
                format_resp = input("Output M3U Plus format? (y/N): ").lower().strip()
                if format_resp in ['y', 'yes']:
                    is_m3u_plus = True
                    
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)

    # Scrape
    print(f"\nStarting scrape on: {target_url}")
    video_items, season_numbers = crawl_recursive(target_url)

    if not video_items:
        print("No videos found.")
        sys.exit(0)

    # Season selection — only prompt when multiple seasons are detected
    if len(season_numbers) > 1:
        sorted_seasons = sorted(season_numbers)
        print(f"\nMultiple seasons found: {', '.join(f'Season {s}' for s in sorted_seasons)}")
        print("Enter season number(s) to include (comma-separated), or press Enter for ALL seasons:")
        try:
            season_choice = input("Season(s): ").strip()
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)

        if season_choice:
            chosen = set()
            for part in season_choice.split(','):
                part = part.strip()
                if part.isdigit():
                    chosen.add(int(part))

            invalid = chosen - season_numbers
            if invalid:
                print(f"Warning: Season(s) {sorted(invalid)} not found. Ignoring.")
                chosen -= invalid

            if chosen:
                video_items = [
                    item for item in video_items
                    if item.get('season')
                    and (m := re.search(r'\d+', item['season']))
                    and int(m.group(0)) in chosen
                ]
                season_numbers = chosen

                if not video_items:
                    print("No videos found for the selected season(s).")
                    sys.exit(0)
                print(f"Filtered to Season(s): {', '.join(str(s) for s in sorted(chosen))}")

    # Sort
    # We sort by filename naturally. S01E01 will parse correctly with natural_sort_key.
    video_items.sort(key=natural_sort_key)

    # Output Filename Logic
    output_path = args.output
    if not output_path:
        # 1. Clean Show Name
        show_name = get_clean_show_name(target_url)
        
        # 2. Season Range
        season_suffix = ""
        if season_numbers:
            min_s = min(season_numbers)
            max_s = max(season_numbers)
            if min_s == max_s:
                season_suffix = f"-Season-{min_s}"
            else:
                season_suffix = f"-Season-{min_s}-to-{max_s}"
        
        ext = "_plus.m3u" if is_m3u_plus else ".m3u"
        output_path = f"{show_name}{season_suffix}{ext}"

    generate_m3u(video_items, output_path, is_m3u_plus)

if __name__ == "__main__":
    main()
