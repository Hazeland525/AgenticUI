import React from 'react';
import './Button.css';

interface ButtonProps {
  child?: string; // ID of child component (rendered separately; optional when renderer provides fallback)
  primary?: boolean;
  action?: {
    name: string;
    context?: Record<string, any>;
  };
  childComponent?: React.ReactNode; // The actual child component to render
  onSave?: () => void;
  icon?: string; // Icon name or SVG path
}

// Helper to load icon SVG
const loadIcon = (iconName: string): string | null => {
  try {
    // Try to load from public/icons directory
    return `/icons/${iconName}.svg`;
  } catch {
    return null;
  }
};

export const Button: React.FC<ButtonProps> = ({ 
  child, 
  primary = false, 
  action, 
  childComponent,
  onSave,
  icon
}) => {
  const handleClick = () => {
    if (action) {
      console.log('Button action:', action);
      // In full implementation, would dispatch action event
    }
    if (onSave) {
      onSave();
    }
  };

  const iconSrc = icon ? loadIcon(icon) : null;

  // Ensure we only render valid React nodes, not objects
  const renderContent = () => {
    if (childComponent && React.isValidElement(childComponent)) {
      return childComponent;
    }
    if (childComponent && typeof childComponent === 'object') {
      console.warn('Button received invalid childComponent (object):', childComponent);
      return null;
    }
    if (child) {
      return child;
    }
    return null;
  };

  // Check if this is an action button (has icon and child text is "Save", "Speak", "Phone", or empty)
  const childText = childComponent && typeof childComponent === 'object' && React.isValidElement(childComponent)
    ? (childComponent.props?.text?.literalString || childComponent.props?.text || '')
    : (typeof childComponent === 'string' ? childComponent : '');
  
  const isActionButton = icon && (
    !childText || 
    childText.trim() === '' || 
    ['Save', 'Speak', 'Phone'].includes(childText.trim())
  );

  return (
    <button 
      className={`a2ui-button ${primary ? 'a2ui-button-primary' : 'a2ui-button-secondary'} ${icon ? 'a2ui-button-with-icon' : ''} ${isActionButton ? 'a2ui-button-action' : ''}`}
      onClick={handleClick}
    >
      {iconSrc && (
        <img 
          src={iconSrc} 
          alt="" 
          className="a2ui-button-icon"
          onError={(e) => {
            // Hide icon if it fails to load
            (e.target as HTMLImageElement).style.display = 'none';
          }}
        />
      )}
      {!isActionButton && renderContent()}
    </button>
  );
};


