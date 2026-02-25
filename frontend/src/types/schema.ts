// A2UI-style primitive component schema
// Uses adjacency list model: flat list of components that reference each other by ID

// String value can be literal or path (simplified: just literal for MVP)
export type StringValue = string | { literalString: string } | { path: string };

// Component definitions
export interface TextComponent {
  Text: {
    text: StringValue;
    usageHint?: 'h1' | 'h2' | 'body' | 'label';
  };
}

export interface ImageComponent {
  Image: {
    url: StringValue;
    fit?: 'contain' | 'cover' | 'fill' | 'none' | 'scale-down';
    usageHint?: 'hero' | 'thumbnail' | 'icon';
  };
}

export interface ButtonComponent {
  Button: {
    child: string; // ID of child component (usually Text)
    primary?: boolean;
    action?: {
      name: string;
      context?: Record<string, any>;
    };
    icon?: string; // Icon name or SVG path
  };
}

export interface RowComponent {
  Row: {
    children: string[] | { explicitList: string[] };
    distribution?: 'start' | 'center' | 'end' | 'spaceBetween' | 'spaceAround' | 'spaceEvenly';
    alignment?: 'start' | 'center' | 'end' | 'stretch';
  };
}

export interface ColumnComponent {
  Column: {
    children: string[] | { explicitList: string[] };
    distribution?: 'start' | 'center' | 'end' | 'spaceBetween' | 'spaceAround' | 'spaceEvenly';
    alignment?: 'start' | 'center' | 'end' | 'stretch';
  };
}

export interface CardComponent {
  Card: {
    child: string; // ID of child component
    background?: string; // Background color (e.g., "white", "transparent", "#f5f5f5")
  };
}

export interface ListComponent {
  List: {
    children: string[] | { explicitList: string[] } | { template: { componentId: string; dataBinding?: string } };
    direction?: 'horizontal' | 'vertical';
  };
}

export interface DividerComponent {
  Divider: {
    axis?: 'horizontal' | 'vertical';
  };
}

export interface ProgressComponent {
  Progress: {
    current?: number;
    total?: number;
    variant?: 'dots' | 'bar';
  };
}

export interface ChipComponent {
  Chip: {
    label: StringValue;
    icon?: string;
    selected?: boolean;
  };
}

export interface StepCarouselComponent {
  StepCarousel: {
    steps: string[]; // Array of step component IDs
    current?: number;
    total?: number;
  };
}

// Union of all component types
export type ComponentDefinition = 
  | TextComponent 
  | ImageComponent 
  | ButtonComponent 
  | RowComponent 
  | ColumnComponent 
  | CardComponent 
  | ListComponent 
  | DividerComponent
  | ProgressComponent
  | ChipComponent
  | StepCarouselComponent;

// UI Component (adjacency list model)
export interface UIComponent {
  id: string;
  weight?: number; // For flex-grow in Row/Column
  component: ComponentDefinition;
}

// UI Response
export interface UIResponse {
  meta?: {
    intent?: string;
    recipe?: string;
    [key: string]: any;
  };
  components: UIComponent[];
  root?: string; // Root component ID (optional, defaults to first component)
}

