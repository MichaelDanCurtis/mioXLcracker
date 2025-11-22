#!/usr/bin/env python3
"""
Hardware Documentation Agent

This agent searches for and downloads hardware documentation for the mio XL MIDI interface.
It looks for:
- User manuals
- Technical specifications
- Datasheets
- SDK documentation
- Protocol documentation
"""

import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"Error: Missing required dependencies. Please run: pip install -r requirements.txt")
    print(f"Missing module: {e.name}")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentationAgent:
    """Agent for discovering and downloading hardware documentation."""
    
    # Known sources for mio XL documentation
    DOCUMENTATION_SOURCES = [
        "https://www.iconnectivity.com/mio",
        "https://www.iconnectivity.com/mioxl",
        "https://www.iconnectivity.com/support",
    ]
    
    # File extensions to consider as documentation
    DOC_EXTENSIONS = [
        '.pdf', '.doc', '.docx', '.txt', '.md', 
        '.html', '.htm', '.xml', '.json', '.zip'
    ]
    
    # Keywords to identify relevant documentation
    DOC_KEYWORDS = [
        'manual', 'guide', 'specification', 'datasheet', 
        'reference', 'documentation', 'sdk', 'api',
        'protocol', 'technical', 'user', 'quickstart',
        'installation', 'setup', 'mio', 'xl', 'midi'
    ]
    
    def __init__(self, output_dir: str = "hardware_docs"):
        """
        Initialize the documentation agent.
        
        Args:
            output_dir: Directory to save downloaded documentation
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        self.found_docs = []
        self.downloaded_files = []
        
        # Create metadata file path
        self.metadata_file = self.output_dir / "documentation_index.json"
    
    def search_for_documentation(self, search_terms: List[str] = None) -> List[Dict]:
        """
        Search for hardware documentation from known sources.
        
        Args:
            search_terms: Additional search terms to look for
            
        Returns:
            List of discovered documentation URLs and metadata
        """
        if search_terms is None:
            search_terms = ["mio XL", "mioXL", "iConnectivity MIDI"]
        
        logger.info(f"Searching for documentation with terms: {search_terms}")
        
        discovered_docs = []
        
        for source in self.DOCUMENTATION_SOURCES:
            try:
                logger.info(f"Checking source: {source}")
                docs = self._scan_website(source)
                discovered_docs.extend(docs)
            except Exception as e:
                logger.warning(f"Failed to scan {source}: {e}")
        
        self.found_docs = discovered_docs
        logger.info(f"Found {len(discovered_docs)} potential documentation files")
        
        return discovered_docs
    
    def _scan_website(self, url: str) -> List[Dict]:
        """
        Scan a website for documentation links.
        
        Args:
            url: Website URL to scan
            
        Returns:
            List of discovered documentation URLs with metadata
        """
        discovered = []
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                
                # Get link text
                link_text = link.get_text(strip=True).lower()
                
                # Check if this is a documentation link
                if self._is_documentation_link(full_url, link_text):
                    doc_info = {
                        'url': full_url,
                        'title': link.get_text(strip=True),
                        'source': url,
                        'discovered_at': datetime.now().isoformat(),
                        'type': self._classify_document(full_url, link_text)
                    }
                    discovered.append(doc_info)
                    logger.info(f"Found: {doc_info['title']} - {full_url}")
        
        except requests.RequestException as e:
            logger.warning(f"Error scanning {url}: {e}")
        
        return discovered
    
    def _is_documentation_link(self, url: str, link_text: str) -> bool:
        """
        Determine if a URL/link points to documentation.
        
        Args:
            url: URL to check
            link_text: Link text to check
            
        Returns:
            True if this appears to be documentation
        """
        # Check file extension
        url_lower = url.lower()
        has_doc_extension = any(url_lower.endswith(ext) for ext in self.DOC_EXTENSIONS)
        
        # Check for keywords in URL or link text
        combined_text = f"{url_lower} {link_text.lower()}"
        has_keyword = any(keyword in combined_text for keyword in self.DOC_KEYWORDS)
        
        return has_doc_extension or has_keyword
    
    def _classify_document(self, url: str, link_text: str) -> str:
        """
        Classify the type of documentation.
        
        Args:
            url: Document URL
            link_text: Link text
            
        Returns:
            Document type classification
        """
        combined = f"{url.lower()} {link_text.lower()}"
        
        if 'manual' in combined or 'guide' in combined:
            return 'manual'
        elif 'specification' in combined or 'spec' in combined:
            return 'specification'
        elif 'datasheet' in combined:
            return 'datasheet'
        elif 'sdk' in combined or 'api' in combined:
            return 'sdk'
        elif 'protocol' in combined:
            return 'protocol'
        elif 'quickstart' in combined or 'getting started' in combined:
            return 'quickstart'
        else:
            return 'general'
    
    def download_documentation(self, doc_list: List[Dict] = None) -> List[str]:
        """
        Download documentation files.
        
        Args:
            doc_list: List of documents to download. If None, uses found_docs
            
        Returns:
            List of successfully downloaded file paths
        """
        if doc_list is None:
            doc_list = self.found_docs
        
        if not doc_list:
            logger.warning("No documentation to download")
            return []
        
        logger.info(f"Downloading {len(doc_list)} documentation files...")
        
        for doc in doc_list:
            try:
                filepath = self._download_file(doc['url'], doc.get('title', 'unknown'))
                if filepath:
                    self.downloaded_files.append(filepath)
                    doc['local_path'] = str(filepath)
                    doc['downloaded_at'] = datetime.now().isoformat()
            except Exception as e:
                logger.error(f"Failed to download {doc['url']}: {e}")
        
        logger.info(f"Successfully downloaded {len(self.downloaded_files)} files")
        
        # Save metadata
        self._save_metadata()
        
        return self.downloaded_files
    
    def _download_file(self, url: str, title: str) -> Optional[Path]:
        """
        Download a single file.
        
        Args:
            url: URL to download
            title: Title/name for the file
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            logger.info(f"Downloading: {url}")
            
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Determine filename
            filename = self._get_filename(url, title, response)
            filepath = self.output_dir / filename
            
            # Don't re-download if file already exists
            if filepath.exists():
                logger.info(f"File already exists: {filename}")
                return filepath
            
            # Download file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Saved: {filename}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return None
    
    def _get_filename(self, url: str, title: str, response: requests.Response) -> str:
        """
        Determine appropriate filename for downloaded file.
        
        Args:
            url: File URL
            title: Document title
            response: HTTP response object
            
        Returns:
            Filename to use
        """
        # Try to get filename from Content-Disposition header
        if 'Content-Disposition' in response.headers:
            import re
            content_disp = response.headers['Content-Disposition']
            filename_match = re.search(r'filename="?([^"]+)"?', content_disp)
            if filename_match:
                return filename_match.group(1)
        
        # Try to get filename from URL
        parsed_url = urlparse(url)
        url_filename = os.path.basename(parsed_url.path)
        if url_filename and '.' in url_filename:
            return url_filename
        
        # Generate filename from title
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
        safe_title = safe_title.strip().replace(' ', '_')[:100]
        
        # Guess extension from content type
        content_type = response.headers.get('Content-Type', '')
        extension = self._guess_extension(content_type)
        
        return f"{safe_title}{extension}"
    
    def _guess_extension(self, content_type: str) -> str:
        """
        Guess file extension from content type.
        
        Args:
            content_type: HTTP Content-Type header value
            
        Returns:
            File extension including the dot
        """
        extensions = {
            'application/pdf': '.pdf',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'text/html': '.html',
            'text/plain': '.txt',
            'application/json': '.json',
            'application/xml': '.xml',
            'application/zip': '.zip',
        }
        
        for mime_type, ext in extensions.items():
            if mime_type in content_type:
                return ext
        
        return '.txt'
    
    def _save_metadata(self):
        """Save metadata about discovered and downloaded documentation."""
        metadata = {
            'last_updated': datetime.now().isoformat(),
            'total_found': len(self.found_docs),
            'total_downloaded': len(self.downloaded_files),
            'documents': self.found_docs
        }
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata saved to {self.metadata_file}")
    
    def create_index(self) -> str:
        """
        Create a markdown index of all documentation.
        
        Returns:
            Path to index file
        """
        index_file = self.output_dir / "INDEX.md"
        
        with open(index_file, 'w') as f:
            f.write("# Hardware Documentation Index\n\n")
            f.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total documents: {len(self.found_docs)}\n")
            f.write(f"Downloaded files: {len(self.downloaded_files)}\n\n")
            
            # Group by type
            by_type = {}
            for doc in self.found_docs:
                doc_type = doc.get('type', 'general')
                if doc_type not in by_type:
                    by_type[doc_type] = []
                by_type[doc_type].append(doc)
            
            # Write each category
            for doc_type, docs in sorted(by_type.items()):
                f.write(f"## {doc_type.title()}\n\n")
                for doc in docs:
                    f.write(f"- **{doc['title']}**\n")
                    f.write(f"  - URL: {doc['url']}\n")
                    if 'local_path' in doc:
                        f.write(f"  - Local: {doc['local_path']}\n")
                    f.write(f"  - Source: {doc['source']}\n")
                    f.write("\n")
        
        logger.info(f"Index created: {index_file}")
        return str(index_file)
    
    def generate_readme(self):
        """Generate a README for the hardware_docs folder."""
        readme_path = self.output_dir / "README.md"
        
        with open(readme_path, 'w') as f:
            f.write("# Hardware Documentation\n\n")
            f.write("This folder contains documentation for the mio XL MIDI interface hardware.\n\n")
            f.write("## Contents\n\n")
            f.write("Documentation has been automatically collected from various sources including:\n")
            for source in self.DOCUMENTATION_SOURCES:
                f.write(f"- {source}\n")
            f.write("\n")
            f.write("## Files\n\n")
            f.write("See `INDEX.md` for a complete list of all documentation.\n\n")
            f.write("## Metadata\n\n")
            f.write("See `documentation_index.json` for detailed metadata about all discovered documentation.\n\n")
            f.write("## Usage\n\n")
            f.write("To update the documentation:\n")
            f.write("```bash\n")
            f.write("python doc_agent.py --search --download\n")
            f.write("```\n")
        
        logger.info(f"README created: {readme_path}")


def main():
    """Main entry point for the documentation agent."""
    parser = argparse.ArgumentParser(
        description="Hardware Documentation Agent - Find and download hardware documentation"
    )
    parser.add_argument(
        '--output-dir',
        default='hardware_docs',
        help='Output directory for downloaded documentation (default: hardware_docs)'
    )
    parser.add_argument(
        '--search',
        action='store_true',
        help='Search for documentation'
    )
    parser.add_argument(
        '--download',
        action='store_true',
        help='Download discovered documentation'
    )
    parser.add_argument(
        '--create-index',
        action='store_true',
        help='Create documentation index'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create agent
    agent = DocumentationAgent(output_dir=args.output_dir)
    
    # If no actions specified, do everything
    if not (args.search or args.download or args.create_index):
        args.search = True
        args.download = True
        args.create_index = True
    
    try:
        # Search for documentation
        if args.search:
            logger.info("Starting documentation search...")
            docs = agent.search_for_documentation()
            logger.info(f"Found {len(docs)} documentation items")
        
        # Download documentation
        if args.download:
            logger.info("Starting documentation download...")
            downloaded = agent.download_documentation()
            logger.info(f"Downloaded {len(downloaded)} files")
        
        # Create index
        if args.create_index:
            logger.info("Creating documentation index...")
            index_path = agent.create_index()
            agent.generate_readme()
            logger.info(f"Index created at: {index_path}")
        
        logger.info("Documentation agent completed successfully")
        
        # Print summary
        print("\n" + "="*60)
        print("DOCUMENTATION AGENT SUMMARY")
        print("="*60)
        print(f"Output directory: {agent.output_dir}")
        print(f"Documents found: {len(agent.found_docs)}")
        print(f"Files downloaded: {len(agent.downloaded_files)}")
        print(f"\nSee {agent.output_dir}/INDEX.md for details")
        print("="*60)
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()
