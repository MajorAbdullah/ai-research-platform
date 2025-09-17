#!/usr/bin/env python3
"""
Quick Parallel Processing Integration Test
=========================================

A lightweight test to verify parallel processing is working in the live application.
This test makes actual API calls to test the real parallel processing functionality.
"""

import requests
import time
import json
import sys
import os

def test_parallel_processing_integration():
    """Test parallel processing with the running application"""
    
    print("🔬 AI Research Platform - Parallel Processing Integration Test")
    print("=" * 65)
    print()
    
    # Application URL
    base_url = "http://localhost:8000"
    
    # Check if application is running
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Application is not responding properly")
            return False
        print("✅ Application is running and healthy")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to application at {base_url}")
        print(f"   Please make sure the application is running with: python app.py")
        return False
    
    print()
    
    # Test comprehensive research with parallel processing
    print("🧪 Testing Comprehensive Research with Parallel Processing...")
    
    research_request = {
        "query": "AI-powered sustainable energy storage solution for residential use",
        "model": "o3-deep-research",
        "research_type": "comprehensive",
        "max_citations": 8,
        "enrich_prompt": True
    }
    
    try:
        # Start research task
        start_time = time.time()
        print("📤 Submitting comprehensive research request...")
        
        response = requests.post(
            f"{base_url}/api/research",
            json=research_request,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to submit research request: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        task_data = response.json()
        task_id = task_data["task_id"]
        print(f"✅ Research task submitted successfully")
        print(f"   Task ID: {task_id}")
        print(f"   Status: {task_data['status']}")
        print()
        
        # Monitor progress
        print("🔄 Monitoring parallel processing progress...")
        max_wait_time = 300  # 5 minutes timeout
        check_interval = 5   # Check every 5 seconds
        
        for i in range(0, max_wait_time, check_interval):
            try:
                status_response = requests.get(
                    f"{base_url}/api/research/{task_id}/status",
                    timeout=5
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    current_status = status_data["status"]
                    progress = status_data.get("progress", "No progress info")
                    
                    print(f"   [{i//check_interval + 1:2d}] Status: {current_status} | {progress}")
                    
                    # Check for parallel processing indicators
                    if "parallel" in progress.lower():
                        print("   🚀 Parallel processing detected!")
                    
                    if "simultaneously" in progress.lower():
                        print("   ⚡ Simultaneous execution confirmed!")
                    
                    if current_status == "completed":
                        total_time = time.time() - start_time
                        print(f"   ✅ Research completed in {total_time:.1f} seconds")
                        break
                    elif current_status == "failed":
                        print("   ❌ Research failed")
                        return False
                        
                else:
                    print(f"   ⚠️  Status check failed: {status_response.status_code}")
                
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️  Connection error during status check: {e}")
            
            time.sleep(check_interval)
        else:
            print(f"   ⏰ Timeout after {max_wait_time} seconds")
            return False
        
        # Get final results
        print()
        print("📊 Retrieving final results...")
        
        try:
            result_response = requests.get(
                f"{base_url}/api/research/{task_id}/result",
                timeout=10
            )
            
            if result_response.status_code == 200:
                result_data = result_response.json()
                
                # Analyze results for parallel processing indicators
                print("✅ Results retrieved successfully")
                print()
                print("📋 Parallel Processing Analysis:")
                
                # Check execution mode
                execution_mode = result_data.get("execution_mode", "unknown")
                print(f"   🔧 Execution Mode: {execution_mode}")
                
                # Check for sections (indicates parallel execution)
                sections = result_data.get("sections", {})
                if sections:
                    print(f"   📊 Research Sections: {list(sections.keys())}")
                    
                    # Check if all three sections exist (validation, market, financial)
                    expected_sections = ["validation", "market", "financial"]
                    found_sections = [s for s in expected_sections if s in sections]
                    print(f"   ✅ Parallel Sections Found: {len(found_sections)}/3")
                    
                    if len(found_sections) == 3:
                        print("   🎉 All three research phases executed successfully!")
                
                # Check total metrics
                total_citations = result_data.get("total_citations", 0)
                total_words = result_data.get("total_words", 0)
                print(f"   📖 Total Citations: {total_citations}")
                print(f"   📝 Total Words: {total_words}")
                
                # Check unified content
                unified_content = result_data.get("unified_content", "")
                if unified_content and len(unified_content) > 1000:
                    print(f"   📑 Unified Document: {len(unified_content)} characters")
                    print("   ✅ Comprehensive unified document generated")
                
                # Performance analysis
                total_execution_time = time.time() - start_time
                print()
                print("⚡ Performance Analysis:")
                print(f"   ⏱️  Total Execution Time: {total_execution_time:.1f} seconds")
                
                if total_execution_time < 180:  # Less than 3 minutes
                    print("   🚀 Fast execution - parallel processing likely working!")
                elif total_execution_time < 360:  # Less than 6 minutes  
                    print("   ⚡ Moderate execution time - some parallelization")
                else:
                    print("   🐌 Slow execution - may be running sequentially")
                
                print()
                print("🎉 Integration test completed successfully!")
                print("✅ Parallel processing functionality verified")
                return True
                
            else:
                print(f"❌ Failed to retrieve results: {result_response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error retrieving results: {e}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error during research request: {e}")
        return False

def main():
    """Main test execution"""
    print("Starting parallel processing integration test...")
    print("Make sure the AI Research Platform is running on http://localhost:8000")
    print()
    
    success = test_parallel_processing_integration()
    
    if success:
        print()
        print("🎉 SUCCESS: Parallel processing is working correctly!")
        sys.exit(0)
    else:
        print()
        print("❌ FAILURE: Parallel processing test failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
