import React from 'react';
import './List.css';

interface ListProps {
  children: string[] | { explicitList: string[] } | { template: { componentId: string; dataBinding?: string } };
  direction?: 'horizontal' | 'vertical';
  childComponents?: React.ReactNode[]; // Actual child components to render
}

export const List: React.FC<ListProps> = ({ 
  children, 
  direction = 'vertical',
  childComponents = []
}) => {
  let childIds: string[] = [];
  
  if (Array.isArray(children)) {
    childIds = children;
  } else if ('explicitList' in children) {
    childIds = children.explicitList;
  } else if ('template' in children) {
    // Template-based lists - for MVP, just show placeholder
    childIds = [children.template.componentId];
  }

  const style: React.CSSProperties = {
    display: 'flex',
    flexDirection: direction === 'horizontal' ? 'row' : 'column',
    gap: '0.5rem',
  };

  return (
    <div className={`a2ui-list a2ui-list-${direction}`} style={style}>
      {childComponents.length > 0 ? childComponents : childIds.map((id, idx) => (
        <div key={idx}>[{id}]</div>
      ))}
    </div>
  );
};


