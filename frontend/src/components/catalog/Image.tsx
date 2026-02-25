import React from 'react';
import './Image.css';

interface ImageProps {
  url?: string | { literalString: string } | { path: string };
  imageUrl?: string | { literalString: string } | { path: string };
  fit?: 'contain' | 'cover' | 'fill' | 'none' | 'scale-down';
  usageHint?: 'hero' | 'thumbnail' | 'icon';
}

export const Image: React.FC<ImageProps> = ({ url, imageUrl, fit = 'cover', usageHint }) => {
  // Schema may use "url" or "imageUrl" (camelCase from LLM)
  const urlProp = url ?? imageUrl;
  // Extract URL value (guard against undefined from schema)
  let urlValue = '';
  if (urlProp != null) {
    if (typeof urlProp === 'string') {
      urlValue = urlProp;
    } else if (typeof urlProp === 'object' && 'literalString' in urlProp) {
      urlValue = urlProp.literalString;
    } else if (typeof urlProp === 'object' && 'path' in urlProp) {
      // For MVP, just show placeholder. In full implementation, would resolve from data model
      urlValue = '';
    }
  }

  const className = `a2ui-image a2ui-image-${usageHint || 'default'}`;
  const style: React.CSSProperties = {
    objectFit: fit,
  };

  if (!urlValue) {
    return null;
  }

  return (
    <img 
      src={urlValue} 
      alt="" 
      className={className}
      style={style}
      onLoad={() => {}}
      onError={(e) => {
        console.error('Image failed to load:', e);
        console.error('Failed URL:', urlValue.substring(0, 100));
      }}
    />
  );
};

