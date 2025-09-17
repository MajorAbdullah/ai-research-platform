#!/usr/bin/env python3
"""
Parallel Processing Test Suite for AI Research Platform
=====================================================

This test suite validates the parallel processing functionality including:
1. ThreadPoolExecutor implementation
2. Concurrent execution timing
3. Result aggregation from parallel tasks
4. Error handling in parallel execution
5. Progress tracking across concurrent tasks
"""

import time
import threading
import concurrent.futures
from unittest.mock import Mock, patch
from typing import Dict, Any
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import application modules
from app import run_progressive_comprehensive_research, research_tasks, ResearchRequest
from services.research_client import OpenAIResearchClient, ResearchWorkflow

class ParallelProcessingTester:
    """Test suite for parallel processing functionality"""
    
    def __init__(self):
        self.test_results = {}
        self.mock_research_data = {
            "validation": {
                "status": "completed",
                "output": "# Validation Analysis\n\nThis idea shows strong potential...",
                "citations": 8,
                "word_count": 1200,
                "processing_time": 2.5
            },
            "market": {
                "status": "completed", 
                "output": "# Market Research\n\nThe market shows significant opportunity...",
                "citations": 12,
                "word_count": 1500,
                "processing_time": 3.2
            },
            "financial": {
                "status": "completed",
                "output": "# Financial Analysis\n\nProjected revenue streams indicate...",
                "citations": 6,
                "word_count": 1100,
                "processing_time": 2.8
            }
        }
    
    def test_threadpool_executor_implementation(self):
        """Test 1: Verify ThreadPoolExecutor is properly implemented"""
        print("🧪 Test 1: ThreadPoolExecutor Implementation")
        
        # Create mock functions that simulate research tasks
        def mock_task(task_name: str, duration: float):
            """Mock research task that takes specified time"""
            start_time = time.time()
            time.sleep(duration)  # Simulate research processing
            end_time = time.time()
            return {
                "task": task_name,
                "duration": duration,
                "actual_time": end_time - start_time,
                "thread_id": threading.current_thread().ident
            }
        
        # Test parallel execution
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit tasks that would take 6 seconds sequentially
            future1 = executor.submit(mock_task, "validation", 2.0)
            future2 = executor.submit(mock_task, "market", 2.0)  
            future3 = executor.submit(mock_task, "financial", 2.0)
            
            # Collect results
            results = [
                future1.result(),
                future2.result(), 
                future3.result()
            ]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify parallel execution
        thread_ids = [result["thread_id"] for result in results]
        unique_threads = len(set(thread_ids))
        
        self.test_results["threadpool_test"] = {
            "parallel_execution_time": total_time,
            "sequential_would_take": 6.0,
            "performance_improvement": 6.0 / total_time,
            "unique_threads_used": unique_threads,
            "expected_threads": 3,
            "success": total_time < 4.0 and unique_threads == 3
        }
        
        print(f"   ⏱️  Parallel execution time: {total_time:.2f}s (Sequential would take: 6.00s)")
        print(f"   🚀 Performance improvement: {6.0/total_time:.1f}x faster")
        print(f"   🧵 Unique threads used: {unique_threads}/3")
        print(f"   ✅ Test passed: {self.test_results['threadpool_test']['success']}")
        print()
        
        return self.test_results["threadpool_test"]["success"]
    
    def test_comprehensive_research_parallel_execution(self):
        """Test 2: Test actual comprehensive research parallel execution"""
        print("🧪 Test 2: Comprehensive Research Parallel Execution")
        
        # Mock the research workflow to avoid actual API calls
        with patch('app.research_workflow') as mock_workflow:
            # Configure mock methods with realistic delays
            def mock_validate_idea(*args, **kwargs):
                time.sleep(1.0)  # Simulate API call delay
                return self.mock_research_data["validation"]
            
            def mock_market_research(*args, **kwargs):
                time.sleep(1.2)  # Simulate different API call delay
                return self.mock_research_data["market"]
            
            def mock_financial_analysis(*args, **kwargs):
                time.sleep(0.8)  # Simulate different API call delay  
                return self.mock_research_data["financial"]
            
            mock_workflow.validate_idea = mock_validate_idea
            mock_workflow.market_research = mock_market_research
            mock_workflow.financial_analysis = mock_financial_analysis
            
            # Create test request
            request = ResearchRequest(
                query="AI-powered fitness app for personalized workouts",
                model="o3-deep-research",
                research_type="comprehensive",
                max_citations=10
            )
            
            # Generate unique task ID
            task_id = f"test-parallel-{int(time.time())}"
            research_tasks[task_id] = {
                "status": "running",
                "progress": "Starting test..."
            }
            
            # Execute parallel comprehensive research
            start_time = time.time()
            result = run_progressive_comprehensive_research(task_id, request)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Validate results
            self.test_results["comprehensive_test"] = {
                "execution_time": execution_time,
                "has_all_sections": all(section in result["sections"] for section in ["validation", "market", "financial"]),
                "execution_mode": result.get("execution_mode"),
                "total_citations": result.get("total_citations", 0),
                "total_words": result.get("total_words", 0),
                "unified_content_generated": "unified_content" in result and len(result["unified_content"]) > 100,
                "progress_tracking": "progress" in result,
                "success": execution_time < 3.0  # Should complete in under 3 seconds with mocks
            }
            
            print(f"   ⏱️  Execution time: {execution_time:.2f}s")
            print(f"   📊 Total citations: {result.get('total_citations', 0)}")
            print(f"   📝 Total words: {result.get('total_words', 0)}")
            print(f"   🔄 Execution mode: {result.get('execution_mode')}")
            print(f"   📑 Unified content generated: {len(result.get('unified_content', '')):.0f} characters")
            print(f"   ✅ Test passed: {self.test_results['comprehensive_test']['success']}")
            print()
            
            return self.test_results["comprehensive_test"]["success"]
    
    def test_error_handling_in_parallel_execution(self):
        """Test 3: Error handling during parallel execution"""
        print("🧪 Test 3: Error Handling in Parallel Execution")
        
        with patch('app.research_workflow') as mock_workflow:
            # Configure one task to fail, others to succeed
            def mock_validate_idea(*args, **kwargs):
                return self.mock_research_data["validation"]
            
            def mock_market_research(*args, **kwargs):
                raise Exception("Simulated API failure")
            
            def mock_financial_analysis(*args, **kwargs):
                return self.mock_research_data["financial"]
            
            mock_workflow.validate_idea = mock_validate_idea
            mock_workflow.market_research = mock_market_research
            mock_workflow.financial_analysis = mock_financial_analysis
            
            # Create test request
            request = ResearchRequest(
                query="Test error handling",
                model="o3-deep-research", 
                research_type="comprehensive",
                max_citations=5
            )
            
            task_id = f"test-error-{int(time.time())}"
            research_tasks[task_id] = {
                "status": "running",
                "progress": "Testing error handling..."
            }
            
            # Execute with simulated failure
            result = run_progressive_comprehensive_research(task_id, request)
            
            # Validate error handling
            validation_success = result["sections"]["validation"]["status"] == "completed"
            market_failed = "error" in result["sections"]["market"]
            financial_success = result["sections"]["financial"]["status"] == "completed"
            
            self.test_results["error_handling_test"] = {
                "validation_completed": validation_success,
                "market_failed_gracefully": market_failed,
                "financial_completed": financial_success,
                "partial_results_available": validation_success and financial_success,
                "unified_content_generated": "unified_content" in result,
                "success": validation_success and market_failed and financial_success
            }
            
            print(f"   ✅ Validation completed: {validation_success}")
            print(f"   ❌ Market failed gracefully: {market_failed}")
            print(f"   ✅ Financial completed: {financial_success}")
            print(f"   📊 Partial results available: {validation_success and financial_success}")
            print(f"   ✅ Test passed: {self.test_results['error_handling_test']['success']}")
            print()
            
            return self.test_results["error_handling_test"]["success"]
    
    def test_performance_comparison(self):
        """Test 4: Performance comparison between sequential and parallel"""
        print("🧪 Test 4: Performance Comparison (Sequential vs Parallel)")
        
        # Mock realistic API delays
        def slow_task(name: str):
            time.sleep(1.5)  # Simulate realistic API call time
            return {"name": name, "completed": True}
        
        # Test sequential execution
        start_time = time.time()
        sequential_results = []
        for task_name in ["validation", "market", "financial"]:
            sequential_results.append(slow_task(task_name))
        sequential_time = time.time() - start_time
        
        # Test parallel execution
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(slow_task, name) for name in ["validation", "market", "financial"]]
            parallel_results = [future.result() for future in futures]
        parallel_time = time.time() - start_time
        
        performance_improvement = sequential_time / parallel_time
        
        self.test_results["performance_comparison"] = {
            "sequential_time": sequential_time,
            "parallel_time": parallel_time,
            "performance_improvement": performance_improvement,
            "efficiency_gain_percent": ((sequential_time - parallel_time) / sequential_time) * 100,
            "success": performance_improvement >= 2.5  # Should be at least 2.5x faster
        }
        
        print(f"   ⏱️  Sequential execution: {sequential_time:.2f}s")
        print(f"   ⚡ Parallel execution: {parallel_time:.2f}s")
        print(f"   🚀 Performance improvement: {performance_improvement:.1f}x faster")
        print(f"   📈 Efficiency gain: {((sequential_time - parallel_time) / sequential_time) * 100:.1f}%")
        print(f"   ✅ Test passed: {self.test_results['performance_comparison']['success']}")
        print()
        
        return self.test_results["performance_comparison"]["success"]
    
    def run_all_tests(self):
        """Run complete parallel processing test suite"""
        print("🔬 AI Research Platform - Parallel Processing Test Suite")
        print("=" * 60)
        print()
        
        tests = [
            ("ThreadPool Executor Implementation", self.test_threadpool_executor_implementation),
            ("Comprehensive Research Parallel Execution", self.test_comprehensive_research_parallel_execution),
            ("Error Handling in Parallel Execution", self.test_error_handling_in_parallel_execution),
            ("Performance Comparison", self.test_performance_comparison)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                print(f"   ❌ Test failed with exception: {e}")
                print()
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Parallel processing is working correctly.")
        else:
            print("⚠️  Some tests failed. Please review the implementation.")
        
        print()
        print("📋 Detailed Results:")
        print(json.dumps(self.test_results, indent=2))
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = ParallelProcessingTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
