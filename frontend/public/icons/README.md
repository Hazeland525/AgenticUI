# Icon SVG Requirements

This directory contains SVG icons used by Button components in the A2UI system.

## Required Icons

The following three icons are required for action buttons:

1. **plus.svg** - Save/Action button
2. **speaker.svg** - AI Speak button  
3. **screen.svg** - Send to Phone button

## SVG Specifications

- **Size**: 16x16 pixels (viewBox should be "0 0 16 16")
- **Format**: SVG with stroke-based design (not filled shapes)
- **Color**: Use `stroke="currentColor"` so icons inherit text color
- **Stroke width**: 2px for good visibility
- **File location**: `frontend/public/icons/`

## Example SVG Structure

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <!-- Your icon paths here -->
</svg>
```

## Icon Descriptions

- **plus.svg**: Plus sign (+) for save/add actions
- **speaker.svg**: Speaker/volume icon for audio/AI speak actions
- **screen.svg**: Phone/screen icon for send to device actions

## Adding New Icons

1. Create SVG file in this directory
2. Follow the specifications above
3. Icons will be automatically loaded by Button components using the icon name (without .svg extension)
