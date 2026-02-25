import React, { useState, useEffect, useRef } from 'react';
import './StepCarousel.css';

interface StepCarouselProps {
  steps: string[]; // Array of step component IDs
  current?: number;
  total?: number;
  childComponents?: React.ReactNode[]; // Rendered step components
}

export const StepCarousel: React.FC<StepCarouselProps> = ({ 
  steps = [],
  current: initialCurrent = 0,
  total = 0,
  childComponents = []
}) => {
  // Use childComponents length if available, otherwise use steps array length
  const numSteps = childComponents.length > 0 ? childComponents.length : steps.length;
  const [currentStep, setCurrentStep] = useState(Math.max(0, Math.min(initialCurrent, numSteps - 1)));
  const carouselRef = useRef<HTMLDivElement>(null);

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(0, prev - 1));
  };

  const handleNext = () => {
    setCurrentStep(prev => Math.min(numSteps - 1, prev + 1));
  };

  const handleDotClick = (index: number) => {
    setCurrentStep(index);
  };

  // Keyboard navigation for TV/remote control
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Only handle if no input is focused (allow typing in inputs)
      if (document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA') {
        return;
      }

      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        setCurrentStep(prev => Math.max(0, prev - 1));
      } else if (event.key === 'ArrowRight') {
        event.preventDefault();
        setCurrentStep(prev => Math.min(numSteps - 1, prev + 1));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [numSteps]);

  const currentStepComponent = childComponents[currentStep] || null;

  return (
    <div className="a2ui-step-carousel" ref={carouselRef} tabIndex={0}>
      <div className="a2ui-step-carousel-content">
        {currentStepComponent}
      </div>
      
      {numSteps > 1 && (
        <div className="a2ui-step-carousel-progress">
          {Array.from({ length: numSteps }).map((_, index) => (
            <button
              key={index}
              className={`a2ui-step-carousel-dot ${index === currentStep ? 'a2ui-step-carousel-dot-active' : ''}`}
              onClick={() => handleDotClick(index)}
              aria-label={`Go to step ${index + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
};
