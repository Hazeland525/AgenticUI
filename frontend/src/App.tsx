import { useState, useRef, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { VideoPlayer, VideoPlayerHandle } from './components/VideoPlayer';
import { ContextExtractor, useVideoContext } from './components/ContextExtractor';
import { Sidebar } from './components/Sidebar';
import { CollectionsPage } from './components/CollectionsPage';
import { QuestionInput } from './components/QuestionInput';
import { askQuestion, getTtsAudio } from './services/agentService';
import { saveItem, SavedItem } from './services/libraryService';
import { getUserProfile } from './services/userProfileService';
import { UIResponse } from './types/schema';
import './App.css';

const MAX_TEXT_PREVIEW = 60;

function getLiteralStr(val: unknown): string {
  if (typeof val === 'string') return val;
  if (val && typeof val === 'object' && 'literalString' in val) {
    const s = (val as { literalString: string }).literalString;
    return typeof s === 'string' ? s : '';
  }
  return '';
}

/** Return a short, human-readable summary of the UI schema for console logs. */
function uiSchemaSummaryForLog(schema: UIResponse): string {
  const intent = (schema.meta as Record<string, string> | undefined)?.intent ?? '—';
  const root = schema.root ?? '—';
  const lines: string[] = [
    `intent: ${intent}  |  root: ${root}`,
    '',
  ];
  schema.components?.forEach((comp) => {
    const cid = comp.id ?? '?';
    const def = comp.component as unknown as Record<string, Record<string, unknown>> | undefined;
    if (!def) {
      lines.push(`  • ${cid}: (empty)`);
      return;
    }
    const compType = Object.keys(def)[0] ?? '?';
    const props = def[compType];
    if (compType === 'Text' && props?.text != null) {
      const usage = (props.usageHint as string) ?? '';
      let content = getLiteralStr(props.text);
      if (content.length > MAX_TEXT_PREVIEW) content = content.slice(0, MAX_TEXT_PREVIEW) + '…';
      lines.push(`  • ${cid} (Text ${usage}): "${content}"`);
    } else if (compType === 'Image') {
      lines.push(`  • ${cid} (Image): [Image]`);
    } else if (compType === 'Card' && props?.child) {
      lines.push(`  • ${cid} (Card): child → ${props.child}`);
    } else if ((compType === 'Column' || compType === 'Row') && props?.children) {
      const ch = props.children as { explicitList?: string[] } | string[];
      const ids = Array.isArray(ch) ? ch : ch?.explicitList ?? [];
      lines.push(`  • ${cid} (${compType}): children → [${ids.join(', ')}]`);
    } else if (compType === 'Button' && props?.child) {
      lines.push(`  • ${cid} (Button): child → ${props.child}`);
    } else if (compType === 'List' && props?.children) {
      const ch = props.children as { explicitList?: string[] } | string[];
      const ids = Array.isArray(ch) ? ch : ch?.explicitList ?? [];
      lines.push(`  • ${cid} (List): [${ids.join(', ')}]`);
    } else if (compType === 'StepCarousel' && props?.steps) {
      const steps = props.steps as string[];
      lines.push(`  • ${cid} (StepCarousel): steps → [${steps.join(', ')}]`);
    } else {
      lines.push(`  • ${cid} (${compType})`);
    }
  });
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
  const videoPlayerRef = useRef<VideoPlayerHandle>(null);
  const navigate = useNavigate();

  const hasVideoSelected = !!videoUrl;
  const hasResult = currentSchema != null;

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
    const tStart = performance.now();
    try {
      // Capture current video frame
      let videoFrame: string | null = null;
      if (videoPlayerRef.current) {
        const t0 = performance.now();
        videoFrame = await videoPlayerRef.current.captureFrame();
        console.log(`[TIMING] App — capture frame: ${(performance.now() - t0).toFixed(0)}ms`, videoFrame ? `(Base64 length: ${videoFrame.length})` : 'null');
      } else {
        console.warn('Video player ref is not available');
      }

      const t1 = performance.now();
      const { uiSchema: schema, verbalSummary } = await askQuestion({
        question,
        videoTime: currentTime,
        videoDuration: duration,
        transcriptSnippet: videoContext.transcriptSnippet,
        videoFrame: videoFrame || undefined,
      });
      const tApi = performance.now() - t1;
      console.log(`[TIMING] App — API (ask): ${tApi.toFixed(0)}ms`);

      if (verbalSummary?.trim()) {
        console.log('[VERBAL ANSWER] App:', verbalSummary.trim());
      }

      // Print a short, readable summary of the UI schema
      console.log('='.repeat(80));
      console.log('UI SCHEMA (summary):');
      console.log(uiSchemaSummaryForLog(schema));
      console.log('='.repeat(80));
      
      setCurrentSchema(schema);

      // Speak short verbal summary via ElevenLabs TTS (duck video volume while playing)
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
          console.log(`[TIMING] App — TTS fetch + play start: ${(performance.now() - t2).toFixed(0)}ms`);
        } catch (e) {
          console.warn('TTS playback failed:', e);
          setIsAiSpeaking(false);
        }
      }

      console.log(`[TIMING] App — TOTAL (to API response): ${(performance.now() - tStart).toFixed(0)}ms`);
    } catch (error) {
      console.error('Error asking question:', error);
      // Show error state
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
            root: 'error-card'
          });
    } finally {
      setIsLoading(false);
    }
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
                            volume={isUserSpeaking || isAiSpeaking ? 0.125 : 1}
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
