import React from 'react';
import './Text.css';

interface TextProps {
  text: string | { literalString: string } | { path: string };
  usageHint?: 'h1' | 'h2' | 'body' | 'label';
}

export const Text: React.FC<TextProps> = ({ text, usageHint = 'body' }) => {
  // Extract text value
  let textValue = '';
  if (typeof text === 'string') {
    textValue = text;
  } else if ('literalString' in text) {
    textValue = text.literalString;
  } else if ('path' in text) {
    // For MVP, just show the path. In full implementation, would resolve from data model
    textValue = `[${text.path}]`;
  }

  // Map semantic usageHints to HTML tags
  const Tag = usageHint === 'h1' ? 'h1' : 
              usageHint === 'h2' ? 'h2' : 
              usageHint === 'label' ? 'small' : 'p';

  return (
    <Tag className={`a2ui-text a2ui-text-${usageHint}`}>
      {textValue}
    </Tag>
  );
};


