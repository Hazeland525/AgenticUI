import React from 'react';
import './Divider.css';

interface DividerProps {
  axis?: 'horizontal' | 'vertical';
}

export const Divider: React.FC<DividerProps> = ({ axis = 'horizontal' }) => {
  return (
    <div className={`a2ui-divider a2ui-divider-${axis}`} />
  );
};


