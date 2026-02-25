import React from 'react';
import './Column.css';

interface ColumnProps {
  children: string[] | { explicitList: string[] };
  distribution?: 'start' | 'center' | 'end' | 'spaceBetween' | 'spaceAround' | 'spaceEvenly';
  alignment?: 'start' | 'center' | 'end' | 'stretch';
  childComponents?: React.ReactNode[]; // Actual child components to render
}

export const Column: React.FC<ColumnProps> = ({ 
  children, 
  distribution = 'start', 
  alignment = 'start',
  childComponents = []
}) => {
  const childIds = Array.isArray(children) ? children : children.explicitList;
  
  const style: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: distribution === 'start' ? 'flex-start' :
                    distribution === 'center' ? 'center' :
                    distribution === 'end' ? 'flex-end' :
                    distribution === 'spaceBetween' ? 'space-between' :
                    distribution === 'spaceAround' ? 'space-around' :
                    'space-evenly',
    alignItems: alignment === 'start' ? 'flex-start' :
                alignment === 'center' ? 'center' :
                alignment === 'end' ? 'flex-end' :
                'stretch',
    gap: '0.5rem',
  };

  return (
    <div className="a2ui-column" style={style}>
      {childComponents.length > 0 ? childComponents : childIds.map((id, idx) => (
        <span key={idx}>[{id}]</span>
      ))}
    </div>
  );
};


