#!/usr/bin/env python3
"""
FastAPI Web Interface for OpenAI Research Client
Local hosting optimized version
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import asyncio
import uuid
from datetime import datetime
import os
import sys
import re
import time
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Embedded research client for Vercel compatibility
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ResearchConfig:
    """Configuration for research requests"""
    model: str = "o3-deep-research"
    background: bool = True
    max_tool_calls: int = 40
    tools: Optional[List[Dict[str, Any]]] = None

class OpenAIResearchClient:
    """Embedded OpenAI Research API client for Vercel"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key, timeout=3600)
        
        self.available_models = {
            "o3-deep-research": {
                "name": "O3 Deep Research",
                "description": "Most comprehensive research model with advanced reasoning capabilities",
                "best_for": "Complex analysis, detailed reports, comprehensive research",
                "cost": "Higher", "speed": "Slower"
            },
            "o4-mini-deep-research": {
                "name": "O4 Mini Deep Research", 
                "description": "Faster, cost-effective research model for quicker insights",
                "best_for": "Quick research, initial exploration, cost-sensitive tasks",
                "cost": "Lower", "speed": "Faster"
            }
        }
    
    def get_available_models(self) -> Dict[str, Any]:
        return self.available_models
    
    def create_response(self, model: str, input_text: str, background: bool = True,
                       tools: Optional[List[Dict[str, Any]]] = None, **kwargs):
        request_data = {"model": model, "input": input_text, "background": background}
        if tools: request_data["tools"] = tools
        request_data.update(kwargs)
        
        try:
            response = self.client.responses.create(**request_data)
            return response
        except Exception as e:
            print(f"Error creating research response: {e}")
            return None
    
    def get_response(self, response_id: str):
        try:
            return self.client.responses.retrieve(response_id)
        except Exception as e:
            print(f"Error retrieving response {response_id}: {e}")
            return None
    
    def wait_for_completion(self, response_id: str, check_interval: int = 5, max_wait: int = 3600):
        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = self.get_response(response_id)
            if response and hasattr(response, 'status'):
                if response.status == 'completed': return response
                elif response.status == 'failed': raise Exception(f"Research task failed: {response}")
            time.sleep(check_interval)
        raise TimeoutError(f"Research task did not complete within {max_wait} seconds")
    
    def enrich_prompt(self, user_request: str, research_type: str = "general") -> str:
        """Enhanced prompt enrichment for better research quality"""
        enrichment_instructions = f"""
        Transform the user's research request into detailed instructions for a researcher.
        
        RESEARCH TYPE: {research_type}
        
        ENHANCED GUIDELINES:
        1. **Maximize Detail & Specificity** - Include all user preferences and key dimensions
        2. **Request Structured Output** - Ask for tables, headers, and organized sections
        3. **Demand Quality Sources** - Require inline citations with full source metadata
        4. **Format Requirements** - Specify markdown formatting with clear hierarchy
        5. **Comprehensive Coverage** - Ensure all aspects of the topic are addressed
        
        For product/service research: prioritize official sites, reviews, comparisons
        For academic research: prefer original papers, authoritative publications
        Always request citation counts, word counts, and structured analysis.
        """
        
        try:
            response = self.client.responses.create(
                model="gpt-4o-mini", input=user_request, 
                instructions=enrichment_instructions
            )
            return response.output_text if hasattr(response, 'output_text') else user_request
        except Exception as e:
            print(f"Error enriching prompt: {e}")
            return user_request

class ResearchWorkflow:
    """Embedded research workflows for Vercel"""
    
    def __init__(self, client: OpenAIResearchClient):
        self.client = client
    
    def _prepare_tools(self, use_web_search: bool = True, use_code_interpreter: bool = False):
        tools = []
        if use_web_search: tools.append({"type": "web_search_preview"})
        if use_code_interpreter: tools.append({"type": "code_interpreter", "container": {"type": "auto"}})
        return tools
    
    def custom_research(self, query: str, model: str = "o3-deep-research", 
                       research_type: str = "general", enrich_prompt: bool = True) -> Dict[str, Any]:
        research_prompt = query
        if enrich_prompt:
            print("Enriching prompt...")
            research_prompt = self.client.enrich_prompt(query, research_type)
        
        tools = self._prepare_tools(use_web_search=True, use_code_interpreter=True)
        response = self.client.create_response(
            model=model, input_text=research_prompt, background=True,
            tools=tools, max_tool_calls=40
        )
        
        if response and response.id:
            completed_response = self.client.wait_for_completion(response.id)
            return {
                "type": "custom_research", "response_id": response.id,
                "output": completed_response.output_text if hasattr(completed_response, 'output_text') else None,
                "status": "completed", "original_query": query,
                "enriched_prompt": research_prompt if enrich_prompt else None
            }
        return {"type": "custom_research", "status": "failed", "response": response}

# Initialize embedded research client
try:
    research_client = OpenAIResearchClient()
    research_workflow = ResearchWorkflow(research_client)
    storage_service = None  # Simplified for Vercel
    print("✓ Embedded research client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize embedded research client: {e}")
    research_client = None
    research_workflow = None
    storage_service = None

app = FastAPI(title="OpenAI Research Interface", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for research tasks (for Vercel compatibility)
research_tasks = {}
completed_results = {}
session_storage = {}

# Fallback OpenAI client for when services aren't available
def get_openai_client():
    """Lazy initialization of OpenAI client as fallback"""
    try:
        from openai import OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            return OpenAI(api_key=api_key, timeout=30.0, max_retries=2)
    except Exception as e:
        print(f"Failed to initialize fallback OpenAI client: {e}")
    return None

class ResearchRequest(BaseModel):
    query: str
    model: str = "o3-deep-research"
    research_type: str = "custom"  # custom, validation, market, financial, comprehensive
    enrich_prompt: bool = True

class ResearchStatus(BaseModel):
    task_id: str
    status: str  # pending, running, completed, failed
    created_at: str
    query: str
    model: str
    research_type: str
    progress: Optional[str] = None
    error: Optional[str] = None

class ResearchResult(BaseModel):
    task_id: str
    status: str
    query: str
    model: str
    research_type: str
    result: Optional[Dict[str, Any]] = None
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None

def extract_citations(text: str) -> int:
    """Extract citation count from research text"""
    if not text:
        return 0
    # Count markdown links and various citation formats
    citations = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
    return len(citations)

def format_research_output(result: Dict[str, Any], research_type: str) -> Dict[str, Any]:
    """Format research result for better display"""
    if not result or not result.get("output"):
        return result
    
    output_text = result["output"]
    
    # Extract metadata
    citation_count = extract_citations(output_text)
    word_count = len(output_text.split()) if output_text else 0
    
    # For comprehensive research, format each section
    if research_type == "comprehensive" and isinstance(result, dict):
        formatted_sections = {}
        total_citations = 0
        
        for section_name, section_data in result.items():
            if isinstance(section_data, dict) and section_data.get("output"):
                section_output = section_data["output"]
                section_citations = extract_citations(section_output)
                total_citations += section_citations
                
                formatted_sections[section_name] = {
                    **section_data,
                    "formatted_output": section_output,
                    "citations": section_citations,
                    "word_count": len(section_output.split())
                }
        
        return {
            "type": "comprehensive",
            "sections": formatted_sections,
            "total_citations": total_citations,
            "total_words": sum(s.get("word_count", 0) for s in formatted_sections.values())
        }
    
    # For single research types
    return {
        **result,
        "formatted_output": output_text,
        "citations": citation_count,
        "word_count": word_count
    }

def run_progressive_comprehensive_research(task_id: str, request: ResearchRequest) -> Dict[str, Any]:
    """Run comprehensive research with progressive updates"""
    if not research_workflow:
        raise Exception("Research workflow not available")
    
    comprehensive_result = {
        "type": "comprehensive",
        "sections": {},
        "progress": {},
        "total_citations": 0,
        "total_words": 0
    }
    
    # Step 1: Validation
    research_tasks[task_id]["progress"] = "Step 1/3: Running idea validation analysis..."
    validation_result = research_workflow.validate_idea(request.query, request.model)
    
    if validation_result.get("status") == "completed":
        formatted_validation = format_research_output(validation_result, "validation")
        comprehensive_result["sections"]["validation"] = formatted_validation
        comprehensive_result["progress"]["validation"] = "completed"
        
        # Update live result for progressive display
        research_tasks[task_id]["partial_result"] = comprehensive_result.copy()
        research_tasks[task_id]["progress"] = "Validation completed! Starting market research..."
    
    # Step 2: Market Research
    research_tasks[task_id]["progress"] = "Step 2/3: Conducting market research analysis..."
    market_result = research_workflow.market_research(request.query, request.model)
    
    if market_result.get("status") == "completed":
        formatted_market = format_research_output(market_result, "market")
        comprehensive_result["sections"]["market"] = formatted_market
        comprehensive_result["progress"]["market"] = "completed"
        
        # Update live result for progressive display
        research_tasks[task_id]["partial_result"] = comprehensive_result.copy()
        research_tasks[task_id]["progress"] = "Market research completed! Starting financial analysis..."
    
    # Step 3: Financial Analysis
    research_tasks[task_id]["progress"] = "Step 3/3: Executing financial analysis..."
    financial_result = research_workflow.financial_analysis(request.query, request.model)
    
    if financial_result.get("status") == "completed":
        formatted_financial = format_research_output(financial_result, "financial")
        comprehensive_result["sections"]["financial"] = formatted_financial
        comprehensive_result["progress"]["financial"] = "completed"
        
        # Calculate totals
        total_citations = sum(
            section.get("citations", 0) 
            for section in comprehensive_result["sections"].values()
        )
        total_words = sum(
            section.get("word_count", 0) 
            for section in comprehensive_result["sections"].values()
        )
        
        comprehensive_result["total_citations"] = total_citations
        comprehensive_result["total_words"] = total_words
        
        # Final update
        research_tasks[task_id]["partial_result"] = comprehensive_result.copy()
        research_tasks[task_id]["progress"] = "All research completed! Generating final report..."
    
    return comprehensive_result

def background_research_task(task_id: str, request: ResearchRequest):
    """Background task for conducting research"""
    start_time = datetime.now()
    
    try:
        # Update task status (simplified for Vercel)
        research_tasks[task_id]["status"] = "running"
        research_tasks[task_id]["progress"] = "Initializing AI research..."
        
        # For Vercel deployment, focus on custom research with proper prompt enrichment
        research_tasks[task_id]["progress"] = "Processing custom research query..."
        result = research_workflow.custom_research(
            request.query, 
            request.model, 
            request.research_type, 
            request.enrich_prompt
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Format the result for better display
        formatted_result = format_research_output(result, request.research_type)
        
        # Store completed result in both memory (for compatibility) and database
        completed_results[task_id] = ResearchResult(
            task_id=task_id,
            status="completed",
            query=request.query,
            model=request.model,
            research_type=request.research_type,
            result=formatted_result,
            created_at=research_tasks[task_id]["created_at"],
            completed_at=end_time.isoformat()
        )
        
        # Add metadata to the completed result
        completed_results[task_id].result["processing_time"] = round(processing_time, 1)
        completed_results[task_id].result["processing_time_formatted"] = f"{int(processing_time // 60)}m {int(processing_time % 60)}s"
        
        research_tasks[task_id]["status"] = "completed"
        research_tasks[task_id]["progress"] = f"Research completed successfully in {int(processing_time // 60)}m {int(processing_time % 60)}s"
        
    except Exception as e:
        research_tasks[task_id]["status"] = "failed"
        research_tasks[task_id]["error"] = str(e)
        completed_results[task_id] = ResearchResult(
            task_id=task_id,
            status="failed",
            query=request.query,
            model=request.model,
            research_type=request.research_type,
            created_at=research_tasks[task_id]["created_at"],
            error=str(e)
        )
        
        # Update failed status in storage service if available
        if storage_service:
            storage_service.update_research_task(task_id, {
                "status": "failed",
                "progress": f"Research failed: {str(e)}"
            })

async def conduct_fallback_research(query: str, model: str, research_type: str) -> Dict[str, Any]:
    """Fallback research function using direct OpenAI API"""
    if not research_client or not hasattr(research_client, 'chat'):
        raise Exception("OpenAI client not available")
    
    # Create research prompt based on type
    if research_type == "validation":
        prompt = f"""Conduct a comprehensive business idea validation analysis for: {query}

Please provide a detailed analysis covering:
1. Market Opportunity Assessment
2. Target Audience Analysis  
3. Competition Landscape
4. Technical Feasibility
5. Risk Assessment
6. Implementation Roadmap

Format the response with clear sections and actionable insights."""
    elif research_type == "market":
        prompt = f"""Perform detailed market research analysis for: {query}

Please provide comprehensive analysis covering:
1. Market Size and Growth Trends
2. Customer Segments and Demographics
3. Competitive Landscape Analysis
4. Market Entry Barriers
5. Pricing Strategy Recommendations
6. Market Opportunities and Threats

Format with clear sections and data-driven insights."""
    elif research_type == "financial":
        prompt = f"""Conduct financial feasibility analysis for: {query}

Please provide detailed financial analysis covering:
1. Revenue Projections and Models
2. Cost Analysis and Structure
3. Break-even Analysis
4. Funding Requirements
5. ROI Calculations
6. Financial Risk Assessment

Format with clear sections and numerical projections where applicable."""
    else:
        prompt = f"""Conduct comprehensive research on: {query}

Please provide detailed analysis with:
1. Overview and Context
2. Key Insights and Findings
3. Data and Statistics
4. Trends and Patterns
5. Recommendations and Next Steps
6. Sources and References

Format with clear sections and actionable recommendations."""

    try:
        response = research_client.chat.completions.create(
            model="gpt-4" if model in ["o3-deep-research", "gpt-4"] else "gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert research analyst. Provide comprehensive, well-structured analysis with actionable insights, data, and clear formatting using markdown headers and bullet points."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0.7
        )
        
        return {
            "status": "completed",
            "output": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main web interface - exact replica of original app.py"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OpenAI Research Interface</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <div x-data="researchApp()" class="container mx-auto px-4 py-8">
            <!-- Header -->
            <div class="text-center mb-8">
                <h1 class="text-4xl font-bold text-gray-900 mb-2">OpenAI Research Interface</h1>
                <p class="text-gray-600">Conduct comprehensive research using advanced AI models</p>
            </div>

            <!-- Model Selection & Research Form -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-8">
                <form @submit.prevent="submitResearch()" class="space-y-6">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Select Research Model</label>
                        <select x-model="selectedModel" class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <template x-for="model in models" :key="model.id">
                                <option :value="model.id" x-text="model.name"></option>
                            </template>
                        </select>
                        <div x-show="selectedModelInfo" class="mt-2 p-3 bg-blue-50 rounded-md">
                            <p class="text-sm text-blue-800" x-text="selectedModelInfo?.description"></p>
                            <div class="mt-1 text-xs text-blue-600">
                                <span x-text="'Best for: ' + selectedModelInfo?.best_for"></span> |
                                <span x-text="'Cost: ' + selectedModelInfo?.cost"></span> |
                                <span x-text="'Speed: ' + selectedModelInfo?.speed"></span>
                            </div>
                        </div>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Research Type</label>
                        <select x-model="researchType" class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="custom">Custom Research</option>
                            <option value="validation">Idea Validation</option>
                            <option value="market">Market Research</option>
                            <option value="financial">Financial Analysis</option>
                            <option value="comprehensive">Comprehensive Analysis (All Three)</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Research Query</label>
                        <textarea 
                            x-model="query" 
                            rows="4" 
                            class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Enter your research question or startup idea...">
                        </textarea>
                    </div>

                    <div class="flex items-center">
                        <input type="checkbox" x-model="enrichPrompt" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
                        <label class="ml-2 block text-sm text-gray-700">Enrich prompt automatically (recommended)</label>
                    </div>

                    <button 
                        type="submit" 
                        :disabled="!query || isLoading"
                        class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed">
                        <span x-show="!isLoading">Start Research</span>
                        <span x-show="isLoading">Starting Research...</span>
                    </button>
                </form>
            </div>

            <!-- Research Status -->
            <div x-show="currentTask" class="bg-white rounded-lg shadow-md p-6 mb-8">
                <h3 class="text-lg font-semibold mb-4">Research Progress</h3>
                
                <!-- Progress Steps -->
                <div class="mb-6">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm font-medium">Progress</span>
                        <span class="text-sm text-gray-600" x-text="getProgressPercentage() + '%'"></span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-3">
                        <div class="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-1000 ease-out" 
                             :style="'width: ' + getProgressPercentage() + '%'"></div>
                    </div>
                </div>

                <!-- Step Indicators -->
                <div class="space-y-3 mb-4">
                    <div class="flex items-center space-x-3">
                        <div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center" 
                             :class="getStepClass(1)">
                            <span x-show="getStepNumber() > 1" class="text-white text-sm">✓</span>
                            <span x-show="getStepNumber() === 1" class="w-3 h-3 bg-white rounded-full animate-pulse"></span>
                            <span x-show="getStepNumber() < 1" class="text-gray-400 text-sm">1</span>
                        </div>
                        <div class="flex-1">
                            <p class="text-sm font-medium" :class="getStepNumber() >= 1 ? 'text-gray-900' : 'text-gray-400'">
                                Initialize Research
                            </p>
                            <p class="text-xs text-gray-500">Setting up AI models and preparing query</p>
                        </div>
                    </div>

                    <div class="flex items-center space-x-3">
                        <div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center" 
                             :class="getStepClass(2)">
                            <span x-show="getStepNumber() > 2" class="text-white text-sm">✓</span>
                            <span x-show="getStepNumber() === 2" class="w-3 h-3 bg-white rounded-full animate-pulse"></span>
                            <span x-show="getStepNumber() < 2" class="text-gray-400 text-sm">2</span>
                        </div>
                        <div class="flex-1">
                            <p class="text-sm font-medium" :class="getStepNumber() >= 2 ? 'text-gray-900' : 'text-gray-400'">
                                Data Collection
                            </p>
                            <p class="text-xs text-gray-500">Gathering information from multiple sources</p>
                        </div>
                    </div>

                    <div class="flex items-center space-x-3">
                        <div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center" 
                             :class="getStepClass(3)">
                            <span x-show="getStepNumber() > 3" class="text-white text-sm">✓</span>
                            <span x-show="getStepNumber() === 3" class="w-3 h-3 bg-white rounded-full animate-pulse"></span>
                            <span x-show="getStepNumber() < 3" class="text-gray-400 text-sm">3</span>
                        </div>
                        <div class="flex-1">
                            <p class="text-sm font-medium" :class="getStepNumber() >= 3 ? 'text-gray-900' : 'text-gray-400'">
                                Analysis & Processing
                            </p>
                            <p class="text-xs text-gray-500">AI analysis and report generation</p>
                        </div>
                    </div>

                    <div class="flex items-center space-x-3">
                        <div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center" 
                             :class="getStepClass(4)">
                            <span x-show="getStepNumber() > 4" class="text-white text-sm">✓</span>
                            <span x-show="getStepNumber() === 4" class="w-3 h-3 bg-white rounded-full animate-pulse"></span>
                            <span x-show="getStepNumber() < 4" class="text-gray-400 text-sm">4</span>
                        </div>
                        <div class="flex-1">
                            <p class="text-sm font-medium" :class="getStepNumber() >= 4 ? 'text-gray-900' : 'text-gray-400'">
                                Final Report
                            </p>
                            <p class="text-xs text-gray-500">Formatting and finalizing results</p>
                        </div>
                    </div>
                </div>

                <!-- Current Status -->
                <div class="bg-blue-50 rounded-lg p-4">
                    <div class="flex items-center space-x-2">
                        <div x-show="currentTask?.status === 'running'" class="flex-shrink-0">
                            <div class="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                        </div>
                        <div>
                            <p class="text-sm font-medium text-blue-900" x-text="currentTask?.progress || 'Processing...'"></p>
                            <p class="text-xs text-blue-700">
                                <span x-text="'Model: ' + (currentTask?.model || 'Unknown')"></span> • 
                                <span x-text="'Type: ' + (currentTask?.research_type || 'custom')"></span>
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Research Results -->
            <div x-show="results.length > 0" class="space-y-6">
                <h2 class="text-2xl font-bold text-gray-900">Research Results</h2>
                <template x-for="result in results" :key="result.task_id">
                    <div class="bg-white rounded-lg shadow-md overflow-hidden">
                        <!-- Result Header -->
                        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b">
                            <div class="flex items-center justify-between mb-2">
                                <h3 class="text-lg font-semibold text-gray-900" x-text="result.query"></h3>
                                <div class="flex items-center space-x-2">
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800" 
                                          x-text="result.model"></span>
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800" 
                                          x-text="result.research_type"></span>
                                </div>
                            </div>
                            
                            <!-- Metadata Row -->
                            <div class="flex items-center justify-between text-sm text-gray-600">
                                <div class="flex items-center space-x-4">
                                    <span x-show="result.result?.processing_time_formatted" class="flex items-center space-x-1">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                        </svg>
                                        <span x-text="result.result.processing_time_formatted"></span>
                                    </span>
                                    <span x-show="getCitationCount(result)" class="flex items-center space-x-1">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                        </svg>
                                        <span x-text="getCitationCount(result) + ' citations'"></span>
                                    </span>
                                    <span x-show="getWordCount(result)" class="flex items-center space-x-1">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                                        </svg>
                                        <span x-text="getWordCount(result) + ' words'"></span>
                                    </span>
                                </div>
                                <span class="text-xs" x-text="'Completed: ' + new Date(result.completed_at).toLocaleString()"></span>
                            </div>
                        </div>

                        <!-- Result Content -->
                        <div class="p-6">
                            <div x-show="result.status === 'completed' && result.result">
                                <!-- Comprehensive Research Display -->
                                <div x-show="result.research_type === 'comprehensive'" class="space-y-6">
                                    <template x-for="(section, sectionName) in result.result?.sections || {}" :key="sectionName">
                                        <div class="border border-gray-200 rounded-lg">
                                            <div class="bg-gray-50 px-4 py-3 border-b">
                                                <h4 class="font-medium text-gray-900 capitalize" x-text="sectionName.replace('_', ' ')"></h4>
                                                <div class="flex items-center space-x-3 text-sm text-gray-600 mt-1">
                                                    <span x-show="section.citations" x-text="section.citations + ' citations'"></span>
                                                    <span x-show="section.word_count" x-text="section.word_count + ' words'"></span>
                                                </div>
                                            </div>
                                            <div class="p-4 max-h-64 overflow-y-auto">
                                                <div class="prose prose-sm max-w-none" x-html="formatMarkdown(section.formatted_output || section.output)"></div>
                                            </div>
                                        </div>
                                    </template>
                                </div>

                                <!-- Single Research Display -->
                                <div x-show="result.research_type !== 'comprehensive'" class="max-h-96 overflow-y-auto">
                                    <div class="prose prose-sm max-w-none" x-html="formatMarkdown(result.result?.formatted_output || result.result?.output || formatResult(result.result))"></div>
                                </div>

                                <!-- Action Buttons -->
                                <div class="mt-6 flex space-x-3">
                                    <button 
                                        @click="downloadResult(result)"
                                        class="inline-flex items-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                        </svg>
                                        Download Report
                                    </button>
                                    <button 
                                        @click="copyResult(result)"
                                        class="inline-flex items-center px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2">
                                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                                        </svg>
                                        Copy to Clipboard
                                    </button>
                                </div>
                            </div>

                            <div x-show="result.status === 'failed'" class="bg-red-50 border border-red-200 rounded-md p-4">
                                <div class="flex items-center">
                                    <svg class="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L5.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                                    </svg>
                                    <p class="text-red-800 text-sm font-medium">Research Failed</p>
                                </div>
                                <p class="text-red-700 text-sm mt-1" x-text="result.error"></p>
                            </div>
                        </div>
                    </div>
                </template>
            </div>
        </div>

        <script>
            function researchApp() {
                return {
                    models: [],
                    selectedModel: 'o3-deep-research',
                    researchType: 'custom',
                    query: '',
                    enrichPrompt: true,
                    isLoading: false,
                    currentTask: null,
                    results: [],

                    async init() {
                        await this.loadModels();
                        this.checkPendingTasks();
                        // Poll for updates every 5 seconds
                        setInterval(() => this.checkPendingTasks(), 5000);
                    },

                    get selectedModelInfo() {
                        return this.models.find(m => m.id === this.selectedModel);
                    },

                    async loadModels() {
                        try {
                            console.log('Loading models...');
                            const response = await fetch('/api/models');
                            console.log('Response status:', response.status);
                            if (!response.ok) {
                                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                            }
                            const data = await response.json();
                            console.log('Models data received:', data);
                            this.models = Object.entries(data).map(([id, info]) => ({
                                id,
                                name: info.name,
                                description: info.description,
                                best_for: info.best_for,
                                cost: info.cost,
                                speed: info.speed
                            }));
                            console.log('Models array:', this.models);
                        } catch (error) {
                            console.error('Failed to load models:', error);
                            // Fallback models if API fails
                            this.models = [
                                {
                                    id: 'o3-deep-research',
                                    name: 'O3 Deep Research',
                                    description: 'Most comprehensive research model with advanced reasoning capabilities',
                                    best_for: 'Complex analysis, detailed reports, comprehensive research',
                                    cost: 'Higher',
                                    speed: 'Slower'
                                },
                                {
                                    id: 'o4-mini-deep-research',
                                    name: 'O4 Mini Deep Research',
                                    description: 'Faster, cost-effective research model for quicker insights',
                                    best_for: 'Quick research, initial exploration, cost-sensitive tasks',
                                    cost: 'Lower',
                                    speed: 'Faster'
                                }
                            ];
                        }
                    },

                    async submitResearch() {
                        if (!this.query.trim()) return;

                        this.isLoading = true;
                        try {
                            const response = await fetch('/api/research', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    query: this.query,
                                    model: this.selectedModel,
                                    research_type: this.researchType,
                                    enrich_prompt: this.enrichPrompt
                                })
                            });

                            if (response.ok) {
                                const task = await response.json();
                                this.currentTask = task;
                                this.query = '';
                            } else {
                                alert('Failed to start research');
                            }
                        } catch (error) {
                            console.error('Error submitting research:', error);
                            alert('Error submitting research');
                        } finally {
                            this.isLoading = false;
                        }
                    },

                    async checkPendingTasks() {
                        if (this.currentTask && (this.currentTask.status === 'pending' || this.currentTask.status === 'running')) {
                            try {
                                // For comprehensive research, check progressive results
                                if (this.currentTask.research_type === 'comprehensive') {
                                    const progressResponse = await fetch(`/api/research/${this.currentTask.task_id}/progressive`);
                                    if (progressResponse.ok) {
                                        const progressData = await progressResponse.json();
                                        this.currentTask = progressData;
                                        
                                        // If there are partial results, add them to results display
                                        if (progressData.partial_result && progressData.partial_result.sections) {
                                            this.updateProgressiveResults(progressData);
                                        }
                                    }
                                }
                                
                                // Check regular status
                                const response = await fetch(`/api/research/${this.currentTask.task_id}/status`);
                                if (response.ok) {
                                    const status = await response.json();
                                    this.currentTask = {...this.currentTask, ...status};

                                    if (status.status === 'completed' || status.status === 'failed') {
                                        await this.loadResults();
                                        this.currentTask = null;
                                    }
                                }
                            } catch (error) {
                                console.error('Error checking task status:', error);
                            }
                        }
                    },

                    updateProgressiveResults(progressData) {
                        // Find existing progressive result or create new one
                        let existingIndex = this.results.findIndex(r => r.task_id === progressData.task_id);
                        
                        const progressiveResult = {
                            task_id: progressData.task_id,
                            query: this.currentTask.query,
                            model: this.currentTask.model,
                            research_type: 'comprehensive',
                            status: 'in-progress',
                            created_at: this.currentTask.created_at,
                            result: progressData.partial_result
                        };
                        
                        if (existingIndex >= 0) {
                            // Update existing progressive result
                            this.results[existingIndex] = progressiveResult;
                        } else {
                            // Add new progressive result
                            this.results.unshift(progressiveResult);
                        }
                    },

                    async loadResults() {
                        try {
                            const response = await fetch('/api/research/results');
                            if (response.ok) {
                                this.results = await response.json();
                            }
                        } catch (error) {
                            console.error('Error loading results:', error);
                        }
                    },

                    getProgressPercentage() {
                        if (!this.currentTask) return 0;
                        const status = this.currentTask.status;
                        const progress = this.currentTask.progress || '';
                        
                        if (status === 'pending') return 10;
                        if (status === 'running') {
                            if (progress.includes('Initializing')) return 25;
                            if (progress.includes('collecting') || progress.includes('Conducting') || progress.includes('Performing')) return 50;
                            if (progress.includes('Processing') || progress.includes('analysis')) return 75;
                            if (progress.includes('Finalizing')) return 90;
                            return 60;
                        }
                        if (status === 'completed') return 100;
                        return 0;
                    },

                    getStepNumber() {
                        if (!this.currentTask) return 0;
                        const progress = this.currentTask.progress || '';
                        
                        if (progress.includes('Initializing')) return 1;
                        if (progress.includes('collecting') || progress.includes('Conducting') || progress.includes('Performing')) return 2;
                        if (progress.includes('Processing') || progress.includes('analysis')) return 3;
                        if (progress.includes('Finalizing') || this.currentTask.status === 'completed') return 4;
                        return 1;
                    },

                    getStepClass(stepNumber) {
                        const current = this.getStepNumber();
                        if (current > stepNumber) return 'bg-green-500';
                        if (current === stepNumber) return 'bg-blue-500';
                        return 'bg-gray-300';
                    },

                    getCitationCount(result) {
                        if (result.research_type === 'comprehensive') {
                            return result.result?.total_citations || 0;
                        }
                        return result.result?.citations || 0;
                    },

                    getWordCount(result) {
                        if (result.research_type === 'comprehensive') {
                            return result.result?.total_words || 0;
                        }
                        return result.result?.word_count || 0;
                    },

                    formatMarkdown(text) {
                        if (!text) return '';
                        
                        // Simple markdown to HTML conversion
                        return text
                            .replace(/### (.*?)\\n/g, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>')
                            .replace(/## (.*?)\\n/g, '<h2 class="text-xl font-bold mt-6 mb-3">$1</h2>')
                            .replace(/# (.*?)\\n/g, '<h1 class="text-2xl font-bold mt-8 mb-4">$1</h1>')
                            .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                            .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                            .replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '<a href="$2" class="text-blue-600 underline" target="_blank">$1</a>')
                            .replace(/\\n- (.*?)(?=\\n|$)/g, '\\n<li class="ml-4">$1</li>')
                            .replace(/(<li.*?>.*?<\\/li>)/gs, '<ul class="list-disc ml-6 mb-2">$1</ul>')
                            .replace(/\\n\\n/g, '</p><p class="mb-3">')
                            .replace(/^/, '<p class="mb-3">')
                            .replace(/$/, '</p>');
                    },

                    formatResult(result) {
                        if (typeof result === 'string') return result;
                        if (result?.formatted_output) return result.formatted_output;
                        if (result?.output) return result.output;
                        return JSON.stringify(result, null, 2);
                    },

                    downloadResult(result) {
                        let content = '';
                        
                        if (result.research_type === 'comprehensive') {
                            content = `# Research Report: ${result.query}\\n\\n`;
                            content += `**Model:** ${result.model}\\n`;
                            content += `**Processing Time:** ${result.result?.processing_time_formatted}\\n`;
                            content += `**Total Citations:** ${this.getCitationCount(result)}\\n`;
                            content += `**Total Words:** ${this.getWordCount(result)}\\n\\n`;
                            content += `---\\n\\n`;
                            
                            for (const [sectionName, section] of Object.entries(result.result?.sections || {})) {
                                content += `# ${sectionName.replace('_', ' ').toUpperCase()}\\n\\n`;
                                content += section.formatted_output || section.output || '';
                                content += `\\n\\n---\\n\\n`;
                            }
                        } else {
                            content = `# Research Report: ${result.query}\\n\\n`;
                            content += `**Model:** ${result.model}\\n`;
                            content += `**Type:** ${result.research_type}\\n`;
                            content += `**Processing Time:** ${result.result?.processing_time_formatted}\\n`;
                            content += `**Citations:** ${this.getCitationCount(result)}\\n`;
                            content += `**Words:** ${this.getWordCount(result)}\\n\\n`;
                            content += `---\\n\\n`;
                            content += this.formatResult(result.result);
                        }
                        
                        const blob = new Blob([content], { type: 'text/markdown' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `research_${result.query.substring(0, 30).replace(/[^a-zA-Z0-9]/g, '_')}.md`;
                        a.click();
                        URL.revokeObjectURL(url);
                    },

                    async copyResult(result) {
                        const content = this.formatResult(result.result);
                        try {
                            await navigator.clipboard.writeText(content);
                            alert('Result copied to clipboard!');
                        } catch (error) {
                            console.error('Failed to copy to clipboard:', error);
                        }
                    },

                    openDashboard(result) {
                        // Store result data for dashboard
                        localStorage.setItem('dashboardData', JSON.stringify(result));
                        // Open React dashboard in new tab
                        window.open('http://localhost:8080', '_blank');
                    }
                }
            }
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    client = get_openai_client() if not research_client else research_client
    return {
        "status": "healthy",
        "platform": "vercel-serverless",
        "research_client_initialized": research_client is not None,
        "openai_available": client is not None,
        "storage_service_available": storage_service is not None,
        "active_tasks": len([t for t in research_tasks.values() if t["status"] in ["pending", "running"]]),
        "completed_results": len(completed_results),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/models")
async def get_models():
    """Get available research models"""
    if research_client and hasattr(research_client, 'get_available_models'):
        return research_client.get_available_models()
    else:
        # Fallback models
        return {
            "o3-deep-research": {
                "name": "O3 Deep Research",
                "description": "Most comprehensive research model with advanced reasoning capabilities",
                "best_for": "Complex analysis, detailed reports, comprehensive research",
                "cost": "Higher",
                "speed": "Slower"
            },
            "o4-mini-deep-research": {
                "name": "O4 Mini Deep Research",
                "description": "Faster, cost-effective research model for quicker insights",
                "best_for": "Quick research, initial exploration, cost-sensitive tasks",
                "cost": "Lower",
                "speed": "Faster"
            }
        }

@app.post("/api/research")
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start a new research task"""
    if not research_client and not get_openai_client():
        raise HTTPException(status_code=500, detail="Research client not initialized")
    
    task_id = str(uuid.uuid4())
    
    # Store task info in memory (for compatibility)
    research_tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "query": request.query,
        "model": request.model,
        "research_type": request.research_type,
        "progress": "Task created, waiting to start..."
    }
    
    # Save task to storage service (database) if available
    if storage_service:
        task_data = {
            "task_id": task_id,
            "query": request.query,
            "model": request.model,
            "research_type": request.research_type,
            "status": "pending",
            "progress": "Task created, waiting to start...",
            "enrich_prompt": request.enrich_prompt
        }
        storage_service.save_research_task(task_data)
    
    # Start background task if workflow is available
    if research_workflow:
        background_tasks.add_task(background_research_task, task_id, request)
    else:
        # Use fallback research
        background_tasks.add_task(conduct_fallback_research_task, task_id, request)
    
    return ResearchStatus(**research_tasks[task_id])

async def conduct_fallback_research_task(task_id: str, request: ResearchRequest):
    """Fallback research task using direct OpenAI API"""
    start_time = datetime.now()
    
    try:
        research_tasks[task_id]["status"] = "running"
        research_tasks[task_id]["progress"] = "Initializing AI research..."
        
        client = get_openai_client()
        if not client:
            raise Exception("OpenAI client not available")
        
        # Create research prompt based on type
        if request.research_type == "validation":
            prompt = f"""Conduct a comprehensive business idea validation analysis for: {request.query}

Please provide a detailed analysis covering:
1. Market Opportunity Assessment
2. Target Audience Analysis  
3. Competition Landscape
4. Technical Feasibility
5. Risk Assessment
6. Implementation Roadmap

Format the response with clear sections and actionable insights."""
        elif request.research_type == "market":
            prompt = f"""Perform detailed market research analysis for: {request.query}

Please provide comprehensive analysis covering:
1. Market Size and Growth Trends
2. Customer Segments and Demographics
3. Competitive Landscape Analysis
4. Market Entry Barriers
5. Pricing Strategy Recommendations
6. Market Opportunities and Threats

Format with clear sections and data-driven insights."""
        elif request.research_type == "financial":
            prompt = f"""Conduct financial feasibility analysis for: {request.query}

Please provide detailed financial analysis covering:
1. Revenue Projections and Models
2. Cost Analysis and Structure
3. Break-even Analysis
4. Funding Requirements
5. ROI Calculations
6. Financial Risk Assessment

Format with clear sections and numerical projections where applicable."""
        else:
            prompt = f"""Conduct comprehensive research on: {request.query}

Please provide detailed analysis with:
1. Overview and Context
2. Key Insights and Findings
3. Data and Statistics
4. Trends and Patterns
5. Recommendations and Next Steps
6. Sources and References

Format with clear sections and actionable recommendations."""

        research_tasks[task_id]["progress"] = "Conducting research analysis..."
        
        # Map custom model names to actual OpenAI models
        model_mapping = {
            "o3-deep-research": "gpt-4-turbo-preview",
            "o4-mini-deep-research": "gpt-3.5-turbo"
        }
        
        actual_model = model_mapping.get(request.model, "gpt-4")
        
        # Enhanced system prompt
        system_prompt = """You are an expert research analyst. Provide comprehensive, well-structured analysis with actionable insights, data, and clear formatting using markdown headers and bullet points."""

        response = client.chat.completions.create(
            model=actual_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Create result in the expected format
        result = {
            "status": "completed",
            "output": content
        }
        
        # Format the result
        formatted_result = format_research_output(result, request.research_type)
        
        # Store completed result
        completed_results[task_id] = ResearchResult(
            task_id=task_id,
            status="completed",
            query=request.query,
            model=request.model,
            research_type=request.research_type,
            result=formatted_result,
            created_at=research_tasks[task_id]["created_at"],
            completed_at=end_time.isoformat()
        )
        
        # Add metadata
        completed_results[task_id].result["processing_time"] = round(processing_time, 1)
        completed_results[task_id].result["processing_time_formatted"] = f"{int(processing_time // 60)}m {int(processing_time % 60)}s"
        
        research_tasks[task_id]["status"] = "completed"
        research_tasks[task_id]["progress"] = f"Research completed successfully in {int(processing_time // 60)}m {int(processing_time % 60)}s"
        
        # Save to storage service if available
        if storage_service:
            storage_service.complete_research_task(task_id, formatted_result)
        
    except Exception as e:
        research_tasks[task_id]["status"] = "failed"
        research_tasks[task_id]["error"] = str(e)
        completed_results[task_id] = ResearchResult(
            task_id=task_id,
            status="failed",
            query=request.query,
            model=request.model,
            research_type=request.research_type,
            created_at=research_tasks[task_id]["created_at"],
            error=str(e)
        )

@app.get("/api/research/{task_id}/status")
async def get_research_status(task_id: str):
    """Get the status of a research task"""
    if task_id not in research_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return ResearchStatus(**research_tasks[task_id])

@app.get("/api/research/{task_id}/progressive")
async def get_progressive_results(task_id: str):
    """Get progressive results for comprehensive research"""
    if task_id not in research_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = research_tasks[task_id]
    
    # Return partial results if available
    if "partial_result" in task_data and task_data["partial_result"]:
        return {
            "task_id": task_id,
            "status": task_data["status"],
            "progress": task_data["progress"],
            "partial_result": task_data["partial_result"],
            "research_type": task_data.get("research_type", "comprehensive")
        }
    
    return {
        "task_id": task_id,
        "status": task_data["status"],
        "progress": task_data["progress"],
        "partial_result": None,
        "research_type": task_data.get("research_type", "comprehensive")
    }

@app.get("/api/research/{task_id}/result")
async def get_research_result(task_id: str):
    """Get the result of a completed research task"""
    if task_id not in completed_results:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return completed_results[task_id]

@app.get("/api/research/results")
async def get_all_results():
    """Get all research results"""
    return list(completed_results.values())

@app.delete("/api/research/{task_id}")
async def delete_research_result(task_id: str):
    """Delete a research result"""
    if task_id in completed_results:
        del completed_results[task_id]
    if task_id in research_tasks:
        del research_tasks[task_id]
    
    return {"message": "Result deleted successfully"}

@app.get("/api/dashboard/overview")
async def get_dashboard_overview():
    """Get dashboard overview metrics from storage service"""
    try:
        if storage_service:
            overview = storage_service.get_dashboard_overview()
            return overview
        else:
            # Fallback to memory-based calculation
            total_ideas = len(completed_results)
            if total_ideas == 0:
                return {
                    "total_ideas": 0,
                    "avg_market_score": 0,
                    "ideas_ready_for_development": 0,
                    "total_market_opportunity": "$0",
                    "new_ideas_this_month": 0,
                    "avg_research_depth": 0,
                    "validation_success_rate": 0
                }
            
            # Calculate metrics from completed research
            completed_research = list(completed_results.values())
            successful_research = [r for r in completed_research if r.status == "completed"]
            
            avg_citations = sum(
                r.result.get("total_citations", r.result.get("citations", 0)) 
                for r in successful_research if r.result
            ) / max(len(successful_research), 1)
            
            return {
                "total_ideas": total_ideas,
                "avg_market_score": 75.5,
                "ideas_ready_for_development": len(successful_research),
                "total_market_opportunity": "$450B",
                "new_ideas_this_month": total_ideas,
                "avg_research_depth": round(avg_citations, 1),
                "validation_success_rate": round((len(successful_research) / total_ideas) * 100, 1) if total_ideas > 0 else 0
            }
    except Exception as e:
        print(f"Error getting dashboard overview: {e}")
        return {
            "total_ideas": 0,
            "avg_market_score": 0,
            "ideas_ready_for_development": 0,
            "total_market_opportunity": "$0",
            "new_ideas_this_month": 0,
            "avg_research_depth": 0,
            "validation_success_rate": 0
        }

@app.get("/api/dashboard/ideas")
async def get_dashboard_ideas():
    """Get all ideas for dashboard from storage service"""
    try:
        if storage_service:
            ideas = storage_service.get_dashboard_ideas()
            return {"ideas": ideas}
        else:
            # Fallback to memory-based calculation
            ideas = []
            
            for result in completed_results.values():
                # Extract market data from research results
                market_score = 75
                feasibility_score = 70
                
                # Try to extract scores from research content if available
                if result.result and isinstance(result.result, dict):
                    output_text = result.result.get("formatted_output", result.result.get("output", ""))
                    if "market opportunity" in str(output_text).lower():
                        market_score = 80
                    if "feasible" in str(output_text).lower():
                        feasibility_score = 75
                
                idea = {
                    "idea_id": result.task_id,
                    "idea_name": result.query[:50] + ("..." if len(result.query) > 50 else ""),
                    "description": result.query,
                    "industry": "technology",
                    "research_model": result.model,
                    "status": "validated" if result.status == "completed" else "initial",
                    "created_at": result.created_at,
                    "last_research": result.completed_at or result.created_at,
                    "scores": {
                        "market_opportunity": market_score,
                        "technical_feasibility": feasibility_score,
                        "competitive_advantage": 65,
                        "risk_level": 4
                    },
                    "research_data": {
                        "total_citations": result.result.get("total_citations", result.result.get("citations", 0)) if result.result else 0,
                        "research_depth_score": 85,
                        "validation_sources": 10,
                        "competitor_analysis_count": 5
                    }
                }
                ideas.append(idea)
            
            return {"ideas": ideas}
    except Exception as e:
        print(f"Error getting dashboard ideas: {e}")
        return {"ideas": []}

@app.get("/dashboard")
async def dashboard_page():
    """Serve the React dashboard"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Idea Insight Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <div id="root">
            <div style="padding: 40px; text-align: center; font-family: Arial, sans-serif;">
                <h1>React Dashboard Integration</h1>
                <p>The React dashboard from the frontend folder would be integrated here.</p>
                <p>For now, you can use the main research interface at <a href="/">http://localhost:8000</a></p>
                <br>
                <h2>Available API Endpoints:</h2>
                <ul style="text-align: left; display: inline-block;">
                    <li><a href="/api/dashboard/overview">/api/dashboard/overview</a> - Dashboard metrics</li>
                    <li><a href="/api/dashboard/ideas">/api/dashboard/ideas</a> - All ideas data</li>
                    <li><a href="/api/models">/api/models</a> - Available research models</li>
                    <li><a href="/api/research/results">/api/research/results</a> - All research results</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """)

# This is the entry point for Vercel
# The app variable will be automatically detected by Vercel's Python runtime
