# Hardware Documentation Agent Usage Guide

This guide demonstrates how to use the hardware documentation agent to gather and organize documentation for the mio XL MIDI interface.

## Quick Start

### Command Line Usage

The simplest way to use the agent is from the command line:

```bash
# Run the full workflow: search, download, and create index
python doc_agent.py

# Or run specific operations:
python doc_agent.py --search          # Search only
python doc_agent.py --download        # Download only
python doc_agent.py --create-index    # Create index only

# Use verbose logging to see detailed progress
python doc_agent.py --verbose

# Save to a custom directory
python doc_agent.py --output-dir my_hardware_docs
```

### Programmatic Usage

You can also use the agent programmatically in your Python code:

```python
from doc_agent import DocumentationAgent

# Create the agent
agent = DocumentationAgent(output_dir="hardware_docs")

# Search for documentation
docs = agent.search_for_documentation()
print(f"Found {len(docs)} documents")

# Download all discovered documentation
downloaded = agent.download_documentation()
print(f"Downloaded {len(downloaded)} files")

# Create organized index
index_path = agent.create_index()
agent.generate_readme()
print(f"Index created at: {index_path}")
```

## What Gets Downloaded

The agent searches for and downloads various types of hardware documentation:

- **User Manuals** - Complete guides for using the hardware
- **Technical Specifications** - Detailed hardware specifications
- **Datasheets** - Component and technical datasheets
- **SDK Documentation** - Software development kit documentation
- **Protocol Documentation** - Communication protocol specifications
- **Quick Start Guides** - Getting started documentation
- **API References** - Programming interface documentation

## Documentation Sources

By default, the agent searches these sources:
- https://www.iconnectivity.com/mio
- https://www.iconnectivity.com/mioxl
- https://www.iconnectivity.com/support

You can modify these sources by editing `DOCUMENTATION_SOURCES` in `doc_agent.py`.

## Output Structure

After running the agent, your `hardware_docs/` folder will contain:

```
hardware_docs/
├── README.md                    # Guide to the documentation folder
├── INDEX.md                     # Organized list of all documentation
├── documentation_index.json     # Detailed metadata in JSON format
├── mio_XL_User_Manual.pdf      # Downloaded documentation files
├── mio_XL_Datasheet.pdf
└── ... (other downloaded files)
```

## Advanced Usage

### Custom Search Terms

You can customize the search terms by modifying the agent:

```python
agent = DocumentationAgent()
docs = agent.search_for_documentation(
    search_terms=["mio XL", "iConnectivity MIDI", "custom term"]
)
```

### Filtering Documents

After searching, you can filter documents before downloading:

```python
agent = DocumentationAgent()
docs = agent.search_for_documentation()

# Filter for only manuals and datasheets
filtered_docs = [
    doc for doc in docs 
    if doc['type'] in ['manual', 'datasheet']
]

# Download only filtered documents
agent.download_documentation(filtered_docs)
```

### Accessing Metadata

The agent saves detailed metadata about all documentation:

```python
import json

# Read metadata
with open('hardware_docs/documentation_index.json', 'r') as f:
    metadata = json.load(f)

print(f"Last updated: {metadata['last_updated']}")
print(f"Total found: {metadata['total_found']}")
print(f"Total downloaded: {metadata['total_downloaded']}")

# Iterate through documents
for doc in metadata['documents']:
    print(f"{doc['title']}: {doc['url']}")
    if 'local_path' in doc:
        print(f"  Local: {doc['local_path']}")
```

## Testing

Run the test suite to verify the agent is working correctly:

```bash
python test_doc_agent.py
```

This will test:
- Agent initialization
- Documentation sources configuration
- Filename sanitization (security)
- Document classification
- Index creation

## Troubleshooting

### No Documents Found

If the agent reports 0 documents found:
- Check your internet connection
- Verify the documentation sources are accessible
- Try running with `--verbose` to see detailed logs
- Check if the websites have changed their structure

### Download Failures

If downloads fail:
- Check your internet connection
- Verify you have write permissions to the output directory
- Some files may be blocked by firewalls or access restrictions
- Try downloading individual files manually to test

### Permission Errors

If you get permission errors when writing files:
```bash
# Ensure the output directory is writable
chmod 755 hardware_docs
```

## Best Practices

1. **Run Regularly** - Documentation gets updated, so run the agent periodically to get the latest versions

2. **Version Control** - Don't commit large PDF files to git. The `.gitignore` is already configured to exclude them.

3. **Review Downloads** - After downloading, review the `INDEX.md` to see what was collected

4. **Backup** - Keep backups of important documentation in case sources become unavailable

5. **Respect Robots.txt** - The agent respects website rate limiting and robots.txt directives

## Security

The agent includes several security features:

- **Filename Sanitization** - Prevents path traversal attacks
- **File Validation** - Checks for complete downloads
- **Updated User-Agent** - Uses current browser strings
- **No Code Execution** - Only downloads documentation files

All security checks have been validated:
- ✅ CodeQL analysis: 0 alerts
- ✅ No known vulnerabilities in dependencies
- ✅ Path traversal protection
- ✅ Input sanitization

## Contributing

To add new documentation sources:

1. Edit `doc_agent.py`
2. Add URLs to `DOCUMENTATION_SOURCES`
3. Run the agent to test
4. Submit a pull request

## Support

For issues or questions:
- Check the README.md for general information
- Review test_doc_agent.py for usage examples
- Open an issue on GitHub if you encounter problems
