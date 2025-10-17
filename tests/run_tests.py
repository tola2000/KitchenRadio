#!/usr/bin/env python3
"""
Test Runner for KitchenRadio Tests

This script runs all the test files in the tests directory.
"""

import sys
import os
import subprocess
import argparse

def run_test(test_file, host="localhost", port=80, verbose=False):
    """Run a single test file."""
    print(f"\n{'='*60}")
    print(f"Running {test_file}")
    print(f"{'='*60}")
    
    cmd = [sys.executable, test_file, host, str(port)]
    
    try:
        if verbose:
            result = subprocess.run(cmd, check=False, capture_output=False)
        else:
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ PASSED")
            else:
                print("❌ FAILED")
                if result.stdout:
                    print("STDOUT:", result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"❌ ERROR running {test_file}: {e}")
        return False

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Run KitchenRadio tests')
    parser.add_argument('--host', '-H', 
                        default='localhost',
                        help='MoOde server host (default: localhost)')
    parser.add_argument('--port', '-p',
                        type=int,
                        default=80,
                        help='MoOde server port (default: 80)')
    parser.add_argument('--test', '-t',
                        help='Run specific test (without .py extension)')
    parser.add_argument('--list', '-l',
                        action='store_true',
                        help='List available tests')
    parser.add_argument('--verbose', '-v',
                        action='store_true',
                        help='Verbose output')
    
    args = parser.parse_args()
    
    # Get test directory
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find all test files
    test_files = []
    for file in os.listdir(test_dir):
        if file.startswith('test_') and file.endswith('.py'):
            test_files.append(os.path.join(test_dir, file))
    
    test_files.sort()
    
    if args.list:
        print("Available tests:")
        for test_file in test_files:
            test_name = os.path.basename(test_file)[:-3]  # Remove .py
            print(f"  {test_name}")
        return
    
    if args.test:
        # Run specific test
        test_file = os.path.join(test_dir, f"{args.test}.py")
        if test_file in test_files:
            success = run_test(test_file, args.host, args.port, args.verbose)
            sys.exit(0 if success else 1)
        else:
            print(f"❌ Test '{args.test}' not found")
            print("Available tests:")
            for test_file in test_files:
                test_name = os.path.basename(test_file)[:-3]
                print(f"  {test_name}")
            sys.exit(1)
    
    # Run all tests
    print(f"🧪 Running all tests against {args.host}:{args.port}")
    print(f"Found {len(test_files)} test files")
    
    passed = 0
    failed = 0
    
    for test_file in test_files:
        if run_test(test_file, args.host, args.port, args.verbose):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total:  {passed + failed}")
    
    if failed > 0:
        print(f"\n⚠️  {failed} test(s) failed!")
        sys.exit(1)
    else:
        print(f"\n🎉 All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
