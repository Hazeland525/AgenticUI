import { UIResponse, UIComponent } from '../types/schema';

function getTextLiteral(comp: { text?: unknown }): string | null {
  const text = comp.text;
  if (typeof text === 'string') return text;
  if (text && typeof text === 'object' && 'literalString' in text) {
    return (text as { literalString: string }).literalString;
  }
  return null;
}

/**
 * Get the main title (h1) from a UI schema.
 * Returns the first Text component with usageHint === 'h1', or null.
 */
export function getTitleFromSchema(schema: UIResponse): string | null {
  if (!schema?.components) return null;
  for (const comp of schema.components) {
    const def = comp.component;
    if (def && typeof def === 'object' && 'Text' in def) {
      const textProps = (def as { Text: { usageHint?: string; text?: unknown } }).Text;
      if (textProps?.usageHint === 'h1') {
        const literal = getTextLiteral(textProps);
        if (literal) return literal;
      }
    }
  }
  return null;
}

function extractImageUrlFromComponent(component: UIComponent): string | null {
  const compDef = component.component;
  if (!compDef || typeof compDef !== 'object') return null;
  if (!('Image' in compDef)) return null;

  const imageProps = (compDef as { Image: { url?: unknown; imageUrl?: unknown } }).Image;
  const urlValue = imageProps?.url ?? imageProps?.imageUrl;

  if (typeof urlValue === 'string') return urlValue;
  if (urlValue && typeof urlValue === 'object' && 'literalString' in urlValue) {
    return (urlValue as { literalString: string }).literalString;
  }
  return null;
}

/**
 * Get the hero or first image URL from a UI schema.
 * Prefers Image with usageHint === 'hero'; otherwise returns the first Image URL.
 */
export function getImageUrlFromSchema(schema: UIResponse): string | null {
  if (!schema?.components) return null;

  // Prefer hero image
  for (const comp of schema.components) {
    const compDef = comp.component;
    if (compDef && typeof compDef === 'object' && 'Image' in compDef) {
      const imageProps = (compDef as { Image: { usageHint?: string } }).Image;
      if (imageProps?.usageHint === 'hero') {
        const url = extractImageUrlFromComponent(comp);
        if (url) return url;
      }
    }
  }

  // Fallback: first Image
  for (const comp of schema.components) {
    const url = extractImageUrlFromComponent(comp);
    if (url) return url;
  }

  return null;
}
