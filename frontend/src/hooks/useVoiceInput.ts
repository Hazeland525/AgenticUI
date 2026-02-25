import { useState, useEffect, useRef } from 'react';

interface UseVoiceInputOptions {
  onTranscript: (text: string) => void;
  onError?: (error: string) => void;
}

export const useVoiceInput = ({ onTranscript, onError }: UseVoiceInputOptions) => {
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const isKeyPressedRef = useRef(false);
  const finalTranscriptRef = useRef('');
  const interimTranscriptRef = useRef('');
  const isProcessingRef = useRef(false);
  const isStoppingRef = useRef(false);

  useEffect(() => {
    // Check if browser supports Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      onError?.('Speech recognition is not supported in this browser');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      // #region agent log
      console.log('[DEBUG] Recognition started');
      fetch('http://127.0.0.1:7242/ingest/e1242d26-8d88-4eb5-bd8c-a16e70f43f3d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useVoiceInput.ts:29',message:'Recognition started',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion
      setIsListening(true);
      finalTranscriptRef.current = '';
      interimTranscriptRef.current = '';
      isProcessingRef.current = false;
      isStoppingRef.current = false;
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      // Ignore results if we're stopping or already processed
      if (isStoppingRef.current || isProcessingRef.current) {
        console.log('[DEBUG] Ignoring recognition result - already stopping/processed');
        return;
      }
      
      let interimTranscript = '';
      let finalCount = 0;
      let interimCount = 0;
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscriptRef.current += transcript + ' ';
          finalCount++;
          // Clear interim when we get final results
          interimTranscriptRef.current = '';
        } else {
          interimTranscript += transcript;
          interimCount++;
        }
      }
      // Update interim transcript ref with the latest interim results
      if (interimTranscript) {
        interimTranscriptRef.current = interimTranscript;
      }
      // #region agent log
      console.log('[DEBUG] Recognition result:', {resultIndex:event.resultIndex,totalResults:event.results.length,finalCount,interimCount,interimTranscript,currentFinal:finalTranscriptRef.current,currentInterim:interimTranscriptRef.current});
      fetch('http://127.0.0.1:7242/ingest/e1242d26-8d88-4eb5-bd8c-a16e70f43f3d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useVoiceInput.ts:33',message:'Recognition result',data:{resultIndex:event.resultIndex,totalResults:event.results.length,finalCount,interimCount,interimTranscript,currentFinal:finalTranscriptRef.current,currentInterim:interimTranscriptRef.current},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
      // #endregion
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/e1242d26-8d88-4eb5-bd8c-a16e70f43f3d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useVoiceInput.ts:46',message:'Recognition error',data:{error:event.error,message:event.message},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
      if (event.error !== 'no-speech') {
        onError?.(`Speech recognition error: ${event.error}`);
      }
    };

    recognition.onend = () => {
      // #region agent log
      console.log('[DEBUG] Recognition ended:', {finalTranscript:finalTranscriptRef.current,interimTranscript:interimTranscriptRef.current,isEmpty:!finalTranscriptRef.current.trim() && !interimTranscriptRef.current.trim(),isProcessing:isProcessingRef.current,isStopping:isStoppingRef.current});
      fetch('http://127.0.0.1:7242/ingest/e1242d26-8d88-4eb5-bd8c-a16e70f43f3d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useVoiceInput.ts:54',message:'Recognition ended',data:{finalTranscript:finalTranscriptRef.current,interimTranscript:interimTranscriptRef.current,isEmpty:!finalTranscriptRef.current.trim() && !interimTranscriptRef.current.trim(),isProcessing:isProcessingRef.current,isStopping:isStoppingRef.current},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
      // #endregion
      setIsListening(false);
      isStoppingRef.current = false;
      
      // Skip processing if already processed by handleKeyUp
      if (isProcessingRef.current) {
        console.log('[DEBUG] Already processed, skipping onend');
        return;
      }
      
      // Process final transcript when recognition ends
      // If no final transcript but we have interim, use the interim result (common when stopping manually)
      const transcriptToUse = finalTranscriptRef.current.trim() || interimTranscriptRef.current.trim();
      
      if (transcriptToUse) {
        isProcessingRef.current = true;
        const rawSpeech = transcriptToUse;
        console.log('[Voice Input] Raw speech captured:', rawSpeech);
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/e1242d26-8d88-4eb5-bd8c-a16e70f43f3d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useVoiceInput.ts:60',message:'Calling onTranscript',data:{rawSpeech,source:finalTranscriptRef.current.trim() ? 'final' : 'interim'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
        // #endregion
        onTranscript(rawSpeech);
        finalTranscriptRef.current = '';
        interimTranscriptRef.current = '';
        isProcessingRef.current = false;
      } else {
        // #region agent log
        console.log('[DEBUG] No transcript to process');
        fetch('http://127.0.0.1:7242/ingest/e1242d26-8d88-4eb5-bd8c-a16e70f43f3d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useVoiceInput.ts:65',message:'No transcript to process',data:{finalTranscript:finalTranscriptRef.current,interimTranscript:interimTranscriptRef.current},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
        // #endregion
      }
    };

    recognitionRef.current = recognition;

    // Handle "s" key press/release
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only trigger if "s" key and not already listening and not typing in an input
      if (e.key === 's' || e.key === 'S') {
        const target = e.target as HTMLElement;
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
          return; // Don't trigger if user is typing
        }
        
        if (!isKeyPressedRef.current && !isListening) {
          isKeyPressedRef.current = true;
          e.preventDefault();
          try {
            // #region agent log
            fetch('http://127.0.0.1:7242/ingest/e1242d26-8d88-4eb5-bd8c-a16e70f43f3d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useVoiceInput.ts:76',message:'Key down - starting recognition',data:{key:e.key,isKeyPressed:isKeyPressedRef.current,isListening},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'})}).catch(()=>{});
            // #endregion
            recognition.start();
          } catch (err) {
            // #region agent log
            fetch('http://127.0.0.1:7242/ingest/e1242d26-8d88-4eb5-bd8c-a16e70f43f3d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useVoiceInput.ts:82',message:'Error starting recognition',data:{error:String(err)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
            // #endregion
            console.error('Error starting recognition:', err);
          }
        }
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.key === 's' || e.key === 'S') {
        // #region agent log
        console.log('[DEBUG] Key up - stopping recognition:', {key:e.key,isListening,currentFinal:finalTranscriptRef.current,currentInterim:interimTranscriptRef.current});
        fetch('http://127.0.0.1:7242/ingest/e1242d26-8d88-4eb5-bd8c-a16e70f43f3d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useVoiceInput.ts:88',message:'Key up - stopping recognition',data:{key:e.key,isListening,currentFinal:finalTranscriptRef.current,currentInterim:interimTranscriptRef.current},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'})}).catch(()=>{});
        // #endregion
        isKeyPressedRef.current = false;
        if (recognitionRef.current && isListening) {
          // Set stopping flag BEFORE stopping to ignore any results that come after
          isStoppingRef.current = true;
          setIsListening(false);
          
          // Stop recognition
          recognitionRef.current.stop();
          
          // Process transcript immediately if we have one (don't wait for onend)
          // This handles the case where onend might not fire when stopping manually
          const transcriptToUse = finalTranscriptRef.current.trim() || interimTranscriptRef.current.trim();
          if (transcriptToUse && !isProcessingRef.current) {
            isProcessingRef.current = true;
            console.log('[DEBUG] Processing transcript from key up:', transcriptToUse);
            const rawSpeech = transcriptToUse;
            console.log('[Voice Input] Raw speech captured:', rawSpeech);
            // #region agent log
            fetch('http://127.0.0.1:7242/ingest/e1242d26-8d88-4eb5-bd8c-a16e70f43f3d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useVoiceInput.ts:145',message:'Calling onTranscript from key up',data:{rawSpeech,source:finalTranscriptRef.current.trim() ? 'final' : 'interim'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
            // #endregion
            onTranscript(rawSpeech);
            finalTranscriptRef.current = '';
            interimTranscriptRef.current = '';
            isProcessingRef.current = false;
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (err) {
          // Ignore errors when stopping
        }
      }
    };
  }, [isListening, onTranscript, onError]);

  return { isListening };
};
