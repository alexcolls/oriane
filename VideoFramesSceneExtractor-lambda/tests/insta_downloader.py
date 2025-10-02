import json
import asyncio
import yt_dlp
import time
from pathlib import Path
from lib.logs import log, print_dict

class InstagramVideoDownloader:
  def __init__(self, download_dir: str = "videos", resolution: int = 720, debug: bool = False):
    """
    Initializes the downloader with a target resolution.

    :param download_dir: Directory where videos will be saved.
    :param resolution: Target resolution (e.g., 720, 1080).
    :param debug: If True, enables detailed logging.
    """
    self.download_dir = Path(download_dir)
    self.download_dir.mkdir(parents=True, exist_ok=True)
    self.resolution = resolution
    self.debug = debug

  async def download_video(self, shortcode: str):
    """
    Downloads an Instagrapip install --break-system-packages yt_dlp
m Reel with the specified resolution.

    :param shortcode: The Instagram Reel shortcode.
    :return: Filename if successful, or None if failed.
    """
    url = f"https://www.instagram.com/reel/{shortcode}/"
    output_template = str(self.download_dir / f"{shortcode}.%(ext)s")

    ydl_opts = {
      "quiet": not self.debug,  # Suppress output if debug is False
      "format": f"bv*[height={self.resolution}]+ba/b[height={self.resolution}]/b[ext=mp4]",  # Best match for resolution
      "outtmpl": output_template,
      "merge_output_format": "mp4",
    }
    loop = asyncio.get_event_loop()
    try:
      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        await loop.run_in_executor(None, ydl.download, [url])
      log(f"Downloaded: {shortcode}.mp4", level="info")
      return shortcode
    except Exception as e:
      log(f"Failed to download {shortcode}: {e}", level="error")
      return None

  async def download_instagram_videos(self, shortcodes: list[str]):
    """
    Downloads multiple Instagram Reels asynchronously.

    :param shortcodes: List of Instagram shortcodes.
    :return: Summary dictionary with success count, errors, and execution time.
    """
    start_time = time.time()

    tasks = [self.download_video(shortcode) for shortcode in shortcodes]
    results = await asyncio.gather(*tasks)

    total_videos = len(shortcodes)
    success = len([res for res in results if res is not None])
    errors = [shortcodes[i] for i, res in enumerate(results) if res is None]

    downloaded_in_secs = round(time.time() - start_time, 2)

    summary = {
      "total_videos": total_videos,
      "success": success,
      "errors": errors,
      "downloaded_in_secs": downloaded_in_secs
    }

    log(f"Download Summary: {summary}", level="info")
    return summary


if __name__ == "__main__":
  instagram_shortcodes = []
  with open('insta_downloader.json', 'r') as file:
    instagram_shortcodes = json.load(file)

  resolution = 480
  debug_mode = True

  monitored_downloader = InstagramVideoDownloader(download_dir="../videos", resolution=resolution, debug=debug_mode)

  async def download_both():
    # Create tasks to ensure they start in parallel
    monitored_task = asyncio.create_task(monitored_downloader.download_instagram_videos(instagram_shortcodes))
    # Wait for both tasks to complete
    monitored_summary, watched_summary = await asyncio.gather(monitored_task)
    return monitored_summary, watched_summary

  monitored_summary, watched_summary = asyncio.run(download_both())

  summary = {
    "monitored": monitored_summary,
    "watched": watched_summary
  }
  
  print_dict(summary)
