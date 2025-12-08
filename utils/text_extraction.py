"""
Text extraction utilities using ONNX embeddings.
Intelligently extracts topic-relevant content from documents.
Uses local ONNX model (./onxx/model_int8.onnx) for fast, efficient inference.
"""

import re
try:
    import numpy as np
    from .onnx_embedder import embed_texts, embed_query
    EMBEDDINGS_AVAILABLE = True
except ImportError as e:
    EMBEDDINGS_AVAILABLE = False
    print(f"Warning: Embedding system not initialized: {e}")


def get_optimal_content_for_scheduling(text, topics, max_length=8000):
    """
    Extract optimal content for study scheduling.
    For large PDFs, intelligently selects introduction + topic-rich sections.
    
    Args:
        text (str): Full document text
        topics (list): Pre-extracted topic list
        max_length (int): Maximum characters to return (default 8000)
    
    Returns:
        str: Optimized content for scheduling (introduction + key sections)
    """
    if len(text) <= max_length:
        return text
    
    # Strategy: Get introduction (first 20%) + key topic sections + conclusion (last 10%)
    intro_length = max_length // 3  # Introduction section
    topic_length = max_length // 2  # Topic content
    conclusion_length = max_length // 6  # Conclusion
    
    sections = []
    
    # 1. Add introduction (first section of document)
    sections.append(text[:intro_length])
    
    # 2. Try to find and include topic sections
    if topics and topic_length > 0:
        for topic in topics[:3]:  # Top 3 topics
            # Simple keyword search for topic mentions
            pattern = re.compile(f".*{re.escape(topic)}.*", re.IGNORECASE | re.MULTILINE)
            matches = pattern.findall(text)
            if matches:
                # Get first match + surrounding context
                match_idx = text.lower().find(topic.lower())
                if match_idx > -1:
                    start = max(0, match_idx - 200)
                    end = min(len(text), match_idx + 600)
                    context = text[start:end]
                    if context not in sections:  # Avoid duplicates
                        sections.append(context)
    
    # 3. Add conclusion (last section of document)
    sections.append(text[-conclusion_length:])
    
    # Combine sections and trim to max_length
    result = "\n\n[...]\n\n".join(sections)
    if len(result) > max_length:
        result = result[:max_length] + "\n\n[Document continues...]"
    
    return result


def cosine_similarity(a, b):
    """Lightweight cosine similarity without sklearn."""
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-12)
    return np.dot(a_norm, b_norm.T)

class TopicAwareTextExtractor:
    """Extract text relevant to a specific topic using ONNX semantic similarity."""
    
    def __init__(self):
        """Initialize extractor with ONNX embeddings (lazy initialization)."""
        self.embeddings_available = EMBEDDINGS_AVAILABLE
    
    def extract_topic_text(self, text, topic, max_length=8000, cached_embeddings=None):
        """
        Extract text most relevant to a specific topic using ONNX semantic similarity.
        
        Args:
            text (str): Full document text
            topic (str): Topic to search for
            max_length (int): Maximum characters to return
            cached_embeddings (dict): Pre-computed embeddings {'sentences': [...], 'embeddings': [...]}
        
        Returns:
            str: Topic-relevant text excerpt (up to max_length chars)
        """
        # Handle None or empty topic
        if not topic:
            return text[:max_length]
        
        if not EMBEDDINGS_AVAILABLE:
            # Fallback to simple keyword search
            return self._fallback_extraction(text, topic, max_length)
        
        try:
            # Use cached embeddings if available
            if cached_embeddings and 'sentences' in cached_embeddings and 'embeddings' in cached_embeddings:
                sentences = cached_embeddings['sentences']
                sentence_embeddings = np.array(cached_embeddings['embeddings'], dtype=np.float32)
            else:
                # Fall back to computing embeddings on-the-fly
                sentences = self._split_sentences(text)
                
                if not sentences:
                    return text[:max_length]
                
                # Encode all sentences with search_document prefix
                sentence_embeddings = embed_texts(sentences, prefix="search_document:")
            
            # Encode topic query with search_query prefix
            topic_embedding = embed_query(topic).reshape(1, -1)
            
            # Calculate similarity between topic and each sentence
            similarities = cosine_similarity(topic_embedding, sentence_embeddings)[0]
            
            # Get indices of most similar sentences
            top_indices = np.argsort(similarities)[::-1][:20]  # Get top 20 most similar
            top_indices = sorted(top_indices)  # Sort by document order
            
            # Build result by taking chunks around top sentences
            result = []
            current_length = 0
            last_idx = -10  # Prevent overlapping chunks
            
            for idx in top_indices:
                if current_length >= max_length:
                    break
                
                # Skip if too close to last added sentence
                if idx - last_idx < 3:
                    continue
                
                # Get context: current sentence + surrounding sentences
                start_idx = max(0, idx - 2)
                end_idx = min(len(sentences), idx + 3)
                
                chunk = " ".join(sentences[start_idx:end_idx])
                
                if chunk not in result:  # Avoid duplicates
                    result.append(chunk)
                    current_length += len(chunk)
                    last_idx = idx
            
            return " ".join(result)[:max_length]
            
        except Exception as e:
            print(f"Error in semantic extraction: {e}")
            return self._fallback_extraction(text, topic, max_length)
    
    def _split_sentences(self, text):
        """Split text into sentences."""
        import re
        
        # Simple sentence splitter
        sentences = re.split(r'[.!?]\s+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        return sentences
    
    def _fallback_extraction(self, text, topic, max_length):
        """Fallback: Simple keyword-based extraction."""
        # Handle None topic
        if not topic:
            return text[:max_length]
        
        # Try to find the topic in the text
        topic_lower = topic.lower()
        text_lower = text.lower()
        
        # Find the position of the topic
        pos = text_lower.find(topic_lower)
        
        if pos > -1:
            # Extract centered around the topic
            start = max(0, pos - 2000)
            end = min(len(text), pos + 6000)
            return text[start:end]
        else:
            # Topic not found, return beginning
            return text[:max_length]
    
    def extract_multiple_topics(self, text, topics, max_length_per_topic=5000):
        """
        Extract text for multiple topics.
        
        Args:
            text (str): Full document text
            topics (list): List of topics to extract
            max_length_per_topic (int): Max chars per topic
        
        Returns:
            dict: {topic: extracted_text, ...}
        """
        result = {}
        for topic in topics:
            result[topic] = self.extract_topic_text(text, topic, max_length_per_topic)
        return result


def get_topic_text(text, topic, use_semantic=True, cached_embeddings=None):
    """
    Convenience function to extract topic-specific text.
    
    Args:
        text (str): Full document text
        topic (str): Topic to extract
        use_semantic (bool): Use semantic similarity (requires ONNX embeddings)
        cached_embeddings (dict): Pre-computed embeddings from database
    
    Returns:
        str: Extracted text relevant to the topic
    """
    if use_semantic and EMBEDDINGS_AVAILABLE:
        extractor = TopicAwareTextExtractor()
        return extractor.extract_topic_text(text, topic, cached_embeddings=cached_embeddings)
    else:
        # Simple fallback
        return _simple_keyword_extraction(text, topic)


def _simple_keyword_extraction(text, topic, max_length=8000):
    """Simple keyword-based extraction (no HF models required)."""
    # Handle None or empty topic
    if not topic:
        return text[:max_length]
    
    topic_lower = topic.lower()
    text_lower = text.lower()
    
    # Find topic position
    pos = text_lower.find(topic_lower)
    
    if pos > -1:
        start = max(0, pos - 2000)
        end = min(len(text), pos + 6000)
        return text[start:end]
    else:
        return text[:max_length]


def split_into_sentences(text):
    """
    Split text into sentences for embedding caching.
    Returns list of sentence strings.
    """
    extractor = TopicAwareTextExtractor()
    return extractor._split_sentences(text)


def compute_embeddings(text):
    """
    Compute and return embeddings for all sentences in text.
    Returns dict with 'sentences' and 'embeddings' (as list of lists for MongoDB).
    Returns None if embeddings not available.
    """
    if not EMBEDDINGS_AVAILABLE:
        return None
    
    try:
        # Split into sentences
        sentences = split_into_sentences(text)
        if not sentences:
            return None
        
        # Compute embeddings
        embeddings = embed_texts(sentences, prefix="search_document:")
        
        # Convert to list of lists for MongoDB storage
        return {
            'sentences': sentences,
            'embeddings': embeddings.tolist()  # Convert numpy array to list
        }
    except Exception as e:
        print(f"Error computing embeddings: {e}")
        return None
