"""
Image search service using LLM to find the most appropriate image from the dataset.
"""
import json
import os
from typing import Optional, Dict, List
import base64
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class ImageSearchService:
    """
    Service for searching and retrieving images from the dataset using LLM.
    """
    
    def __init__(self):
        self.metadata_path = Path(__file__).parent.parent / "images" / "metadata.json"
        self.images_dir = Path(__file__).parent.parent / "images"
        self.metadata = self._load_metadata()
        
        # Initialize Gemini for image search
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def _load_metadata(self) -> Dict:
        """Load image metadata from JSON file."""
        try:
            with open(self.metadata_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"food": [], "people": [], "objects": [], "places": []}
    
    def _build_search_prompt(self, question: str, answer_context: str, available_images: str) -> str:
        """Build prompt for LLM to semantically match answer to image descriptions."""
        return f"""You are an image search assistant. Your task is to select the most appropriate image using a SEMANTIC layer: read the Description and Tags of each available image and pick the one that best matches what the answer is about.

**User Question:** {question}

**Answer Context:** {answer_context}

**Available Images (read descriptions to find the best match):**
{available_images}

**Semantic matching instructions:**
1. Understand what the answer is about (e.g. "artichoke", "grilled asparagus", "pasta shells").
2. Read each image's Description and Tags in the list above. Pick the image whose description/tags best describe that same subject.
3. You MUST return the exact "id" value as written in the Available Images list (e.g. if the list shows "ID: artichoke_raw", return imageId "artichoke_raw" — not "artichoke"). Copy the id string exactly.
4. Return ONLY a JSON object with this exact structure:
{{
  "imageId": "exact-id-from-list",
  "category": "food|people|objects|places",
  "reasoning": "Brief explanation: which description/tags matched the answer"
}}

Example: For answer about artichoke, the list has "ID: artichoke_raw, ... Description: Two whole raw artichokes...". Return imageId "artichoke_raw".
Example: For answer about pasta shells, the list has "ID: pasta_shells_raw" or "ID: pasta_shells_dish". Return one of those exact ids.

Return ONLY the JSON object, no markdown formatting or code blocks."""
    
    def _find_image_semantic_fallback(
        self, category_images: List[Dict], image_id: str, answer_context: str
    ) -> Optional[Dict]:
        """
        When LLM returns a non-exact id (e.g. "artichoke"), find the best matching
        image by description/tags (e.g. match to artichoke_raw).
        """
        if not category_images or not (image_id or answer_context):
            return None
        key = (image_id or "").strip().lower()
        # Build search tokens from answer_context (first ~50 chars, lowercase words)
        context_lower = (answer_context or "")[:200].lower()
        context_words = [w for w in context_lower.replace(",", " ").split() if len(w) > 2]
        for img in category_images:
            meta_id = (img.get("id") or "").lower()
            desc = (img.get("description") or "").lower()
            tags = [t.lower() for t in img.get("tags") or []]
            # Exact id substring (e.g. key "artichoke" in meta_id "artichoke_raw")
            if key and key in meta_id:
                return img
            if key and (key in desc or key in tags):
                return img
            # Answer context word in description or tags
            for w in context_words:
                if w in desc or w in tags or w in meta_id:
                    return img
        return None
    
    async def search_image(self, question: str, answer_context: str) -> Optional[Dict]:
        """
        Search for the most appropriate image using LLM.
        
        Args:
            question: The user's question
            answer_context: The answer or context about what the answer contains
        
        Returns:
            Dict with image info (id, category, filename, path) or None if no match
        """
        # Build list of available images
        available_images = []
        for category, images in self.metadata.items():
            for img in images:
                available_images.append(
                    f"- ID: {img['id']}, Category: {category}, "
                    f"Tags: {', '.join(img['tags'])}, Description: {img['description']}"
                )
        
        available_images_str = "\n".join(available_images)
        
        # Build prompt
        prompt = self._build_search_prompt(question, answer_context, available_images_str)
        
        # Query LLM
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            raw_text = response.text.strip()
            result = json.loads(raw_text)
            image_id = result.get("imageId")
            category = result.get("category")
            
            print(f"[IMAGE SEARCH] LLM response: imageId={image_id!r} category={category!r} raw={raw_text[:200]!r}")
            
            if not image_id or not category:
                print(f"[IMAGE SEARCH] return None: missing imageId or category (imageId={image_id!r} category={category!r})")
                return None
            
            # Normalize category to match metadata keys (lowercase: food, people, objects, places)
            category_key = (category or "").strip().lower()
            category_images = self.metadata.get(category_key, [])
            print(f"[IMAGE SEARCH] category_key={category_key!r} category_images count={len(category_images)}")
            
            selected_image = next(
                (img for img in category_images if img["id"] == image_id),
                None
            )
            if selected_image:
                print(f"[IMAGE SEARCH] exact match: id={image_id!r}")
            else:
                # Semantic fallback: if no exact match, find by description/tags (e.g. "artichoke" -> artichoke_raw)
                selected_image = self._find_image_semantic_fallback(
                    category_images, image_id, answer_context
                )
                if selected_image:
                    print(f"[IMAGE SEARCH] semantic fallback match: LLM id={image_id!r} -> metadata id={selected_image.get('id')!r}")
                else:
                    print(f"[IMAGE SEARCH] return None: no exact or semantic match for imageId={image_id!r} in category {category_key!r} ({len(category_images)} images)")
            
            if not selected_image:
                return None
            
            # Build full path (use category_key for filesystem)
            image_path = self.images_dir / category_key / selected_image["filename"]
            
            return {
                "id": image_id,
                "category": category_key,
                "filename": selected_image["filename"],
                "path": str(image_path),
                "reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            import traceback
            print(f"[IMAGE SEARCH] Error: {e}")
            traceback.print_exc()
            return None
    
    def get_image_as_data_url(self, image_path: str) -> Optional[str]:
        """
        Convert image file to data URL (base64).
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Data URL string or None if file doesn't exist
        """
        path = Path(image_path)
        if not path.exists():
            return None
        
        try:
            with open(path, 'rb') as f:
                image_data = f.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                
                # Determine MIME type from extension
                ext = path.suffix.lower()
                mime_types = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                mime_type = mime_types.get(ext, 'image/jpeg')
                
                return f"data:{mime_type};base64,{base64_data}"
        except Exception as e:
            print(f"Error reading image file: {e}")
            return None

