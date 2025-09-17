#!/usr/bin/env python3
"""
FastAPI Web Interface for OpenAI Research Client
Provides a modern web interface for conducting research with model selection
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import json
import asyncio
import uuid
from datetime import datetime
import os
import sqlite3
import re
import concurrent.futures
import uvicorn
from pathlib import Path
from services.research_client import OpenAIResearchClient, ResearchWorkflow
from services.storage_service import storage_service
from models.database import SessionLocal, ResearchTask, ResearchResult, init_database
from sqlalchemy.orm import Session

# Get the project root directory (cloud optimized)
PROJECT_ROOT = Path(__file__).parent.absolute()
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# FastAPI app with comprehensive documentation
app = FastAPI(
    title="AI Research Platform API",
    description="""
    🔬 **AI Research Platform** - Comprehensive research automation platform powered by OpenAI models.
    
    ## Features
    
    * **Multi-type Research**: Custom, validation, market, financial, and comprehensive research
    * **Model Selection**: Support for various OpenAI models including O3 Deep Research
    * **Task Management**: Asynchronous research task processing with real-time status tracking
    * **Document Storage**: Organized research document management with metadata
    * **Dashboard Analytics**: Research metrics and portfolio management
    * **Health Monitoring**: System health and performance monitoring
    
    ## Research Types
    
    * **Custom**: General-purpose research on any topic
    * **Validation**: Business idea validation and feasibility analysis  
    * **Market**: Market analysis and competitive intelligence
    * **Financial**: Financial analysis and investment research
    * **Comprehensive**: Deep, multi-faceted research with extensive analysis
    
    ## Getting Started
    
    1. Check system health at `/health`
    2. Browse available models at `/api/models`
    3. Submit research requests to `/api/research`
    4. Monitor progress with `/api/research/{task_id}/status`
    5. Retrieve results from `/api/research/{task_id}/result`
    
    ## Web Interface
    
    Access the full web interface at the root URL for an intuitive research experience.
    """,
    version="2.0.0",
    contact={
        "name": "AI Research Platform",
        "url": "https://github.com/MajorAbdullah/ai-research-platform",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc",  # ReDoc documentation
)

@app.on_event("startup")
async def startup_event():
    """Handle application startup events"""
    print("\n🚀 AI Research Platform starting up...")
    print("   Loading previous research results...")
    # Results are already loaded during import, but we can add additional startup logic here
    print("✅ Startup complete - Server ready to accept requests")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080", "http://localhost:8081", "http://127.0.0.1:3000", "http://127.0.0.1:5173", "http://127.0.0.1:8080", "http://127.0.0.1:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for research tasks (in production, use a proper database)
research_tasks = {}
completed_results = {}

def load_previous_results():
    """Load and display all previous research results from database"""
    try:
        # Initialize database if it doesn't exist
        init_database()
        
        # Get database session
        db = SessionLocal()
        
        # Query all completed research tasks
        completed_tasks = db.query(ResearchTask).filter(
            ResearchTask.status == "completed"
        ).order_by(ResearchTask.completed_at.desc()).all()
        
        if not completed_tasks:
            print("\n📊 No previous research results found.")
            print("   Ready to start your first research project!")
            db.close()
            return
        
        print(f"\n📊 Found {len(completed_tasks)} previous research results:")
        print("=" * 80)
        
        for i, task in enumerate(completed_tasks, 1):
            # Calculate processing time
            processing_time = "Unknown"
            if task.started_at and task.completed_at:
                duration = task.completed_at - task.started_at
                processing_time = f"{duration.total_seconds():.1f}s"
            
            # Get word count and citations from result data
            word_count = 0
            citations = 0
            if task.result_data:
                word_count = task.result_data.get('word_count', 0)
                citations = task.result_data.get('citations', 0)
            
            print(f"\n{i:2d}. 📝 {task.query[:60]}{'...' if len(task.query) > 60 else ''}")
            print(f"    🆔 Task ID: {task.task_id}")
            print(f"    📊 Type: {task.research_type.title()} | Model: {task.model}")
            print(f"    ⏱️  Completed: {task.completed_at.strftime('%Y-%m-%d %H:%M:%S') if task.completed_at else 'Unknown'}")
            print(f"    📈 Processing Time: {processing_time} | Words: {word_count:,} | Citations: {citations}")
            if task.md_document_path:
                print(f"    📄 Document: {task.md_document_path}")
            
            # Load result into completed_results for API access
            if task.result_data:
                completed_results[task.task_id] = {
                    "task_id": task.task_id,
                    "status": "completed",
                    "query": task.query,
                    "model": task.model,
                    "research_type": task.research_type,
                    "result": task.result_data,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "processing_time": processing_time,
                    "md_document_path": task.md_document_path
                }
        
        print("=" * 80)
        print(f"✅ Loaded {len(completed_results)} research results into memory")
        print("   All previous results are now accessible via API endpoints\n")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error loading previous results: {e}")
        print("   Continuing with empty result set...")

# Initialize database and load previous results
load_previous_results()

# Initialize research client
try:
    research_client = OpenAIResearchClient()
    research_workflow = ResearchWorkflow(research_client)
    print("✓ Research client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize research client: {e}")
    research_client = None
    research_workflow = None

class ResearchRequest(BaseModel):
    """Research request model for submitting research tasks"""
    query: str = Field(
        ..., 
        description="Research query or topic to investigate",
        example="AI applications in renewable energy storage"
    )
    model: str = Field(
        default="o3-deep-research",
        description="OpenAI model to use for research",
        example="o3-deep-research"
    )
    research_type: str = Field(
        default="custom",
        description="Type of research to conduct",
        enum=["custom", "validation", "market", "financial", "comprehensive"],
        example="market"
    )
    enrich_prompt: bool = Field(
        default=True,
        description="Whether to enhance the query with additional context and formatting"
    )
    max_citations: int = Field(
        default=15,
        description="Maximum number of citations/sources to include in the research (5-100)",
        ge=5,
        le=100,
        example=20
    )

class ResearchStatus(BaseModel):
    """Research task status information"""
    task_id: str = Field(..., description="Unique identifier for the research task")
    status: str = Field(..., description="Current status of the research task", enum=["pending", "running", "completed", "failed"])
    created_at: str = Field(..., description="Timestamp when the task was created")
    query: str = Field(..., description="Original research query")
    model: str = Field(..., description="OpenAI model being used")
    research_type: str = Field(..., description="Type of research being conducted")
    progress: Optional[str] = Field(None, description="Current progress information")
    error: Optional[str] = Field(None, description="Error message if task failed")

class ResearchResult(BaseModel):
    """Complete research result with metadata"""
    task_id: str = Field(..., description="Unique identifier for the research task")
    status: str = Field(..., description="Final status of the research task")
    query: str = Field(..., description="Original research query")
    model: str = Field(..., description="OpenAI model used")
    research_type: str = Field(..., description="Type of research conducted")
    result: Optional[Dict[str, Any]] = Field(None, description="Research results including analysis, citations, and metadata")
    created_at: str = Field(..., description="Timestamp when the task was created")
    completed_at: Optional[str] = Field(None, description="Timestamp when the task completed")
    error: Optional[str] = Field(None, description="Error message if task failed")

def extract_citations(text: str) -> int:
    """Extract citation count from research text"""
    import re
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

import asyncio
import concurrent.futures

def run_progressive_comprehensive_research(task_id: str, request: ResearchRequest) -> Dict[str, Any]:
    """Run comprehensive research with parallel execution for faster results"""
    
    # Initialize progress tracking
    research_tasks[task_id]["progress"] = "🚀 Starting parallel comprehensive research (3 phases simultaneously)..."
    
    # Define research functions with citation control
    def run_validation():
        return research_workflow.validate_idea(request.query, request.model, request.max_citations)
    
    def run_market():
        return research_workflow.market_research(request.query, request.model, request.max_citations)
    
    def run_financial():
        return research_workflow.financial_analysis(request.query, request.model, request.max_citations)
    
    # Track parallel execution progress
    progress_status = {
        "validation": "running",
        "market": "running", 
        "financial": "running"
    }
    
    research_tasks[task_id]["progress"] = "⚡ Running validation, market, and financial analysis in parallel..."
    
    # Execute all three research types in parallel using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all tasks
        future_validation = executor.submit(run_validation)
        future_market = executor.submit(run_market)
        future_financial = executor.submit(run_financial)
        
        # Wait for completion and collect results
        results = {}
        
        # Collect validation result
        try:
            validation_result = future_validation.result()
            results["validation"] = format_research_output(validation_result, "validation")
            progress_status["validation"] = "completed"
        except Exception as e:
            print(f"Validation research failed: {e}")
            results["validation"] = {"status": "failed", "error": str(e)}
        
        # Collect market result
        try:
            market_result = future_market.result()
            results["market"] = format_research_output(market_result, "market")
            progress_status["market"] = "completed"
        except Exception as e:
            print(f"Market research failed: {e}")
            results["market"] = {"status": "failed", "error": str(e)}
        
        # Collect financial result
        try:
            financial_result = future_financial.result()
            results["financial"] = format_research_output(financial_result, "financial")
            progress_status["financial"] = "completed"
        except Exception as e:
            print(f"Financial research failed: {e}")
            results["financial"] = {"status": "failed", "error": str(e)}
    
    # Calculate totals
    total_citations = sum(
        section.get("citations", 0) 
        for section in results.values() 
        if isinstance(section, dict)
    )
    total_words = sum(
        section.get("word_count", 0) 
        for section in results.values()
        if isinstance(section, dict)
    )
    
    # Create unified comprehensive result
    comprehensive_result = {
        "type": "comprehensive",
        "sections": results,
        "progress": progress_status,
        "total_citations": total_citations,
        "total_words": total_words,
        "execution_mode": "parallel",
        "unified_content": create_unified_comprehensive_document(results, request.query)
    }
    
    # Final progress update
    completed_count = sum(1 for status in progress_status.values() if status == "completed")
    research_tasks[task_id]["progress"] = f"✅ Parallel execution completed! {completed_count}/3 phases successful. Generating unified document..."
    
    return comprehensive_result

def create_unified_comprehensive_document(results: Dict[str, Any], query: str) -> str:
    """Create a single unified document from all comprehensive research results"""
    
    unified_content = f"""# Comprehensive Research Report: {query}

## Executive Summary

This comprehensive analysis examines the business opportunity from three critical perspectives: idea validation, market analysis, and financial viability. All research phases were conducted simultaneously for maximum efficiency and cross-validation of insights.

"""
    
    # Add validation section
    if "validation" in results and results["validation"].get("formatted_output"):
        unified_content += f"""## 🔍 Business Idea Validation

{results["validation"]["formatted_output"]}

---

"""
    
    # Add market research section
    if "market" in results and results["market"].get("formatted_output"):
        unified_content += f"""## 📊 Market Research & Analysis

{results["market"]["formatted_output"]}

---

"""
    
    # Add financial analysis section
    if "financial" in results and results["financial"].get("formatted_output"):
        unified_content += f"""## 💰 Financial Analysis & Projections

{results["financial"]["formatted_output"]}

---

"""
    
    # Add comprehensive conclusion
    unified_content += f"""## 🎯 Comprehensive Conclusion & Recommendations

Based on the parallel analysis across validation, market research, and financial assessment:

### Key Findings Summary
- **Validation Score**: Based on market need, solution fit, and competitive positioning
- **Market Opportunity**: Total addressable market size and growth potential  
- **Financial Viability**: Revenue projections, costs, and ROI analysis

### Strategic Recommendations
The convergence of insights from all three research phases provides a robust foundation for decision-making. This unified analysis enables confident strategic planning with validated assumptions across multiple business dimensions.

### Next Steps
1. **Immediate Actions**: Based on validation findings
2. **Market Entry Strategy**: Leveraging market research insights
3. **Financial Planning**: Implementing financial projections and milestones

*This comprehensive report was generated using parallel research execution for maximum efficiency and insight integration.*
"""
    
    return unified_content

def background_research_task(task_id: str, request: ResearchRequest):
    """Background task for conducting research"""
    start_time = datetime.now()
    
    try:
        # Update task status in storage service
        storage_service.update_research_task(task_id, {
            "status": "running",
            "progress": "Initializing AI research..."
        })
        
        research_tasks[task_id]["status"] = "running"
        research_tasks[task_id]["progress"] = "Initializing AI research..."
        
        if request.research_type == "validation":
            research_tasks[task_id]["progress"] = "Conducting idea validation analysis..."
            storage_service.update_research_task(task_id, {"progress": "Conducting idea validation analysis..."})
            result = research_workflow.validate_idea(request.query, request.model, request.max_citations)
        elif request.research_type == "market":
            research_tasks[task_id]["progress"] = "Performing market research analysis..."
            storage_service.update_research_task(task_id, {"progress": "Performing market research analysis..."})
            result = research_workflow.market_research(request.query, request.model, request.max_citations)
        elif request.research_type == "financial":
            research_tasks[task_id]["progress"] = "Executing financial analysis..."
            storage_service.update_research_task(task_id, {"progress": "Executing financial analysis..."})
            result = research_workflow.financial_analysis(request.query, request.model, request.max_citations)
        elif request.research_type == "comprehensive":
            # Progressive comprehensive research
            result = run_progressive_comprehensive_research(task_id, request)
        else:  # custom research
            research_tasks[task_id]["progress"] = "Processing custom research query..."
            storage_service.update_research_task(task_id, {"progress": "Processing custom research query..."})
            result = research_workflow.custom_research(
                request.query, 
                request.model, 
                "general", 
                request.enrich_prompt,
                request.max_citations
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
        
        # Save to storage service (database + documents)
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
        
        # Update failed status in storage service
        storage_service.update_research_task(task_id, {
            "status": "failed",
            "progress": f"Research failed: {str(e)}"
        })

@app.get(
    "/", 
    response_class=HTMLResponse,
    summary="Web Interface",
    description="Serve the main web interface for the AI Research Platform",
    response_description="HTML web interface for interactive research",
    tags=["Web Interface"]
)
async def home():
    """
    Serve the main web interface for the AI Research Platform.
    
    Provides a user-friendly interface for:
    - Submitting research requests
    - Monitoring task progress
    - Viewing research results
    - Managing research portfolio
    - Previous research results display
    
    Returns:
        HTMLResponse: Complete web interface with interactive features
    """
    # Read the template file (cloud optimized path)
    try:
        template_path = TEMPLATES_DIR / "index.html"
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Template file not found at {template_path}. Please check the templates directory."
    except Exception as e:
        return f"Error loading template: {str(e)}"

@app.get("/api/research/previous")
async def get_previous_results():
    """Get previous research results for display in web interface"""
    try:
        # Use SQLAlchemy ORM for cloud optimization
        db = SessionLocal()
        
        # Query completed research tasks with their results
        completed_tasks = db.query(ResearchTask).filter(
            ResearchTask.status == "completed"
        ).order_by(ResearchTask.completed_at.desc()).limit(10).all()
        
        results = []
        for task in completed_tasks:
            # Calculate processing time
            processing_time = "0s"
            if task.completed_at and task.started_at:
                duration = task.completed_at - task.started_at
                total_seconds = int(duration.total_seconds())
                if total_seconds >= 60:
                    minutes = total_seconds // 60
                    seconds = total_seconds % 60
                    processing_time = f"{minutes}m {seconds}s"
                else:
                    processing_time = f"{total_seconds}s"
            
            # Extract citations and word count from result_data
            citations = 0
            word_count = 0
            if task.result_data:
                try:
                    import json
                    result_json = json.loads(task.result_data) if isinstance(task.result_data, str) else task.result_data
                    citations = result_json.get("citations", 0)
                    word_count = result_json.get("word_count", 0)
                except:
                    pass
            
            results.append({
                "id": task.task_id,
                "query": task.query,
                "model": task.model,
                "research_type": task.research_type,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "processing_time": processing_time,
                "word_count": word_count,
                "citations": citations,
                "document_path": task.md_document_path
            })
        
        db.close()
        return results
        
    except Exception as e:
        print(f"Error loading previous results: {e}")
        return []

# The embedded HTML template has been moved to templates/index.html for better maintainability

@app.get(
    "/api/models",
    summary="Get Available Models",
    description="Retrieve all available OpenAI models for research tasks",
    response_description="Dictionary of available models with their capabilities",
    tags=["Models"]
)
async def get_models():
    """
    Get all available OpenAI models for research tasks.
    
    Returns a dictionary containing model information including:
    - Model names and identifiers
    - Model capabilities and descriptions
    - Recommended use cases
    
    Raises:
        HTTPException: If the research client is not properly initialized
    """
    if not research_client:
        raise HTTPException(status_code=500, detail="Research client not initialized")
    
    return research_client.get_available_models()

@app.post(
    "/api/research",
    response_model=ResearchStatus,
    summary="Start Research Task",
    description="Submit a new research request with citation control and get a task ID for tracking progress",
    response_description="Research task status with unique task ID",
    tags=["Research"]
)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """
    Start a new research task with the specified parameters.
    
    This endpoint creates a new research task that runs asynchronously in the background.
    You can track the progress using the returned task_id.
    
    **Research Types:**
    - **custom**: General-purpose research on any topic
    - **validation**: Business idea validation and feasibility analysis
    - **market**: Market analysis and competitive intelligence  
    - **financial**: Financial analysis and investment research
    - **comprehensive**: Deep, multi-faceted research with **parallel execution** for faster results
    
    **Citation Control:**
    Specify how many citations/sources you want in your research (5-100):
    - **5-10**: Quick overview with key sources
    - **15-25**: Balanced research with good source coverage  
    - **30-50**: In-depth research with extensive references
    - **50-100**: Comprehensive research with maximum source validation
    
    **Process:**
    1. Task is created with a unique ID
    2. Research runs asynchronously in the background
    3. For comprehensive research, all phases run in **parallel** for speed
    4. Use `/api/research/{task_id}/status` to check progress
    5. Retrieve results from `/api/research/{task_id}/result` when completed
    
    Args:
        request: Research request containing query, model, type, citation preferences, and options
        
    Returns:
        ResearchStatus: Initial task status with task_id for tracking
        
    Raises:
        HTTPException: If research client is not initialized
    """
    if not research_client or not research_workflow:
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
    
    # Save task to storage service (database)
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
    
    # Start background task
    background_tasks.add_task(background_research_task, task_id, request)
    
    return ResearchStatus(**research_tasks[task_id])

@app.get(
    "/api/research/{task_id}/status",
    response_model=ResearchStatus,
    summary="Get Research Status",
    description="Check the current status and progress of a research task",
    response_description="Current task status including progress information",
    tags=["Research"]
)
async def get_research_status(task_id: str):
    """
    Get the current status and progress of a research task.
    
    Returns detailed information about the task including:
    - Current status (pending, running, completed, failed)
    - Progress information
    - Task metadata (query, model, research type)
    - Error information if applicable
    
    Args:
        task_id: Unique identifier for the research task
        
    Returns:
        ResearchStatus: Current status and progress information
        
    Raises:
        HTTPException: If task_id is not found
    """
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

@app.get(
    "/api/research/{task_id}/result",
    response_model=ResearchResult,
    summary="Get Research Result",
    description="Retrieve the complete results of a finished research task",
    response_description="Complete research results with analysis and metadata",
    tags=["Research"]
)
async def get_research_result(task_id: str):
    """
    Retrieve the complete results of a finished research task.
    
    This endpoint returns the full research output including:
    - Research analysis and findings
    - Citations and sources
    - Word count and metadata
    - Processing time and performance metrics
    
    Args:
        task_id: Unique identifier for the research task
        
    Returns:
        ResearchResult: Complete research results and metadata
        
    Raises:
        HTTPException: If result is not found or task is not yet completed
    """
    if task_id not in completed_results:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return completed_results[task_id]

@app.get("/api/research/results")
async def get_all_results():
    """Get all research results"""
    return list(completed_results.values())

@app.get(
    "/api/research/{task_id}/download",
    summary="Download Research Document",
    description="Download the complete research document as a Markdown file",
    response_description="Markdown file containing the full research report",
    tags=["Research"]
)
async def download_research_document(task_id: str):
    """
    Download the complete research document as a Markdown file.
    
    This endpoint provides access to the full research document that was
    generated and saved when the research task was completed.
    
    Args:
        task_id: Unique identifier for the research task
        
    Returns:
        FileResponse: Markdown file download with full research content
        
    Raises:
        HTTPException: If document is not found or task doesn't exist
    """
    from fastapi.responses import FileResponse
    from services.document_manager import research_docs
    import os
    
    # Get document path from document manager
    doc_path = research_docs.get_document_path(task_id)
    
    if not doc_path or not os.path.exists(doc_path):
        raise HTTPException(status_code=404, detail="Research document not found")
    
    # Extract filename for download
    filename = os.path.basename(doc_path)
    
    return FileResponse(
        path=doc_path,
        filename=filename,
        media_type='text/markdown',
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get(
    "/api/research/documents",
    summary="List Research Documents", 
    description="Get a list of all saved research documents with metadata",
    response_description="List of research documents with creation info and download links",
    tags=["Research"]
)
async def list_research_documents(research_type: Optional[str] = None):
    """
    Get a list of all saved research documents.
    
    Returns metadata for all research documents including:
    - Document creation date and details
    - Research type and model used
    - Download links for full documents
    - Word count and other metrics
    
    Args:
        research_type: Optional filter by research type (custom, validation, market, financial, comprehensive)
        
    Returns:
        list: List of document metadata with download information
    """
    from services.document_manager import research_docs
    
    documents = research_docs.list_documents(research_type)
    
    # Add download URLs to each document
    for doc in documents:
        doc['download_url'] = f"/api/research/{doc['task_id']}/download"
    
    return {
        "documents": documents,
        "total_count": len(documents),
        "filter_applied": research_type
    }

@app.delete("/api/research/{task_id}")
async def delete_research_result(task_id: str):
    """Delete a research result"""
    if task_id in completed_results:
        del completed_results[task_id]
    if task_id in research_tasks:
        del research_tasks[task_id]
    
    return {"message": "Result deleted successfully"}

@app.get(
    "/api/dashboard/overview",
    summary="Dashboard Overview",
    description="Get comprehensive dashboard metrics and analytics",
    response_description="Dashboard overview with research statistics and metrics",
    tags=["Dashboard"]
)
async def get_dashboard_overview():
    """
    Get comprehensive dashboard overview with research metrics.
    
    Returns key performance indicators including:
    - Total number of research ideas processed
    - Average market scores across all research
    - Number of ideas ready for development
    - Success rates and performance metrics
    
    Returns:
        dict: Dashboard overview metrics and statistics
    """
    try:
        # Get real metrics from storage service
        overview = storage_service.get_dashboard_overview()
        return overview
    except Exception as e:
        print(f"Error getting dashboard overview: {e}")
        # Fallback to memory-based calculation for compatibility
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
            "avg_market_score": 75.5,  # Mock score - would calculate from results
            "ideas_ready_for_development": len(successful_research),
            "total_market_opportunity": "$450B",  # Mock - would calculate from market research
            "new_ideas_this_month": total_ideas,
            "avg_research_depth": round(avg_citations, 1),
            "validation_success_rate": round((len(successful_research) / total_ideas) * 100, 1) if total_ideas > 0 else 0
        }

@app.get("/api/dashboard/ideas")
async def get_dashboard_ideas():
    """Get all ideas for dashboard from storage service"""
    try:
        # Get real ideas from storage service
        ideas = storage_service.get_dashboard_ideas()
        return {"ideas": ideas}
    except Exception as e:
        print(f"Error getting dashboard ideas: {e}")
        # Fallback to memory-based calculation for compatibility
        ideas = []
        
        for result in completed_results.values():
            # Extract market data from research results
            market_score = 75  # Default score
            feasibility_score = 70  # Default score
            
            # Try to extract scores from research content if available
            if result.result and isinstance(result.result, dict):
                # Parse research output for scores (simplified)
                output_text = result.result.get("formatted_output", result.result.get("output", ""))
                if "market opportunity" in str(output_text).lower():
                    market_score = 80
                if "feasible" in str(output_text).lower():
                    feasibility_score = 75
            
            idea = {
                "idea_id": result.task_id,
                "idea_name": result.query[:50] + ("..." if len(result.query) > 50 else ""),
                "description": result.query,
                "industry": "technology",  # Would be extracted from research
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

@app.get("/dashboard")
async def dashboard_page():
    """Serve the React dashboard"""
    # Serve the React app built files
    # This would normally serve from a dist folder after building the React app
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

@app.get(
    "/health",
    summary="System Health Check",
    description="Check the health status of the AI Research Platform",
    response_description="System health information including service status and metrics",
    tags=["System"]
)
async def health_check():
    """
    Check the health status of the AI Research Platform.
    
    Returns:
        - System status (healthy/unhealthy)
        - Research client initialization status
        - Number of active research tasks
        - Number of completed research results
    """
    return {
        "status": "healthy",
        "research_client_initialized": research_client is not None,
        "active_tasks": len([t for t in research_tasks.values() if t["status"] in ["pending", "running"]]),
        "completed_results": len(completed_results)
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting OpenAI Research Interface...")
    print("Open your browser to: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
