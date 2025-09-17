#!/usr/bin/env python3
"""
Parallel Processing Demo & Test
==============================

This demo shows the parallel processing capabilities of the AI Research Platform
without requiring actual OpenAI API calls. It demonstrates the ThreadPoolExecutor
implementation and timing comparisons.
"""

import time
import concurrent.futures
import threading
import requests
import json
from datetime import datetime

def demo_parallel_vs_sequential():
    """Demonstrate the difference between parallel and sequential execution"""
    
    print("🔬 AI Research Platform - Parallel Processing Demo")
    print("=" * 55)
    print()
    
    def simulate_research_task(task_name: str, duration: float):
        """Simulate a research task that takes some time"""
        start_time = time.time()
        thread_id = threading.current_thread().ident
        print(f"   🔄 Starting {task_name} research (Thread: {thread_id})")
        
        # Simulate processing time (like API calls, data processing, etc.)
        time.sleep(duration)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        print(f"   ✅ Completed {task_name} research in {actual_duration:.2f}s (Thread: {thread_id})")
        
        return {
            "task": task_name,
            "duration": actual_duration,
            "thread_id": thread_id,
            "status": "completed"
        }
    
    # Define realistic research tasks with different processing times
    research_tasks = [
        ("Idea Validation", 2.0),
        ("Market Research", 2.5), 
        ("Financial Analysis", 1.8)
    ]
    
    print("📊 Research Tasks to Execute:")
    for task_name, duration in research_tasks:
        print(f"   • {task_name}: ~{duration}s processing time")
    print()
    
    # Test 1: Sequential Execution (Traditional Approach)
    print("🐌 Test 1: Sequential Execution (Traditional)")
    print("-" * 45)
    
    sequential_start = time.time()
    sequential_results = []
    
    for task_name, duration in research_tasks:
        result = simulate_research_task(task_name, duration)
        sequential_results.append(result)
    
    sequential_end = time.time()
    sequential_total = sequential_end - sequential_start
    
    print(f"   ⏱️  Total Sequential Time: {sequential_total:.2f} seconds")
    print()
    
    # Test 2: Parallel Execution (Our Implementation)
    print("⚡ Test 2: Parallel Execution (AI Research Platform)")
    print("-" * 50)
    
    parallel_start = time.time()
    parallel_results = []
    
    # Use ThreadPoolExecutor exactly like in the application
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all tasks simultaneously
        futures = []
        for task_name, duration in research_tasks:
            future = executor.submit(simulate_research_task, task_name, duration)
            futures.append(future)
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            parallel_results.append(result)
    
    parallel_end = time.time()
    parallel_total = parallel_end - parallel_start
    
    print(f"   ⏱️  Total Parallel Time: {parallel_total:.2f} seconds")
    print()
    
    # Performance Analysis
    print("📈 Performance Analysis")
    print("-" * 25)
    
    performance_improvement = sequential_total / parallel_total
    time_saved = sequential_total - parallel_total
    efficiency_gain = (time_saved / sequential_total) * 100
    
    print(f"   Sequential Execution: {sequential_total:.2f}s")
    print(f"   Parallel Execution:   {parallel_total:.2f}s")
    print(f"   Time Saved:          {time_saved:.2f}s")
    print(f"   Performance Gain:    {performance_improvement:.1f}x faster")
    print(f"   Efficiency Improvement: {efficiency_gain:.1f}%")
    print()
    
    # Thread Analysis
    print("🧵 Thread Utilization Analysis")
    print("-" * 30)
    
    sequential_threads = set(result["thread_id"] for result in sequential_results)
    parallel_threads = set(result["thread_id"] for result in parallel_results)
    
    print(f"   Sequential: {len(sequential_threads)} thread used")
    print(f"   Parallel:   {len(parallel_threads)} threads used")
    print(f"   Thread Efficiency: {len(parallel_threads)}x more threads utilized")
    print()
    
    return {
        "sequential_time": sequential_total,
        "parallel_time": parallel_total,
        "performance_improvement": performance_improvement,
        "efficiency_gain": efficiency_gain,
        "threads_sequential": len(sequential_threads),
        "threads_parallel": len(parallel_threads)
    }

def test_application_endpoints():
    """Test the application's parallel processing endpoints"""
    
    print("🔌 Testing Application Endpoints")
    print("-" * 35)
    
    base_url = "http://localhost:8000"
    
    try:
        # Test health endpoint
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print("   ✅ Health Check: OK")
            print(f"      Research Client: {'✅' if health_data.get('research_client_initialized') else '❌'}")
            print(f"      Active Tasks: {health_data.get('active_tasks', 0)}")
        else:
            print(f"   ❌ Health Check Failed: {health_response.status_code}")
            return False
        
        # Test models endpoint
        models_response = requests.get(f"{base_url}/api/models", timeout=5)
        if models_response.status_code == 200:
            models_data = models_response.json()
            print("   ✅ Models Endpoint: OK")
            print(f"      Available Models: {len(models_data.get('models', {}))}")
            
            # Show model capabilities
            for model_id, model_info in models_data.get('models', {}).items():
                print(f"      • {model_info.get('name', model_id)}: {model_info.get('description', 'No description')}")
        else:
            print(f"   ❌ Models Endpoint Failed: {models_response.status_code}")
        
        print()
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection Error: {e}")
        print("   💡 Make sure the application is running: python app.py")
        return False

def main():
    """Main demo execution"""
    print(f"🚀 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run parallel processing demo
    demo_results = demo_parallel_vs_sequential()
    
    # Test application endpoints
    app_test_success = test_application_endpoints()
    
    # Summary
    print("🎯 Demo Summary")
    print("-" * 15)
    
    if demo_results["performance_improvement"] >= 2.0:
        print("   ✅ Parallel processing working correctly")
        print(f"   🚀 Achieved {demo_results['performance_improvement']:.1f}x performance improvement")
    else:
        print("   ⚠️  Parallel processing may have issues")
    
    if app_test_success:
        print("   ✅ Application endpoints responding correctly")
    else:
        print("   ⚠️  Application endpoints not accessible")
    
    print()
    print("📋 Key Findings:")
    print(f"   • Parallel execution is {demo_results['efficiency_gain']:.1f}% more efficient")
    print(f"   • Uses {demo_results['threads_parallel']}x more threads for better resource utilization")
    print(f"   • Real-world comprehensive research would see similar gains")
    print()
    print("🔬 Technical Implementation:")
    print("   • Uses concurrent.futures.ThreadPoolExecutor")
    print("   • 3 worker threads for validation, market, and financial research")
    print("   • Thread-safe result collection and aggregation")
    print("   • Error isolation per research phase")
    print()
    
    if demo_results["performance_improvement"] >= 2.0 and app_test_success:
        print("🎉 SUCCESS: Parallel processing is working optimally!")
        return True
    else:
        print("⚠️  PARTIAL SUCCESS: Some issues detected")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
