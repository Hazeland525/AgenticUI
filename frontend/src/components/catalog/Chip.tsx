import React from 'react';
import './Chip.css';

interface ChipProps {
  label: string | { literalString: string } | { path: string };
  icon?: string;
  selected?: boolean;
}

export const Chip: React.FC<ChipProps> = ({ label, icon, selected = false }) => {
  // Extract label value
  let labelValue = '';
  if (typeof label === 'string') {
    labelValue = label;
  } else if ('literalString' in label) {
    labelValue = label.literalString;
  } else if ('path' in label) {
    labelValue = `[${label.path}]`;
  }

  const iconSrc = icon ? `/icons/${icon}.svg` : null;

  return (
    <div className={`a2ui-chip ${selected ? 'a2ui-chip-selected' : ''}`}>
      {iconSrc && (
        <img 
          src={iconSrc} 
          alt="" 
          className="a2ui-chip-icon"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = 'none';
          }}
        />
      )}
      <span className="a2ui-chip-label">{labelValue}</span>
    </div>
  );
};
