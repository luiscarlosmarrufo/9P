#!/usr/bin/env python3
"""
vLLM server for 9P classification inference
Provides OpenAI-compatible API for Stage 2 classification fallback
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import asyncio
from contextlib import asynccontextmanager

from vllm import LLM, SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
MODEL_NAME = os.getenv("MODEL_NAME", "microsoft/DialoGPT-medium")
GPU_MEMORY_UTILIZATION = float(os.getenv("GPU_MEMORY_UTILIZATION", "0.8"))
MAX_MODEL_LEN = int(os.getenv("MAX_MODEL_LEN", "2048"))
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

# Global engine instance
engine: Optional[AsyncLLMEngine] = None

# Pydantic models for API
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")

class ChatCompletionRequest(BaseModel):
    model: str = Field(default=MODEL_NAME, description="Model to use")
    messages: List[ChatMessage] = Field(..., description="List of messages")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=2048)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    stop: Optional[List[str]] = Field(default=None)
    stream: bool = Field(default=False)

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Dict[str, int]

class HealthResponse(BaseModel):
    status: str
    model: str
    gpu_memory_utilization: float
    max_model_len: int

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global engine
    
    # Startup
    logger.info(f"Starting vLLM server with model: {MODEL_NAME}")
    
    try:
        # Initialize vLLM engine
        engine_args = AsyncEngineArgs(
            model=MODEL_NAME,
            gpu_memory_utilization=GPU_MEMORY_UTILIZATION,
            max_model_len=MAX_MODEL_LEN,
            disable_log_stats=True,
            trust_remote_code=True
        )
        
        engine = AsyncLLMEngine.from_engine_args(engine_args)
        logger.info("vLLM engine initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize vLLM engine: {e}")
        raise
    
    yield
    
    # Shutdown
    if engine:
        logger.info("Shutting down vLLM engine")

# Create FastAPI app
app = FastAPI(
    title="9P vLLM Inference Server",
    description="OpenAI-compatible API for 9P classification using vLLM",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if engine else "unhealthy",
        model=MODEL_NAME,
        gpu_memory_utilization=GPU_MEMORY_UTILIZATION,
        max_model_len=MAX_MODEL_LEN
    )

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    """Create a chat completion (OpenAI-compatible)"""
    if not engine:
        raise HTTPException(status_code=503, detail="vLLM engine not initialized")
    
    try:
        # Convert messages to prompt
        prompt = format_messages_to_prompt(request.messages)
        
        # Create sampling parameters
        sampling_params = SamplingParams(
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            stop=request.stop,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty
        )
        
        # Generate response
        request_id = f"chat-{hash(prompt) % 1000000}"
        
        # Use vLLM engine to generate
        results = engine.generate(prompt, sampling_params, request_id)
        
        # Process results
        async for result in results:
            if result.finished:
                generated_text = result.outputs[0].text
                
                # Create response
                response = ChatCompletionResponse(
                    id=request_id,
                    created=int(asyncio.get_event_loop().time()),
                    model=request.model,
                    choices=[
                        ChatCompletionChoice(
                            index=0,
                            message=ChatMessage(role="assistant", content=generated_text),
                            finish_reason="stop"
                        )
                    ],
                    usage={
                        "prompt_tokens": len(prompt.split()),
                        "completion_tokens": len(generated_text.split()),
                        "total_tokens": len(prompt.split()) + len(generated_text.split())
                    }
                )
                
                return response
        
        raise HTTPException(status_code=500, detail="Failed to generate response")
        
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/completions")
async def create_completion(request: Dict[str, Any]):
    """Create a text completion (OpenAI-compatible)"""
    if not engine:
        raise HTTPException(status_code=503, detail="vLLM engine not initialized")
    
    try:
        prompt = request.get("prompt", "")
        max_tokens = request.get("max_tokens", 512)
        temperature = request.get("temperature", 0.1)
        top_p = request.get("top_p", 0.95)
        stop = request.get("stop")
        
        # Create sampling parameters
        sampling_params = SamplingParams(
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stop=stop
        )
        
        # Generate response
        request_id = f"completion-{hash(prompt) % 1000000}"
        results = engine.generate(prompt, sampling_params, request_id)
        
        # Process results
        async for result in results:
            if result.finished:
                generated_text = result.outputs[0].text
                
                return {
                    "id": request_id,
                    "object": "text_completion",
                    "created": int(asyncio.get_event_loop().time()),
                    "model": request.get("model", MODEL_NAME),
                    "choices": [
                        {
                            "text": generated_text,
                            "index": 0,
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": len(prompt.split()),
                        "completion_tokens": len(generated_text.split()),
                        "total_tokens": len(prompt.split()) + len(generated_text.split())
                    }
                }
        
        raise HTTPException(status_code=500, detail="Failed to generate response")
        
    except Exception as e:
        logger.error(f"Error in completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible)"""
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_NAME,
                "object": "model",
                "created": 1677610602,
                "owned_by": "9p-analytics"
            }
        ]
    }

def format_messages_to_prompt(messages: List[ChatMessage]) -> str:
    """Convert chat messages to a single prompt string"""
    prompt_parts = []
    
    for message in messages:
        if message.role == "system":
            prompt_parts.append(f"System: {message.content}")
        elif message.role == "user":
            prompt_parts.append(f"User: {message.content}")
        elif message.role == "assistant":
            prompt_parts.append(f"Assistant: {message.content}")
    
    # Add assistant prompt
    prompt_parts.append("Assistant:")
    
    return "\n".join(prompt_parts)

def create_9p_classification_prompt(text: str, brand_context: str = "") -> str:
    """Create a specialized prompt for 9P classification"""
    
    system_prompt = """You are an expert marketing analyst specializing in the 9P marketing mix framework. 
Your task is to analyze social media content and classify it according to the 9 marketing mix dimensions:

1. Product - Features, quality, design, branding, packaging
2. Place - Distribution channels, locations, accessibility
3. Price - Pricing strategies, value perception, discounts
4. Publicity - Advertising, PR, marketing communications
5. Post-consumption - Customer service, support, loyalty programs
6. Purpose - Brand mission, values, social responsibility
7. Partnerships - Collaborations, sponsorships, alliances
8. People - Staff, customers, community, influencers
9. Planet - Environmental impact, sustainability, green practices

Analyze the following text and provide scores (0.0-1.0) for each dimension, plus sentiment analysis.
Respond ONLY with valid JSON in this exact format:

{
    "nine_p": {
        "product": 0.0,
        "place": 0.0,
        "price": 0.0,
        "publicity": 0.0,
        "postconsumption": 0.0,
        "purpose": 0.0,
        "partnerships": 0.0,
        "people": 0.0,
        "planet": 0.0
    },
    "sentiment": {
        "label": "positive|neutral|negative",
        "positive": 0.0,
        "neutral": 0.0,
        "negative": 0.0
    },
    "confidence": 0.0
}"""

    user_prompt = f"""Text to analyze: "{text}"
    
{f"Brand context: {brand_context}" if brand_context else ""}

Please analyze this text according to the 9P framework and provide the JSON response."""

    return f"{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"

@app.post("/classify")
async def classify_text(request: Dict[str, Any]):
    """Custom endpoint for 9P classification"""
    if not engine:
        raise HTTPException(status_code=503, detail="vLLM engine not initialized")
    
    try:
        text = request.get("text", "")
        brand_context = request.get("brand_context", "")
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # Create specialized prompt
        prompt = create_9p_classification_prompt(text, brand_context)
        
        # Create sampling parameters optimized for JSON output
        sampling_params = SamplingParams(
            temperature=0.1,  # Low temperature for consistent JSON
            top_p=0.9,
            max_tokens=512,
            stop=["\n\n", "User:", "System:"]
        )
        
        # Generate response
        request_id = f"classify-{hash(text) % 1000000}"
        results = engine.generate(prompt, sampling_params, request_id)
        
        # Process results
        async for result in results:
            if result.finished:
                generated_text = result.outputs[0].text.strip()
                
                try:
                    # Try to parse as JSON
                    classification_result = json.loads(generated_text)
                    return classification_result
                except json.JSONDecodeError:
                    # If JSON parsing fails, return error
                    logger.error(f"Failed to parse JSON: {generated_text}")
                    raise HTTPException(
                        status_code=500, 
                        detail="Failed to generate valid JSON classification"
                    )
        
        raise HTTPException(status_code=500, detail="Failed to generate classification")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in classification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info(f"Starting vLLM server on {HOST}:{PORT}")
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=True
    )
