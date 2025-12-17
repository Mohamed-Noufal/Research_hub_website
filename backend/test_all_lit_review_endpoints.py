"""
Comprehensive Test Script for Literature Review Endpoints
Tests all endpoints under the literature review feature including:
- Comparison endpoints
- Findings & Gaps endpoints
- Methodology endpoints
- Synthesis endpoints
- Analysis endpoints
- Table Config endpoints
"""

import requests
import json
import sys
from typing import Dict, Any, List
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
USER_ID = "550e8400-e29b-41d4-a716-446655440000"

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


class LiteratureReviewTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.project_id = None
        self.paper_ids = []
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, 
                     expected_status: int = 200, description: str = ""):
        """Generic endpoint tester"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url)
            elif method.upper() == "POST":
                response = requests.post(url, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data)
            elif method.upper() == "PATCH":
                response = requests.patch(url, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == expected_status:
                print_success(f"{method} {endpoint} - {description}")
                self.test_results["passed"] += 1
                return response
            else:
                error_msg = f"{method} {endpoint} - Expected {expected_status}, got {response.status_code}"
                print_error(error_msg)
                print_error(f"Response: {response.text[:200]}")
                self.test_results["failed"] += 1
                self.test_results["errors"].append({
                    "endpoint": endpoint,
                    "method": method,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:500]
                })
                return None
                
        except requests.exceptions.ConnectionError:
            error_msg = f"Connection Error - Server not running at {self.base_url}"
            print_error(error_msg)
            self.test_results["failed"] += 1
            self.test_results["errors"].append({
                "endpoint": endpoint,
                "method": method,
                "error": "Connection Error - Server not running"
            })
            return None
        except Exception as e:
            error_msg = f"{method} {endpoint} - Exception: {str(e)}"
            print_error(error_msg)
            self.test_results["failed"] += 1
            self.test_results["errors"].append({
                "endpoint": endpoint,
                "method": method,
                "error": str(e)
            })
            return None
    
    def setup_test_project(self):
        """Create a test literature review project"""
        print_header("SETUP: Creating Test Project")
        
        # Create literature review
        response = self.test_endpoint(
            "POST",
            "/users/literature-reviews",
            data={
                "title": f"Test Literature Review {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "description": "Automated test project",
                "paper_ids": []
            },
            description="Create literature review project"
        )
        
        if response and response.status_code == 200:
            data = response.json()
            self.project_id = data.get("id")
            print_info(f"Created project with ID: {self.project_id}")
            
            # Seed with demo data
            seed_response = self.test_endpoint(
                "POST",
                f"/users/literature-reviews/{self.project_id}/seed",
                description="Seed project with demo data"
            )
            
            if seed_response and seed_response.status_code == 200:
                print_success("Project seeded with demo data")
                return True
        
        print_error("Failed to create test project")
        return False
    
    def test_comparison_endpoints(self):
        """Test all comparison endpoints"""
        print_header("TESTING: Comparison Endpoints")
        
        if not self.project_id:
            print_warning("No project ID available, skipping comparison tests")
            return
        
        # GET comparison config
        self.test_endpoint(
            "GET",
            f"/projects/{self.project_id}/comparison/config",
            description="Get comparison configuration"
        )
        
        # UPDATE comparison config
        self.test_endpoint(
            "PUT",
            f"/projects/{self.project_id}/comparison/config",
            data={
                "selected_paper_ids": [1, 2],
                "insights_similarities": "Test similarities",
                "insights_differences": "Test differences"
            },
            description="Update comparison configuration"
        )
        
        # GET comparison attributes
        self.test_endpoint(
            "GET",
            f"/projects/{self.project_id}/comparison/attributes",
            description="Get comparison attributes"
        )
        
        # UPDATE comparison attribute
        self.test_endpoint(
            "PATCH",
            f"/projects/{self.project_id}/comparison/attributes/1",
            data={
                "attribute_name": "sample_size",
                "attribute_value": "100 participants"
            },
            description="Update comparison attribute"
        )
    
    def test_findings_endpoints(self):
        """Test all findings & gaps endpoints"""
        print_header("TESTING: Findings & Gaps Endpoints")
        
        if not self.project_id:
            print_warning("No project ID available, skipping findings tests")
            return
        
        # GET research gaps
        self.test_endpoint(
            "GET",
            f"/projects/{self.project_id}/gaps",
            description="Get research gaps"
        )
        
        # CREATE research gap
        gap_response = self.test_endpoint(
            "POST",
            f"/projects/{self.project_id}/gaps",
            data={
                "description": "Test research gap",
                "priority": "High",
                "notes": "This is a test gap"
            },
            description="Create research gap"
        )
        
        gap_id = None
        if gap_response and gap_response.status_code == 200:
            gap_id = gap_response.json().get("id")
        
        # UPDATE research gap
        if gap_id:
            self.test_endpoint(
                "PATCH",
                f"/projects/{self.project_id}/gaps/{gap_id}",
                data={
                    "description": "Updated research gap",
                    "priority": "Medium"
                },
                description="Update research gap"
            )
        
        # GET findings
        self.test_endpoint(
            "GET",
            f"/projects/{self.project_id}/findings",
            description="Get findings"
        )
        
        # UPDATE finding
        self.test_endpoint(
            "PATCH",
            f"/projects/{self.project_id}/findings/1",
            data={
                "key_finding": "Test key finding",
                "limitations": "Test limitations"
            },
            description="Update finding for paper"
        )
        
        # DELETE research gap
        if gap_id:
            self.test_endpoint(
                "DELETE",
                f"/projects/{self.project_id}/gaps/{gap_id}",
                description="Delete research gap"
            )
    
    def test_methodology_endpoints(self):
        """Test all methodology endpoints"""
        print_header("TESTING: Methodology Endpoints")
        
        if not self.project_id:
            print_warning("No project ID available, skipping methodology tests")
            return
        
        # GET methodology data
        self.test_endpoint(
            "GET",
            f"/projects/{self.project_id}/methodology",
            description="Get methodology data"
        )
        
        # UPDATE methodology data
        self.test_endpoint(
            "PATCH",
            f"/projects/{self.project_id}/methodology/1",
            data={
                "methodology_description": "Test methodology description",
                "methodology_context": "Test context",
                "approach_novelty": "Novel approach"
            },
            description="Update methodology data"
        )
    
    def test_synthesis_endpoints(self):
        """Test all synthesis endpoints"""
        print_header("TESTING: Synthesis Endpoints")
        
        if not self.project_id:
            print_warning("No project ID available, skipping synthesis tests")
            return
        
        # GET synthesis data
        self.test_endpoint(
            "GET",
            f"/projects/{self.project_id}/synthesis",
            description="Get synthesis data"
        )
        
        # UPDATE synthesis structure
        self.test_endpoint(
            "PUT",
            f"/projects/{self.project_id}/synthesis/structure",
            data={
                "columns": [
                    {"id": "col1", "title": "Theme 1"},
                    {"id": "col2", "title": "Theme 2"}
                ],
                "rows": [
                    {"id": "row1", "label": "Paper 1"}
                ]
            },
            description="Update synthesis structure"
        )
        
        # UPDATE synthesis cell
        self.test_endpoint(
            "PATCH",
            f"/projects/{self.project_id}/synthesis/cells",
            data={
                "row_id": "row1",
                "column_id": "col1",
                "value": "Test cell value"
            },
            description="Update synthesis cell"
        )
    
    def test_analysis_endpoints(self):
        """Test all analysis endpoints"""
        print_header("TESTING: Analysis Endpoints")
        
        if not self.project_id:
            print_warning("No project ID available, skipping analysis tests")
            return
        
        # GET analysis config
        self.test_endpoint(
            "GET",
            f"/projects/{self.project_id}/analysis/config",
            description="Get analysis configuration"
        )
        
        # UPDATE analysis config
        self.test_endpoint(
            "PUT",
            f"/projects/{self.project_id}/analysis/config",
            data={
                "chart_preferences": {
                    "methodology_chart_type": "bar",
                    "timeline_chart_type": "line",
                    "show_quality_cards": True
                }
            },
            description="Update analysis configuration"
        )
    
    def test_table_config_endpoints(self):
        """Test table config endpoints"""
        print_header("TESTING: Table Config Endpoints")
        
        if not self.project_id:
            print_warning("No project ID available, skipping table config tests")
            return
        
        # GET table config
        self.test_endpoint(
            "GET",
            f"/projects/{self.project_id}/tables/library/config",
            description="Get table configuration"
        )
        
        # UPDATE table config
        self.test_endpoint(
            "PUT",
            f"/projects/{self.project_id}/tables/library/config",
            data={
                "visible_columns": ["title", "authors", "year"],
                "column_order": ["title", "authors", "year"],
                "custom_fields": {}
            },
            description="Update table configuration"
        )
        
        # GET project papers
        self.test_endpoint(
            "GET",
            f"/projects/{self.project_id}/papers",
            description="Get project papers"
        )
    
    def test_user_endpoints(self):
        """Test user literature review CRUD endpoints"""
        print_header("TESTING: User Literature Review Endpoints")
        
        # GET all literature reviews
        self.test_endpoint(
            "GET",
            "/users/literature-reviews",
            description="Get all literature reviews"
        )
        
        # UPDATE literature review
        if self.project_id:
            self.test_endpoint(
                "PUT",
                f"/users/literature-reviews/{self.project_id}",
                data={
                    "title": "Updated Test Project",
                    "description": "Updated description"
                },
                description="Update literature review"
            )
    
    def cleanup(self):
        """Clean up test data"""
        print_header("CLEANUP: Removing Test Data")
        
        if self.project_id:
            self.test_endpoint(
                "DELETE",
                f"/users/literature-reviews/{self.project_id}",
                description="Delete test project"
            )
    
    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")
        
        total = self.test_results["passed"] + self.test_results["failed"]
        print(f"Total Tests: {total}")
        print_success(f"Passed: {self.test_results['passed']}")
        print_error(f"Failed: {self.test_results['failed']}")
        
        if self.test_results["errors"]:
            print_header("ERRORS DETAIL")
            for i, error in enumerate(self.test_results["errors"], 1):
                print(f"\n{Colors.RED}Error {i}:{Colors.RESET}")
                print(f"  Endpoint: {error.get('endpoint')}")
                print(f"  Method: {error.get('method')}")
                if 'expected' in error:
                    print(f"  Expected Status: {error.get('expected')}")
                    print(f"  Actual Status: {error.get('actual')}")
                    print(f"  Response: {error.get('response', '')[:200]}")
                if 'error' in error:
                    print(f"  Error: {error.get('error')}")
        
        # Save detailed report
        report_file = "lit_review_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print_info(f"\nDetailed report saved to: {report_file}")
        
        return self.test_results["failed"] == 0
    
    def run_all_tests(self):
        """Run all tests"""
        print_header("LITERATURE REVIEW ENDPOINTS TEST SUITE")
        print_info(f"Testing against: {self.base_url}")
        print_info(f"User ID: {USER_ID}")
        
        # Setup
        if not self.setup_test_project():
            print_error("Failed to setup test project. Aborting tests.")
            return False
        
        # Run all endpoint tests
        self.test_user_endpoints()
        self.test_comparison_endpoints()
        self.test_findings_endpoints()
        self.test_methodology_endpoints()
        self.test_synthesis_endpoints()
        self.test_analysis_endpoints()
        self.test_table_config_endpoints()
        
        # Cleanup
        self.cleanup()
        
        # Summary
        return self.print_summary()


def main():
    """Main test runner"""
    tester = LiteratureReviewTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
