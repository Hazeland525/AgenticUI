import React, { useState } from 'react';
import { useVoiceInputGoogleCloud } from '../hooks/useVoiceInputGoogleCloud';
import { refineSpeech } from '../services/agentService';
import './QuestionInput.css';

interface QuestionInputProps {
  onSubmit: (question: string) => void;
  isLoading?: boolean;
  onListeningChange?: (isListening: boolean) => void;
}

export const QuestionInput: React.FC<QuestionInputProps> = ({ onSubmit, isLoading = false, onListeningChange }) => {
  const [question, setQuestion] = useState('');
  const [isRefining, setIsRefining] = useState(false);

  const handleTranscript = async (rawSpeech: string) => {
    if (!rawSpeech.trim()) {
      return;
    }
    
    console.log('[QuestionInput] Processing raw speech:', rawSpeech);
    setIsRefining(true);
    try {
      const t0 = performance.now();
      const refinedQuestion = await refineSpeech(rawSpeech);
      console.log(`[TIMING] Question Input — interpretation (refine): ${(performance.now() - t0).toFixed(0)}ms`);
      console.log('[QuestionInput] Refined speech:', refinedQuestion);
      setQuestion(refinedQuestion);
      // Auto-submit the refined question
      if (refinedQuestion.trim() && !isLoading) {
        onSubmit(refinedQuestion.trim());
        setQuestion('');
      }
    } catch (error) {
      console.error('Error refining speech:', error);
      // Fallback: use raw speech
      setQuestion(rawSpeech);
    } finally {
      setIsRefining(false);
    }
  };

  const { isListening } = useVoiceInputGoogleCloud({
    onTranscript: handleTranscript,
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
            value={question}
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

