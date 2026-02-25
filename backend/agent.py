"""
Core agent class with LLM integration, schema validation, and retry logic.
Similar to A2UI's agent.py pattern.
"""
import json
import logging
from typing import Optional, Tuple
from models.schema import UIResponse, UIComponent
from services.gemini_service import GeminiService
from prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class Agent:
    """
    Core agent that processes questions and generates UI schemas.
    Includes validation and retry logic similar to A2UI.
    """
    
    def __init__(self, max_retries: int = 3):
        """
        Initialize the agent.
        
        Args:
            max_retries: Maximum number of retry attempts for schema generation
        """
        self.gemini_service = GeminiService()
        self.prompt_builder = PromptBuilder()
        self.max_retries = max_retries
    
    # Removed explicit intent detection - LLM decides based on prompt instructions
    # This follows A2UI's pattern where the agent (LLM) determines the UI type
    
    def validate_schema(self, schema: dict) -> Tuple[bool, Optional[UIResponse]]:
        """
        Validate the generated schema against our UI schema model.
        
        Args:
            schema: Generated schema dictionary
        
        Returns:
            Tuple of (is_valid, validated_schema or None)
        """
        try:
            # Validate using Pydantic model
            validated = UIResponse(**schema)
            return True, validated
        except Exception as e:
            logger.warning(f"Schema validation failed: {e}")
            logger.warning(f"Schema that failed validation: {json.dumps(schema, indent=2)[:1000]}")
            return False, None
    
    def create_fallback_schema(self, question: str) -> UIResponse:
        """
        Create a fallback schema if generation fails.
        Uses primitive components (A2UI style).
        
        Args:
            question: Original user question
        
        Returns:
            Fallback UIResponse
        """
        return UIResponse(
            meta={"intent": "OTHER", "error": "Generation failed"},
            components=[
                UIComponent(
                    id="fallback-card",
                    component={"Card": {"child": "fallback-content"}}
                ),
                UIComponent(
                    id="fallback-content",
                    component={"Column": {"children": {"explicitList": ["fallback-title", "fallback-text"]}}}
                ),
                UIComponent(
                    id="fallback-title",
                    component={"Text": {"text": {"literalString": "Response"}, "usageHint": "h3"}}
                ),
                UIComponent(
                    id="fallback-text",
                    component={"Text": {"text": {"literalString": f"Unable to generate detailed response for: {question}"}, "usageHint": "body"}}
                )
            ],
            root="fallback-card"
        )
    
    async def generate_ui_schema(
        self,
        question: str,
        video_time: Optional[float] = None,
        video_duration: Optional[float] = None,
        transcript_snippet: Optional[str] = None,
        video_frame: Optional[str] = None
    ) -> UIResponse:
        """
        Generate UI schema with validation and retry logic.
        Similar to A2UI's agent pattern with retries.
        
        Args:
            question: User's question
            video_time: Current video timestamp
            video_duration: Total video duration
            transcript_snippet: Transcript text at current time
        
        Returns:
            Validated UIResponse schema
        """
        # Build context
        context = self.prompt_builder.build_context(
            video_time=video_time,
            video_duration=video_duration,
            transcript_snippet=transcript_snippet
        )
        
        # Retry loop with validation
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Build prompt - LLM will decide which component type to use
                prompt = self.prompt_builder.build_prompt(
                    question=question,
                    context=context
                )
                
                # Generate response from LLM (with image if available)
                raw_response = await self.gemini_service.generate_content(
                    prompt, 
                    image_data=video_frame
                )
                
                # Parse JSON - try to extract JSON from markdown code blocks if present
                try:
                    # Remove markdown code blocks if present
                    cleaned_response = raw_response.strip()
                    if cleaned_response.startswith("```"):
                        # Extract JSON from markdown code block
                        lines = cleaned_response.split("\n")
                        # Remove first line (```json or ```)
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        # Remove last line (```)
                        if lines and lines[-1].strip() == "```":
                            lines = lines[:-1]
                        cleaned_response = "\n".join(lines)
                    
                    schema_dict = json.loads(cleaned_response)
                    # Print the raw JSON from LLM
                    logger.info("=" * 80)
                    logger.info("RAW JSON FROM LLM:")
                    logger.info(json.dumps(schema_dict, indent=2))
                    logger.info("=" * 80)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                    logger.error(f"Raw response that failed to parse (first 1000 chars): {raw_response[:1000]}")
                    logger.error(f"Full raw response length: {len(raw_response)}")
                    last_error = e
                    continue
                
                # Validate schema
                is_valid, validated_schema = self.validate_schema(schema_dict)
                
                if is_valid and validated_schema:
                    logger.info(f"Successfully generated and validated schema (attempt {attempt + 1})")
                    # Print the validated/final schema
                    logger.info("=" * 80)
                    logger.info("VALIDATED UI SCHEMA (sent to frontend):")
                    logger.info(json.dumps(validated_schema.model_dump(), indent=2))
                    logger.info("=" * 80)
                    return validated_schema
                else:
                    logger.error(f"Schema validation failed (attempt {attempt + 1}/{self.max_retries})")
                    logger.error(f"Schema dict that failed: {json.dumps(schema_dict, indent=2)[:1000]}")
                    last_error = ValueError("Schema validation failed")
                    continue
                    
            except Exception as e:
                logger.error(f"Error generating schema (attempt {attempt + 1}/{self.max_retries}): {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                last_error = e
                continue
        
        # All retries failed, return fallback
        logger.error(f"All retry attempts failed. Last error: {last_error}")
        return self.create_fallback_schema(question)

