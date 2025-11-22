#!/usr/bin/env python3
"""
Test script for the documentation agent.

This script demonstrates how to use the DocumentationAgent class programmatically.
"""

import sys
import logging
from doc_agent import DocumentationAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_agent_initialization():
    """Test that the agent can be initialized."""
    logger.info("Testing agent initialization...")
    agent = DocumentationAgent(output_dir="hardware_docs")
    assert agent.output_dir.exists(), "Output directory should exist"
    assert agent.session is not None, "Session should be initialized"
    logger.info("✓ Agent initialized successfully")
    return agent


def test_documentation_sources():
    """Test that documentation sources are configured."""
    logger.info("Testing documentation sources...")
    agent = DocumentationAgent()
    assert len(agent.DOCUMENTATION_SOURCES) > 0, "Should have documentation sources"
    assert len(agent.DOC_EXTENSIONS) > 0, "Should have file extensions"
    assert len(agent.DOC_KEYWORDS) > 0, "Should have search keywords"
    logger.info(f"✓ Configured with {len(agent.DOCUMENTATION_SOURCES)} sources")
    return agent


def test_filename_sanitization():
    """Test filename sanitization function."""
    logger.info("Testing filename sanitization...")
    agent = DocumentationAgent()
    
    # Test path traversal prevention
    dangerous_names = [
        "../../../etc/passwd",
        "..\\..\\windows\\system32",
        "file/with/slashes.txt",
        "file\\with\\backslashes.txt",
        "file\x00with\x00nulls.txt",
    ]
    
    for dangerous_name in dangerous_names:
        safe_name = agent._sanitize_filename(dangerous_name)
        assert '..' not in safe_name, f"Should remove '..' from {dangerous_name}"
        assert '/' not in safe_name, f"Should remove '/' from {dangerous_name}"
        assert '\\' not in safe_name, f"Should remove '\\' from {dangerous_name}"
        assert '\x00' not in safe_name, f"Should remove null bytes from {dangerous_name}"
        logger.info(f"  {dangerous_name} → {safe_name}")
    
    logger.info("✓ Filename sanitization working correctly")


def test_document_classification():
    """Test document type classification."""
    logger.info("Testing document classification...")
    agent = DocumentationAgent()
    
    test_cases = [
        ("http://example.com/user_manual.pdf", "User Manual", "manual"),
        ("http://example.com/spec.pdf", "Technical Specification", "specification"),
        ("http://example.com/datasheet.pdf", "Datasheet", "datasheet"),
        ("http://example.com/api.html", "API Documentation", "sdk"),
        ("http://example.com/protocol.txt", "MIDI Protocol", "protocol"),
        ("http://example.com/quickstart.pdf", "Quick Start", "quickstart"),
        ("http://example.com/info.pdf", "General Info", "general"),
    ]
    
    for url, link_text, expected_type in test_cases:
        doc_type = agent._classify_document(url, link_text)
        assert doc_type == expected_type, f"Expected {expected_type}, got {doc_type}"
        logger.info(f"  {link_text} → {doc_type}")
    
    logger.info("✓ Document classification working correctly")


def test_create_index():
    """Test index creation."""
    logger.info("Testing index creation...")
    agent = DocumentationAgent(output_dir="hardware_docs")
    
    # Add some mock documents
    agent.found_docs = [
        {
            'url': 'http://example.com/manual.pdf',
            'title': 'User Manual',
            'source': 'http://example.com',
            'discovered_at': '2025-11-22T12:00:00',
            'type': 'manual'
        },
        {
            'url': 'http://example.com/spec.pdf',
            'title': 'Technical Specification',
            'source': 'http://example.com',
            'discovered_at': '2025-11-22T12:00:00',
            'type': 'specification'
        }
    ]
    
    index_path = agent.create_index()
    assert index_path, "Should return index path"
    
    index_file = agent.output_dir / "INDEX.md"
    assert index_file.exists(), "Index file should exist"
    
    with open(index_file, 'r') as f:
        content = f.read()
        assert 'User Manual' in content, "Should contain document titles"
        assert 'Technical Specification' in content, "Should contain document titles"
    
    logger.info("✓ Index creation working correctly")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Documentation Agent Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_agent_initialization()
        print()
        
        test_documentation_sources()
        print()
        
        test_filename_sanitization()
        print()
        
        test_document_classification()
        print()
        
        test_create_index()
        print()
        
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        logger.error(f"Test failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
