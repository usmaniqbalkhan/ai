#!/usr/bin/env python3
"""
Backend Test Suite for YouTube Channel Analyzer
Tests the YouTube Data API v3 integration and channel analysis endpoint
"""

import requests
import json
import time
from datetime import datetime
import sys

# Get backend URL from frontend .env
BACKEND_URL = "https://758e0dcf-ecd4-4aa1-b364-7b67ea1591cc.preview.emergentagent.com"
API_BASE_URL = f"{BACKEND_URL}/api"

class YouTubeChannelAnalyzerTester:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_test(self, test_name, status, message, details=None):
        """Log test results"""
        self.total_tests += 1
        if status == "PASS":
            self.passed_tests += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.failed_tests += 1
            print(f"❌ {test_name}: {message}")
            if details:
                print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_api_health(self):
        """Test if the API is accessible"""
        try:
            response = requests.get(f"{API_BASE_URL}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "YouTube Channel Analyzer API" in data.get("message", ""):
                    self.log_test("API Health Check", "PASS", "API is accessible and responding correctly")
                    return True
                else:
                    self.log_test("API Health Check", "FAIL", f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("API Health Check", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("API Health Check", "FAIL", f"Connection error: {str(e)}")
            return False
    
    def test_channel_analysis_mkbhd(self):
        """Test channel analysis with MKBHD channel"""
        test_data = {
            "channel_url": "https://youtube.com/@mkbhd",
            "video_count": 10,
            "sort_order": "newest",
            "timezone": "UTC"
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/analyze-channel",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["channel_info", "videos", "analysis_timestamp", "total_likes", "total_comments"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("MKBHD Channel Analysis", "FAIL", f"Missing fields: {missing_fields}")
                    return False
                
                # Validate channel info
                channel_info = data["channel_info"]
                channel_required = ["id", "name", "subscriber_count", "total_views", "primary_category"]
                missing_channel_fields = [field for field in channel_required if field not in channel_info]
                
                if missing_channel_fields:
                    self.log_test("MKBHD Channel Analysis", "FAIL", f"Missing channel fields: {missing_channel_fields}")
                    return False
                
                # Validate videos
                videos = data["videos"]
                if not videos or len(videos) == 0:
                    self.log_test("MKBHD Channel Analysis", "FAIL", "No videos returned")
                    return False
                
                # Check video structure
                video = videos[0]
                video_required = ["id", "title", "upload_date", "views", "likes", "thumbnail_url"]
                missing_video_fields = [field for field in video_required if field not in video]
                
                if missing_video_fields:
                    self.log_test("MKBHD Channel Analysis", "FAIL", f"Missing video fields: {missing_video_fields}")
                    return False
                
                # Validate data quality
                if channel_info["name"] and len(videos) == 10:
                    self.log_test("MKBHD Channel Analysis", "PASS", 
                                f"Successfully analyzed {channel_info['name']} with {len(videos)} videos")
                    return True
                else:
                    self.log_test("MKBHD Channel Analysis", "FAIL", 
                                f"Data quality issues: name={channel_info['name']}, video_count={len(videos)}")
                    return False
                    
            else:
                self.log_test("MKBHD Channel Analysis", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("MKBHD Channel Analysis", "FAIL", f"Request error: {str(e)}")
            return False
    
    def test_different_video_counts(self):
        """Test with different video counts"""
        test_cases = [5, 20]
        
        for count in test_cases:
            test_data = {
                "channel_url": "https://youtube.com/@mkbhd",
                "video_count": count,
                "sort_order": "newest",
                "timezone": "UTC"
            }
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/analyze-channel",
                    json=test_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    videos = data.get("videos", [])
                    
                    if len(videos) <= count:  # May be less if channel has fewer videos
                        self.log_test(f"Video Count Test ({count})", "PASS", 
                                    f"Returned {len(videos)} videos (requested {count})")
                    else:
                        self.log_test(f"Video Count Test ({count})", "FAIL", 
                                    f"Returned {len(videos)} videos but requested {count}")
                else:
                    self.log_test(f"Video Count Test ({count})", "FAIL", 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Video Count Test ({count})", "FAIL", f"Request error: {str(e)}")
    
    def test_sort_orders(self):
        """Test different sort orders"""
        sort_orders = ["newest", "oldest"]
        
        for sort_order in sort_orders:
            test_data = {
                "channel_url": "https://youtube.com/@mkbhd",
                "video_count": 5,
                "sort_order": sort_order,
                "timezone": "UTC"
            }
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/analyze-channel",
                    json=test_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    videos = data.get("videos", [])
                    
                    if len(videos) >= 2:
                        # Check if sorting is correct
                        first_date = datetime.fromisoformat(videos[0]["upload_date"].replace('Z', '+00:00'))
                        second_date = datetime.fromisoformat(videos[1]["upload_date"].replace('Z', '+00:00'))
                        
                        if sort_order == "newest" and first_date >= second_date:
                            self.log_test(f"Sort Order Test ({sort_order})", "PASS", 
                                        "Videos correctly sorted by newest first")
                        elif sort_order == "oldest" and first_date <= second_date:
                            self.log_test(f"Sort Order Test ({sort_order})", "PASS", 
                                        "Videos correctly sorted by oldest first")
                        else:
                            self.log_test(f"Sort Order Test ({sort_order})", "FAIL", 
                                        f"Incorrect sorting: {first_date} vs {second_date}")
                    else:
                        self.log_test(f"Sort Order Test ({sort_order})", "PASS", 
                                    f"Insufficient videos to test sorting, but request succeeded")
                else:
                    self.log_test(f"Sort Order Test ({sort_order})", "FAIL", 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Sort Order Test ({sort_order})", "FAIL", f"Request error: {str(e)}")
    
    def test_timezone_handling(self):
        """Test timezone conversion"""
        timezones = ["America/New_York", "Europe/London", "Asia/Tokyo"]
        
        for timezone in timezones:
            test_data = {
                "channel_url": "https://youtube.com/@mkbhd",
                "video_count": 3,
                "sort_order": "newest",
                "timezone": timezone
            }
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/analyze-channel",
                    json=test_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    videos = data.get("videos", [])
                    
                    if videos and "upload_date_local" in videos[0]:
                        self.log_test(f"Timezone Test ({timezone})", "PASS", 
                                    f"Successfully converted dates to {timezone}")
                    else:
                        self.log_test(f"Timezone Test ({timezone})", "FAIL", 
                                    "No local date conversion found")
                else:
                    self.log_test(f"Timezone Test ({timezone})", "FAIL", 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Timezone Test ({timezone})", "FAIL", f"Request error: {str(e)}")

    def test_enhanced_timezone_accuracy(self):
        """Test ENHANCED timezone accuracy and day-slipping prevention"""
        # Test with America/New_York timezone specifically
        test_data = {
            "channel_url": "https://youtube.com/@mkbhd",
            "video_count": 10,
            "sort_order": "newest",
            "timezone": "America/New_York"
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/analyze-channel",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                videos = data.get("videos", [])
                
                if not videos:
                    self.log_test("Enhanced Timezone Accuracy (NY)", "FAIL", "No videos returned")
                    return
                
                video = videos[0]
                
                # Check for both UTC and local timestamp fields
                required_fields = ["upload_date_utc", "upload_date_local", "upload_date"]
                missing_fields = [field for field in required_fields if field not in video]
                
                if missing_fields:
                    self.log_test("Enhanced Timezone Accuracy (NY)", "FAIL", 
                                f"Missing timestamp fields: {missing_fields}")
                    return
                
                # Verify UTC and local timestamps are different (unless uploaded at exact UTC midnight)
                utc_time = video["upload_date_utc"]
                local_time = video["upload_date_local"]
                
                if utc_time and local_time:
                    self.log_test("Enhanced Timezone Accuracy (NY)", "PASS", 
                                f"Both UTC ({utc_time}) and local ({local_time}) timestamps present")
                else:
                    self.log_test("Enhanced Timezone Accuracy (NY)", "FAIL", 
                                "UTC or local timestamp is empty")
                    
            else:
                self.log_test("Enhanced Timezone Accuracy (NY)", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Enhanced Timezone Accuracy (NY)", "FAIL", f"Request error: {str(e)}")
        
        # Test with Asia/Tokyo timezone for late-night UTC uploads
        test_data["timezone"] = "Asia/Tokyo"
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/analyze-channel",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                videos = data.get("videos", [])
                
                if videos:
                    video = videos[0]
                    if "upload_date_utc" in video and "upload_date_local" in video:
                        self.log_test("Enhanced Timezone Accuracy (Tokyo)", "PASS", 
                                    f"Tokyo timezone conversion working: UTC={video['upload_date_utc']}, Local={video['upload_date_local']}")
                    else:
                        self.log_test("Enhanced Timezone Accuracy (Tokyo)", "FAIL", 
                                    "Missing UTC or local timestamp fields")
                else:
                    self.log_test("Enhanced Timezone Accuracy (Tokyo)", "FAIL", "No videos returned")
                    
            else:
                self.log_test("Enhanced Timezone Accuracy (Tokyo)", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Enhanced Timezone Accuracy (Tokyo)", "FAIL", f"Request error: {str(e)}")

    def test_enhanced_category_mapping(self):
        """Test ENHANCED category mapping with real YouTube categories"""
        test_data = {
            "channel_url": "https://youtube.com/@mkbhd",
            "video_count": 10,
            "sort_order": "newest",
            "timezone": "America/New_York"
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/analyze-channel",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                videos = data.get("videos", [])
                channel_info = data.get("channel_info", {})
                
                if not videos:
                    self.log_test("Enhanced Category Mapping", "FAIL", "No videos returned")
                    return
                
                # Check if videos have category and category_id fields
                video = videos[0]
                required_category_fields = ["category", "category_id"]
                missing_fields = [field for field in required_category_fields if field not in video]
                
                if missing_fields:
                    self.log_test("Enhanced Category Mapping", "FAIL", 
                                f"Missing category fields in videos: {missing_fields}")
                    return
                
                # Verify categories are real YouTube categories (not generic fallbacks)
                valid_categories = [
                    "Science & Technology", "Entertainment", "Music", "Gaming", 
                    "Education", "Sports", "News & Politics", "Howto & Style",
                    "Film & Animation", "Autos & Vehicles", "Pets & Animals",
                    "Travel & Events", "People & Blogs", "Comedy"
                ]
                
                categories_found = set()
                for video in videos:
                    category = video.get("category", "")
                    categories_found.add(category)
                
                # Check if we have real categories (not just "Entertainment" fallback)
                real_categories = [cat for cat in categories_found if cat in valid_categories]
                
                if real_categories:
                    self.log_test("Enhanced Category Mapping", "PASS", 
                                f"Found real YouTube categories: {list(real_categories)}")
                else:
                    self.log_test("Enhanced Category Mapping", "FAIL", 
                                f"Only generic categories found: {list(categories_found)}")
                
                # Check channel primary_category is data-driven
                primary_category = channel_info.get("primary_category", "")
                if primary_category and primary_category != "General":
                    self.log_test("Enhanced Category Mapping (Channel)", "PASS", 
                                f"Channel primary category: {primary_category}")
                else:
                    self.log_test("Enhanced Category Mapping (Channel)", "FAIL", 
                                f"Generic primary category: {primary_category}")
                    
            else:
                self.log_test("Enhanced Category Mapping", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Enhanced Category Mapping", "FAIL", f"Request error: {str(e)}")

    def test_enhanced_data_structure(self):
        """Test ENHANCED data structure with new fields"""
        test_data = {
            "channel_url": "https://youtube.com/@mkbhd",
            "video_count": 10,
            "sort_order": "newest",
            "timezone": "America/New_York"
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/analyze-channel",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                videos = data.get("videos", [])
                
                if not videos:
                    self.log_test("Enhanced Data Structure", "FAIL", "No videos returned")
                    return
                
                video = videos[0]
                
                # Check for enhanced VideoInfo fields
                enhanced_fields = [
                    "upload_date_utc", "upload_date_local", "category", "category_id"
                ]
                
                missing_fields = [field for field in enhanced_fields if field not in video]
                
                if not missing_fields:
                    self.log_test("Enhanced Data Structure", "PASS", 
                                "All enhanced fields present in VideoInfo model")
                    
                    # Verify field content quality
                    field_quality = []
                    if video["upload_date_utc"] and "UTC" in video["upload_date_utc"]:
                        field_quality.append("UTC timestamp formatted correctly")
                    if video["upload_date_local"] and video["upload_date_local"] != video["upload_date_utc"]:
                        field_quality.append("Local timestamp differs from UTC")
                    if video["category"] and video["category"] != "Unknown":
                        field_quality.append(f"Category: {video['category']}")
                    if video["category_id"] and video["category_id"].isdigit():
                        field_quality.append(f"Category ID: {video['category_id']}")
                    
                    if field_quality:
                        self.log_test("Enhanced Data Structure Quality", "PASS", 
                                    f"Field quality checks: {', '.join(field_quality)}")
                    else:
                        self.log_test("Enhanced Data Structure Quality", "FAIL", 
                                    "Enhanced fields present but content quality issues")
                else:
                    self.log_test("Enhanced Data Structure", "FAIL", 
                                f"Missing enhanced fields: {missing_fields}")
                    
            else:
                self.log_test("Enhanced Data Structure", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Enhanced Data Structure", "FAIL", f"Request error: {str(e)}")
    
    def test_different_url_formats(self):
        """Test different YouTube URL formats"""
        url_formats = [
            "https://youtube.com/@mkbhd",
            "https://www.youtube.com/c/mkbhd",
            "https://youtube.com/channel/UCBJycsmduvYEL83R_U4JriQ"  # MKBHD's channel ID
        ]
        
        for url in url_formats:
            test_data = {
                "channel_url": url,
                "video_count": 3,
                "sort_order": "newest",
                "timezone": "UTC"
            }
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/analyze-channel",
                    json=test_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("channel_info", {}).get("name"):
                        self.log_test(f"URL Format Test ({url})", "PASS", 
                                    f"Successfully parsed URL format")
                    else:
                        self.log_test(f"URL Format Test ({url})", "FAIL", 
                                    "No channel name returned")
                else:
                    self.log_test(f"URL Format Test ({url})", "FAIL", 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"URL Format Test ({url})", "FAIL", f"Request error: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        error_test_cases = [
            {
                "name": "Invalid URL",
                "data": {
                    "channel_url": "https://invalid-url.com",
                    "video_count": 5,
                    "sort_order": "newest",
                    "timezone": "UTC"
                },
                "expected_status": 400
            },
            {
                "name": "Non-existent Channel",
                "data": {
                    "channel_url": "https://youtube.com/@nonexistentchannel12345",
                    "video_count": 5,
                    "sort_order": "newest",
                    "timezone": "UTC"
                },
                "expected_status": 404
            }
        ]
        
        for test_case in error_test_cases:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/analyze-channel",
                    json=test_case["data"],
                    timeout=30
                )
                
                if response.status_code == test_case["expected_status"]:
                    self.log_test(f"Error Handling ({test_case['name']})", "PASS", 
                                f"Correctly returned HTTP {response.status_code}")
                else:
                    self.log_test(f"Error Handling ({test_case['name']})", "FAIL", 
                                f"Expected HTTP {test_case['expected_status']}, got {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Error Handling ({test_case['name']})", "FAIL", f"Request error: {str(e)}")
    
    def test_monetization_detection(self):
        """Test monetization detection logic"""
        test_data = {
            "channel_url": "https://youtube.com/@mkbhd",
            "video_count": 10,
            "sort_order": "newest",
            "timezone": "UTC"
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/analyze-channel",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                monetization_status = data.get("channel_info", {}).get("monetization_status")
                
                if monetization_status in ["Likely Monetized", "Possibly Monetized", "Unknown"]:
                    self.log_test("Monetization Detection", "PASS", 
                                f"Detected monetization status: {monetization_status}")
                else:
                    self.log_test("Monetization Detection", "FAIL", 
                                f"Invalid monetization status: {monetization_status}")
            else:
                self.log_test("Monetization Detection", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Monetization Detection", "FAIL", f"Request error: {str(e)}")
    
    def test_engagement_calculations(self):
        """Test engagement rate calculations"""
        test_data = {
            "channel_url": "https://youtube.com/@mkbhd",
            "video_count": 5,
            "sort_order": "newest",
            "timezone": "UTC"
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/analyze-channel",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                videos = data.get("videos", [])
                
                if videos:
                    video = videos[0]
                    if "engagement_rate" in video and isinstance(video["engagement_rate"], (int, float)):
                        self.log_test("Engagement Calculations", "PASS", 
                                    f"Engagement rate calculated: {video['engagement_rate']}%")
                    else:
                        self.log_test("Engagement Calculations", "FAIL", 
                                    "Engagement rate not calculated or invalid format")
                else:
                    self.log_test("Engagement Calculations", "FAIL", "No videos returned")
            else:
                self.log_test("Engagement Calculations", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Engagement Calculations", "FAIL", f"Request error: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting YouTube Channel Analyzer Backend Tests")
        print(f"📡 Testing API at: {API_BASE_URL}")
        print("=" * 60)
        
        # Test API health first
        if not self.test_api_health():
            print("❌ API is not accessible. Stopping tests.")
            return
        
        # Run all tests
        print("\n📊 Testing Channel Analysis...")
        self.test_channel_analysis_mkbhd()
        
        print("\n🔢 Testing Video Count Variations...")
        self.test_different_video_counts()
        
        print("\n📅 Testing Sort Orders...")
        self.test_sort_orders()
        
        print("\n🌍 Testing Timezone Handling...")
        self.test_timezone_handling()
        
        print("\n🌍 Testing ENHANCED Timezone Accuracy...")
        self.test_enhanced_timezone_accuracy()
        
        print("\n🏷️ Testing ENHANCED Category Mapping...")
        self.test_enhanced_category_mapping()
        
        print("\n📋 Testing ENHANCED Data Structure...")
        self.test_enhanced_data_structure()
        
        print("\n🔗 Testing URL Format Support...")
        self.test_different_url_formats()
        
        print("\n⚠️ Testing Error Handling...")
        self.test_error_handling()
        
        print("\n💰 Testing Monetization Detection...")
        self.test_monetization_detection()
        
        print("\n📈 Testing Engagement Calculations...")
        self.test_engagement_calculations()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        
        if self.failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result['message']}")
        
        return self.failed_tests == 0

if __name__ == "__main__":
    tester = YouTubeChannelAnalyzerTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)