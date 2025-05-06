"""
Enhanced YouTube transcript tool for the AI agent project.
Handles video transcript extraction and specific content finding.
"""

import os
import re
from typing import Optional
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
from .base_tool import EnhancedTool

class YouTubeTranscriptTool(EnhancedTool):
    """Tool for extracting and analyzing YouTube video transcripts."""
    
    name = "YouTubeTranscriptTool"
    description = "Extract transcripts from YouTube videos and find specific content. DO NOT use visit_webpage function!"
    inputs = {
        "video_id": {
            "type": "string",
            "description": "YouTube Video ID (the part after 'watch?v=' in the URL, NOT the full URL)"
        },
        "search_term": {
            "type": "string",
            "description": "Optional term or phrase to search for in the transcript",
            "nullable": True
        }
    }
    output_type = "string"
    
    def __init__(self):
        super().__init__()
        # Initialize whisper model (lazy loading)
        self.whisper_model = None
    
    def forward(self, video_id: str, search_term: Optional[str] = None) -> str:
        """
        Extract and search YouTube video transcript.
        
        Args:
            video_id: YouTube video ID (not full URL)
            search_term: Term to search for in transcript
            
        Returns:
            Transcript or search results
        """
        # Extract video_id from URL if user accidentally passed full URL
        if "youtube.com" in video_id or "youtu.be" in video_id:
            url_pattern = r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)'
            match = re.search(url_pattern, video_id)
            if match:
                video_id = match.group(1)
                
        try:
            # First try the official transcript API
            transcript = self._get_transcript_via_api(video_id)
            
            # If API fails, try downloading and transcribing
            if not transcript:
                transcript = self._get_transcript_via_download(video_id)
            
            # If both methods fail
            if not transcript:
                return "Could not retrieve transcript for this video."
            
            # If search term provided, find the relevant sections
            if search_term:
                return self._find_in_transcript(transcript, search_term)
            
            return transcript
            
        except Exception as e:
            return f"Error processing YouTube video: {str(e)}"
    
    def _get_transcript_via_api(self, video_id: str) -> str:
        """Use YouTube Transcript API to get transcript."""
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try manually created transcript first
            try:
                transcript = transcript_list.find_manually_created_transcript(['en'])
                transcript_data = transcript.fetch()
            except Exception:
                # If not found, try auto-generated transcript
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                    transcript_data = transcript.fetch()
                except Exception:
                    return ""
            
            # Format transcript as plain text with timestamps
            formatted_transcript = ""
            for entry in transcript_data:
                start_time = int(entry['start'])
                minutes, seconds = divmod(start_time, 60)
                timestamp = f"[{minutes:02d}:{seconds:02d}]"
                formatted_transcript += f"{timestamp} {entry['text']}\n"
            
            return formatted_transcript
        
        except TranscriptsDisabled:
            return "Transcripts are disabled for this video."
        except Exception as e:
            # Return empty string to trigger fallback method
            return ""
    
    def _get_transcript_via_download(self, video_id: str) -> str:
        """Download audio and transcribe with Whisper."""
        # Early return if whisper is not available
        if not WHISPER_AVAILABLE:
            return "Whisper transcription is not available (install openai-whisper package)."
            
        audio_filename = f"{video_id}.mp3"
        
        try:
            # Download audio
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': audio_filename,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
            
            # Transcribe audio with Whisper
            if os.path.exists(audio_filename):
                # Lazy loading of whisper model
                if self.whisper_model is None:
                    try:
                        self.whisper_model = whisper.load_model("base")
                    except Exception as e:
                        return f"Error loading Whisper model: {str(e)}"
                
                try:
                    result = self.whisper_model.transcribe(audio_filename)
                    return result["text"]
                except Exception as e:
                    return f"Error during transcription: {str(e)}"
            else:
                return "Failed to download audio for transcription."
                
        except Exception as e:
            return f"Error obtaining transcript: {str(e)}"
        finally:
            # Clean up downloaded file
            if os.path.exists(audio_filename):
                try:
                    os.remove(audio_filename)
                except:
                    pass
    
    def _find_in_transcript(self, transcript: str, search_term: str) -> str:
        """Find sections in transcript containing the search term."""
        search_term = search_term.lower()
        
        # Special case for direct quotes
        if search_term.startswith('"') and search_term.endswith('"') or search_term.startswith('"') and search_term.endswith('"'):
            quote = search_term.strip('"').strip('"').lower()
            
            # Try to find exact quote
            transcript_lower = transcript.lower()
            start_pos = transcript_lower.find(quote)
            if start_pos != -1:
                # Get the context around the quote
                context_start = max(0, start_pos - 100)
                context_end = min(len(transcript), start_pos + len(quote) + 100)
                return transcript[context_start:context_end].strip()
        
        # For questions like "what does X say in response to Y?"
        if "response to" in search_term:
            match = re.search(r'response to ["\']([^"\']+)["\']', search_term)
            if match:
                trigger_phrase = match.group(1).lower()
                
                # Find the trigger phrase
                transcript_lines = transcript.split('\n')
                for i, line in enumerate(transcript_lines):
                    if trigger_phrase.lower() in line.lower() and i < len(transcript_lines) - 1:
                        # Return the next line which should contain the response
                        return transcript_lines[i+1].strip()
        
        # For general search terms
        results = []
        lines = transcript.split('\n')
        
        for i, line in enumerate(lines):
            if search_term in line.lower():
                context_start = max(0, i - 1)
                context_end = min(len(lines), i + 2)
                context = '\n'.join(lines[context_start:context_end])
                results.append(context)
        
        if results:
            return '\n\n'.join(results)
        else:
            # If nothing found, check if this is a question about specific content
            if "?" in search_term:
                # For questions about specific content like "what does X say about Y"
                # Extract entities and try broader search
                words = set(search_term.lower().replace('?', '').split())
                filtered_words = [w for w in words if len(w) > 3 and w not in {'what', 'when', 'where', 'how', 'does', 'did', 'say', 'said', 'about', 'mentions', 'talk', 'talks', 'discuss', 'discusses'}]
                
                if filtered_words:
                    broader_results = []
                    for term in filtered_words:
                        for i, line in enumerate(lines):
                            if term in line.lower():
                                broader_results.append(line)
                    
                    if broader_results:
                        return '\n'.join(broader_results[:3])
            
            return f"Could not find '{search_term}' in the transcript." 