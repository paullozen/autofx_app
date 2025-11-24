import json
import os
import time
import re
import zipfile
from pathlib import Path
import googleapiclient.discovery
from dotenv import load_dotenv
from support_scripts.paths import COMMENTS_OUTPUT_DIR, OUTPUT_ROOT

# Carrega variáveis de ambiente do arquivo .env
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)
API_KEY = os.getenv("YT_API_KEY")

if not API_KEY:
    raise Exception("API Key not found in .env. Ensure you have YT_API_KEY=YOUR_TOKEN in the .env file.")

# Comments destination folder
COMMENTS_DIR = COMMENTS_OUTPUT_DIR
COMMENTS_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_INFO_DIR = OUTPUT_ROOT / "video_info"
VIDEO_INFO_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_COMMENTS_ZIP = OUTPUT_ROOT / "comentarios_coletados.zip"
GENERAL_INFO_COMMENT_LIMIT = 500

def get_channel_id_from_handle(api_key, handle):
    """Gets channel_id from channel @handle"""
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    request = youtube.search().list(
        part="snippet",
        q=handle,
        type="channel",
        maxResults=1
    )
    response = request.execute()

    if 'items' in response and len(response['items']) > 0:
        return response['items'][0]['id']['channelId']
    else:
        raise Exception("Não foi possível encontrar o canal para o handle fornecido.")

def get_channel_video_ids(api_key, channel_id, max_results=None, order_by_popularity=False):
    """
    Gets channel video IDs. If max_results is None, returns as many as possible.
    """
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    video_ids = []
    next_page_token = None

    while True:
        if max_results is not None:
            remaining = max_results - len(video_ids)
            if remaining <= 0:
                break
            request_max = min(50, remaining)
        else:
            request_max = 50

        request = youtube.search().list(
            part="id",
            type="video",
            channelId=channel_id,
            maxResults=request_max,
            order="viewCount" if order_by_popularity else "date",
            pageToken=next_page_token
        )
        response = request.execute()

        items = response.get('items', [])
        for item in items:
            video_id = item.get('id', {}).get('videoId')
            if video_id:
                video_ids.append(video_id)

        if not items:
            break

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return video_ids

def clean_comment(comment):
    """Removes HTML links and special characters/emoji from comment"""
    comment = re.sub(r'<a href=".*?">.*?</a>', '', comment)
    return strip_special_characters(comment)


def strip_special_characters(text: str) -> str:
    """Eliminates emojis and symbols outside basic ASCII"""
    ascii_text = text.encode("ascii", "ignore").decode("ascii", "ignore")
    ascii_text = ascii_text.replace("\r", " ").replace("\n", " ")
    ascii_text = re.sub(r"[^A-Za-z0-9 .,!?;:'\"()\-]", "", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()

def get_video_title(api_key, video_id):
    """Gets video title"""
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    request = youtube.videos().list(part="snippet", id=video_id)
    response = request.execute()
    if response['items']:
        return response['items'][0]['snippet']['title']
    return video_id  # fallback if title not found

def sanitize_filename(name):
    """Removes invalid characters from filenames"""
    return re.sub(r'[\\/*?:"<>|]', "", name)


def chunk_list(items, chunk_size=50):
    """Split a list into smaller chunks"""
    for idx in range(0, len(items), chunk_size):
        yield items[idx : idx + chunk_size]


def normalize_toon_value(value: str | int | float | None) -> str:
    """Sanitize values for Token-Oriented-Object Notation output."""
    if value is None:
        return ""
    text = str(value)
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace(",", ";")


def build_toon_block(label: str, rows: list[dict], fields: list[str]) -> str:
    """Builds a TOON block with header and data rows."""
    header = f"{label}[{len(rows)}]{{{','.join(fields)}}}:"
    lines = [header]
    for row in rows:
        values = [normalize_toon_value(row.get(field, "")) for field in fields]
        lines.append("  " + ",".join(values))
    return "\n".join(lines)


def fetch_video_comments(api_key, video_id, max_results=GENERAL_INFO_COMMENT_LIMIT):
    """Returns a list of cleaned comments for a video."""
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    comments: list[str] = []
    next_page_token = None

    while len(comments) < max_results:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(100, max_results - len(comments)),
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response.get('items', []):
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(clean_comment(comment))
            if len(comments) >= max_results:
                break

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return comments


def get_videos_public_info(api_key, video_ids):
    """Fetches public info (snippet/statistics) of videos"""
    if not video_ids:
        return []

    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    info_map = {}

    for chunk in chunk_list(video_ids, 50):
        request = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(chunk)
        )
        response = request.execute()

        for item in response.get('items', []):
            snippet = item.get('snippet', {})
            statistics = item.get('statistics', {})
            content_details = item.get('contentDetails', {})
            video_id = item.get('id')

            info_map[video_id] = {
                "id": video_id,
                "title": snippet.get('title', 'Untitled'),
                "description": snippet.get('description', '').strip(),
                "published_at": snippet.get('publishedAt', ''),
                "channel_title": snippet.get('channelTitle', ''),
                "duration": content_details.get('duration', ''),
                "view_count": statistics.get('viewCount', '0'),
                "like_count": statistics.get('likeCount', '0'),
                "comment_count": statistics.get('commentCount', '0'),
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }

    return [info_map[video_id] for video_id in video_ids if video_id in info_map]


def save_video_info_files(handle, videos_info):
    """Saves public info in TOON and JSON."""
    if not videos_info:
        raise ValueError("videos_info must contain at least one item")

    sanitized_handle = sanitize_filename(handle.lstrip("@")) or "canal"
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    toon_file = VIDEO_INFO_DIR / f"{sanitized_handle}_toon_{timestamp}.txt"
    json_file = VIDEO_INFO_DIR / f"{sanitized_handle}_{timestamp}.json"

    toon_video_fields = [
        "title",
        "channel_title",
        "published_at",
        "duration",
        "view_count",
        "like_count",
        "comment_count",
        "description",
    ]

    video_rows = [
        {field: info.get(field, "") for field in toon_video_fields}
        for info in videos_info
    ]

    comment_rows = []
    for video_index, info in enumerate(videos_info, start=1):
        for comment_text in info.get("comments", []):
            comment_rows.append(
                {
                    "video_index": video_index,
                    "comment": comment_text,
                }
            )

    videos_block = build_toon_block("videos", video_rows, toon_video_fields)
    comments_block = build_toon_block("comments", comment_rows, ["video_index", "comment"])

    with open(toon_file, "w", encoding="utf-8") as f:
        f.write(f"canal{{handle,video_count}}:\n  {normalize_toon_value(handle)},{len(videos_info)}\n")
        f.write(videos_block + "\n")
        f.write(comments_block + "\n")

    payload = {
        "channel_handle": handle,
        "video_count": len(videos_info),
        "videos": videos_info,
    }
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return toon_file, json_file

def get_video_comments(api_key, video_id, max_results=5000):
    """Gets comments from a video, numbers them and saves with title"""
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    next_page_token = None

    # Fetches video title
    title = get_video_title(api_key, video_id)
    safe_title = sanitize_filename(title)
    output_file = COMMENTS_DIR / f"{safe_title}.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        index = 1
        total_saved = 0
        while total_saved < max_results:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(100, max_results - total_saved),
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                cleaned_comment = clean_comment(comment)
                f.write(f"{index}. {cleaned_comment}\n\n")
                index += 1
                total_saved += 1

                if total_saved >= max_results:
                    break

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

    return output_file, total_saved, title

def extract_video_id(video_input):
    """Extracts video_id from different URL formats"""
    if re.fullmatch(r"^[a-zA-Z0-9_-]{11}$", video_input):
        return video_input
    
    match = re.search(r"(?:v=|\/)([a-zA-Z0-9_-]{11})", video_input)
    if match:
        return match.group(1)

    return None

def zip_files(file_list, zip_filename: str | Path = DEFAULT_COMMENTS_ZIP):
    """Creates a single ZIP file containing all collected files"""
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for file in file_list:
            zipf.write(file)
    return zip_filename

if __name__ == "__main__":
    modo = input("Choose collection mode | Channel (c); Video (v): ").strip().lower()

    if modo == "c":
        handle = input("Enter channel @handle: ").strip()
        order_choice = input("Order by popularity? (y/N): ").strip().lower()
        order_by_popularity = order_choice == "y"
        coleta_tipo = input("Collect general info (g) or comments (c)? ").strip().lower()

        if coleta_tipo not in {"g", "c"}:
            raise SystemExit("Invalid option! Use 'g' for general info or 'c' for comments.")

        max_videos_input = input("Number of videos to collect (Enter for max available): ").strip()
        max_videos = int(max_videos_input) if max_videos_input else None
        max_comments = None
        if coleta_tipo == "c":
            max_comments = int(input("Number of comments per video: "))

        print(f"Fetching channel ID for {handle}...")
        channel_id = get_channel_id_from_handle(API_KEY, handle)
        print(f"Channel ID found: {channel_id}")

        print("Fetching channel videos...")
        video_ids = get_channel_video_ids(API_KEY, channel_id, max_videos, order_by_popularity)
        if not video_ids:
            raise SystemExit("No videos found for the provided channel.")
        print(f"Videos collected: {video_ids}")

        if coleta_tipo == "g":
            print("Collecting public video info...")
            videos_info = get_videos_public_info(API_KEY, video_ids)
            if not videos_info:
                print("Could not get video info.")
            else:
                print("Collecting comments (max 500 per video)...")
                for index, info in enumerate(videos_info, start=1):
                    print(f"  Video {index}/{len(videos_info)}: {info['title']}")
                    info["comments"] = fetch_video_comments(API_KEY, info["id"], GENERAL_INFO_COMMENT_LIMIT)
                    time.sleep(1)
                toon_file, json_file = save_video_info_files(handle, videos_info)
                print(f"TOON info saved to: {toon_file}")
                print(f"JSON info saved to: {json_file}")
        else:
            arquivos = []
            for i, video_id in enumerate(video_ids):
                print(f"\n--- Video {i+1}/{len(video_ids)} ---")
                output_file, num_comments, title = get_video_comments(API_KEY, video_id, max_comments)
                arquivos.append(output_file)
                print(f"'{title}' → {num_comments} comments saved to {output_file}")
                time.sleep(2)

            print("\nCollection finished!")
            if arquivos:
                zip_filename = zip_files(arquivos)
                print(f"Files zipped to: {zip_filename}")

    elif modo in ["video", "v"]:
        video_input = input("Paste video link or ID only: ").strip()
        video_id = extract_video_id(video_input)

        if not video_id:
            print("Invalid URL or ID! Make sure it is in the correct format.")
        else:
            print(f"Video ID found: {video_id}")
            print("Starting comment collection...")
            output_file, num_comments, title = get_video_comments(API_KEY, video_id, 5000)
            print(f"'{title}' → {num_comments} comments saved to {output_file}")

    else:
        print("Invalid mode. Use 'c' for channel or 'v' for video.")
