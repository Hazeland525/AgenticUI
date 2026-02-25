import { useState, useEffect } from 'react';

export interface VideoContext {
  currentTime: number;
  duration: number;
  transcriptSnippet?: string;
}

interface ContextExtractorProps {
  currentTime: number;
  duration: number;
  onContextChange?: (context: VideoContext) => void;
}

export const useVideoContext = (
  currentTime: number,
  duration: number
): VideoContext => {
  const [transcriptSnippet, setTranscriptSnippet] = useState<string | undefined>();

  // For MVP, we'll just return the time context
  // In a full implementation, this would extract transcript snippets
  useEffect(() => {
    // Placeholder for transcript extraction
    // In a real implementation, you'd extract transcript based on currentTime
    setTranscriptSnippet(undefined);
  }, [currentTime]);

  return {
    currentTime,
    duration,
    transcriptSnippet,
  };
};

export const ContextExtractor: React.FC<ContextExtractorProps> = ({
  currentTime,
  duration,
  onContextChange,
}) => {
  const context = useVideoContext(currentTime, duration);

  useEffect(() => {
    if (onContextChange) {
      onContextChange(context);
    }
  }, [context, onContextChange]);

  return null; // This component doesn't render anything
};

