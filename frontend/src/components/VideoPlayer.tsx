import { useState, useRef, useImperativeHandle, forwardRef } from 'react';
import ReactPlayer from 'react-player';
import './VideoPlayer.css';

interface VideoPlayerProps {
  url?: string;
  onTimeUpdate?: (currentTime: number, duration: number) => void;
  hasResults?: boolean;
  volume?: number;
}

export interface VideoPlayerHandle {
  captureFrame: () => Promise<string | null>;
}

export const VideoPlayer = forwardRef<VideoPlayerHandle, VideoPlayerProps>(
  ({ url, onTimeUpdate, hasResults = false, volume = 1 }, ref) => {
    const playerRef = useRef<any>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [duration, setDuration] = useState(0);
    const [error, setError] = useState<string | null>(null);

    // Expose captureFrame method via ref
    useImperativeHandle(ref, () => ({
      captureFrame: async (): Promise<string | null> => {
        try {
          // Find video element in the DOM (ReactPlayer renders it inside the container)
          const container = containerRef.current;
          if (!container) {
            return null;
          }

          // ReactPlayer renders the video element inside, try to find it
          const video = container.querySelector('video') as HTMLVideoElement;
          if (!video || video.readyState < 2) {
            // Video not ready (HAVE_CURRENT_DATA = 2)
            return null;
          }

          // Check if video has valid dimensions
          if (video.videoWidth === 0 || video.videoHeight === 0) {
            return null;
          }

          // Downscale to max 320px width for smaller upload and faster processing
          const maxWidth = 320;
          const w = video.videoWidth;
          const h = video.videoHeight;
          const scale = w > maxWidth ? maxWidth / w : 1;
          const cw = Math.round(w * scale);
          const ch = Math.round(h * scale);

          const canvas = document.createElement('canvas');
          canvas.width = cw;
          canvas.height = ch;
          const ctx = canvas.getContext('2d');
          if (!ctx) {
            return null;
          }

          ctx.drawImage(video, 0, 0, w, h, 0, 0, cw, ch);

          // JPEG quality 0.3 for smaller payload
          const dataUrl = canvas.toDataURL('image/jpeg', 0.3);
          // Return base64 data without the data URL prefix
          return dataUrl.split(',')[1] || null;
        } catch (error) {
          console.error('Error capturing video frame:', error);
          return null;
        }
      },
    }));

  // Get duration when it changes
  const handleDurationChange = (dur: number) => {
    if (dur && !isNaN(dur) && isFinite(dur) && dur > 0) {
      setDuration(dur);
    }
  };

  // Handle player ready
  const handleReady = () => {
    setError(null);
    // Try to get duration after a short delay
    setTimeout(() => {
      if (playerRef.current) {
        try {
          const internalPlayer = playerRef.current.getInternalPlayer();
          if (internalPlayer && 'duration' in internalPlayer) {
            const dur = internalPlayer.duration;
            if (dur && !isNaN(dur) && isFinite(dur) && dur > 0) {
              setDuration(dur);
            }
          }
        } catch (e) {
          // Ignore - duration will come from onDurationChange
        }
      }
    }, 100);
  };

  // Handle errors
  const handleError = (error: any) => {
    console.error('Video player error:', error);
    setError('Failed to load video. Please try a different file or format.');
  };

  const handleProgress = (state: { playedSeconds: number; played: number; loadedSeconds?: number } | any) => {
    // Type guard to ensure we have the correct state structure
    if (state && typeof state === 'object' && 'playedSeconds' in state) {
      const time = state.playedSeconds;
      
      if (onTimeUpdate) {
        onTimeUpdate(time, duration || 0);
      }
    }
  };

  if (!url) {
    return (
      <div className={`video-player-container${hasResults ? ' has-results' : ''}`}>
        <div className="video-player-placeholder">
          <p>No video selected</p>
          <p className="video-player-hint">Select a video file to play</p>
        </div>
      </div>
    );
  }

  const playerProps = {
    ref: playerRef,
    src: url, // ReactPlayer uses 'src' not 'url'
    controls: true,
    width: '100%',
    height: '100%',
    volume,
    onReady: handleReady,
    onProgress: handleProgress,
    onError: handleError,
    onDurationChange: handleDurationChange,
  };

  return (
    <div className={`video-player-container${hasResults ? ' has-results' : ''}`} ref={containerRef}>
      {error && (
        <div className="video-player-error">
          <p>{error}</p>
        </div>
      )}
      {/* @ts-ignore - ReactPlayer type definitions may not match runtime behavior */}
      <ReactPlayer {...playerProps} />
    </div>
  );
});

