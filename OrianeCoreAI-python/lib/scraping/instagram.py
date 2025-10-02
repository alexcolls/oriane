import os
import time
import json
import logging
import requests
import tempfile
import subprocess
from instaloader import Instaloader, Post
from env import DEBUG

# Configure logging.
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Optional logging: disable if DISABLE_LOGS env var is "1"
if not DEBUG:
    logger.disabled = True

# Use an absolute path for the cookies file (in the same directory as this module)
COOKIES_FILE = os.path.join(os.getcwd(), "instagram_cookies.json")

# Credentials (adjust as needed or source from environment variables)
EMAIL = "beenzer.app@gmail.com"
USERNAME = "beenzer_app"  # Not used here but retained for clarity.
PASSWORD = "BeenzerApp23!"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.5735.110 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

session = requests.Session()
insta_loader = Instaloader()


def save_cookies():
    """Save Instagram session cookies to the absolute cookies file."""
    try:
        with open(COOKIES_FILE, "w") as f:
            json.dump(session.cookies.get_dict(), f)
        logger.info("Cookies saved successfully.")
    except Exception as e:
        logger.error(f"Error saving cookies: {e}")


def load_cookies():
    """Load Instagram session cookies from the absolute cookies file."""
    if os.path.exists(COOKIES_FILE):
        try:
            with open(COOKIES_FILE, "r") as f:
                cookies = json.load(f)
            session.cookies.update(cookies)
            logger.info("Loaded Instagram cookies from: " + COOKIES_FILE)
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
    else:
        logger.warning("No cookies file found at " + COOKIES_FILE + ". Attempting login...")


def login_instagram():
    """Log in to Instagram using requests and save session cookies."""
    login_url = "https://www.instagram.com/accounts/login/ajax/"
    timestamp = int(time.time())
    payload = {
        "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{timestamp}:{PASSWORD}",
        "username": EMAIL,  # Using email as username.
        "queryParams": "{}",
        "optIntoOneTap": "false",
    }
    session.headers.update(HEADERS)
    session.headers.update({"X-CSRFToken": "missing"})

    try:
        session.get("https://www.instagram.com/", timeout=10)
        csrf_token = session.cookies.get("csrftoken", "")
        session.headers.update({"X-CSRFToken": csrf_token})
    except Exception as e:
        logger.error(f"Error obtaining CSRF token: {e}")
        return False

    try:
        response = session.post(login_url, data=payload, headers=session.headers, timeout=10)
        resp_json = response.json()
        if response.status_code == 200 and resp_json.get("authenticated"):
            logger.info("Login successful!")
            save_cookies()
            return True
        else:
            logger.error(f"Login failed: {resp_json}")
            return False
    except Exception as e:
        logger.error(f"Exception during login: {e}")
        return False


def reencode_video(input_file: str, output_file: str) -> bool:
    """
    Use ffmpeg with error-resilient flags to re-encode a video.
    Returns True if re-encoding succeeds.
    """
    command = [
        "ffmpeg",
        "-y",
        "-err_detect", "ignore_err",
        "-i", input_file,
        "-c", "copy",
        output_file,
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        logger.info("Re-encoding succeeded.")
        return True
    else:
        logger.error(f"Re-encoding failed: {result.stderr.decode()}")
        return False


def validate_video_content(video_content: bytes, min_size: int = 10000) -> bytes | None:
    """
    Validate that the video content is sufficiently large and can be opened with OpenCV.
    If not, attempt to re-encode it using ffmpeg.
    Returns validated video bytes or None if validation fails.
    """
    if len(video_content) < min_size:
        logger.warning("Video content too small; possibly invalid.")
        return None

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_in:
        tmp_in.write(video_content)
        tmp_in.flush()
        input_file = tmp_in.name

    try:
        import cv2
        cap = cv2.VideoCapture(input_file)
        if cap.isOpened():
            cap.release()
            os.remove(input_file)
            return video_content  # Valid video.
        cap.release()
    except Exception as e:
        logger.error(f"Exception during OpenCV validation: {e}")

    # If video failed validation, attempt re-encoding.
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_out:
        output_file = tmp_out.name

    if reencode_video(input_file, output_file):
        try:
            with open(output_file, "rb") as f:
                reencoded_content = f.read()
            os.remove(input_file)
            os.remove(output_file)
            logger.info("Re-encoded video successfully validated.")
            return reencoded_content
        except Exception as e:
            logger.error(f"Error reading re-encoded file: {e}")
    else:
        logger.error("Re-encoding failed; video remains invalid.")
    os.remove(input_file)
    if os.path.exists(output_file):
        os.remove(output_file)
    return None


def get_instagram_reel(shortcode: str, timeout: int = 10) -> bytes | None:
    """
    Fetch Instagram reel video content using session cookies and Instaloader.
    Returns validated video bytes if successful, or None otherwise.
    """
    load_cookies()

    try:
        logger.info(f"Fetching Instagram post: {shortcode}...")
        response = session.get(f"https://www.instagram.com/p/{shortcode}/", headers=HEADERS, timeout=timeout)
        if response.status_code == 403:
            logger.error("Access Denied. Session may be invalid. Try reloading cookies.")
            return None
        elif response.status_code != 200:
            logger.error(f"Failed to access Instagram post: HTTP {response.status_code}")
            return None

        logger.info("Successfully accessed Instagram post. Extracting video URL...")
        post = Post.from_shortcode(insta_loader.context, shortcode)
        if not post.is_video:
            logger.warning(f"[{shortcode}] This post is not a video.")
            return None

        video_url = post.video_url
        logger.info(f"Found video URL: {video_url}")

        video_response = session.get(video_url, headers=HEADERS, timeout=timeout)
        if video_response.status_code == 200:
            logger.info(f"Successfully fetched video for shortcode: {shortcode} (size: {len(video_response.content)} bytes)")
            validated_video = validate_video_content(video_response.content)
            if validated_video is None:
                logger.error(f"Validation failed for video {shortcode}")
            return validated_video
        else:
            logger.error(f"Failed to fetch video. HTTP {video_response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching video for {shortcode}: {e}")
    return None


def get_instagram_shortcode(url: str) -> str | None:
    """
    Extract the shortcode from an Instagram URL.
    If the URL is a full Instagram URL, extract the shortcode; otherwise,
    assume the input is already the shortcode.
    """
    try:
        if "http" in url and "instagram.com" in url:
            # Support both 'reel' and 'p' style URLs.
            if "reel" in url:
                return url.rstrip("/").split("/")[-1]
            elif "/p/" in url:
                return url.rstrip("/").split("/")[-1]
        return url
    except Exception as e:
        logger.error(f"Error extracting shortcode from URL {url}: {e}")
    return None


if __name__ == "__main__":
    # For testing purposes, replace with a valid shortcode.
    test_shortcode = "C1t-cMpMasZ"
    video_data = get_instagram_reel(test_shortcode)
    if video_data:
        logger.info(f"Fetched and validated video data of size: {len(video_data)} bytes")
    else:
        logger.error("Failed to fetch a valid video.")
