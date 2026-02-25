import axios from 'axios';
import { UIResponse } from '../types/schema';

const API_BASE_URL = 'http://localhost:8000/api';

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
