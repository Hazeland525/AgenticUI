import React, { useMemo } from 'react';
import { UIResponse, UIComponent } from '../types/schema';
import { renderComponents } from '../utils/renderer';
import './Sidebar.css';

interface SidebarProps {
  onAskQuestion: (question: string) => Promise<void>;
  onSave?: (uiSchema: UIResponse) => void;
  onMuteToggle?: () => void;
  isLoading?: boolean;
  currentSchema?: UIResponse | null;
  currentQuestion?: string;
}

// Helper to extract image URL from Image component
function extractImageUrl(component: UIComponent): string | null {
  const compDef = component.component;
  if (!compDef || typeof compDef !== 'object') return null;
  
  if ('Image' in compDef) {
    const imageProps = compDef.Image;
    const urlValue = imageProps?.url;
    
    if (typeof urlValue === 'string') {
      return urlValue;
    } else if (urlValue && typeof urlValue === 'object') {
      if ('literalString' in urlValue) {
        return urlValue.literalString;
      }
    }
  }
  return null;
}

// Helper to find and extract background image from schema
function findBackgroundImage(schema: UIResponse | null): { url: string; componentId: string } | null {
  if (!schema || !schema.components) return null;
  
  // First, try to find an Image with hero usageHint
  for (const component of schema.components) {
    const compDef = component.component;
    if (compDef && typeof compDef === 'object' && 'Image' in compDef) {
      const imageProps = compDef.Image;
      const usageHint = imageProps?.usageHint;
      if (usageHint === 'hero') {
        const url = extractImageUrl(component);
        if (url) {
          return { url, componentId: component.id };
        }
      }
    }
  }
  
  // If no hero found, use the first Image component
  for (const component of schema.components) {
    const compDef = component.component;
    if (compDef && typeof compDef === 'object' && 'Image' in compDef) {
      const url = extractImageUrl(component);
      if (url) {
        return { url, componentId: component.id };
      }
    }
  }
  
  return null;
}

// Helper to filter out Image components from schema
function filterImageComponents(schema: UIResponse, imageComponentIds: Set<string>): UIResponse {
  return {
    ...schema,
    components: schema.components.filter(comp => !imageComponentIds.has(comp.id)),
  };
}

export const Sidebar: React.FC<SidebarProps> = ({
  onAskQuestion,
  onSave,
  onMuteToggle,
  isLoading = false,
  currentSchema = null,
  currentQuestion = '',
}) => {
  const handleSave = (componentId: string) => {
    if (currentSchema && onSave) {
      onSave(currentSchema);
    }
  };

  // Extract background image
  const backgroundImage = useMemo(() => {
    return findBackgroundImage(currentSchema);
  }, [currentSchema]);

  // Filter out image components from schema for rendering
  const filteredSchema = useMemo(() => {
    if (!currentSchema || !backgroundImage) return currentSchema;
    return filterImageComponents(currentSchema, new Set([backgroundImage.componentId]));
  }, [currentSchema, backgroundImage]);

  return (
    <div className="sidebar">
      {/* Background image container that can overflow */}
      {backgroundImage && (
        <div 
          className="sidebar-background-image"
          style={{
            backgroundImage: `url(${backgroundImage.url})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat',
          }}
        />
      )}
      
      {/* Gradient overlay for merging effect */}
      {backgroundImage && <div className="sidebar-gradient-overlay" />}
      
      <div className="sidebar-content">
        {/* Content wrapper */}
        <div className="sidebar-content-wrapper">
          {currentQuestion && (
            <div className="sidebar-question">
              "{currentQuestion}"
            </div>
          )}
          {isLoading && (
            <div className="sidebar-loading">
              <p>Processing your question...</p>
            </div>
          )}
          {!isLoading && filteredSchema && (
            <div className="sidebar-components">
              {renderComponents(filteredSchema, handleSave, onMuteToggle).map((component, index) => (
                <div key={index} className="sidebar-answer-wrapper">
                  {component}
                </div>
              ))}
            </div>
          )}
          {!isLoading && !filteredSchema && (
            <div className="sidebar-empty">
              <p>Ask a question to see results here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};


