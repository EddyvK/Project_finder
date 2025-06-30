"""OpenAI handler for skill embeddings."""

import openai
import logging
from typing import List, Dict, Any
import numpy as np
from backend.config_manager import config_manager

logger = logging.getLogger(__name__)


class OpenAIHandler:
    """Handler for OpenAI API interactions for embeddings."""

    def __init__(self, api_key: str = None):
        """Initialize the OpenAI handler with API key."""
        self.logger = logging.getLogger(__name__)

        if not api_key:
            api_keys = config_manager.get_api_keys()
            api_key = api_keys.get("openai", "")

        if not api_key:
            raise ValueError("OpenAI API key is required")

        # Use legacy API key approach for maximum compatibility
        openai.api_key = api_key
        self.client = openai
        self.model = "text-embedding-3-large"
        self.logger.info("OpenAI legacy API key set successfully")

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text string."""
        try:
            if not text or not text.strip():
                return []

            response = self.client.embeddings.create(
                model=self.model,
                input=text.strip()
            )

            embedding = response.data[0].embedding
            self.logger.debug(f"Generated embedding for text: {text[:50]}...")
            return embedding

        except Exception as e:
            self.logger.error(f"Error getting embedding for text '{text[:50]}...': {str(e)}")
            return []

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts in a batch."""
        try:
            if not texts:
                return []

            # Filter out empty texts
            valid_texts = [text.strip() for text in texts if text and text.strip()]

            if not valid_texts:
                return []

            response = self.client.embeddings.create(
                model=self.model,
                input=valid_texts
            )

            embeddings = [data.embedding for data in response.data]
            self.logger.debug(f"Generated {len(embeddings)} embeddings in batch")
            return embeddings

        except Exception as e:
            self.logger.error(f"Error getting batch embeddings: {str(e)}")
            return []

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate similarity between two embeddings."""
        try:
            if not embedding1 or not embedding2:
                return 0.0

            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Normalize vectors
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            vec1_normalized = vec1 / norm1
            vec2_normalized = vec2 / norm2

            # Calculate cosine similarity
            similarity = np.dot(vec1_normalized, vec2_normalized)
            return float(similarity)

        except Exception as e:
            self.logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0

    def calculate_euclidean_distance(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate Euclidean distance between two embeddings."""
        try:
            if not embedding1 or not embedding2:
                return float('inf')

            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Calculate Euclidean distance
            distance = np.linalg.norm(vec1 - vec2)
            return float(distance)

        except Exception as e:
            self.logger.error(f"Error calculating Euclidean distance: {str(e)}")
            return float('inf')

    def calculate_distance(self, embedding1: List[float], embedding2: List[float], method: str = None) -> float:
        """Calculate distance between two embeddings using specified method."""
        if not method:
            method = config_manager.get_distance_model()

        if method.lower() == "euclidian":
            return self.calculate_euclidean_distance(embedding1, embedding2)
        else:
            # Default to cosine similarity
            return self.calculate_similarity(embedding1, embedding2)