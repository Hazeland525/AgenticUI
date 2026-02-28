import axios from 'axios';
import { UIResponse } from '../types/schema';

const API_BASE_URL = 'http://localhost:8000/api';

/** Format ms for [STEP] lines: at most 1 decimal (e.g. 6.8 or 9212). */
export function formatStepMs(ms: number): string {
  const r = Math.round(ms * 10) / 10;
  return r % 1 === 0 ? String(Math.round(r)) : r.toFixed(1);
}

/** Get TTS audio blob from backend (ElevenLabs). Returns object URL for playback. */
export const getTtsAudio = async (text: string): Promise<string> => {
  const response = await axios.post<Blob>(
    `${API_BASE_URL}/text-to-speech`,
    { text },
    { responseType: 'blob' }
  );
  const blob = response.data;
  return URL.createObjectURL(blob);
};

export interface AskRequest {
  question: string;
  videoTime?: number;
  videoDuration?: number;
  transcriptSnippet?: string;
  videoFrame?: string; // Base64 encoded image data
}

export interface AskResponse {
  uiSchema: UIResponse;
  verbalSummary?: string; // Short summary for TTS only, not displayed in UI
}

export const askQuestion = async (request: AskRequest): Promise<AskResponse> => {
  try {
    const response = await axios.post<AskResponse>(
      `${API_BASE_URL}/ask`,
      request
    );
    return {
      uiSchema: response.data.uiSchema,
      verbalSummary: response.data.verbalSummary ?? undefined,
    };
  } catch (error) {
    console.error('Error asking question:', error);
    throw error;
  }
};

export interface RefineSpeechRequest {
  raw_speech: string;
}

export interface RefineSpeechResponse {
  refined_question: string;
}

export const refineSpeech = async (rawSpeech: string): Promise<string> => {
  try {
    const response = await axios.post<RefineSpeechResponse>(
      `${API_BASE_URL}/refine-speech`,
      { raw_speech: rawSpeech }
    );
    return response.data.refined_question;
  } catch (error) {
    console.error('Error refining speech:', error);
    // Fallback: return original speech if refinement fails
    return rawSpeech;
  }
};

export interface SpeechToTextRequest {
  audio_data: string; // Base64 encoded audio
  language_code?: string;
  audio_format?: string; // e.g., "webm_opus"
}

export interface SpeechToTextResponse {
  transcript: string;
}

export const speechToText = async (
  audioData: string,
  languageCode: string = "en-US",
  audioFormat: string = "webm_opus"
): Promise<string> => {
  try {
    const response = await axios.post<SpeechToTextResponse>(
      `${API_BASE_URL}/speech-to-text`,
      { audio_data: audioData, language_code: languageCode, audio_format: audioFormat }
    );
    return response.data.transcript;
  } catch (error) {
    console.error('Error transcribing speech:', error);
    throw error;
  }
};

/** Context for voice ask (video frame + time for main call). */
export interface AskWithVoiceContext {
  videoFrame?: string;
  videoTime?: number;
  videoDuration?: number;
  transcriptSnippet?: string;
}

/** Result of ask-with-voice stream (same as AskResponse), or a voice command (no Gemini). */
export interface AskWithVoiceResult {
  uiSchema?: UIResponse;
  verbalSummary?: string;
  /** When set, backend detected a voice command; no uiSchema. */
  voiceCommand?: 'add_to_collection' | 'go_to_collection_page';
  /** Optional timings from caller (step1 = getVoiceContext, step2 = askWithVoice) for [TOTAL] Voice flow. */
  voiceTimings?: { step1Ms: number; step2Ms: number; step2aMs?: number; step2bMs?: number };
  /** Set by askWithVoice: streaming call 1 (transcribe + refine) vs rest (main call). */
  step2aMs?: number;
  step2bMs?: number;
}

/**
 * Send audio to backend; stream transcript chunks via onChunk, then resolve with main result.
 * Uses Gemini to transcribe+refine in one step, then runs main ask (with image) in parallel.
 */
export const askWithVoice = async (
  audioData: string,
  context: AskWithVoiceContext,
  callbacks: { onChunk: (text: string) => void }
): Promise<AskWithVoiceResult> => {
  const response = await fetch(`${API_BASE_URL}/ask-with-voice`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      audio_data: audioData,
      videoFrame: context.videoFrame,
      videoTime: context.videoTime,
      videoDuration: context.videoDuration,
      transcriptSnippet: context.transcriptSnippet,
    }),
  });

  if (!response.ok) {
    const t = await response.text();
    throw new Error(t || `ask-with-voice ${response.status}`);
  }
  const reader = response.body?.getReader();
  if (!reader) throw new Error('No response body');

  const tStreamStart = performance.now();
  let tLastChunk: number | null = null;
  const decoder = new TextDecoder();
  let buffer = '';
  let result: AskWithVoiceResult | null = null;
  let eventType = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.startsWith('event: ')) {
        eventType = line.slice(7).trim();
      } else if (line.startsWith('data: ') && eventType) {
        try {
          const data = JSON.parse(line.slice(6)) as Record<string, unknown>;
          if (eventType === 'transcript_chunk' && typeof data.text === 'string') {
            tLastChunk = performance.now();
            callbacks.onChunk(data.text);
          } else if (eventType === 'voice_command' && typeof data.command === 'string') {
            result = { voiceCommand: data.command as 'add_to_collection' | 'go_to_collection_page' };
          } else if (eventType === 'result') {
            result = data as unknown as AskWithVoiceResult;
            const tResult = performance.now();
            const step2aMs = tLastChunk != null ? tLastChunk - tStreamStart : 0;
            const step2bMs = tResult - (tLastChunk ?? tStreamStart);
            result.step2aMs = step2aMs;
            result.step2bMs = step2bMs;
          } else if (eventType === 'error' && data.message) {
            throw new Error(String(data.message));
          }
        } catch (e) {
          if (result != null) break;
          if (e instanceof Error && e.message !== 'Unexpected end of JSON input') throw e;
        }
        eventType = '';
      }
    }
    if (result != null) break;
  }
  if (!result) throw new Error('No result from ask-with-voice');
  return result as AskWithVoiceResult;
};
