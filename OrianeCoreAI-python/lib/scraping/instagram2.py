import requests
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.instagram.com/",
}

def get_instagram_shortcode(url: str) -> str:
    """
    Extract the shortcode from an Instagram URL or return it directly if it's already a shortcode.
    
    Args:
      url (str): The Instagram URL or shortcode.
    
    Returns:
      str: The extracted shortcode or None if invalid.
    """
    try:
        if "http" in url:
            if "instagram.com" not in url or "/reel/" not in url:
                print("Invalid Instagram URL")
                return None
            parts = url.rstrip("/").split("/")
            if len(parts) >= 2:
                return parts[-1]
        return url  # If it's already a shortcode, return it
    except Exception as e:
        print(f"Error extracting shortcode: {e}")
        return None

def get_instagram_reel(url_or_shortcode: str, timeout=10):
    """
    Fetch the Instagram reel video URL by scraping the webpage.
    
    Args:
        url_or_shortcode (str): The Instagram reel URL or shortcode.
        timeout (int): Timeout for the request.
    
    Returns:
        str: The direct video URL if found, otherwise None.
    """
    shortcode = get_instagram_shortcode(url_or_shortcode)
    if not shortcode:
        print("Invalid shortcode")
        return None

    reel_url = f"https://www.instagram.com/reel/{shortcode}/"

    try:
        response = requests.get(reel_url, headers=HEADERS, timeout=timeout)

        if response.status_code != 200:
            print(f"Failed to fetch Instagram page. Status code: {response.status_code}")
            return None

        html = response.text

        # Regex pattern to extract the video URL
        video_url_match = re.search(r'"video_url":"(https:[^"]+)"', html)

        if video_url_match:
            video_url = video_url_match.group(1).replace("\\u0026", "&")
            return video_url
        else:
            print("Failed to extract video URL. Instagram may have changed the structure.")
            return None

    except requests.RequestException as e:
        print(f"Error fetching Instagram reel: {e}")
        return None
