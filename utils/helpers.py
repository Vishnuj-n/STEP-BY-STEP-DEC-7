"""
Helper utilities for Mind Palace application.
Uses Groq Cloud API with OpenAI models, fallback to Gemini for large content.
"""
import json
import os
from PyPDF2 import PdfReader
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Groq client for LLM API calls
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# Gemini client for large content fallback (optional, only if API key is available)
gemini_client = None
try:
    from google import genai
    if os.getenv('GEMINI_API_KEY'):
        gemini_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
except ImportError:
    pass  # Gemini not installed, will use Groq only

def load_prompt(prompt_file):
    """Load a prompt configuration from JSON file."""
    prompt_path = os.path.join('prompts', prompt_file)
    with open(prompt_path, 'r') as f:
        return json.load(f)

def extract_text_from_pdf(pdf_file):
    """Extract text content from a PDF file."""
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def call_llm(prompt_config, context_text="", target_text="", **kwargs):
    """
    Call Groq API for standard text generation using OpenAI models.
    
    Args:
        prompt_config (dict): Dictionary with 'system_instruction' and 'user_instruction'
        context_text (str): The main content/document text to process
        target_text (str): Target topic, concept, or specific text (used in formatting)
        **kwargs: Additional variables to format the user_instruction
    
    Returns:
        str: Generated text response from LLM
    """
    model_name = os.getenv('GROQ_MODELS', 'openai/gpt-oss-120b')
    
    # Format user instruction with provided variables
    # Supports multiple placeholder names for backward compatibility with different prompts
    format_vars = {
        'target_text': target_text,
        'text': context_text,  # Support {text} placeholder
        'topic': target_text,  # Support {topic} placeholder
        **kwargs
    }
    user_instruction = prompt_config['user_instruction'].format(**format_vars)
    
    # Build final prompt with clear structure
    if context_text:
        full_prompt = f"{user_instruction}\n\nCONTENT:\n{context_text}"
    else:
        full_prompt = user_instruction
    
    # Get system instruction (optional)
    system_instruction = prompt_config.get('system_instruction', '')
    
    # Build messages array
    messages = []
    if system_instruction:
        messages.append({
            "role": "system",
            "content": system_instruction
        })
    messages.append({
        "role": "user",
        "content": full_prompt
    })
    
    # Estimate token count (rough estimate: 4 chars per token)
    total_text = system_instruction + full_prompt if system_instruction else full_prompt
    estimated_tokens = len(total_text) // 4
    
    # Use Gemini for large content if available, otherwise use Groq
    if estimated_tokens > 7500 and gemini_client:
        # Use Gemini API for large content
        try:
            response = gemini_client.models.generate_content(
                model=os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp'),
                contents=full_prompt
            )
            return response.text
        except Exception as e:
            # Fallback to Groq if Gemini fails
            print(f"Gemini fallback failed: {e}. Using Groq instead.")
    
    # Use Groq API (default for small content or if Gemini unavailable)
    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model_name,
        temperature=0.7,
        max_tokens=4096
    )
    return chat_completion.choices[0].message.content

def parse_json_response(response_text):
    """
    Extract and parse JSON from LLM response.
    Handles cases where JSON is wrapped in markdown code blocks.
    """
    # Try to extract JSON from markdown code blocks
    if '```json' in response_text:
        start = response_text.find('```json') + 7
        end = response_text.find('```', start)
        json_text = response_text[start:end].strip()
    elif '```' in response_text:
        start = response_text.find('```') + 3
        end = response_text.find('```', start)
        json_text = response_text[start:end].strip()
    else:
        json_text = response_text.strip()
    
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        # If parsing fails, return the raw text
        return response_text

def chunk_text(text, max_length=5000):
    """Split text into chunks for processing."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        current_length += len(word) + 1
        if current_length > max_length:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


def call_llm_structured(prompt_text, schema_class, model_name="openai/gpt-oss-120b"):
    """
    Call Groq API with structured output using Pydantic schema.
    
    Follows Groq's schema requirements:
    - All properties must be required (optional fields not supported)
    - additionalProperties must be false (enforced via ConfigDict(extra='forbid'))
    - Supports: primitives, objects, arrays, enums, anyOf
    
    Args:
        prompt_text (str): The prompt to send to LLM
        schema_class: Pydantic BaseModel with ConfigDict(extra='forbid')
        model_name (str): Model to use (default: openai/gpt-oss-120b)
    
    Returns:
        Instance of schema_class with validated data
    
    Raises:
        ValueError: If response doesn't match schema
    """
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Output JSON only using the schema provided."
            },
            {
                "role": "user",
                "content": prompt_text
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": schema_class.__name__.lower(),
                "schema": schema_class.model_json_schema()
            }
        },
        temperature=0.7,
        max_tokens=4096
    )
    
    # Parse and validate response using Pydantic
    try:
        raw_result = json.loads(response.choices[0].message.content or "{}")
        return schema_class.model_validate(raw_result)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response from Groq: {e}")
    except Exception as e:
        raise ValueError(f"Schema validation failed: {e}")
