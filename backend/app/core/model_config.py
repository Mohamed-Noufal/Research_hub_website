"""
Model Configuration - Flexible LLM model selection
Allows users to choose their preferred LLM provider and model.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import os


class ModelProvider(str, Enum):
    """Supported LLM providers."""
    GROQ = "groq"
    TOGETHER = "together"
    OPENAI = "openai"
    GOOGLE = "google"  # Gemini


@dataclass
class ModelConfig:
    """Configuration for a single model."""
    id: str                    # e.g., "qwen/qwen3-32b"
    name: str                  # Display name: "Qwen 32B"
    provider: ModelProvider
    context_length: int        # Max tokens
    input_cost_per_m: float    # $ per million input tokens
    output_cost_per_m: float   # $ per million output tokens
    speed: str                 # "ultra-fast", "fast", "moderate"
    quality: int               # 1-5 stars
    description: str           # Short description
    requires_api_key: str      # Env var name for API key


# ==================== AVAILABLE MODELS ====================

AVAILABLE_MODELS: Dict[str, ModelConfig] = {
    # GROQ Models (Free tier available)
    "groq/qwen3-32b": ModelConfig(
        id="qwen/qwen3-32b",
        name="Qwen 32B (Groq)",
        provider=ModelProvider.GROQ,
        context_length=32768,
        input_cost_per_m=0.0,  # Free with rate limits
        output_cost_per_m=0.0,
        speed="ultra-fast",
        quality=4,
        description="Fast, free, great for development. Rate limited.",
        requires_api_key="GROQ_API_KEY"
    ),
    "groq/llama-3.1-70b": ModelConfig(
        id="llama-3.1-70b-versatile",
        name="Llama 3.1 70B (Groq)",
        provider=ModelProvider.GROQ,
        context_length=131072,
        input_cost_per_m=0.0,
        output_cost_per_m=0.0,
        speed="ultra-fast",
        quality=5,
        description="Meta's best open model. Fast inference on Groq.",
        requires_api_key="GROQ_API_KEY"
    ),
    
    # TOGETHER AI Models (Cheap, $5 free credit)
    "together/llama-3.1-70b": ModelConfig(
        id="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        name="Llama 3.1 70B (Together)",
        provider=ModelProvider.TOGETHER,
        context_length=131072,
        input_cost_per_m=0.88,
        output_cost_per_m=0.88,
        speed="fast",
        quality=5,
        description="Excellent quality, good price. $5 free credit.",
        requires_api_key="TOGETHER_API_KEY"
    ),
    "together/qwen2.5-72b": ModelConfig(
        id="Qwen/Qwen2.5-72B-Instruct-Turbo",
        name="Qwen 2.5 72B (Together)",
        provider=ModelProvider.TOGETHER,
        context_length=32768,
        input_cost_per_m=1.20,
        output_cost_per_m=1.20,
        speed="fast",
        quality=5,
        description="Alibaba's latest, excellent for code and reasoning.",
        requires_api_key="TOGETHER_API_KEY"
    ),
    
    # OPENAI Models (If user has subscription)
    "openai/gpt-4o-mini": ModelConfig(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider=ModelProvider.OPENAI,
        context_length=128000,
        input_cost_per_m=0.15,
        output_cost_per_m=0.60,
        speed="fast",
        quality=4,
        description="Cheap GPT-4 variant, good for most tasks.",
        requires_api_key="OPENAI_API_KEY"
    ),
    "openai/gpt-5-nano": ModelConfig(
        id="gpt-5-nano",
        name="GPT-5 Nano",
        provider=ModelProvider.OPENAI,
        context_length=128000,
        input_cost_per_m=0.05,
        output_cost_per_m=0.40,
        speed="ultra-fast",
        quality=3,
        description="Ultra-cheap GPT-5, good for simple tasks.",
        requires_api_key="OPENAI_API_KEY"
    ),
    "openai/gpt-5-mini": ModelConfig(
        id="gpt-5-mini",
        name="GPT-5 Mini",
        provider=ModelProvider.OPENAI,
        context_length=128000,
        input_cost_per_m=0.25,
        output_cost_per_m=2.00,
        speed="fast",
        quality=4,
        description="Balanced GPT-5 variant, good quality/cost ratio.",
        requires_api_key="OPENAI_API_KEY"
    ),
    "openai/gpt-5.1": ModelConfig(
        id="gpt-5.1",
        name="GPT-5.1 Standard",
        provider=ModelProvider.OPENAI,
        context_length=256000,
        input_cost_per_m=1.25,
        output_cost_per_m=10.00,
        speed="moderate",
        quality=5,
        description="Best reasoning, premium quality. Latest GPT.",
        requires_api_key="OPENAI_API_KEY"
    ),
    
    # GOOGLE Gemini Models
    "google/gemini-3-flash": ModelConfig(
        id="gemini-3-flash",
        name="Gemini 3 Flash",
        provider=ModelProvider.GOOGLE,
        context_length=1000000,
        input_cost_per_m=0.50,  # 4x cheaper than Pro!
        output_cost_per_m=3.00,
        speed="ultra-fast",
        quality=4,
        description="Fast & cheap! 1M context window. 4x cheaper than Pro.",
        requires_api_key="GOOGLE_API_KEY"
    ),
    
    # QWEN 3 Large Models (Best value!)
    "together/qwen3-235b": ModelConfig(
        id="Qwen/Qwen3-235B-A22B-Instruct",
        name="Qwen3 235B (Best Value!)",
        provider=ModelProvider.TOGETHER,
        context_length=131072,
        input_cost_per_m=0.18,
        output_cost_per_m=0.54,
        speed="fast",
        quality=5,
        description="235B params at $0.18/M! Best quality/cost ratio in 2026.",
        requires_api_key="TOGETHER_API_KEY"
    ),
}


# ==================== MODEL CATEGORIES ====================

MODEL_CATEGORIES = {
    "free": ["groq/qwen3-32b", "groq/llama-3.1-70b"],
    "budget": ["openai/gpt-4o-mini", "openai/gpt-5-nano", "google/gemini-3-flash"],
    "balanced": ["together/llama-3.1-70b", "together/qwen2.5-72b", "together/qwen3-235b"],
    "premium": ["openai/gpt-5.1"],
}


# ==================== HELPER FUNCTIONS ====================

def get_available_models(check_api_keys: bool = True) -> List[ModelConfig]:
    """
    Get list of available models.
    
    Args:
        check_api_keys: If True, only return models with valid API keys
        
    Returns:
        List of available ModelConfig objects
    """
    if not check_api_keys:
        return list(AVAILABLE_MODELS.values())
    
    available = []
    for model in AVAILABLE_MODELS.values():
        api_key = os.getenv(model.requires_api_key)
        if api_key:
            available.append(model)
    
    return available


def get_model_by_id(model_id: str) -> Optional[ModelConfig]:
    """Get model config by ID."""
    return AVAILABLE_MODELS.get(model_id)


def get_models_by_provider(provider: ModelProvider) -> List[ModelConfig]:
    """Get all models for a provider."""
    return [m for m in AVAILABLE_MODELS.values() if m.provider == provider]


def get_models_by_category(category: str) -> List[ModelConfig]:
    """Get models by budget category (free, budget, balanced, premium)."""
    model_ids = MODEL_CATEGORIES.get(category, [])
    return [AVAILABLE_MODELS[mid] for mid in model_ids if mid in AVAILABLE_MODELS]


def get_default_model() -> ModelConfig:
    """Get default model (first available)."""
    available = get_available_models()
    if available:
        return available[0]
    # Fallback to Groq even without checking key
    return AVAILABLE_MODELS["groq/qwen3-32b"]


def estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """
    Estimate cost for a request.
    
    Args:
        model_id: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Estimated cost in USD
    """
    model = get_model_by_id(model_id)
    if not model:
        return 0.0
    
    input_cost = (input_tokens / 1_000_000) * model.input_cost_per_m
    output_cost = (output_tokens / 1_000_000) * model.output_cost_per_m
    return input_cost + output_cost


# ==================== FOR FRONTEND API ====================

def get_models_for_ui() -> List[Dict[str, Any]]:
    """
    Get model list formatted for frontend dropdown.
    
    Returns:
        List of dicts with model info for UI
    """
    models = []
    for key, model in AVAILABLE_MODELS.items():
        has_key = bool(os.getenv(model.requires_api_key))
        models.append({
            "id": key,
            "name": model.name,
            "provider": model.provider.value,
            "quality": model.quality,
            "speed": model.speed,
            "cost_tier": "free" if model.input_cost_per_m == 0 else 
                        "budget" if model.input_cost_per_m < 1 else 
                        "balanced" if model.input_cost_per_m < 3 else "premium",
            "context_length": model.context_length,
            "description": model.description,
            "available": has_key,
            "requires_key": not has_key
        })
    
    # Sort: available first, then by quality
    models.sort(key=lambda m: (not m["available"], -m["quality"]))
    return models
