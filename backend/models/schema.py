"""
A2UI-style primitive component schema.
Uses adjacency list model: flat list of components that reference each other by ID.
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union, Literal

# String value can be literal or path (simplified for MVP)
StringValue = Union[str, Dict[str, str]]

# Component definitions
class TextComponent(BaseModel):
    Text: Dict[str, Any]  # { "text": StringValue, "usageHint": Optional[str] }

class ImageComponent(BaseModel):
    Image: Dict[str, Any]  # { "url": StringValue, "fit": Optional[str], "usageHint": Optional[str] }

class ButtonComponent(BaseModel):
    Button: Dict[str, Any]  # { "child": str, "primary": Optional[bool], "action": Optional[Dict], "icon": Optional[str] }

class ProgressComponent(BaseModel):
    Progress: Dict[str, Any]  # { "current": Optional[int], "total": Optional[int], "variant": Optional[str] }

class RowComponent(BaseModel):
    Row: Dict[str, Any]  # { "children": List[str] or Dict, "distribution": Optional[str], "alignment": Optional[str] }

class ColumnComponent(BaseModel):
    Column: Dict[str, Any]  # { "children": List[str] or Dict, "distribution": Optional[str], "alignment": Optional[str] }

class CardComponent(BaseModel):
    Card: Dict[str, Any]  # { "child": str, "background": Optional[str] }

class ListComponent(BaseModel):
    List: Dict[str, Any]  # { "children": List[str] or Dict, "direction": Optional[str] }

class DividerComponent(BaseModel):
    Divider: Dict[str, Any]  # { "axis": Optional[str] }

class ChipComponent(BaseModel):
    Chip: Dict[str, Any]  # { "label": StringValue, "icon": Optional[str], "selected": Optional[bool] }

class StepCarouselComponent(BaseModel):
    StepCarousel: Dict[str, Any]  # { "steps": List[str], "current": Optional[int], "total": Optional[int] }

# Component union type (using discriminated union pattern)
ComponentDefinition = Union[
    TextComponent,
    ImageComponent,
    ButtonComponent,
    RowComponent,
    ColumnComponent,
    CardComponent,
    ListComponent,
    DividerComponent,
    ProgressComponent,
    ChipComponent,
    StepCarouselComponent
]

class UIComponent(BaseModel):
    """A2UI component in adjacency list format"""
    id: str
    weight: Optional[float] = None  # For flex-grow in Row/Column
    component: Dict[str, Any]  # Flexible component definition (e.g., {"Text": {...}} or {"Row": {...}})

class UIResponse(BaseModel):
    """A2UI response with flat list of components"""
    meta: Optional[Dict[str, Any]] = None  # { "intent": "...", "recipe": "..." } - for debugging/analytics
    components: List[UIComponent]
    root: Optional[str] = None  # Root component ID (optional, defaults to first component)

