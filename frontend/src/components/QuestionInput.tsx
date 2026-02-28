import React, { useRef, useState } from 'react';
import { useVoiceInputGoogleCloud } from '../hooks/useVoiceInputGoogleCloud';
import { askWithVoice, refineSpeech, formatStepMs } from '../services/agentService';
import type { AskWithVoiceContext, AskWithVoiceResult } from '../services/agentService';
import './QuestionInput.css';

interface QuestionInputProps {
  onSubmit: (question: string) => void;
  isLoading?: boolean;
  onListeningChange?: (isListening: boolean) => void;
  /** When set, voice uses Gemini ask-with-voice (stream transcript + main call). */
  getVoiceContext?: () => Promise<AskWithVoiceContext>;
  onVoiceResult?: (result: AskWithVoiceResult, refinedQuestion: string) => void;
  onVoiceStart?: () => void;
  onVoiceError?: () => void;
  /** Called when getVoiceContext is done and first transcript chunk arrived; use to switch sidebar to streaming state. */
  onVoiceStreamingStart?: (streamingTextSoFar: string) => void;
  /** Called on each transcript chunk so parent can show live question in sidebar. */
  onVoiceStreamingChunk?: (streamingTextSoFar: string) => void;
}

export const QuestionInput: React.FC<QuestionInputProps> = ({
  onSubmit,
  isLoading = false,
  onListeningChange,
  getVoiceContext,
  onVoiceResult,
  onVoiceStart,
  onVoiceError,
  onVoiceStreamingStart,
  onVoiceStreamingChunk,
}) => {
  const [question, setQuestion] = useState('');
  const [isRefining, setIsRefining] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const streamingRef = useRef('');
  const firstChunkSentRef = useRef(false);

  const handleTranscript = async (rawSpeech: string) => {
    if (!rawSpeech.trim()) return;
    setIsRefining(true);
    try {
      const t0 = performance.now();
      const refinedQuestion = await refineSpeech(rawSpeech);
      const step1Ms = performance.now() - t0;
      console.log(`[STEP] 1. refineSpeech — ${formatStepMs(step1Ms)}ms`, { refined: refinedQuestion.slice(0, 60) });
      setQuestion(refinedQuestion);
      if (refinedQuestion.trim() && !isLoading) {
        onSubmit(refinedQuestion.trim());
        setQuestion('');
      }
      console.log('────────────────────────────────');
      console.log(`[TOTAL] Legacy voice — ${Math.round(step1Ms).toLocaleString()}ms`);
    } catch (error) {
      console.error('Legacy voice failed:', error);
      setQuestion(rawSpeech);
    } finally {
      setIsRefining(false);
    }
  };

  const handleVoiceAudio = async (base64Audio: string) => {
    if (!getVoiceContext || !onVoiceResult) return;
    firstChunkSentRef.current = false;
    onVoiceStart?.();
    streamingRef.current = '';
    setStreamingText('');
    try {
      const t0 = performance.now();
      const context = await getVoiceContext();
      const step1Ms = performance.now() - t0;
      console.log(`[STEP] 1. getVoiceContext — ${formatStepMs(step1Ms)}ms`);

      const t1 = performance.now();
      const result = await askWithVoice(base64Audio, context, {
        onChunk: (text) => {
          streamingRef.current += text;
          const displayText = streamingRef.current.replace(/\n?---\s*$/, '').trimEnd();
          setStreamingText(displayText);
          if (!firstChunkSentRef.current) {
            firstChunkSentRef.current = true;
            onVoiceStreamingStart?.(displayText);
          }
          onVoiceStreamingChunk?.(displayText);
        },
      });
      const step2Ms = performance.now() - t1;
      if (result.step2aMs != null && result.step2bMs != null) {
        console.log(`[STEP] 2a. STT streaming — ${formatStepMs(result.step2aMs)}ms`);
        console.log(`[STEP] 2b. Main call (stream) — ${formatStepMs(result.step2bMs)}ms`);
      }
      console.log(`[STEP] 2. STT + main call (stream) — ${formatStepMs(step2Ms)}ms`);

      const refined = streamingRef.current.replace(/\n?---\s*$/, '').trim();
      result.voiceTimings = {
        step1Ms,
        step2Ms,
        step2aMs: result.step2aMs,
        step2bMs: result.step2bMs,
      };
      onVoiceResult(result, refined);
      streamingRef.current = '';
      setStreamingText('');
    } catch (error) {
      console.error('Voice flow failed:', error);
      setStreamingText('');
      onVoiceError?.();
    }
  };

  const { isListening } = useVoiceInputGoogleCloud({
    onTranscript: getVoiceContext && onVoiceResult ? undefined : handleTranscript,
    onVoiceAudio: getVoiceContext && onVoiceResult ? handleVoiceAudio : undefined,
    onError: (error) => console.error('Voice input error:', error),
    onListeningChange,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim() && !isLoading) {
      onSubmit(question.trim());
      setQuestion('');
    }
  };

  const showProcessing = !isListening && (isRefining || isLoading);

  return (
    <>
      {/* "I'm listening..." or "Processing..." - same style as Collections page */}
      {(isListening || showProcessing) && (
        <div className="voice-status">
          <span className="voice-status-text">
            {isListening ? "I'm listening..." : 'Processing...'}
          </span>
        </div>
      )}

      <div className="question-input-wrapper">
        <form className="question-input" onSubmit={handleSubmit}>
          <input
            type="text"
            className="question-input-field"
            placeholder="Ask a question about the video... (Hold 'S' to speak)"
            value={streamingText || question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={isLoading || isRefining}
          />
          <button
            type="submit"
            className="question-input-button"
            disabled={!question.trim() || isLoading || isRefining}
          >
            {isLoading ? 'Asking...' : isRefining ? 'Processing...' : 'Ask'}
          </button>
        </form>
      </div>
    </>
  );
};

