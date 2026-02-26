import { useState, useRef, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { VideoPlayer, VideoPlayerHandle } from './components/VideoPlayer';
import { ContextExtractor, useVideoContext } from './components/ContextExtractor';
import { Sidebar } from './components/Sidebar';
import { CollectionsPage } from './components/CollectionsPage';
import { QuestionInput } from './components/QuestionInput';
import { askQuestion, getTtsAudio, formatStepMs } from './services/agentService';
import type { AskWithVoiceResult } from './services/agentService';
import { saveItem, SavedItem } from './services/libraryService';
import { getUserProfile } from './services/userProfileService';
import { UIResponse } from './types/schema';
import './App.css';

const MAX_TEXT_PREVIEW = 60;

/** Format ms for [TOTAL] line (e.g. 11130 → "11,130"). */
function fmtMs(ms: number): string {
  return Math.round(ms).toLocaleString();
}

function getLiteralStr(val: unknown): string {
  if (typeof val === 'string') return val;
  if (val && typeof val === 'object' && 'literalString' in val) {
    const s = (val as { literalString: string }).literalString;
    return typeof s === 'string' ? s : '';
  }
  return '';
}

/** Build a map id -> component from schema. */
function componentMap(schema: UIResponse): Map<string, { id: string; component: unknown }> {
  const map = new Map<string, { id: string; component: unknown }>();
  schema.components?.forEach((c) => {
    if (c.id != null) map.set(c.id, { id: c.id, component: c.component });
  });
  return map;
}

/** Return a hierarchical, structured view of the UI schema (tree from root). */
function uiSchemaHierarchyForLog(schema: UIResponse): string {
  const intent = (schema.meta as Record<string, string> | undefined)?.intent ?? '—';
  const rootId = schema.root ?? '';
  const map = componentMap(schema);
  const lines: string[] = [
    `intent: ${intent}  |  root: ${rootId}`,
    '',
  ];

  function formatComponent(id: string, indent: number): void {
    const comp = map.get(id);
    if (!comp) {
      lines.push('  '.repeat(indent) + `${id}: (missing)`);
      return;
    }
    const def = comp.component as Record<string, Record<string, unknown>> | undefined;
    if (!def) {
      lines.push('  '.repeat(indent) + `${id}: (empty)`);
      return;
    }
    const compType = Object.keys(def)[0] ?? '?';
    const props = def[compType] as Record<string, unknown> | undefined;

    if (compType === 'Text' && props?.text != null) {
      const usage = (props.usageHint as string) ?? '';
      let content = getLiteralStr(props.text);
      if (content.length > MAX_TEXT_PREVIEW) content = content.slice(0, MAX_TEXT_PREVIEW) + '…';
      lines.push('  '.repeat(indent) + `${id} (Text ${usage}): "${content}"`);
    } else if (compType === 'Image') {
      lines.push('  '.repeat(indent) + `${id} (Image): [Image]`);
    } else if (compType === 'Card' && props?.child) {
      const childId = props.child as string;
      lines.push('  '.repeat(indent) + `${id} (Card): child → ${childId}`);
      formatComponent(childId, indent + 1);
    } else if ((compType === 'Column' || compType === 'Row') && props?.children) {
      const ch = props.children as { explicitList?: string[] } | string[];
      const ids = Array.isArray(ch) ? ch : ch?.explicitList ?? [];
      lines.push('  '.repeat(indent) + `${id} (${compType}): children → [${ids.join(', ')}]`);
      ids.forEach((childId) => formatComponent(childId, indent + 1));
    } else if (compType === 'Button' && props?.child) {
      const childId = props.child as string;
      lines.push('  '.repeat(indent) + `${id} (Button): child → ${childId}`);
      formatComponent(childId, indent + 1);
    } else if (compType === 'List' && props?.children) {
      const ch = props.children as { explicitList?: string[] } | string[];
      const ids = Array.isArray(ch) ? ch : ch?.explicitList ?? [];
      lines.push('  '.repeat(indent) + `${id} (List): [${ids.join(', ')}]`);
      ids.forEach((childId) => formatComponent(childId, indent + 1));
    } else if (compType === 'StepCarousel' && props?.steps) {
      const steps = (props.steps as string[]) ?? [];
      lines.push('  '.repeat(indent) + `${id} (StepCarousel): steps → [${steps.join(', ')}]`);
      steps.forEach((stepId) => formatComponent(stepId, indent + 1));
    } else if (compType === 'Chip' && props?.text != null) {
      const content = getLiteralStr(props.text);
      lines.push('  '.repeat(indent) + `${id} (Chip): "${content.slice(0, 40)}${content.length > 40 ? '…' : ''}"`);
    } else if (compType === 'Chip' && props?.label != null) {
      const content = getLiteralStr(props.label);
      lines.push('  '.repeat(indent) + `${id} (Chip): "${content.slice(0, 40)}${content.length > 40 ? '…' : ''}"`);
    } else {
      lines.push('  '.repeat(indent) + `${id} (${compType})`);
    }
  }

  if (rootId) formatComponent(rootId, 0);
  return lines.join('\n');
}

// Pre-loaded videos - add your video filenames here
// Videos should be placed in: frontend/public/videos/
const PRELOADED_VIDEOS = [
  { name: 'Cooking', path: '/videos/chefTable.mp4' },
  { name: 'Frederik Bille Brahe', path: '/videos/Frederik-Bille-Brahe.mp4' },
  { name: 'Korean Street Food', path: '/videos/KoreanStreetFood.mp4' },
  // Add your video filenames here, e.g.:
  // { name: 'Sample Video', path: '/videos/sample.mp4' },
  // { name: 'Demo Video', path: '/videos/demo.mp4' },
];

function App() {
  const [videoUrl, setVideoUrl] = useState<string>('');
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [currentSchema, setCurrentSchema] = useState<UIResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState<string>('');
  const [profileAvatar, setProfileAvatar] = useState<string>('/icons/profile1.jpg');
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  const [isVoiceProcessing, setIsVoiceProcessing] = useState(false);
  const videoPlayerRef = useRef<VideoPlayerHandle>(null);
  const hasEverHadResultRef = useRef(false);
  const navigate = useNavigate();

  const hasVideoSelected = !!videoUrl;
  /** First time: full screen. After first result, keep sidebar visible so the video never resizes back to full screen. */
  const hasResult =
    currentSchema != null || (isVoiceProcessing && hasEverHadResultRef.current);

  useEffect(() => {
    let cancelled = false;
    getUserProfile().then((p) => {
      if (!cancelled && p?.avatarUrl) setProfileAvatar(p.avatarUrl);
    });
    return () => { cancelled = true; };
  }, []);

  const videoContext = useVideoContext(currentTime, duration);

  const handleTimeUpdate = (time: number, dur: number) => {
    setCurrentTime(time);
    setDuration(dur);
  };

  const handleAskQuestion = async (question: string) => {
    setIsLoading(true);
    setCurrentQuestion(question);
    try {
      let step1Ms = 0;
      let videoFrame: string | null = null;
      if (videoPlayerRef.current) {
        const t0 = performance.now();
        videoFrame = await videoPlayerRef.current.captureFrame();
        step1Ms = performance.now() - t0;
        console.log(`[STEP] 1. Capture frame — ${formatStepMs(step1Ms)}ms`, videoFrame ? `(base64 length: ${videoFrame.length})` : 'null');
      } else {
        console.warn('[STEP] 1. Video player ref not available');
      }

      const t1 = performance.now();
      const { uiSchema: schema, verbalSummary } = await askQuestion({
        question,
        videoTime: currentTime,
        videoDuration: duration,
        transcriptSnippet: videoContext.transcriptSnippet,
        videoFrame: videoFrame || undefined,
      });
      const step2Ms = performance.now() - t1;
      console.log(`[STEP] 2. API (ask) — ${formatStepMs(step2Ms)}ms`, {
        components: schema.components?.length ?? 0,
        verbalSummary: verbalSummary ? `${verbalSummary.slice(0, 50)}...` : 'none',
      });
      console.log('='.repeat(80));
      console.log('UI SCHEMA (structure + content):');
      console.log(uiSchemaHierarchyForLog(schema));
      console.log('='.repeat(80));

      setCurrentSchema(schema);
      hasEverHadResultRef.current = true;

      let step3Ms = 0;
      if (verbalSummary && verbalSummary.trim()) {
        try {
          const t2 = performance.now();
          const audioUrl = await getTtsAudio(verbalSummary.trim());
          const audio = new Audio(audioUrl);
          audio.onended = () => {
            setIsAiSpeaking(false);
            URL.revokeObjectURL(audioUrl);
          };
          audio.onerror = () => {
            setIsAiSpeaking(false);
            URL.revokeObjectURL(audioUrl);
          };
          setIsAiSpeaking(true);
          await audio.play();
          step3Ms = performance.now() - t2;
          console.log(`[STEP] 3. TTS fetch + play start — ${formatStepMs(step3Ms)}ms`);
        } catch (e) {
          console.warn('TTS playback failed:', e);
          setIsAiSpeaking(false);
        }
      } else {
        console.log('[STEP] 3. TTS — skipped (no verbalSummary)');
      }

      console.log('────────────────────────────────');
      console.log(`[TOTAL] Ask (text) flow — ${fmtMs(step1Ms + step2Ms + step3Ms)}ms`);
    } catch (error) {
      console.error('Error asking question:', error);
      setCurrentSchema({
            components: [
              {
                id: 'error-card',
                component: { Card: { child: 'error-content' } }
              },
              {
                id: 'error-content',
                component: { Column: { children: { explicitList: ['error-title', 'error-text'] } } }
              },
              {
                id: 'error-title',
                component: { Text: { text: { literalString: 'Error' }, usageHint: 'h2' } }
              },
              {
                id: 'error-text',
                component: { Text: { text: { literalString: 'Failed to get response. Please try again.' }, usageHint: 'body' } }
              }
            ],
            root: 'error-card',
            meta: {},
          });
      hasEverHadResultRef.current = true;
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceResult = async (result: AskWithVoiceResult, refinedQuestion: string) => {
    console.log('Voice result received', {
      refinedQuestion: refinedQuestion.slice(0, 60),
      components: result.uiSchema.components?.length ?? 0,
    });
    console.log('='.repeat(80));
    console.log('UI SCHEMA (structure + content):');
    console.log(uiSchemaHierarchyForLog(result.uiSchema));
    console.log('='.repeat(80));

    setCurrentSchema(result.uiSchema);
    setCurrentQuestion(refinedQuestion);
    hasEverHadResultRef.current = true;

    let step3Ms = 0;
    if (result.verbalSummary?.trim()) {
      try {
        const t0 = performance.now();
        const audioUrl = await getTtsAudio(result.verbalSummary.trim());
        const audio = new Audio(audioUrl);
        audio.onended = () => {
          setIsAiSpeaking(false);
          URL.revokeObjectURL(audioUrl);
        };
        audio.onerror = () => {
          setIsAiSpeaking(false);
          URL.revokeObjectURL(audioUrl);
        };
        setIsAiSpeaking(true);
        await audio.play();
        step3Ms = performance.now() - t0;
        console.log(`[STEP] 3. TTS fetch + play start — ${formatStepMs(step3Ms)}ms`);
      } catch (e) {
        console.warn('TTS playback failed:', e);
        setIsAiSpeaking(false);
      }
    } else {
      console.log('[STEP] 3. TTS — skipped (no verbalSummary)');
    }

    const step1Ms = result.voiceTimings?.step1Ms ?? 0;
    const step2Ms = result.voiceTimings?.step2Ms ?? 0;
    const totalMs = step1Ms + step2Ms + step3Ms;
    console.log('────────────────────────────────');
    console.log(`[TOTAL] Voice flow — ${fmtMs(totalMs)}ms`);
    setIsLoading(false);
    setIsVoiceProcessing(false);
  };

  const handleSave = async (schema: UIResponse) => {
    try {
      await saveItem({
        question: currentQuestion,
        uiSchema: schema,
        videoTime: currentTime,
      });
      alert('Saved successfully!');
    } catch (error) {
      console.error('Error saving:', error);
      alert('Failed to save. Please try again.');
    }
  };

  const handleLoadItem = (item: SavedItem) => {
    setCurrentSchema(item.uiSchema);
    setCurrentQuestion(item.question);
    hasEverHadResultRef.current = true;
  };

  const handlePreloadedVideoSelect = (path: string) => {
    setVideoUrl(path);
  };

  return (
    <div className="app">
      <Routes>
        <Route
          path="/collections"
          element={<CollectionsPage onLoadItem={handleLoadItem} />}
        />
        <Route
          path="/"
          element={
            <>
              <div className="app-body">
                <div className="app-left">
                  {hasVideoSelected ? (
                    <>
                      <div className="app-video-area">
                        <div className={`video-section${hasResult ? ' has-results' : ''}`}>
                          <VideoPlayer
                            ref={videoPlayerRef}
                            url={videoUrl}
                            onTimeUpdate={handleTimeUpdate}
                            hasResults={hasResult}
                            volume={isUserSpeaking || isAiSpeaking ? 0 : 1}
                          />
                          <ContextExtractor
                            currentTime={currentTime}
                            duration={duration}
                          />
                        </div>
                      </div>
                      <header className="app-topbar app-topbar-overlay">
                        <img src="/icons/videoplay.svg" alt="Video" className="provider-icon" />
                        <select
                          className="video-title-select"
                          onChange={(e) => {
                            if (e.target.value) {
                              handlePreloadedVideoSelect(e.target.value);
                            }
                          }}
                          value={videoUrl || ''}
                        >
                          <option value="">Select Video</option>
                          {PRELOADED_VIDEOS.map((video, index) => (
                            <option key={index} value={video.path}>
                              {video.name}
                            </option>
                          ))}
                        </select>
                      </header>
                    </>
                  ) : (
                    <>
                      <header className="app-topbar">
                        <img src="/icons/videoplay.svg" alt="Video" className="provider-icon" />
                        <select
                          className="video-title-select"
                          onChange={(e) => {
                            if (e.target.value) {
                              handlePreloadedVideoSelect(e.target.value);
                            }
                          }}
                          value={videoUrl || ''}
                        >
                          <option value="">Select Video</option>
                          {PRELOADED_VIDEOS.map((video, index) => (
                            <option key={index} value={video.path}>
                              {video.name}
                            </option>
                          ))}
                        </select>
                      </header>
                      <div className="app-empty" aria-hidden />
                    </>
                  )}
                </div>
                <div className="app-sidebar-column">
                  <Sidebar
                    onAskQuestion={handleAskQuestion}
                    onSave={handleSave}
                    isLoading={isLoading}
                    currentSchema={currentSchema}
                    currentQuestion={currentQuestion}
                  />
                </div>
                <div className="app-profile-overlay">
                  <button
                    type="button"
                    className="app-profile-overlay-btn"
                    onClick={() => navigate('/collections')}
                    aria-label="My collections"
                  >
                    <img src={profileAvatar} alt="" />
                  </button>
                </div>
              </div>
              {hasVideoSelected && (
                <QuestionInput
                  onSubmit={handleAskQuestion}
                  isLoading={isLoading}
                  onListeningChange={setIsUserSpeaking}
                  getVoiceContext={async () => {
                    const frame = await videoPlayerRef.current?.captureFrame() ?? null;
                    return {
                      videoFrame: frame ?? undefined,
                      videoTime: currentTime,
                      videoDuration: duration,
                      transcriptSnippet: videoContext.transcriptSnippet,
                    };
                  }}
                  onVoiceResult={handleVoiceResult}
                  onVoiceStart={() => {
                    setCurrentQuestion('processing the question...');
                    setCurrentSchema(null);
                    setIsVoiceProcessing(true);
                    setIsLoading(true);
                  }}
                  onVoiceError={() => {
                    setIsLoading(false);
                    setIsVoiceProcessing(false);
                  }}
                />
              )}
            </>
          }
        />
      </Routes>
    </div>
  );
}

export default App;
