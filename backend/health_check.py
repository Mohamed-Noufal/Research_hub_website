#!/usr/bin/env python3
"""
Health check script for all academic sources.
Tests each source individually and provides detailed error diagnostics.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add backend to path and load environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from app.services.arxiv_service import ArxivService
from app.services.semantic_scholar_service import SemanticScholarService
from app.services.openalex_service import OpenAlexService
from app.services.crossref_service import CrossRefService
from app.services.core_service import COREService
from app.services.pubmed_service import PubMedService
from app.services.biorxiv_service import bioRxivService
from app.services.europe_pmc_service import EuropePMCService
from app.services.eric_service import ERICService
from app.core.config import settings

class HealthChecker:
    """Health checker for all academic sources"""

    def __init__(self):
        self.results = {}
        # Use biomedical query for Europe PMC since it's life sciences focused
        self.test_query = "cancer research"

        # Initialize services
        self.services = {
            "arxiv": ArxivService(),
            "semantic_scholar": SemanticScholarService(api_key=getattr(settings, 'SEMANTIC_SCHOLAR_API_KEY', None)),
            "openalex": OpenAlexService(email=getattr(settings, 'OPENALEX_EMAIL', None)),
            "crossref": CrossRefService(email=getattr(settings, 'OPENALEX_EMAIL', None)),
            "core": COREService(),
            "pubmed": PubMedService(),
            "biorxiv": bioRxivService(),
            "europe_pmc": EuropePMCService(),
            "eric": ERICService()
        }

    async def check_service(self, name: str, service) -> Dict[str, Any]:
        """Check a single service"""
        print(f"🔍 Testing {name}...")

        result = {
            "service": name,
            "status": "unknown",
            "papers_found": 0,
            "error": None,
            "response_time": 0,
            "details": {}
        }

        start_time = datetime.now()

        try:
            # Test search
            papers = await service.search(self.test_query, limit=3)
            end_time = datetime.now()

            result["status"] = "success" if papers else "no_results"
            result["papers_found"] = len(papers) if papers else 0
            result["response_time"] = (end_time - start_time).total_seconds()

            if papers:
                result["details"]["sample_title"] = papers[0].get("title", "")[:50] + "..."
                result["details"]["sources"] = list(set(p.get("source") for p in papers))

            print(f"✅ {name}: {len(papers) if papers else 0} papers")

        except Exception as e:
            end_time = datetime.now()
            result["status"] = "error"
            result["error"] = str(e)
            result["response_time"] = (end_time - start_time).total_seconds()

            print(f"❌ {name}: {str(e)}")

        return result

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run health checks for all services"""
        print("🏥 ACADEMIC SOURCES HEALTH CHECK")
        print("=" * 50)
        print(f"Test Query: '{self.test_query}'")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()

        # Run checks sequentially to avoid rate limiting
        for name, service in self.services.items():
            result = await self.check_service(name, service)
            self.results[name] = result

            # Small delay between checks
            await asyncio.sleep(0.5)

        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_query": self.test_query,
            "summary": {},
            "services": self.results,
            "recommendations": []
        }

        # Calculate summary
        total_services = len(self.results)
        successful = sum(1 for r in self.results.values() if r["status"] == "success")
        errors = sum(1 for r in self.results.values() if r["status"] == "error")
        no_results = sum(1 for r in self.results.values() if r["status"] == "no_results")

        report["summary"] = {
            "total_services": total_services,
            "successful": successful,
            "errors": errors,
            "no_results": no_results,
            "success_rate": successful / total_services if total_services > 0 else 0
        }

        # Generate recommendations
        if errors > 0:
            report["recommendations"].append("Check API keys in .env file for failing services")
            report["recommendations"].append("Verify internet connection and API endpoints")
            report["recommendations"].append("Some services may have rate limits - try again later")

        if successful == 0:
            report["recommendations"].append("CRITICAL: No services are working - check network and configuration")

        return report

    def print_report(self, report: Dict[str, Any]):
        """Print formatted report"""
        print("\n" + "=" * 60)
        print("HEALTH CHECK REPORT")
        print("=" * 60)

        summary = report["summary"]
        print(f"Test Query: {report['test_query']}")
        print(f"Total Services: {summary['total_services']}")
        print(f"Successful: {summary['successful']}")
        print(f"Errors: {summary['errors']}")
        print(f"No Results: {summary['no_results']}")
        print(".1f")

        # Service details
        print("\n📊 SERVICE STATUS:")
        for name, result in report["services"].items():
            status_icon = {
                "success": "✅",
                "error": "❌",
                "no_results": "⚠️",
                "unknown": "❓"
            }.get(result["status"], "❓")

            status_text = f"{status_icon} {name}: {result['status']}"
            if result["papers_found"] > 0:
                status_text += f" ({result['papers_found']} papers)"
            if result["error"]:
                status_text += f" - {result['error'][:50]}..."

            print(f"  {status_text}")

        # Recommendations
        if report["recommendations"]:
            print("\n💡 RECOMMENDATIONS:")
            for rec in report["recommendations"]:
                print(f"  • {rec}")

        print(f"\n📄 Full report saved to: health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save report to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"health_report_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"Report saved to: {filename}")

async def main():
    """Main function"""
    checker = HealthChecker()
    report = await checker.run_all_checks()
    checker.print_report(report)
    checker.save_report(report)

if __name__ == "__main__":
    asyncio.run(main())
