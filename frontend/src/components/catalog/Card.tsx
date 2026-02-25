import React from 'react';
import './Card.css';

interface CardProps {
  child: string; // ID of child component
  childComponent?: React.ReactNode; // Actual child component to render
  background?: string; // Background color (e.g., "white", "transparent", "#f5f5f5")
}

export const Card: React.FC<CardProps> = ({ child, childComponent, background }) => {
  const style: React.CSSProperties = {
    backgroundColor: 'transparent', // Always transparent, ignore background prop
  };
  
  // Only handle transparent case for border removal
  if (background === 'transparent') {
    style.boxShadow = 'none';
    style.border = 'none';
  }

  const className = background === 'transparent' 
    ? 'a2ui-card a2ui-card-transparent' 
    : 'a2ui-card';

  return (
    <div className={className} style={style}>
      {childComponent || <span>[{child}]</span>}
    </div>
  );
};

