import { useState, useEffect, useRef } from 'react';
import { speechToText } from '../services/agentService';

interface UseVoiceInputOptions {
  /** When user finishes speaking, call with transcribed text (legacy: STT + refine). */
  onTranscript?: (text: string) => void;
  /** When provided, voice sends raw base64 audio to this callback instead of STT (e.g. for ask-with-voice). */
  onVoiceAudio?: (base64Audio: string) => void;
  onError?: (error: string) => void;
  onListeningChange?: (isListening: boolean) => void;
}

export const useVoiceInputGoogleCloud = ({ onTranscript, onVoiceAudio, onError, onListeningChange }: UseVoiceInputOptions) => {
  const [isListening, setIsListening] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const isKeyPressedRef = useRef(false);
  const isProcessingRef = useRef(false);
  const isRecordingRef = useRef(false);

  useEffect(() => {
    // Handle "s" key press/release
    const handleKeyDown = async (e: KeyboardEvent) => {
      // Only trigger if "s" key and not already listening and not typing in an input
      if (e.key === 's' || e.key === 'S') {
        const target = e.target as HTMLElement;
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
          return; // Don't trigger if user is typing
        }
        
        if (!isKeyPressedRef.current && !isRecordingRef.current) {
          console.log('[Voice Input] Key pressed - starting capture');
          isKeyPressedRef.current = true;
          isRecordingRef.current = true;
          e.preventDefault();
          
          try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ 
              audio: {
                channelCount: 1, // Mono
                sampleRate: 16000, // 16kHz
                echoCancellation: true,
                noiseSuppression: true,
              } 
            });
            
            streamRef.current = stream;
            
            // Create MediaRecorder with WAV format (if supported) or WebM
            const options: MediaRecorderOptions = {
              mimeType: 'audio/webm;codecs=opus', // WebM with Opus codec
            };
            
            // Check if the mimeType is supported
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
              delete options.mimeType; // Let browser choose
            }
            
            const mediaRecorder = new MediaRecorder(stream, options);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];
            
            // Add error handler
            mediaRecorder.onerror = (event) => {
              console.error('MediaRecorder error:', event);
              setIsListening(false);
              isRecordingRef.current = false;
              if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
                streamRef.current = null;
              }
            };
            
            mediaRecorder.ondataavailable = (event) => {
              if (event.data.size > 0) {
                audioChunksRef.current.push(event.data);
              }
            };
            
            mediaRecorder.onstop = async () => {
              // Wait a moment to ensure all data is collected
              await new Promise(resolve => setTimeout(resolve, 50));
              
              if (audioChunksRef.current.length === 0) {
                setIsListening(false);
                isRecordingRef.current = false;
                if (streamRef.current) {
                  streamRef.current.getTracks().forEach(track => track.stop());
                  streamRef.current = null;
                }
                return;
              }
              
              const finalTotalSize = audioChunksRef.current.reduce((sum, chunk) => sum + chunk.size, 0);
              if (finalTotalSize === 0) {
                setIsListening(false);
                isRecordingRef.current = false;
                if (streamRef.current) {
                  streamRef.current.getTracks().forEach(track => track.stop());
                  streamRef.current = null;
                }
                return;
              }
              
              // Combine audio chunks
              const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm;codecs=opus' });
              
              // Convert to base64
              const reader = new FileReader();
              reader.onloadend = async () => {
                try {
                  const base64Audio = (reader.result as string).split(',')[1]; // Remove data:audio/webm;base64, prefix
                  if (onVoiceAudio) {
                    onVoiceAudio(base64Audio);
                  } else if (onTranscript) {
                    const t0 = performance.now();
                    const transcript = await speechToText(base64Audio);
                    console.log(`[TIMING] Question Input — speech recognition: ${(performance.now() - t0).toFixed(0)}ms`);
                    if (transcript && transcript.trim()) {
                      console.log('[Voice Input] Raw speech captured:', transcript);
                      onTranscript(transcript);
                    }
                  }
                } catch (error) {
                  console.error('Error transcribing speech:', error);
                  onError?.(`Failed to transcribe speech: ${error}`);
                } finally {
                  setIsListening(false);
                  isProcessingRef.current = false;
                  isRecordingRef.current = false;
                  if (streamRef.current) {
                    streamRef.current.getTracks().forEach(track => track.stop());
                    streamRef.current = null;
                  }
                }
              };
              
              reader.onerror = () => {
                console.error('Error reading audio blob');
                onError?.('Failed to process audio');
                setIsListening(false);
                isProcessingRef.current = false;
                isRecordingRef.current = false;
                if (streamRef.current) {
                  streamRef.current.getTracks().forEach(track => track.stop());
                  streamRef.current = null;
                }
              };
              
              reader.readAsDataURL(audioBlob);
            };
            
            // Start recording with timeslice (100ms) to capture data periodically
            mediaRecorder.start(100);
            setIsListening(true);
            isProcessingRef.current = false;
            
          } catch (err) {
            console.error('Error starting audio capture:', err);
            onError?.(`Failed to access microphone: ${err}`);
            setIsListening(false);
            isKeyPressedRef.current = false;
            isRecordingRef.current = false;
          }
        }
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.key === 's' || e.key === 'S') {
        console.log('[Voice Input] Key released - stopping capture');
        isKeyPressedRef.current = false;
        
        if (mediaRecorderRef.current && isRecordingRef.current && mediaRecorderRef.current.state !== 'inactive') {
          isProcessingRef.current = true;
          mediaRecorderRef.current.stop();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      
      // Cleanup - but only if we're not actively recording
      if (mediaRecorderRef.current && !isRecordingRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      if (streamRef.current && !isRecordingRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
    };
  }, [onTranscript, onError, onListeningChange]);

  useEffect(() => {
    onListeningChange?.(isListening);
  }, [isListening, onListeningChange]);

  return { isListening };
};
