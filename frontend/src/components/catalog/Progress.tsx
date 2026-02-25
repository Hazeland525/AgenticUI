import React from 'react';
import './Progress.css';

interface ProgressProps {
  current?: number;
  total?: number;
  variant?: 'dots' | 'bar';
}

export const Progress: React.FC<ProgressProps> = ({ 
  current = 0, 
  total = 0,
  variant = 'dots'
}) => {
  if (variant === 'bar') {
    const percentage = total > 0 ? (current / total) * 100 : 0;
    return (
      <div className="a2ui-progress a2ui-progress-bar">
        <div 
          className="a2ui-progress-bar-fill" 
          style={{ width: `${percentage}%` }}
        />
      </div>
    );
  }

  // Dots variant (default)
  const dots = [];
  for (let i = 0; i < total; i++) {
    dots.push(
      <div
        key={i}
        className={`a2ui-progress-dot ${i < current ? 'a2ui-progress-dot-active' : ''}`}
      />
    );
  }

  return (
    <div className="a2ui-progress a2ui-progress-dots">
      {dots}
    </div>
  );
};
