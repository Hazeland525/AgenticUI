import React, { useState, useEffect } from 'react';
import { getLibrary, deleteItem, SavedItem } from '../services/libraryService';
import { renderComponents } from '../utils/renderer';
import './Library.css';

interface LibraryProps {
  onLoadItem?: (item: SavedItem) => void;
}

export const Library: React.FC<LibraryProps> = ({ onLoadItem }) => {
  const [items, setItems] = useState<SavedItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLibrary();
  }, []);

  const loadLibrary = async () => {
    try {
      setLoading(true);
      const libraryItems = await getLibrary();
      setItems(libraryItems);
    } catch (error) {
      console.error('Error loading library:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (itemId: number) => {
    try {
      await deleteItem(itemId);
      await loadLibrary();
    } catch (error) {
      console.error('Error deleting item:', error);
    }
  };

  const handleLoad = (item: SavedItem) => {
    if (onLoadItem) {
      onLoadItem(item);
    }
  };

  if (loading) {
    return (
      <div className="library">
        <div className="library-header">
          <h2>Library</h2>
        </div>
        <div className="library-loading">
          <p>Loading saved items...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="library">
      <div className="library-header">
        <h2>Library</h2>
        <button className="library-refresh" onClick={loadLibrary}>
          Refresh
        </button>
      </div>
      <div className="library-content">
        {items.length === 0 ? (
          <div className="library-empty">
            <p>No saved items yet</p>
          </div>
        ) : (
          items.map((item) => (
            <div key={item.id} className="library-item">
              <div className="library-item-header">
                <h3 className="library-item-question">{item.question}</h3>
                <div className="library-item-actions">
                  <button
                    className="library-item-load"
                    onClick={() => handleLoad(item)}
                  >
                    Load
                  </button>
                  <button
                    className="library-item-delete"
                    onClick={() => handleDelete(item.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
              <div className="library-item-preview">
                {renderComponents(item.uiSchema)}
              </div>
              <div className="library-item-meta">
                {item.videoTime && (
                  <span>Video time: {item.videoTime.toFixed(2)}s</span>
                )}
                <span>{new Date(item.timestamp).toLocaleString()}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

