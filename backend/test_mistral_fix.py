"""Test script for the fixed Mistral handler."""

import asyncio
import logging
from backend.mistral_handler import MistralHandler
from backend.config_manager import config_manager
from backend.logger_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def test_mistral_fix():
    """Test the fixed Mistral handler."""
    try:
        # Get API key
        api_keys = config_manager.get_api_keys()
        if not api_keys.get("mistral"):
            print("No Mistral API key found")
            return

        # Initialize handler
        handler = MistralHandler(api_keys["mistral"])

        # Test with sample text
        sample_text = """
        Für eine freiberufliche Tätigkeit suchen wir eine/einen Controller (w/m/d) zur Unterstützung im Projekt.

        Aufgaben:
        - Erstellung des Monatsabschlusses für August
        - Unterstützung im Rahmen der Abschlusstätigkeiten mit externen/internen Prüfern
        - Schnittstelle zu den beteiligten kaufmännischen Controllingeinheiten vom Kunden
        - Unterstützung in einem Projekt zur Derivatebilanzierung
        - Sonderaufgaben zur Unterstützung der Gesamtprojektleitung und des Projektmanagement Office

        Qualifikationen:
        - Mehrjährige Berufserfahrung im Bereich Controlling/Accounting, mit vertieften Abschlusskenntnissen
        - Grundlegende Kenntnisse der Rechnungslegung nach HGB und IFRS
        - Sehr gute Kenntnisse im SAP-Umfeld (R/3 Co & FI oder BCS) sowie sicherer Umgang mit MS-Office-Produkten insbesondere Excel und einem Business Warehouse System (Analysis for Office)

        Einsatzmodalitäten:
        - ab 01.07.2025 für 6 Wochen mit Option auf Verlängerung
        - Aufwand: 4-5 Tage/ Woche
        - Anteil remote: 90%, Anteil vor Ort: 10%
        - Einsatzort: vorwiegend Mannheim
        """

        print("Testing Mistral handler with sample text...")
        project_data = await handler.extract_project_details(sample_text)

        print(f"Extracted project data: {project_data}")

        # Check requirements specifically
        requirements = project_data.get('requirements', [])
        print(f"Number of requirements: {len(requirements)}")

        # Test that we get a list of strings, not a JSON string
        if requirements and isinstance(requirements, list):
            print("✅ Requirements extracted correctly as a list")
            for i, req in enumerate(requirements, 1):
                print(f"  {i}. {req}")
        else:
            print("❌ Requirements not extracted correctly")

        # Test other fields
        print(f"Title: {project_data.get('title', 'Not found')}")
        print(f"Description: {project_data.get('description', 'Not found')[:100]}...")
        print(f"Release date: {project_data.get('release_date', 'Not found')}")
        print(f"Start date: {project_data.get('start_date', 'Not found')}")
        print(f"Location: {project_data.get('location', 'Not found')}")
        print(f"Duration: {project_data.get('duration', 'Not found')}")
        print(f"Budget: {project_data.get('budget', 'Not found')}")

    except Exception as e:
        logger.error(f"Error testing Mistral handler: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(test_mistral_fix())