from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import aiohttp
import asyncio
from urllib.parse import urlparse, parse_qs
import re
import json
import pytz

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# YouTube API configuration
YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']
YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class ChannelAnalysisRequest(BaseModel):
    channel_url: str
    video_count: Optional[int] = 20
    sort_order: Optional[str] = "newest"  # "newest" or "oldest"
    timezone: Optional[str] = "UTC"

class VideoInfo(BaseModel):
    id: str
    title: str
    upload_date: datetime
    upload_date_local: str
    upload_date_utc: str
    duration: str
    views: int
    likes: Optional[int] = 0
    comments: Optional[int] = 0
    engagement_rate: Optional[float] = 0.0
    time_gap_hours: Optional[float] = 0.0
    time_gap_text: Optional[str] = ""
    thumbnail_url: str
    category: str
    category_id: str

class ChannelInfo(BaseModel):
    id: str
    name: str
    creation_date: str
    subscriber_count: str
    total_views: int
    recent_views_30_days: int
    total_uploads: int
    primary_category: str
    monetization_status: str
    upload_frequency: Dict[str, Any]

class ChannelAnalysis(BaseModel):
    channel_info: ChannelInfo
    videos: List[VideoInfo]
    analysis_timestamp: datetime
    total_likes: int
    total_comments: int
    avg_views_per_video: float
    avg_likes_per_video: float

# Helper functions
def extract_channel_id_from_url(url: str) -> Optional[str]:
    """Extract channel ID from various YouTube URL formats"""
    patterns = [
        r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
        r'youtube\.com/c/([a-zA-Z0-9_-]+)',
        r'youtube\.com/user/([a-zA-Z0-9_-]+)',
        r'youtube\.com/@([a-zA-Z0-9_-]+)',
        r'youtu\.be/([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def format_number(num: int) -> str:
    """Format large numbers with K, M, B suffixes"""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)

def parse_duration(duration: str) -> str:
    """Parse ISO 8601 duration to readable format"""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return "0:00"
    
    hours, minutes, seconds = match.groups()
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0
    seconds = int(seconds) if seconds else 0
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def calculate_time_gap(current_date: datetime, previous_date: datetime) -> tuple:
    """Calculate time gap between two dates"""
    if not previous_date:
        return 0.0, ""
    
    diff = previous_date - current_date
    total_hours = diff.total_seconds() / 3600
    
    if total_hours < 24:
        return total_hours, f"{int(total_hours)} hours"
    else:
        days = int(total_hours // 24)
        remaining_hours = int(total_hours % 24)
        if remaining_hours > 0:
            return total_hours, f"{days} day{'s' if days != 1 else ''} {remaining_hours} hours"
        else:
            return total_hours, f"{days} day{'s' if days != 1 else ''}"

def detect_monetization(channel_data: dict, video_data: list) -> str:
    """Detect monetization status based on available data"""
    # Check for channel memberships, merch shelf, etc.
    monetization_indicators = 0
    
    # Check if channel has many videos with high engagement (likely monetized)
    if len(video_data) > 10:
        avg_views = sum(int(v.get('statistics', {}).get('viewCount', 0)) for v in video_data) / len(video_data)
        if avg_views > 10000:
            monetization_indicators += 1
    
    # Check subscriber count
    subscriber_count = int(channel_data.get('statistics', {}).get('subscriberCount', 0))
    if subscriber_count > 1000:
        monetization_indicators += 1
    
    if monetization_indicators >= 2:
        return "Likely Monetized"
    elif monetization_indicators == 1:
        return "Possibly Monetized"
    else:
        return "Unknown"

async def get_channel_by_handle_or_id(session: aiohttp.ClientSession, identifier: str) -> Optional[dict]:
    """Get channel data by handle or channel ID"""
    # Try as channel ID first
    url = f"{YOUTUBE_API_BASE_URL}/channels"
    params = {
        'part': 'snippet,statistics,topicDetails,brandingSettings',
        'id': identifier,
        'key': YOUTUBE_API_KEY
    }
    
    async with session.get(url, params=params) as response:
        if response.status == 200:
            data = await response.json()
            if data.get('items'):
                return data['items'][0]
    
    # Try as username
    params['forUsername'] = identifier
    del params['id']
    
    async with session.get(url, params=params) as response:
        if response.status == 200:
            data = await response.json()
            if data.get('items'):
                return data['items'][0]
    
    # Try to search for the channel
    search_url = f"{YOUTUBE_API_BASE_URL}/search"
    search_params = {
        'part': 'snippet',
        'q': identifier,
        'type': 'channel',
        'key': YOUTUBE_API_KEY
    }
    
    async with session.get(search_url, params=search_params) as response:
        if response.status == 200:
            data = await response.json()
            if data.get('items'):
                channel_id = data['items'][0]['snippet']['channelId']
                # Get full channel data
                return await get_channel_by_handle_or_id(session, channel_id)
    
    return None

async def get_channel_videos(session: aiohttp.ClientSession, channel_id: str, max_results: int = 50) -> List[dict]:
    """Get videos from a channel"""
    videos = []
    next_page_token = None
    
    while len(videos) < max_results:
        url = f"{YOUTUBE_API_BASE_URL}/search"
        params = {
            'part': 'snippet',
            'channelId': channel_id,
            'type': 'video',
            'order': 'date',
            'maxResults': min(50, max_results - len(videos)),
            'key': YOUTUBE_API_KEY
        }
        
        if next_page_token:
            params['pageToken'] = next_page_token
        
        async with session.get(url, params=params) as response:
            if response.status != 200:
                break
                
            data = await response.json()
            videos.extend(data.get('items', []))
            
            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break
    
    return videos[:max_results]

async def get_video_details(session: aiohttp.ClientSession, video_ids: List[str]) -> List[dict]:
    """Get detailed information for a list of video IDs"""
    video_details = []
    
    # Process videos in batches of 50 (YouTube API limit)
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i+50]
        url = f"{YOUTUBE_API_BASE_URL}/videos"
        params = {
            'part': 'snippet,statistics,contentDetails',
            'id': ','.join(batch_ids),
            'key': YOUTUBE_API_KEY
        }
        
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                video_details.extend(data.get('items', []))
    
    return video_details

async def get_video_categories(session: aiohttp.ClientSession, region_code: str = "US") -> Dict[str, str]:
    """Get YouTube video categories mapping"""
    url = f"{YOUTUBE_API_BASE_URL}/videoCategories"
    params = {
        'part': 'snippet',
        'regionCode': region_code,
        'key': YOUTUBE_API_KEY
    }
    
    async with session.get(url, params=params) as response:
        if response.status == 200:
            data = await response.json()
            categories = {}
            for item in data.get('items', []):
                category_id = item['id']
                category_title = item['snippet']['title']
                categories[category_id] = category_title
            return categories
        else:
            # Fallback categories for common IDs
            return {
                '1': 'Film & Animation',
                '2': 'Autos & Vehicles', 
                '10': 'Music',
                '15': 'Pets & Animals',
                '17': 'Sports',
                '19': 'Travel & Events',
                '20': 'Gaming',
                '22': 'People & Blogs',
                '23': 'Comedy',
                '24': 'Entertainment',
                '25': 'News & Politics',
                '26': 'Howto & Style',
                '27': 'Education',
                '28': 'Science & Technology'
            }

@api_router.post("/analyze-channel")
async def analyze_channel(request: ChannelAnalysisRequest):
    """Analyze a YouTube channel and return comprehensive data"""
    try:
        # Extract channel identifier from URL
        channel_identifier = extract_channel_id_from_url(request.channel_url)
        if not channel_identifier:
            raise HTTPException(status_code=400, detail="Invalid YouTube channel URL")
        
        async with aiohttp.ClientSession() as session:
            # Get channel information
            channel_data = await get_channel_by_handle_or_id(session, channel_identifier)
            if not channel_data:
                raise HTTPException(status_code=404, detail="Channel not found or is private")
            
            channel_id = channel_data['id']
            
            # Get channel videos
            videos_data = await get_channel_videos(session, channel_id, request.video_count)
            if not videos_data:
                raise HTTPException(status_code=404, detail="No videos found for this channel")
            
            # Get detailed video information
            video_ids = [video['id']['videoId'] for video in videos_data]
            video_details = await get_video_details(session, video_ids)
            
            # Process timezone
            user_timezone = pytz.timezone(request.timezone) if request.timezone != "UTC" else pytz.UTC
            
            # Process videos
            processed_videos = []
            previous_date = None
            
            # Sort videos by date
            video_details.sort(
                key=lambda x: x['snippet']['publishedAt'], 
                reverse=(request.sort_order == "newest")
            )
            
            total_likes = 0
            total_comments = 0
            recent_views_30_days = 0
            
            for video in video_details:
                # Parse upload date
                upload_date = datetime.fromisoformat(video['snippet']['publishedAt'].replace('Z', '+00:00'))
                
                # Convert to user timezone
                upload_date_local = upload_date.astimezone(user_timezone)
                upload_date_local_str = upload_date_local.strftime("%b %d, %Y, %I:%M %p")
                
                # Get statistics
                stats = video.get('statistics', {})
                views = int(stats.get('viewCount', 0))
                likes = int(stats.get('likeCount', 0))
                comments = int(stats.get('commentCount', 0))
                
                # Calculate engagement rate
                engagement_rate = (likes + comments) / views * 100 if views > 0 else 0
                
                # Calculate time gap from previous video
                time_gap_hours, time_gap_text = calculate_time_gap(upload_date, previous_date)
                
                # Check if video is from last 30 days
                if (datetime.now(timezone.utc) - upload_date).days <= 30:
                    recent_views_30_days += views
                
                processed_video = VideoInfo(
                    id=video['id'],
                    title=video['snippet']['title'],
                    upload_date=upload_date,
                    upload_date_local=upload_date_local_str,
                    duration=parse_duration(video['contentDetails']['duration']),
                    views=views,
                    likes=likes,
                    comments=comments,
                    engagement_rate=round(engagement_rate, 2),
                    time_gap_hours=round(time_gap_hours, 1),
                    time_gap_text=time_gap_text,
                    thumbnail_url=f"https://img.youtube.com/vi/{video['id']}/hqdefault.jpg"
                )
                
                processed_videos.append(processed_video)
                previous_date = upload_date
                total_likes += likes
                total_comments += comments
            
            # Process channel information
            channel_stats = channel_data.get('statistics', {})
            channel_snippet = channel_data['snippet']
            
            # Get primary category
            topic_details = channel_data.get('topicDetails', {})
            primary_category = "General"
            if topic_details and 'topicCategories' in topic_details:
                categories = topic_details['topicCategories']
                if categories:
                    # Extract category name from URL
                    category_url = categories[0]
                    primary_category = category_url.split('/')[-1].replace('_', ' ').title()
            
            # Detect monetization
            monetization_status = detect_monetization(channel_data, video_details)
            
            # Calculate upload frequency (simplified)
            upload_frequency = {
                "last_30_days": len([v for v in processed_videos if (datetime.now(timezone.utc) - v.upload_date).days <= 30]),
                "last_90_days": len([v for v in processed_videos if (datetime.now(timezone.utc) - v.upload_date).days <= 90])
            }
            
            # Create channel info
            channel_info = ChannelInfo(
                id=channel_id,
                name=channel_snippet['title'],
                creation_date=datetime.fromisoformat(channel_snippet['publishedAt'].replace('Z', '+00:00')).strftime("%b %d, %Y"),
                subscriber_count=format_number(int(channel_stats.get('subscriberCount', 0))),
                total_views=int(channel_stats.get('viewCount', 0)),
                recent_views_30_days=recent_views_30_days,
                total_uploads=int(channel_stats.get('videoCount', len(processed_videos))),
                primary_category=primary_category,
                monetization_status=monetization_status,
                upload_frequency=upload_frequency
            )
            
            # Create final analysis
            analysis = ChannelAnalysis(
                channel_info=channel_info,
                videos=processed_videos,
                analysis_timestamp=datetime.now(timezone.utc),
                total_likes=total_likes,
                total_comments=total_comments,
                avg_views_per_video=round(sum(v.views for v in processed_videos) / len(processed_videos)) if processed_videos else 0,
                avg_likes_per_video=round(total_likes / len(processed_videos)) if processed_videos else 0
            )
            
            return analysis
    
    except Exception as e:
        logging.error(f"Error analyzing channel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing channel: {str(e)}")

@api_router.get("/")
async def root():
    return {"message": "YouTube Channel Analyzer API"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()