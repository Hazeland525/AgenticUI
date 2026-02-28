"""
Prompt builder for generating UI schema prompts.
Similar to A2UI's prompt_builder.py pattern.
Uses conditional instructions to let the LLM decide which component type to use.
"""
import json
from typing import Optional, Dict, List


def detect_intent(question: str) -> str:
    """
    Detect user intent from question using keyword matching.
    Uses pattern-based intents that work across multiple domains.
    
    Args:
        question: User's question
        
    Returns:
        Intent string: "SIMPLE_IDENTIFICATION", "STEP_BY_STEP", "ITEM_LISTING", "ENTITY_DETAIL", or "OTHER"
    """
    q = question.lower()
    
    # Step-by-step patterns: how-to, tutorial, guide, steps, instructions
    if any(k in q for k in ["how to", "how do", "steps", "guide", "tutorial", "instructions", "walkthrough", "recipe", "make", "cook", "build", "create", "assemble"]):
        return "STEP_BY_STEP"
    
    # Item listing patterns: where, nearby, list, show me, find, options
    if any(k in q for k in ["where", "nearby", "near me", "list", "show me", "find", "options", "available", "stores", "restaurants", "places", "locations", "near", "can i buy", "can i find"]):
        return "ITEM_LISTING"
    
    # Simple identification patterns: basic "what is this", "what is X" (simple questions)
    if any(k in q for k in ["what is this", "what's this", "what is that", "what's that", "what is it", "what's it"]):
        return "SIMPLE_IDENTIFICATION"
    
    # Entity detail patterns: detailed explanations, tell me about, identify, explain
    if any(k in q for k in ["what is", "what's", "who is", "who's", "tell me about", "identify", "explain", "describe", "what are", "what food", "what object"]):
        return "ENTITY_DETAIL"
    
    return "OTHER"


class PromptBuilder:
    """Builds prompts for LLM to generate UI schemas"""
    
    def __init__(self):
        self.examples = self._load_examples()
        self.component_rules = self._load_component_rules()
    
    def _load_component_rules(self) -> str:
        """Load conditional rules for component composition (A2UI primitive style)"""
        return """
--- COMPONENT COMPOSITION RULES ---
You MUST compose UI using primitive components. Build layouts by combining:

**Layout Components:**
- Row: Horizontal layout (children arranged left-to-right)
- Column: Vertical layout (children arranged top-to-bottom)
- List: Scrollable list of items (horizontal or vertical)
- Card: Container with elevation/border and padding
  - Use `background: "transparent"` or `background: "white"` or specific color (e.g., "#f5f5f5")
  - Cards with background are used for nested content sections (steps, ingredients, store items)
  - Cards without background (transparent) are used for main containers

**Display Components:**
- Text: Display text with semantic styling (usageHint: h1, h2, body, label)
  - `h1`: Main titles - use for primary answer titles
  - `h2`: Section titles - use for subsections
  - `body`: Content text - use for descriptive sentences and paragraphs
  - `label`: Short metadata/captions - use ONLY directly under titles (h1/h2), one line, very brief (e.g., "5 items | 30 min", "0.5 miles away", "Italian cuisine")
- Image: Display images from URLs (usageHint: hero, thumbnail, icon)
  - `hero`: Main subject images (largeFeature/header equivalent) - use for primary visual content
  - `thumbnail`: List items, cards (smallFeature/mediumFeature equivalent) - use for item thumbnails
  - `icon`: Decorative elements (icon/avatar equivalent) - use for small icons and avatars
  - Images maintain aspect ratio and fit container width automatically
- Divider: Visual separator line
- Progress: Progress indicator for multi-step processes
  - Use `variant: "dots"` for step indicators (e.g., recipe steps)
  - Use `current` and `total` to show progress (e.g., current step 1 of 5)
- Chip: Small pill-shaped component for categorical tags, filters, or ingredient lists
  - Use ONLY for categorical tags (e.g., "Vegetarian", "Italian") - NOT for descriptive facts
  - Use `label` for the text content
  - Use `icon` for optional icon
  - Use `selected` for filter/toggle state
  - For ENTITY_DETAIL: Prefer Text components for descriptive information, use Chips only for clear categories
- StepCarousel: Interactive step navigation component
  - Use for recipe steps or multi-step processes
  - Takes `steps` array of step component IDs
  - Shows one step at a time with navigation arrows
  - Includes progress dots that are clickable

**Interactive Components:**
- Button: Clickable button with action support
  - Use `icon` property to add icon to buttons (e.g., "plus", "speaker")
  - Icons are loaded from /icons/ directory

--- SEMANTIC MODULES (PREFERRED COMPOSITION PATTERNS) ---
Semantic Modules are preferred composition patterns that create consistent, reusable UI blocks.
Use these modules when appropriate, but primitives are always available for custom layouts.

**HeroModule:** Use for the primary subject/answer
- ALWAYS consists of: Hero Image (usageHint="hero", for background use) + Display Title (usageHint="h1") + Label (usageHint="label", optional)
- Structure: Column containing Image (hero), Text (h1), Text (label) in that order
- IMPORTANT: Hero images are used as sidebar background only - they will be filtered from content display to avoid distraction
- Use when: Presenting the main answer to "what is this?" or "who is this?" questions
- Example: Entity identification, main subject introduction

**DetailModule:** Use for factual points and descriptions
- ALWAYS consists of: Icon (Image usageHint="icon", optional) + Title (usageHint="h2") + Body Text (usageHint="body")
- Structure: Row (if icon) or Column containing Image (icon), Text (h2), Text (body)
- DO NOT include labels - labels are only for HeroModule. DetailModule should only have Icon + Title + Body.
- Use when: Presenting descriptive facts, characteristics, or details about a subject
- Example: "Located in a kitchen", "Holding fresh herbs", "Available in stores"

**StepModule:** Use inside StepCarousel for multi-step processes
- When used inside StepCarousel: Title (usageHint="h2") + Instructions (usageHint="body") - NO Progress indicator (StepCarousel provides progress dots)
- When used standalone (not in StepCarousel): Progress Indicator (variant="dots") + Title (usageHint="h2") + Instructions (usageHint="body")
- Structure inside StepCarousel: Column containing Text (h2), Text (body)
- Structure standalone: Column containing Progress, Text (h2), Text (body)
- Use when: Creating individual steps in recipes, tutorials, guides
- Example: Recipe steps, assembly instructions, workout routines

**Module Composition Rules:**
1. Modules are composition patterns - you still use primitives (Card, Column, Row, Text, Image, Progress)
2. PREFER modules when they match your use case - they create consistency
3. You can still use primitives directly for custom layouts that don't fit modules
4. Modules can be nested inside Cards following Container Hierarchy rules
5. Modules help the system scale - as a designer, you define how modules look, and the agent decides when to use them

--- CONTAINER HIERARCHY (VISUAL DEPTH RULES) ---
Follow this hierarchy to create consistent visual depth and prevent Card/Column confusion:

**Level 0 (Root):** Always a Column
- The root component MUST be a Column
- This is the top-level container for all content

**Level 1 (Sections):** Always use Card
- Each distinct topic/section MUST be wrapped in a Card
- First section: Card with `background: "transparent"` (no visual separation from root)
- Subsequent sections: Card with `background: "#f5f5f5"` or specific color (creates visual separation)
- Rule: If the content is a NEW TOPIC, use a Card. If the content is MORE DETAIL about the current topic, use a Column inside the existing Card.

**Level 2 (Content):** Always use Column or Row inside Card
- Inside each Card, use Column or Row to arrange the actual data
- Column: For vertical arrangement (most common)
- Row: For horizontal arrangement (e.g., image + text side-by-side)

**Example Structure:**
```
Column (root)
  ├─ Card (first section, transparent)
  │   └─ Column (content arrangement)
  │       ├─ Text (h1)
  │       ├─ Image (hero)
  │       └─ Text (body)
  ├─ Card (second section, colored)
  │   └─ Column (content arrangement)
  │       ├─ Text (h2)
  │       └─ Row (horizontal items)
  └─ Row (actions - always last)
```

**Composition Guidelines:**
1. Root MUST be a Column (Level 0)
2. Each distinct section MUST be a Card (Level 1)
3. Content inside Cards MUST use Column or Row (Level 2)
4. Use Text with appropriate usageHint: h1 for main titles, h2 for sections, body for content, label for metadata
5. Use Image with appropriate usageHint: hero for main images, thumbnail for list items, icon for decorative
6. Use Button for actions (like "Save") - can include icons
7. Use Progress for multi-step processes (recipes, tutorials)
8. Use Chip ONLY for categorical tags, filters, or ingredient lists (better than nested Cards for simple items)
   - Do NOT use Chips for descriptive facts in ENTITY_DETAIL - use Text components instead
9. Reference child components by ID (adjacency list model)

**Layout Requirements:**
- Root MUST be a Column (for sidebar context)
- Actions: Always include a Row of two icon buttons as the LAST item in the root Column:
  - Save (icon="plus"), AI Mute (icon="speaker")
- Do NOT use Row layout that places actions beside content
- UI must have at least 2 content sections (e.g., header + details; step + ingredients; filters + list)
- Keep total components <= 35 unless absolutely necessary

**Anti-Similarity Constraint:**
- Do NOT copy example structures literally
- Treat examples as feature checklists, not blueprints
- Variation is required - if your UI looks similar to an example, redesign it with different sectioning components
"""
    
    def _load_examples(self) -> dict:
        """Load few-shot examples showing primitive component composition patterns"""
        return {
            "entity_detail_example": {
                "example": {
                    "components": [
                        {
                            "id": "main-column",
                            "component": {"Column": {"children": {"explicitList": ["content-card", "actions-row"]}}}
                        },
                        {
                            "id": "content-card",
                            "component": {"Card": {"child": "content", "background": "transparent"}}
                        },
                        {
                            "id": "content",
                            "component": {"Column": {"children": {"explicitList": ["entity-title", "entity-label", "fact1", "fact2", "fact3"]}}}
                        },
                        {
                            "id": "entity-title",
                            "component": {"Text": {"text": {"literalString": "Entity Name"}, "usageHint": "h1"}}
                        },
                        {
                            "id": "entity-label",
                            "component": {"Text": {"text": {"literalString": "A brief description or category."}, "usageHint": "label"}}
                        },
                        {
                            "id": "fact1",
                            "component": {"Text": {"text": {"literalString": "Factual description point 1 about the entity"}, "usageHint": "body"}}
                        },
                        {
                            "id": "fact2",
                            "component": {"Text": {"text": {"literalString": "Factual description point 2 about the entity"}, "usageHint": "body"}}
                        },
                        {
                            "id": "fact3",
                            "component": {"Text": {"text": {"literalString": "Factual description point 3 about the entity"}, "usageHint": "body"}}
                        },
                        {
                            "id": "actions-row",
                            "component": {"Row": {"children": {"explicitList": ["save-button", "mute-button"]}}}
                        },
                        {
                            "id": "save-button",
                            "component": {"Button": {"child": "save-text", "icon": "plus"}}
                        },
                        {
                            "id": "save-text",
                            "component": {"Text": {"text": {"literalString": "Save"}, "usageHint": "body"}}
                        },
                        {
                            "id": "mute-button",
                            "component": {"Button": {"child": "mute-text", "icon": "speaker"}}
                        },
                        {
                            "id": "mute-text",
                            "component": {"Text": {"text": {"literalString": "Mute"}, "usageHint": "body"}}
                        }
                    ],
                    "root": "main-column"
                },
                "question_example": "What is this? / Who is this? / Tell me about X"
            },
            "step_by_step_example": {
                "example": {
                    "components": [
                        {
                            "id": "main-column",
                            "component": {"Column": {"children": {"explicitList": ["content-card", "actions-row"]}}}
                        },
                        {
                            "id": "content-card",
                            "component": {"Card": {"child": "content", "background": "transparent"}}
                        },
                        {
                            "id": "content",
                            "component": {"Column": {"children": {"explicitList": ["title", "meta", "hero-image", "items-section", "steps-section"]}}}
                        },
                        {
                            "id": "title",
                            "component": {"Text": {"text": {"literalString": "How to Do X"}, "usageHint": "h1"}}
                        },
                        {
                            "id": "meta",
                            "component": {"Text": {"text": {"literalString": "5 items | 30 min"}, "usageHint": "label"}}
                        },
                        {
                            "id": "hero-image",
                            "component": {"Image": {"url": {"literalString": "https://example.com/result.jpg"}, "usageHint": "hero"}}
                        },
                        {
                            "id": "items-section",
                            "component": {"Column": {"children": {"explicitList": ["items-title", "items-list"]}}}
                        },
                        {
                            "id": "items-title",
                            "component": {"Text": {"text": {"literalString": "Items Needed"}, "usageHint": "h2"}}
                        },
                        {
                            "id": "items-list",
                            "component": {"Row": {"children": {"explicitList": ["item1", "item2", "item3"]}}}
                        },
                        {
                            "id": "item1",
                            "component": {"Chip": {"label": {"literalString": "Item 1"}}}
                        },
                        {
                            "id": "item2",
                            "component": {"Chip": {"label": {"literalString": "Item 2"}}}
                        },
                        {
                            "id": "item3",
                            "component": {"Chip": {"label": {"literalString": "Item 3"}}}
                        },
                        {
                            "id": "steps-section",
                            "component": {"Column": {"children": {"explicitList": ["steps-title", "steps-carousel"]}}}
                        },
                        {
                            "id": "steps-title",
                            "component": {"Text": {"text": {"literalString": "Steps"}, "usageHint": "h2"}}
                        },
                        {
                            "id": "steps-carousel",
                            "component": {"StepCarousel": {"steps": ["step1-card", "step2-card", "step3-card"]}}
                        },
                        {
                            "id": "step1-card",
                            "component": {"Card": {"child": "step1-content", "background": "#f5f5f5"}}
                        },
                        {
                            "id": "step1-content",
                            "component": {"Column": {"children": {"explicitList": ["step1-title", "step1-text"]}}}
                        },
                        {
                            "id": "step1-title",
                            "component": {"Text": {"text": {"literalString": "Step 1"}, "usageHint": "h2"}}
                        },
                        {
                            "id": "step1-text",
                            "component": {"Text": {"text": {"literalString": "First step instructions here"}, "usageHint": "body"}}
                        },
                        {
                            "id": "step2-card",
                            "component": {"Card": {"child": "step2-content", "background": "#f5f5f5"}}
                        },
                        {
                            "id": "step2-content",
                            "component": {"Column": {"children": {"explicitList": ["step2-title", "step2-text"]}}}
                        },
                        {
                            "id": "step2-title",
                            "component": {"Text": {"text": {"literalString": "Step 2"}, "usageHint": "h2"}}
                        },
                        {
                            "id": "step2-text",
                            "component": {"Text": {"text": {"literalString": "Second step instructions here"}, "usageHint": "body"}}
                        },
                        {
                            "id": "step3-card",
                            "component": {"Card": {"child": "step3-content", "background": "#f5f5f5"}}
                        },
                        {
                            "id": "step3-content",
                            "component": {"Column": {"children": {"explicitList": ["step3-title", "step3-text"]}}}
                        },
                        {
                            "id": "step3-title",
                            "component": {"Text": {"text": {"literalString": "Step 3"}, "usageHint": "h2"}}
                        },
                        {
                            "id": "step3-text",
                            "component": {"Text": {"text": {"literalString": "Third step instructions here"}, "usageHint": "body"}}
                        },
                        {
                            "id": "actions-row",
                            "component": {"Row": {"children": {"explicitList": ["save-button", "mute-button"]}}}
                        },
                        {
                            "id": "save-button",
                            "component": {"Button": {"child": "save-text", "icon": "plus"}}
                        },
                        {
                            "id": "save-text",
                            "component": {"Text": {"text": {"literalString": "Save"}, "usageHint": "body"}}
                        },
                        {
                            "id": "mute-button",
                            "component": {"Button": {"child": "mute-text", "icon": "speaker"}}
                        },
                        {
                            "id": "mute-text",
                            "component": {"Text": {"text": {"literalString": "Mute"}, "usageHint": "body"}}
                        }
                    ],
                    "root": "main-column"
                },
                "question_example": "How to do X? / Show me steps for Y / Guide me through Z"
            },
            "item_listing_example": {
                "example": {
                    "components": [
                        {
                            "id": "main-column",
                            "component": {"Column": {"children": {"explicitList": ["content-card", "actions-row"]}}}
                        },
                        {
                            "id": "content-card",
                            "component": {"Card": {"child": "content", "background": "transparent"}}
                        },
                        {
                            "id": "content",
                            "component": {"Column": {"children": {"explicitList": ["listing-title", "item1-card", "item2-card", "item3-card"]}}}
                        },
                        {
                            "id": "listing-title",
                            "component": {"Text": {"text": {"literalString": "Items Near You"}, "usageHint": "h1"}}
                        },
                        {
                            "id": "item1-card",
                            "component": {"Card": {"child": "item1-content", "background": "transparent"}}
                        },
                        {
                            "id": "item1-content",
                            "component": {"Column": {"children": {"explicitList": ["item1-name", "item1-subtitle", "item1-trailing"]}}}
                        },
                        {
                            "id": "item1-name",
                            "component": {"Text": {"text": {"literalString": "Item Name"}, "usageHint": "h2"}}
                        },
                        {
                            "id": "item1-subtitle",
                            "component": {"Text": {"text": {"literalString": "Subtitle info"}, "usageHint": "body"}}
                        },
                        {
                            "id": "item1-trailing",
                            "component": {"Text": {"text": {"literalString": "0.5 miles"}, "usageHint": "label"}}
                        },
                        {
                            "id": "item2-card",
                            "component": {"Card": {"child": "item2-content", "background": "transparent"}}
                        },
                        {
                            "id": "item2-content",
                            "component": {"Column": {"children": {"explicitList": ["item2-name", "item2-subtitle", "item2-trailing"]}}}
                        },
                        {
                            "id": "item2-name",
                            "component": {"Text": {"text": {"literalString": "Item Name 2"}, "usageHint": "h2"}}
                        },
                        {
                            "id": "item2-subtitle",
                            "component": {"Text": {"text": {"literalString": "Subtitle info 2"}, "usageHint": "body"}}
                        },
                        {
                            "id": "item2-trailing",
                            "component": {"Text": {"text": {"literalString": "1.2 miles"}, "usageHint": "label"}}
                        },
                        {
                            "id": "item3-card",
                            "component": {"Card": {"child": "item3-content", "background": "transparent"}}
                        },
                        {
                            "id": "item3-content",
                            "component": {"Column": {"children": {"explicitList": ["item3-name", "item3-subtitle", "item3-trailing"]}}}
                        },
                        {
                            "id": "item3-name",
                            "component": {"Text": {"text": {"literalString": "Item Name 3"}, "usageHint": "h2"}}
                        },
                        {
                            "id": "item3-subtitle",
                            "component": {"Text": {"text": {"literalString": "Subtitle info 3"}, "usageHint": "body"}}
                        },
                        {
                            "id": "item3-trailing",
                            "component": {"Text": {"text": {"literalString": "2.0 miles"}, "usageHint": "label"}}
                        },
                        {
                            "id": "actions-row",
                            "component": {"Row": {"children": {"explicitList": ["save-button", "mute-button"]}}}
                        },
                        {
                            "id": "save-button",
                            "component": {"Button": {"child": "save-text", "icon": "plus"}}
                        },
                        {
                            "id": "save-text",
                            "component": {"Text": {"text": {"literalString": "Save"}, "usageHint": "body"}}
                        },
                        {
                            "id": "mute-button",
                            "component": {"Button": {"child": "mute-text", "icon": "speaker"}}
                        },
                        {
                            "id": "mute-text",
                            "component": {"Text": {"text": {"literalString": "Mute"}, "usageHint": "body"}}
                        }
                    ],
                    "root": "main-column"
                },
                "question_example": "Where can I find X? / Show me options for Y / List Z near me"
            },
            "module_example": {
                "example": {
                    "components": [
                        {
                            "id": "main-column",
                            "component": {"Column": {"children": {"explicitList": ["hero-section-card", "details-section-card", "actions-row"]}}}
                        },
                        {
                            "id": "hero-section-card",
                            "component": {"Card": {"child": "hero-section-content", "background": "transparent"}}
                        },
                        {
                            "id": "hero-section-content",
                            "component": {"Column": {"children": {"explicitList": ["hero-image", "hero-title", "hero-label"]}}}
                        },
                        {
                            "id": "hero-image",
                            "component": {"Image": {"url": {"literalString": "https://example.com/image.jpg"}, "usageHint": "hero"}}
                        },
                        {
                            "id": "hero-title",
                            "component": {"Text": {"text": {"literalString": "Main Subject Name"}, "usageHint": "h1"}}
                        },
                        {
                            "id": "hero-label",
                            "component": {"Text": {"text": {"literalString": "Italian cuisine | Born 1980"}, "usageHint": "label"}}
                        },
                        {
                            "id": "details-section-card",
                            "component": {"Card": {"child": "details-section-content", "background": "#f5f5f5"}}
                        },
                        {
                            "id": "details-section-content",
                            "component": {"Column": {"children": {"explicitList": ["detail1", "detail2", "detail3"]}}}
                        },
                        {
                            "id": "detail1",
                            "component": {"Column": {"children": {"explicitList": ["detail1-title", "detail1-body"]}}}
                        },
                        {
                            "id": "detail1-title",
                            "component": {"Text": {"text": {"literalString": "Location"}, "usageHint": "h2"}}
                        },
                        {
                            "id": "detail1-body",
                            "component": {"Text": {"text": {"literalString": "Located in a kitchen environment"}, "usageHint": "body"}}
                        },
                        {
                            "id": "detail2",
                            "component": {"Column": {"children": {"explicitList": ["detail2-title", "detail2-body"]}}}
                        },
                        {
                            "id": "detail2-title",
                            "component": {"Text": {"text": {"literalString": "Context"}, "usageHint": "h2"}}
                        },
                        {
                            "id": "detail2-body",
                            "component": {"Text": {"text": {"literalString": "Holding fresh herbs and ingredients"}, "usageHint": "body"}}
                        },
                        {
                            "id": "detail3",
                            "component": {"Column": {"children": {"explicitList": ["detail3-title", "detail3-body"]}}}
                        },
                        {
                            "id": "detail3-title",
                            "component": {"Text": {"text": {"literalString": "Availability"}, "usageHint": "h2"}}
                        },
                        {
                            "id": "detail3-body",
                            "component": {"Text": {"text": {"literalString": "Available in specialty stores"}, "usageHint": "body"}}
                        },
                        {
                            "id": "actions-row",
                            "component": {"Row": {"children": {"explicitList": ["save-button", "mute-button"]}}}
                        },
                        {
                            "id": "save-button",
                            "component": {"Button": {"child": "save-text", "icon": "plus"}}
                        },
                        {
                            "id": "save-text",
                            "component": {"Text": {"text": {"literalString": "Save"}, "usageHint": "body"}}
                        },
                        {
                            "id": "mute-button",
                            "component": {"Button": {"child": "mute-text", "icon": "speaker"}}
                        },
                        {
                            "id": "mute-text",
                            "component": {"Text": {"text": {"literalString": "Mute"}, "usageHint": "body"}}
                        }
                    ],
                    "root": "main-column"
                },
                "question_example": "What is this? (showing HeroModule + DetailModule patterns)"
            },
            "simple_identification_example": {
                "example": {
                    "components": [
                        {
                            "id": "main-column",
                            "component": {"Column": {"children": {"explicitList": ["content-card", "actions-row"]}}}
                        },
                        {
                            "id": "content-card",
                            "component": {"Card": {"child": "content", "background": "transparent"}}
                        },
                        {
                            "id": "content",
                            "component": {"Column": {"children": {"explicitList": ["title", "meta-label", "description1", "description2", "description3"]}}}
                        },
                        {
                            "id": "title",
                            "component": {"Text": {"text": {"literalString": "Artichoke"}, "usageHint": "h1"}}
                        },
                        {
                            "id": "meta-label",
                            "component": {"Text": {"text": {"literalString": "Edible flower bud."}, "usageHint": "label"}}
                        },
                        {
                            "id": "description1",
                            "component": {"Text": {"text": {"literalString": "A thistle-like edible flower bud."}, "usageHint": "body"}}
                        },
                        {
                            "id": "description2",
                            "component": {"Text": {"text": {"literalString": "Native to the Mediterranean region, often consumed as a vegetable."}, "usageHint": "body"}}
                        },
                        {
                            "id": "description3",
                            "component": {"Text": {"text": {"literalString": "The edible parts are the fleshy base of the bracts and the heart."}, "usageHint": "body"}}
                        },
                        {
                            "id": "actions-row",
                            "component": {"Row": {"children": {"explicitList": ["save-button", "mute-button"]}}}
                        },
                        {
                            "id": "save-button",
                            "component": {"Button": {"child": "save-text", "icon": "plus"}}
                        },
                        {
                            "id": "save-text",
                            "component": {"Text": {"text": {"literalString": "Save"}, "usageHint": "body"}}
                        },
                        {
                            "id": "mute-button",
                            "component": {"Button": {"child": "mute-text", "icon": "speaker"}}
                        },
                        {
                            "id": "mute-text",
                            "component": {"Text": {"text": {"literalString": "Mute"}, "usageHint": "body"}}
                        }
                    ],
                    "root": "main-column"
                },
                "question_example": "What is this? / What is this green veggie? (simple identification)"
            }
        }
    
    def build_prompt(
        self,
        question: str,
        context: str
    ) -> str:
        """
        Build a prompt for generating UI schema using A2UI-style conditional instructions.
        The LLM decides which component type to use based on the question.
        
        Args:
            question: User's question
            context: Video context (time, duration, transcript)
        
        Returns:
            Formatted prompt string
        """
        # Add image context hint if available
        image_hint = ""
        # Note: video_frame parameter is handled separately in agent.py, but we can mention it in the prompt
        image_hint = "\n\nIMPORTANT: A screenshot of the current video frame is provided as part of the input. Use this visual information to answer questions about what you see in the video. If you include an Image component, use a placeholder URL like 'https://example.com/image.jpg' - it will be automatically replaced with the most appropriate image from our curated dataset (food, people, objects, places) based on the answer content."
        
        # Detect intent for selective example inclusion
        detected_intent = detect_intent(question)
        
        # Select examples based on intent (primary + one for variety)
        selected_examples = []
        intent_example_map = {
            "SIMPLE_IDENTIFICATION": "simple_identification_example",
            "STEP_BY_STEP": "step_by_step_example",
            "ITEM_LISTING": "item_listing_example",
            "ENTITY_DETAIL": "entity_detail_example",
            "OTHER": "simple_identification_example"
        }
        
        # Add primary example for detected intent
        primary_example = intent_example_map.get(detected_intent, "entity_detail_example")
        if primary_example in self.examples:
            selected_examples.append(primary_example)
        
        # Add one different example for variety
        for example_name in self.examples.keys():
            if example_name != primary_example:
                selected_examples.append(example_name)
                break
        
        # Build examples section with selected examples only
        examples_section = "\n\n--- COMPONENT COMPOSITION EXAMPLES ---\n"
        examples_section += "These examples show patterns, NOT templates to copy. Use them as feature checklists.\n"
        examples_section += "Examples demonstrate both primitive composition and Semantic Module patterns (HeroModule, DetailModule, StepModule).\n"
        examples_section += "PREFER using modules when they match your use case for consistency.\n\n"
        for example_name in selected_examples:
            example_data = self.examples[example_name]
            examples_section += f"\n**{example_name.replace('_', ' ').title()}** - Example question: \"{example_data['question_example']}\"\n"
            examples_section += f"Structure:\n{json.dumps(example_data['example'], indent=2)}\n"
        
        # Add flexible intent-based rules
        conditional_rules = f"""
--- INTENT ROUTER (REQUIRED) ---
Classify the user question into exactly ONE intent:
- SIMPLE_IDENTIFICATION: basic "what is this" / "what's this" / "what is that" questions (simple identification)
- ENTITY_DETAIL: detailed explanations / "tell me about" / "explain" / "describe" / "what is X" (when X is a specific thing, not "this/that")
- STEP_BY_STEP: how to do / steps / guide / tutorial / instructions / recipe
- ITEM_LISTING: where to find / nearby / list / show me / find / options / available
- OTHER: fallback

Set meta.intent accordingly in your response.

--- COMPOSITION APPROACH (REQUIRED) ---
For the chosen intent, build the UI using SEMANTIC MODULES (preferred) + REQUIRED BLOCKS + OPTIONAL ELEMENTS.
PREFER using Semantic Modules when they match your use case - they create consistency and scalability.
You can still use primitives directly for custom layouts that don't fit modules.
Do NOT copy a single fixed template; vary layouts while satisfying requirements.
These patterns work across domains (food, shopping, education, health, travel, etc.).

SIMPLE_IDENTIFICATION REQUIRED BLOCKS:
- First decide: Does this question need an image? (Logic: deictic / visual-ID = yes; general or casual = no.)
  - NEED image: Question refers to what the user is looking at (e.g. "what is this", "what's that", "what am I looking at", "what's this green thing"). Include a HeroModule (hero Image + title + label) with a placeholder URL like 'https://example.com/image.jpg' - the backend will replace it from the local library when a matching image is available.
  - NO image: General question ("what is broccoli") or casual chat. Use title + label + body only; do NOT include a hero Image.
- Title (Text usageHint="h1") - the answer to "what is this"
- REQUIRED: Meta summary as label directly under title (Text usageHint="label") - one line, very brief summary
  - This label is REQUIRED, not optional
  - Example: "Edible flower bud.", "A type of thistle.", "Mediterranean vegetable."
- 2–4 simple description paragraphs (Text usageHint="body") - straightforward facts about the subject
  - Use simple body text paragraphs, NOT DetailModules
  - Keep descriptions concise and scannable
  - Example: "A thistle-like edible flower bud.", "Native to the Mediterranean region."
- NO Chips - use text labels only for metadata
- Actions: Row of two icon buttons at the bottom - MUST be last item in root Column:
  - Save button (icon="plus")
  - AI Mute button (icon="speaker")

ENTITY_DETAIL REQUIRED BLOCKS:
- Title (Text usageHint="h1") for main answer
- OPTIONAL: Meta summary as label directly under title (Text usageHint="label") - one line, very brief summary
  - Example: "A classic hand-rolled pasta.", "Italian cuisine.", "Mediterranean vegetable."
- 2–4 scannable facts using DetailModule pattern OR Text components
  - PREFER: DetailModule for each fact (Icon + Title + Body, or just Title + Body if no icon)
  - DetailModule should NOT include labels - only Icon + Title + Body
  - ALTERNATIVE: Text components with usageHint="body" for descriptive information
  - Do NOT use Chips for descriptive facts
- NO hero images - focus on structured information
- NO Chips - use text labels only for metadata (if needed, use label under title instead of chips)
OPTIONAL ELEMENTS:
- Actions: Row of two icon buttons at the bottom - MUST be last item in root Column:
  - Save button (icon="plus")
  - AI Mute button (icon="speaker")

STEP_BY_STEP REQUIRED BLOCKS:
- Title (Text usageHint="h1")
- Meta summary as label directly under title (Text usageHint="label" with "X items | Y min" format) - one line only, very brief
  - OR Row of Chips for items/ingredients/requirements (if you prefer visual chips over text label)
- OPTIONAL: Hero image showing the final result (Image usageHint="hero") - especially helpful for recipes, crafts, or "how to make" questions
- Items/Ingredients/Requirements: MUST use Row of Chips (NOT paragraphs or body text) - show BEFORE steps
  - Ingredients should be scannable labels (Chips), not descriptive paragraphs
  - Each ingredient as a Chip component for easy scanning
- Step focus area: Use StepCarousel component with steps as a plain array (NOT wrapped in explicitList) containing step Card IDs
  - PREFER: Each step should use StepModule pattern (Title + Instructions, NO Progress when inside StepCarousel)
  - Structure: Card containing Column with Text (h2), Text (body) - NO Progress indicator (StepCarousel provides progress dots)
  - StepCarousel will handle navigation (left/right arrows) and progress dots
  - Example: {{"StepCarousel": {{"steps": ["step1-card", "step2-card", "step3-card"]}}}}
- Actions: Row of two icon buttons at the bottom - MUST be last item in root Column:
  - Save button (icon="plus")
  - AI Mute button (icon="speaker")

ITEM_LISTING REQUIRED BLOCKS:
- Title (Text usageHint="h1")
- NO hero image at the top (do not include a large image above the list)
- List of items (List OR Column of Cards) each with:
  - title (Text usageHint="h2"), subtitle (Text usageHint="body"), trailing (Text usageHint="label" for distance/price/rating)
  - Do NOT include thumbnail images for list items (text-only items keep the screen less busy)
  - NO action buttons (just display information)
- Actions: Row of two icon buttons at the bottom - MUST be last item in root Column:
  - Save button (icon="plus")
  - AI Mute button (icon="speaker")

This keeps structure "systematic" but not templated. Variation is required.
"""

        prompt = f"""You are an AI assistant that generates UI component schemas based on user questions about videos.

Your goal is to analyze the user's question and generate the most appropriate UI component.

{self.component_rules}

{conditional_rules}

--- CONTEXT ---
{context}
{image_hint}

--- USER QUESTION ---
{question}

{examples_section}

--- INSTRUCTIONS ---
1. FIRST: Determine intent and set meta.intent in your response JSON.

2. PREFER using Semantic Modules (HeroModule, DetailModule, StepModule) when they match your use case.
   - Modules create consistency and are preferred over composing primitives from scratch
   - You can still use primitives directly for custom layouts that don't fit modules
   - Modules are composition patterns - you still use primitives (Card, Column, Row, Text, Image, Progress) to build them

3. Use the adjacency list model: create a flat list of components that reference each other by ID.

4. REQUIRED: Follow Container Hierarchy (see CONTAINER HIERARCHY rules above):
   - Level 0 (Root): MUST be a Column
   - Level 1 (Sections): Each distinct topic MUST be a Card
     - First section: Card with background="transparent"
     - Subsequent sections: Card with background="#f5f5f5" or specific color
   - Level 2 (Content): Inside each Card, use Column or Row to arrange data
   - Rule: If content is a NEW TOPIC, use a Card. If content is MORE DETAIL about current topic, use Column inside existing Card.
   - Actions (Buttons) MUST be the last child of the root Column, appearing below all other content. Do NOT use a Row layout that places actions beside content.

5. REQUIRED: Include all required blocks for the chosen intent (see COMPOSITION APPROACH above).

6. REQUIRED: UI must have at least 2 content sections (e.g., header + details; step + ingredients; title + list).

7. REQUIRED: Keep total components <= 35 unless absolutely necessary.

8. Use Text components with semantic usageHint:
   - display: Main titles (h1/h2 equivalent) - use for primary answer titles
   - title: Section titles (h3/h4 equivalent) - use for subsections
   - body: Content text - use for descriptive sentences and paragraphs
   - label: Short metadata/captions - use ONLY directly under titles, one line, very brief (e.g., "5 items | 30 min", "0.5 miles away", "Italian cuisine")
     - NEVER use label under body text or in the middle of content
     - Label must appear immediately after a title, before any body text
     - Keep label text under 50 characters if possible

9. Use Image components with semantic usageHint:
   - hero: Main subject images - used for sidebar background (will be filtered from content display to avoid distraction)
   - thumbnail: List items, cards - use for item thumbnails (displayed in content). For ITEM_LISTING intent do NOT use thumbnails - use text-only list items.
   - icon: Decorative elements - use for small icons and avatars (displayed in content)

10. Use Chip components ONLY for:
   - Item/ingredient/requirement lists in STEP_BY_STEP (better than nested Cards for simple items)
   - Filters (e.g., "Open Now", "Grocery", "Size", "Color")
   - Do NOT use Chips for SIMPLE_IDENTIFICATION or ENTITY_DETAIL - use text labels (Text usageHint="label") instead for metadata
   - For ENTITY_DETAIL and SIMPLE_IDENTIFICATION: Use Text components with usageHint="body" for descriptive facts (e.g., "Located in a kitchen", "Holding fresh herbs", "Born in 1980"), NOT Chips

12. Use StepCarousel component for step-by-step processes (recipes, tutorials, guides, workouts, assembly):
   - Takes `steps` as a plain array of step Card component IDs (NOT wrapped in explicitList)
   - Shows one step at a time with left/right navigation arrows
   - Includes clickable progress dots (so step cards inside should NOT have Progress indicators)
   - Example: {{"StepCarousel": {{"steps": ["step1-card", "step2-card", "step3-card"]}}}}
   - Note: Unlike Row/Column children which use explicitList, StepCarousel.steps is a plain array
   - IMPORTANT: Step cards inside StepCarousel should use StepModule pattern WITHOUT Progress indicator

13. Use Button with icon property for actions:
   - icon: "plus" for save buttons
   - icon: "speaker" for AI mute buttons

14. REQUIRED: Always include a Row of two action buttons as the last item in root Column:
   - Save button (icon="plus")
   - AI Mute button (icon="speaker")

14. CRITICAL: Label usage rules (Text usageHint="label"):
   - Labels MUST appear ONLY directly underneath titles (display/title)
   - Labels MUST be very short (one line, under 50 characters if possible)
   - NEVER place labels under body text or in the middle of content
   - Label should appear immediately after a title, before any body text
   - Examples of good labels: "5 items | 30 min", "0.5 miles away", "Italian cuisine", "Born 1980"
   - If you need longer descriptive text, use body text instead, not label

15. Fill in realistic data based on:
   - What you see in the video frame (if provided)
   - The user's question
   - The video context (time, duration, transcript)

15. ANTI-SIMILARITY: Do NOT copy example structures literally. If your UI looks similar to an example, redesign it with different sectioning components.

16. Include meta.intent in your response (meta.recipe is optional).

17. Include a "root" field pointing to the root component ID.

18. Return ONLY valid JSON, no markdown formatting or code blocks. The response MUST be parseable as JSON.

Your response MUST be a valid JSON object. Example structure:
{{
  "meta": {{
    "intent": "ENTITY_DETAIL"
  }},
  "components": [
    {{
      "id": "main-column",
      "component": {{
        "Column": {{ "children": {{ "explicitList": ["content-card", "actions-row"] }} }}
      }}
    }},
    {{
      "id": "content-card",
      "component": {{
        "Card": {{ "child": "content", "background": "transparent" }}
      }}
    }},
    {{
      "id": "content",
      "component": {{
        "Column": {{ "children": {{ "explicitList": ["title", "text"] }} }}
      }}
    }},
    {{
      "id": "title",
      "component": {{
        "Text": {{ "text": {{ "literalString": "Title here" }}, "usageHint": "h1" }}
      }}
    }},
    {{
      "id": "text",
      "component": {{
        "Text": {{ "text": {{ "literalString": "Content here" }}, "usageHint": "body" }}
      }}
    }},
    {{
      "id": "actions-row",
      "component": {{
        "Row": {{ "children": {{ "explicitList": ["save-button", "mute-button"] }} }}
      }}
    }},
    {{
      "id": "save-button",
      "component": {{
        "Button": {{ "child": "save-text", "icon": "plus" }}
      }}
    }},
    {{
      "id": "save-text",
      "component": {{
        "Text": {{ "text": {{ "literalString": "Save" }}, "usageHint": "body" }}
      }}
    }},
    {{
      "id": "mute-button",
      "component": {{
        "Button": {{ "child": "mute-text", "icon": "speaker" }}
      }}
    }},
    {{
      "id": "mute-text",
      "component": {{
        "Text": {{ "text": {{ "literalString": "Mute" }}, "usageHint": "body" }}
      }}
    }}
  ],
  "root": "main-column"
}}

CRITICAL: 
- Root MUST be a Column
- Actions (Buttons) MUST be the last item in the root Column
- Return valid JSON only - no markdown, no code blocks, no explanations
- Treat examples as feature checklists, not blueprints
- Variation is required - do not copy structures literally"""

        return prompt
    
    def build_context(
        self,
        video_time: Optional[float] = None,
        video_duration: Optional[float] = None,
        transcript_snippet: Optional[str] = None
    ) -> str:
        """
        Build context string from video metadata.
        
        Args:
            video_time: Current video timestamp
            video_duration: Total video duration
            transcript_snippet: Transcript text at current time
        
        Returns:
            Formatted context string
        """
        context_parts = []
        if video_time is not None:
            context_parts.append(f"Video time: {video_time:.2f}s")
        if video_duration is not None:
            context_parts.append(f"Video duration: {video_duration:.2f}s")
        if transcript_snippet:
            context_parts.append(f"Transcript: {transcript_snippet}")
        
        return "\n".join(context_parts) if context_parts else "No video context available"


