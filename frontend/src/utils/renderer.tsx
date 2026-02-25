import React from 'react';
import { UIComponent, UIResponse, ComponentDefinition } from '../types/schema';
import { componentCatalog } from '../components/catalog';

interface RendererProps {
  schema: UIResponse;
  onSave?: (componentId: string) => void;
}

// Helper to get component type name from component definition
function getComponentType(component: ComponentDefinition): string {
  // Add null/undefined check
  if (!component || typeof component !== 'object') {
    console.warn('Renderer: Invalid component definition:', component);
    return 'Unknown';
  }
  
  // Get the first key from the component object (it should be the component type)
  const keys = Object.keys(component);
  if (keys.length > 0) {
    return keys[0]; // Return the first key (e.g., "Card", "Text", "Image")
  }
  return 'Unknown';
}

// Helper to get component props from component definition
function getComponentProps(component: ComponentDefinition): any {
  // Add null/undefined check
  if (!component || typeof component !== 'object') {
    console.warn('Renderer: Invalid component definition for props:', component);
    return {};
  }
  
  // Get the first key and return its value
  const keys = Object.keys(component);
  if (keys.length > 0) {
    const key = keys[0] as keyof ComponentDefinition;
    return (component as any)[key];
  }
  return {};
}

// Fallback label when a Button has no child component (e.g. LLM omitted it)
function getButtonFallbackLabel(componentId: string): string {
  const id = (componentId || '').toLowerCase();
  if (id.includes('save')) return 'Save';
  if (id.includes('speak')) return 'Speak';
  if (id.includes('phone')) return 'Phone';
  return 'Button';
}

export const renderComponents = (schema: UIResponse, onSave?: (componentId: string) => void): React.ReactNode[] => {
  if (!schema || !schema.components || schema.components.length === 0) {
    console.warn('Renderer: No components in schema');
    return [];
  }

  // Build component map for quick lookup
  const componentMap = new Map<string, UIComponent>();
  schema.components.forEach(comp => {
    componentMap.set(comp.id, comp);
  });

  // Recursive function to render a component and its children
  const renderComponent = (componentId: string, visited: Set<string> = new Set()): React.ReactNode => {
    // Prevent infinite loops
    if (visited.has(componentId)) {
      console.warn(`Circular reference detected for component: ${componentId}`);
      return null;
    }
    visited.add(componentId);

    const component = componentMap.get(componentId);
    if (!component) {
      // Missing refs can happen when backend removes a component (e.g. placeholder image) but a parent still lists the id
      return null;
    }

    // Add check for component.component
    if (!component.component) {
      console.warn(`Component ${componentId} has no component definition`);
      return null;
    }
    
    const componentType = getComponentType(component.component);
    const Component = componentCatalog[componentType];
    
    if (!Component) {
      console.warn(`Component type "${componentType}" not found in catalog. Available:`, Object.keys(componentCatalog));
      return null;
    }

    const props = getComponentProps(component.component);
    
    // Filter out any component definition objects from props (safety check)
    const cleanProps = { ...props };
    // Remove any keys that look like component definitions (e.g., {Text: {...}})
    Object.keys(cleanProps).forEach(key => {
      if (cleanProps[key] && typeof cleanProps[key] === 'object' && !Array.isArray(cleanProps[key])) {
        const obj = cleanProps[key];
        // Check if it looks like a component definition (has keys like Text, Image, etc.)
        const componentKeys = ['Text', 'Image', 'Button', 'Row', 'Column', 'Card', 'List', 'Divider', 'Progress', 'Chip', 'StepCarousel'];
        if (Object.keys(obj).some(k => componentKeys.includes(k))) {
          console.warn(`Renderer: Found component definition in props for ${componentId}, removing:`, key);
          delete cleanProps[key];
        }
      }
    });
    
    const handleSave = () => {
      if (onSave) {
        onSave(component.id);
      }
    };

    // Handle child references based on component type
    let childComponents: React.ReactNode[] | undefined;
    let childComponent: React.ReactNode | undefined;

    if (componentType === 'Row' || componentType === 'Column') {
      const childIds = Array.isArray(props.children) 
        ? props.children 
        : ('explicitList' in props.children ? props.children.explicitList : []);
      childComponents = childIds.map(id => renderComponent(id, new Set(visited)));
    } else if (componentType === 'Card' || componentType === 'Button') {
      if (props.child && typeof props.child === 'string') {
        childComponent = renderComponent(props.child, new Set(visited));
      } else {
        if (componentType === 'Button') {
          // Button without child: use fallback label so it still renders (no warning)
          childComponent = React.createElement('span', { className: 'a2ui-button-fallback' }, getButtonFallbackLabel(componentId));
        } else {
          if (props.child) {
            console.warn(`Component ${componentId} (${componentType}) has invalid child property (not a string):`, props.child);
          } else {
            console.warn(`Component ${componentId} (${componentType}) has no child property`);
          }
          childComponent = null;
        }
      }
    } else if (componentType === 'List') {
      if (Array.isArray(props.children)) {
        childComponents = props.children.map(id => renderComponent(id, new Set(visited)));
      } else if ('explicitList' in props.children) {
        childComponents = props.children.explicitList.map(id => renderComponent(id, new Set(visited)));
      } else if ('template' in props.children) {
        // For template-based lists, render the template component
        childComponent = renderComponent(props.children.template.componentId, new Set(visited));
      }
    } else if (componentType === 'StepCarousel') {
      // StepCarousel takes an array of step component IDs
      const stepIds = Array.isArray(props.steps) ? props.steps : [];
      childComponents = stepIds.map(id => renderComponent(id, new Set(visited)));
    }
    // Progress component doesn't have children, it's self-contained

    // Render the component with resolved children
    if (childComponents !== undefined) {
      return (
        <Component
          key={component.id}
          {...cleanProps}
          childComponents={childComponents}
          onSave={handleSave}
        />
      );
    } else if (childComponent !== undefined) {
      return (
        <Component
          key={component.id}
          {...cleanProps}
          childComponent={childComponent}
          onSave={handleSave}
        />
      );
    } else {
      return (
        <Component
          key={component.id}
          {...cleanProps}
          onSave={handleSave}
        />
      );
    }
  };

  // Determine root component(s)
  const rootIds = schema.root 
    ? [schema.root]
    : schema.components.length > 0 
      ? [schema.components[0].id] // Default to first component
      : [];

  // Render root components
  const rendered = rootIds.map(id => renderComponent(id)).filter(Boolean) as React.ReactNode[];
  return rendered;
};

