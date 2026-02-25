import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getLibrary, SavedItem, deleteItem } from '../services/libraryService';
import { getUserProfile, UserProfile } from '../services/userProfileService';
import { recommend, RecommendResponse } from '../services/recommendService';
import { getTtsAudio } from '../services/agentService';
import { getTitleFromSchema, getImageUrlFromSchema } from '../utils/schemaExtractors';
import { useVoiceInputGoogleCloud } from '../hooks/useVoiceInputGoogleCloud';
import PlaceCard from './PlaceCard';
import './CollectionsPage.css';

interface CollectionsPageProps {
  onLoadItem?: (item: SavedItem) => void;
}

export const CollectionsPage: React.FC<CollectionsPageProps> = ({ onLoadItem }) => {
  const [items, setItems] = useState<SavedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [recommendInput, setRecommendInput] = useState('');
  const [recommendLoading, setRecommendLoading] = useState(false);
  const [recommendResult, setRecommendResult] = useState<RecommendResponse | null>(null);
  const [recommendError, setRecommendError] = useState<string | null>(null);
  const [lastRecommendQuestion, setLastRecommendQuestion] = useState<string | null>(null);
  const navigate = useNavigate();

  const { isListening } = useVoiceInputGoogleCloud({
    onTranscript: (text) => {
      console.log('User said:', text);
      setRecommendInput(text);
      // Auto-submit after voice input
      if (text.trim()) {
        handleRecommend(text.trim());
      }
    },
    onError: (error) => {
      console.error('Voice input error:', error);
      setRecommendError('Failed to transcribe speech. Please try again.');
    },
  });

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        setLoading(true);
        const [libraryItems, userProfile] = await Promise.all([
          getLibrary(),
          getUserProfile(),
        ]);
        if (!cancelled) {
          setItems(libraryItems);
          setProfile(userProfile ?? null);
        }
      } catch (err) {
        console.error('Error loading library:', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  const handleBack = () => {
    navigate(-1);
  };

  const handleCardClick = (item: SavedItem) => {
    if (onLoadItem) onLoadItem(item);
    navigate('/');
  };

  const handleRecommend = async (message?: string) => {
    const msg = (message || recommendInput).trim();
    if (!msg) return;
    setLastRecommendQuestion(msg);
    setRecommendLoading(true);
    setRecommendError(null);
    setRecommendResult(null);
    const tStart = performance.now();
    try {
      const t0 = performance.now();
      const data = await recommend(msg);
      const tApi = performance.now() - t0;
      console.log(`[TIMING] Collections — API (recommend): ${tApi.toFixed(0)}ms`);
      if (data.verbalSummary?.trim()) {
        console.log('[VERBAL ANSWER] Collections:', data.verbalSummary.trim());
      }
      setRecommendResult(data);
      if (data.verbalSummary?.trim()) {
        try {
          const t1 = performance.now();
          const audioUrl = await getTtsAudio(data.verbalSummary.trim());
          const audio = new Audio(audioUrl);
          audio.onended = () => URL.revokeObjectURL(audioUrl);
          audio.onerror = () => URL.revokeObjectURL(audioUrl);
          await audio.play();
          console.log(`[TIMING] Collections — TTS fetch + play start: ${(performance.now() - t1).toFixed(0)}ms`);
        } catch (e) {
          console.warn('Recommendation TTS playback failed:', e);
        }
      }
      console.log(`[TIMING] Collections — TOTAL (to API response): ${(performance.now() - tStart).toFixed(0)}ms`);
    } catch (err) {
      setRecommendError(err instanceof Error ? err.message : 'Request failed');
    } finally {
      setRecommendLoading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, itemId: number) => {
    e.stopPropagation();
    try {
      await deleteItem(itemId);
      setItems((prevItems) => prevItems.filter((item) => item.id !== itemId));
    } catch (err) {
      console.error('Failed to delete item:', err);
    }
  };

  return (
    <div className="collections-page">
      <header className="collections-header">
        <button
          type="button"
          className="collections-back-btn"
          onClick={handleBack}
          aria-label="Go back"
        >
          <img src="/icons/back.svg" alt="" />
        </button>
        <div className="collections-header-title-wrap">
          <h1 className="collections-header-title">
            {profile?.name ? `${profile.name}'s collections` : 'My collections'}
          </h1>
        </div>
      </header>

      <main className="collections-content">
        <section className={`collections-recommend${recommendResult ? ' has-results' : ''}`}>
          {isListening ? (
            <div className="voice-status collections-voice-status-inline">
              <span className="voice-status-text">I'm listening...</span>
            </div>
          ) : recommendLoading ? (
            <div className="voice-status collections-voice-status-inline">
              <span className="voice-status-text">Processing...</span>
            </div>
          ) : !recommendResult ? (
            <div className="collections-recommend-idle">
              <div className="collections-recommend-prompt">
                <span className="collections-recommend-prompt-mic" aria-hidden>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3Z" />
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                    <line x1="12" x2="12" y1="19" y2="22" />
                  </svg>
                </span>
                <span className="collections-recommend-prompt-text">Ask for getting recommendations</span>
              </div>
              <div className="collections-recommend-input-wrap">
                <label htmlFor="collections-recommend-input" className="collections-recommend-label">
                  Get recommendations (press S for voice, or type)
                </label>
                <div className="collections-recommend-row">
                  <input
                    id="collections-recommend-input"
                    type="text"
                    className="collections-recommend-input"
                    placeholder="Recommend me some restaurants for Friday"
                    value={recommendInput}
                    onChange={(e) => setRecommendInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleRecommend()}
                    disabled={recommendLoading}
                  />
                  <button
                    type="button"
                    className="collections-recommend-btn"
                    onClick={() => handleRecommend()}
                    disabled={recommendLoading || !recommendInput.trim()}
                  >
                    Get recommendations
                  </button>
                </div>
                {recommendError && (
                  <p className="collections-recommend-error">{recommendError}</p>
                )}
              </div>
            </div>
          ) : null}
          {recommendResult && (
            <div className="collections-recommend-result">
              {lastRecommendQuestion && (
                <div className="collections-recommend-user-question">
                  "{lastRecommendQuestion}"
                </div>
              )}
              <p className="collections-recommend-reasoning">{recommendResult.reasoning}</p>
              <div className="collections-recommend-grid">
                {recommendResult.places.map((place, i) => (
                  <PlaceCard
                    key={place.placeId ?? i}
                    name={place.name}
                    address={place.address}
                    rating={place.rating}
                    priceLevel={place.priceLevel}
                    photoUri={place.photoUri}
                    placeUrl={place.placeUrl}
                  />
                ))}
              </div>
            </div>
          )}
        </section>

        {loading && (
          <div className="collections-loading">
            <p>Loading saved items...</p>
          </div>
        )}
        {!loading && items.length === 0 && (
          <div className="collections-empty">
            <p>No saved items yet</p>
          </div>
        )}
        {!loading && items.length > 0 && (
          <div className="collections-grid">
            {items.map((item) => {
              const imageUrl = getImageUrlFromSchema(item.uiSchema);
              const title = getTitleFromSchema(item.uiSchema) ?? item.question;
              return (
                <div
                  key={item.id}
                  role="button"
                  tabIndex={0}
                  className="collections-card"
                  onClick={() => handleCardClick(item)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleCardClick(item);
                    }
                  }}
                >
                  {imageUrl ? (
                    <img
                      src={imageUrl}
                      alt=""
                      className="collections-card-image"
                    />
                  ) : (
                    <span className="collections-card-no-image" aria-hidden />
                  )}
                  <span className="collections-card-title">{title}</span>
                  <button
                    type="button"
                    className="collections-card-delete"
                    onClick={(e) => handleDelete(e, item.id)}
                    aria-label="Delete item"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.5 4.478v.227a48.816 48.816 0 013.878.512.75.75 0 11-.256 1.478l-.209-.035-1.005 13.07a3 3 0 01-2.991 2.77H8.084a3 3 0 01-2.991-2.77L4.087 6.66l-.209.035a.75.75 0 01-.256-1.478A48.567 48.567 0 017.5 4.705v-.227c0-1.564 1.213-2.9 2.816-2.951a52.662 52.662 0 013.369 0c1.603.051 2.815 1.387 2.815 2.951zm-6.136-1.452a51.196 51.196 0 013.273 0C14.39 3.05 15 3.684 15 4.478v.113a49.488 49.488 0 00-6 0v-.113c0-.794.609-1.428 1.364-1.452zm-.355 5.945a.75.75 0 10-1.5.058l.347 9a.75.75 0 101.499-.058l-.346-9zm5.48.058a.75.75 0 10-1.498-.058l-.347 9a.75.75 0 001.5.058l.345-9z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
};
