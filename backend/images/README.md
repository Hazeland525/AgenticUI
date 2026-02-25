# Image Dataset

This directory contains a curated dataset of images organized by category for use in the AgenticUI prototype.

## Structure

```
images/
  metadata.json          # Image catalog with attributes
  food/                  # Food-related images
  people/                # People-related images
  objects/               # Object-related images
  places/                # Place-related images
```

## Adding Images

1. **Add the image file** to the appropriate category directory (e.g., `food/pasta.jpg`)

2. **Update `metadata.json`** to include the new image:
   ```json
   {
     "id": "unique-id",
     "filename": "pasta.jpg",
     "tags": ["food", "italian", "pasta", "cooking"],
     "description": "Plate of pasta with sauce"
   }
   ```

3. **Image Requirements:**
   - Supported formats: JPG, JPEG, PNG, GIF, WebP
   - Recommended size: 800x600px or similar aspect ratio
   - File size: Keep under 2MB for performance

## Categories

- **food**: Food items, dishes, meals, restaurants
- **people**: People, professionals, celebrities, actors
- **objects**: Objects, products, devices, items
- **places**: Locations, landscapes, buildings, venues

## How It Works

When a user asks a question, the system:
1. Generates a UI schema with a placeholder image URL
2. Extracts the answer context from the generated schema
3. Uses an LLM to search the image dataset and find the most appropriate image
4. Replaces the placeholder with the selected image (converted to data URL)

The LLM matches images based on:
- The user's question
- The answer content
- Image tags and descriptions in the metadata

