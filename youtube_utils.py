import os
import json
import time
import subprocess
import urllib.parse
from datetime import datetime
from functools import wraps
import re

import googleapiclient.discovery
from googleapiclient.http import HttpError
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Constants ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# --- Session State Management ---
def init_session_state(st):
    """Initializes session state variables for API keys and clients."""
    if 'youtube_api_keys' not in st.session_state:
        st.session_state.youtube_api_keys = []
    if 'gemini_api_key' not in st.session_state:
        st.session_state.gemini_api_key = ""
    if 'current_api_key_index' not in st.session_state:
        st.session_state.current_api_key_index = 0
    if 'youtube_client' not in st.session_state:
        st.session_state.youtube_client = None
    if 'gspread_client' not in st.session_state:
        st.session_state.gspread_client = None
    if 'spreadsheet' not in st.session_state:
        st.session_state.spreadsheet = None
    if 'clients_initialized' not in st.session_state:
        st.session_state.clients_initialized = False

def initialize_clients(st):
    """Initializes YouTube client and stores it in session_state."""
    # Initialize YouTube client
    if st.session_state.get('youtube_api_keys'):
        current_key = st.session_state.youtube_api_keys[st.session_state.current_api_key_index]
        try:
            st.session_state.youtube_client = googleapiclient.discovery.build('youtube', 'v3', developerKey=current_key)
        except Exception as e:
            st.error(f"YouTube API 클라이언트 초기화 실패: {e}")
            st.session_state.youtube_client = None
    else:
        st.session_state.youtube_client = None

    # Gspread client initialization is no longer needed here.
    # It can be added back if some features require it.
    st.session_state.gspread_client = None
    st.session_state.spreadsheet = None

def switch_to_next_api_key(st):
    """Switches to the next available API key."""
    if not st.session_state.youtube_api_keys:
        st.warning("사용 가능한 API 키가 없습니다.")
        return False
    
    st.session_state.current_api_key_index = (st.session_state.current_api_key_index + 1) % len(st.session_state.youtube_api_keys)
    current_key = st.session_state.youtube_api_keys[st.session_state.current_api_key_index]
    
    try:
        st.session_state.youtube_client = googleapiclient.discovery.build('youtube', 'v3', developerKey=current_key)
        st.info(f"API 키 변경 완료. (인덱스: {st.session_state.current_api_key_index})")
        return True
    except Exception as e:
        st.error(f"API 클라이언트 생성 실패: {e}")
        return False

def with_api_quota_handling(func):
    """Decorator to handle YouTube API quota errors by switching keys."""
    @wraps(func)
    def wrapper(st, *args, **kwargs):
        max_retries = len(st.session_state.get('youtube_api_keys', []))
        for attempt in range(max_retries):
            try:
                return func(st, *args, **kwargs)
            except Exception as e:
                error_str = str(e)
                if "quota" in error_str.lower() or "exceeded" in error_str.lower():
                    st.warning(f"API 할당량 초과 감지. 다음 키로 전환합니다...")
                    if attempt < max_retries - 1:
                        if switch_to_next_api_key(st):
                            st.info(f"다음 API 키로 재시도 ({attempt+2}/{max_retries})")
                            continue
                        else:
                            st.error("다음 API 키로 전환 실패.")
                            break
                raise e
        # This part is reached if all retries fail
        st.error("모든 API 키의 할당량을 소진했거나 오류가 발생했습니다.")
        return None
    return wrapper

@with_api_quota_handling
def get_channel_id(st, channel_link):
    youtube = st.session_state.youtube_client
    if not youtube:
        st.error("YouTube 클라이언트가 초기화되지 않았습니다.")
        return None
    
    if '/channel/' in channel_link:
        return channel_link.split('/channel/')[1].split('/')[0]
    
    elif '/@' in channel_link:
        handle_encoded = channel_link.split('/@')[1].split('?')[0]
        handle = urllib.parse.unquote(handle_encoded)
        
        search_response = youtube.search().list(
            q=handle, type='channel', part='id,snippet', maxResults=5
        ).execute()
        
        items = search_response.get('items', [])
        for item in items:
            candidate_id = item['id'].get('channelId')
            # The search by handle can be inaccurate, so we verify with channel details
            channel_details_resp = youtube.channels().list(part='snippet', id=candidate_id).execute()
            if channel_details_resp.get('items'):
                snippet = channel_details_resp['items'][0]['snippet']
                # Check if customUrl or title matches the handle
                if snippet.get('customUrl', '').lower() == handle.lower() or snippet.get('title', '').lower() == handle.lower():
                    return candidate_id
        
        # If no exact match is found, return the first result as a fallback
        if items:
            return items[0]['id'].get('channelId')
        st.warning(f"핸들 '{handle}'에 해당하는 채널을 찾지 못했습니다.")
        return None

    else: # Treat as a channel name search
        search_response = youtube.search().list(
            q=channel_link, type='channel', part='id', maxResults=1
        ).execute()
        if search_response.get('items'):
            return search_response['items'][0]['id']['channelId']
            
    st.warning(f"채널 ID를 찾을 수 없습니다: {channel_link}")
    return None

def get_video_id(url):
    """Extracts video ID from a YouTube URL."""
    if "youtube.com/watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return None

def process_urls(st, urls, video_count, min_view_count, comment_count, script_numbering, comment_numbering, existing_video_ids=None):
    """Processes a list of URLs, with numbering options."""
    if existing_video_ids is None:
        existing_video_ids = set()
    else:
        existing_video_ids = set(existing_video_ids)

    all_results = []
    script_index = 1
    comment_index = 1
    
    for url in urls:
        video_id = get_video_id(url)
        if video_id:
            if video_id in existing_video_ids:
                continue # 이미 수집된 개별 영상은 건너뜁니다.
            with st.spinner(f"영상 처리 중: {url}"):
                video_info = get_video_details(st, video_id, comment_count)
                if video_info:
                    # Apply numbering if requested
                    if script_numbering and video_info["자막"] not in ["자막 없음", "자막 추출 오류"]:
                        video_info["자막"] = f"{script_index}. {video_info['자막']}"
                        script_index += 1
                    if comment_numbering and isinstance(video_info["댓글"], list):
                        numbered_comments = [f"{comment_index}.{i+1} {comment}" for i, comment in enumerate(video_info["댓글"])]
                        video_info["댓글"] = "\n".join(numbered_comments)
                        comment_index += 1
                    
                    all_results.append(video_info)
                    existing_video_ids.add(video_id) # 중복 처리를 위해 추가
        else: # Assume it's a channel URL or name
            with st.spinner(f"채널 처리 중: {url}"):
                channel_id = get_channel_id(st, url)
                if channel_id:
                    videos = get_latest_videos(st, channel_id, video_count, min_view_count, existing_video_ids=existing_video_ids)
                    for video in videos:
                        with st.spinner(f"영상 '{video['title']}' 처리 중..."):
                             video_info = get_video_details(st, video['videoId'], comment_count)
                             if video_info:
                                # Apply numbering if requested
                                if script_numbering and video_info["자막"] not in ["자막 없음", "자막 추출 오류"]:
                                    video_info["자막"] = f"{script_index}. {video_info['자막']}"
                                    script_index += 1
                                if comment_numbering and isinstance(video_info["댓글"], list):
                                    numbered_comments = [f"{comment_index}.{i+1} {comment}" for i, comment in enumerate(video_info["댓글"])]
                                    video_info["댓글"] = "\n".join(numbered_comments)
                                    comment_index += 1

                                all_results.append(video_info)
                                existing_video_ids.add(video['videoId']) # 중복 처리를 위해 추가
    return all_results

def get_video_details(st, video_id, comment_count):
    """Fetches all details for a single video."""
    youtube = st.session_state.youtube_client
    try:
        video_response = youtube.videos().list(
            id=video_id,
            part='snippet,statistics'
        ).execute()
        
        if not video_response.get('items'):
            st.warning(f"영상 정보를 가져올 수 없습니다: {video_id}")
            return None
            
        item = video_response['items'][0]
        title = item['snippet'].get('title', 'N/A')
        channel_title = item['snippet'].get('channelTitle', 'N/A')
        published_at = item['snippet'].get('publishedAt', '')
        view_count = item.get('statistics', {}).get('viewCount', 0)
        
        if published_at:
            dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            published_at = dt.strftime("%Y-%m-%d %H:%M:%S")

        transcript = get_video_transcript(st, video_id)
        comments = get_top_comments(st, video_id, comment_count)
        description = item['snippet'].get('description', '설명 없음')
        
        return {
            "채널명": channel_title,
            "제목": title,
            "영상 URL": f"https://www.youtube.com/watch?v={video_id}",
            "조회수": int(view_count),
            "게시일": published_at,
            "자막": transcript,
            "댓글": "\n".join(comments) if isinstance(comments, list) else comments,
            "설명": description
        }
    except Exception as e:
        st.error(f"영상({video_id}) 처리 중 오류: {e}")
        return None

@with_api_quota_handling
def get_latest_videos(st, channel_id, max_results, min_view_count, existing_video_ids=None):
    if existing_video_ids is None:
        existing_video_ids = set()
    else:
        existing_video_ids = set(existing_video_ids)

    youtube = st.session_state.youtube_client

    # 1. 채널 정보에서 업로드 플레이리스트 ID 가져오기
    try:
        channel_info = get_channel_info(st, channel_id)
        uploads_playlist_id = channel_info.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')
        if not uploads_playlist_id:
            st.error(f"채널의 업로드 목록을 찾을 수 없습니다: {channel_id}")
            return []
    except Exception as e:
        st.error(f"채널 정보를 가져오는 중 오류 발생: {e}")
        return []

    # 2. 플레이리스트를 페이지네이션하며 새로운 영상 찾기
    new_videos = []
    next_page_token = None
    
    # 충분한 새 영상을 찾거나 플레이리스트 끝에 도달할 때까지 반복
    while len(new_videos) < max_results:
        try:
            playlist_request = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=50,  # 페이지당 최대 50개
                pageToken=next_page_token
            )
            playlist_response = playlist_request.execute()
        except Exception as e:
            st.error(f"플레이리스트 항목을 가져오는 중 오류 발생: {e}")
            break

        playlist_items = playlist_response.get("items", [])
        if not playlist_items:
            break  # 플레이리스트에 더 이상 영상이 없음

        # 현재 페이지의 영상 ID 목록 추출
        video_ids_on_page = [
            item.get("snippet", {}).get("resourceId", {}).get("videoId")
            for item in playlist_items if item.get("snippet", {}).get("resourceId", {}).get("kind") == "youtube#video"
        ]
        video_ids_on_page = [vid_id for vid_id in video_ids_on_page if vid_id]

        # 이미 수집된 ID 제외
        ids_to_check = [vid_id for vid_id in video_ids_on_page if vid_id not in existing_video_ids]

        if ids_to_check:
            # 3. 새로운 영상 ID의 통계 정보를 가져와 조회수 필터링
            try:
                video_response = youtube.videos().list(
                    id=','.join(ids_to_check),
                    part='statistics,snippet'
                ).execute()
                video_items = video_response.get('items', [])
            except Exception as e:
                st.warning(f"영상 통계 정보를 가져오는 중 오류 발생: {e}")
                video_items = []

            for item in video_items:
                view_count = int(item.get('statistics', {}).get('viewCount', 0))
                if view_count >= min_view_count:
                    new_videos.append({
                        'videoId': item.get('id'),
                        'title': item.get('snippet', {}).get('title', 'No Title'),
                        'viewCount': view_count
                    })
                    if len(new_videos) >= max_results:
                        break  # 요청한 개수를 채웠으면 중단

        if len(new_videos) >= max_results:
            break

        # 4. 다음 페이지 토큰 확인
        next_page_token = playlist_response.get("nextPageToken")
        if not next_page_token:
            break  # 플레이리스트의 끝

    return new_videos[:max_results]

@with_api_quota_handling
def get_top_comments(st, video_id, max_results):
    youtube = st.session_state.youtube_client
    try:
        comment_response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            order="relevance",
            textFormat="plainText",
            maxResults=max_results
        ).execute()
        
        comments = [item["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for item in comment_response.get("items", [])]
        return comments if comments else "댓글 없음"
    except Exception as e:
        st.warning(f"댓글을 가져오는 중 오류 발생: {e}")
        return "댓글 가져오기 실패"

def get_video_transcript(st, video_id, lang='ko'):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    temp_filename_base = f"temp_sub_{video_id}_{int(time.time())}"
    output_template = f"{temp_filename_base}.%(ext)s"
    subtitle_path = ""

    try:
        command = ['yt-dlp', '--skip-download', '--write-sub', '--write-auto-sub', '--sub-format', 'vtt', '--sub-lang', lang, '-o', output_template, video_url]
        
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', startupinfo=startupinfo)

        subtitle_path = f"{temp_filename_base}.{lang}.vtt"
        if not os.path.exists(subtitle_path):
             subtitle_path_alt = f"{temp_filename_base}.vtt"
             if os.path.exists(subtitle_path_alt):
                 subtitle_path = subtitle_path_alt
             else:
                return "자막 없음"

        with open(subtitle_path, 'r', encoding='utf-8') as f:
            vtt_content = f.read()

        lines = vtt_content.splitlines()
        transcript_lines = [re.sub(r'<[^>]+>', '', line).strip() for line in lines if '-->' not in line and line.strip() and not line.strip().isdigit() and not line.upper().startswith(('WEBVTT', 'KIND:', 'LANGUAGE:'))]
        
        unique_lines = []
        for line in transcript_lines:
            if not unique_lines or unique_lines[-1] != line:
                unique_lines.append(line)

        return "\n".join(unique_lines) if unique_lines else "자막 없음"

    except Exception as e:
        st.error(f"yt-dlp 실행 중 오류: {e}")
        return "자막 추출 오류"
    finally:
        if subtitle_path and os.path.exists(subtitle_path):
            os.remove(subtitle_path)

@with_api_quota_handling
def get_channel_info(st, channel_id):
    youtube = st.session_state.youtube_client
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=channel_id
    )
    response = request.execute()
    return response.get("items", [{}])[0]

@with_api_quota_handling
def get_uploaded_videos_playlist(st, uploads_playlist_id):
    youtube = st.session_state.youtube_client
    videos = []
    next_page_token = None
    while True:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        videos.extend(response.get("items", []))
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    return videos

def analyze_upload_patterns(videos):
    """Analyzes upload time patterns using pandas."""
    import pandas as pd
    from datetime import timedelta, timezone

    if not videos:
        return {}

    dates = []
    for video in videos:
        published_at_str = video.get("snippet", {}).get("publishedAt")
        if published_at_str:
            try:
                dt_utc = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                dates.append(dt_utc)
            except ValueError:
                continue # Skip if date format is wrong
    
    if not dates:
        return {}

    df = pd.DataFrame(dates, columns=["date_utc"])
    df["date_kst"] = df["date_utc"] + timedelta(hours=9)

    df["weekday"] = df["date_kst"].dt.weekday
    df["hour"] = df["date_kst"].dt.hour

    weekday_map = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}
    weekday_counts = df["weekday"].map(weekday_map).value_counts().reindex(["월", "화", "수", "목", "금", "토", "일"], fill_value=0)
    hourly_counts = df["hour"].value_counts().reindex(range(24), fill_value=0)
    
    return {"weekday": weekday_counts, "hourly": hourly_counts}

# ... (Remove old functions that read from sheets like run_process, process_video_links)

# ... (Other functions like get_latest_videos, get_transcript_with_yt_dlp, etc. will be moved here and adapted)
# They should take 'st' as the first argument to access session_state and UI elements. 
