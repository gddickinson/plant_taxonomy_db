# Plant Taxonomy Database - Enhanced Version

APython application for building and querying a comprehensive plant taxonomy database with **robust error handling, logging, and multiple fallback data sources**.

## 🆕 What's New in Enhanced Version

### Comprehensive Logging
- **Color-coded console output** for easy debugging
- **File logging** with detailed timestamps and context
- **Component-specific loggers** (database, API, models, utils)
- **DEBUG/INFO/WARNING/ERROR levels** for granular control

### Multiple Data Sources with Fallback
- **ITIS** (Integrated Taxonomic Information System) - Primary source
- **GBIF** (Global Biodiversity Information Facility) - Fallback
- **Automatic fallback** when primary source fails
- **Connection testing** before operations

### Enhanced Error Handling
- **Retry logic** with exponential backoff
- **Informative error messages** explaining what went wrong
- **Graceful degradation** when services unavailable
- **Exception hierarchy** for better error catching

### Better User Experience
- **Real-time status updates** during operations
- **Progress indicators** for long operations
- **Clear error messages** with suggested fixes
- **Connection test** before attempting operations

## Quick Start

### Installation

```bash
pip install requests  # Only dependency
```

### Test the Enhanced Features

```bash
# Run with verbose logging
python demo_enhanced.py --verbose

# Interactive mode
python demo_enhanced.py --interactive

# Original offline tests still work
python test_offline.py
```

## Enhanced Features Demo

### 1. Connection Testing

The enhanced version tests all data sources before attempting operations:

```
🔌 CONNECTION TEST 🔌

[1] Testing ITIS (itis.gov)...
    ✓ ITIS: Connected

[2] Testing GBIF (gbif.org)...
    ✓ GBIF: Connected

✓ 2 data source(s) available: ITIS, GBIF
```

### 2. Automatic Fallback

When ITIS fails, automatically tries GBIF:

```python
from api.data_source_manager import DataSourceManager

manager = DataSourceManager()
results, source, msg = manager.search_with_best_source("Quercus alba")

# If ITIS is down:
# WARNING - ITIS failed: Connection timeout
# INFO - Falling back to next data source...
# INFO - Trying GBIF...
# ✓ Found 5 results from GBIF
```

### 3. Comprehensive Logging

View detailed logs in `logs/plant_taxonomy_*.log`:

```
2025-01-17 15:30:12 - INFO - plant_taxonomy.api.itis - Searching ITIS for: 'Arabidopsis'
2025-01-17 15:30:14 - INFO - plant_taxonomy.api.itis - Found 2 results
2025-01-17 15:30:14 - INFO - plant_taxonomy.api.itis - Fetching hierarchy for TSN: 505310
2025-01-17 15:30:16 - INFO - plant_taxonomy.api.itis - Retrieved hierarchy with 7 ranks
```

### 4. Better Error Messages

Old version:
```
Error searching ITIS: ConnectionError
```

Enhanced version:
```
✗ ITIS connection failed: Failed to connect to ITIS after 3 attempts. 
  Please check your internet connection and try again.

Trying fallback data source GBIF...
```

## Project Structure (Enhanced)

```
plant_taxonomy_db_enhanced/
├── database/
│   └── db_manager.py           # Database operations
├── api/
│   ├── itis_client.py          # Enhanced ITIS client with retries
│   ├── gbif_client.py          # NEW: GBIF client
│   └── data_source_manager.py  # NEW: Manages multiple sources
├── models/
│   └── taxonomy.py             # Data models
├── utils/
│   ├── formatting.py           # Display utilities
│   ├── test_data.py            # Sample data
│   └── logger.py               # NEW: Logging configuration
├── demo_enhanced.py            # NEW: Enhanced demo script
├── test_offline.py             # Offline testing
└── README.md                   # This file
```

## Usage Examples

### Example 1: Search with Fallback

```python
from api.data_source_manager import DataSourceManager
from utils.logger import setup_quick_logging

# Setup logging
setup_quick_logging(verbose=True)

# Create manager (tries ITIS first, falls back to GBIF)
manager = DataSourceManager(prefer_itis=True)

# Test connections
status = manager.test_all_connections()
# Returns: {'ITIS': True, 'GBIF': True}

# Search with automatic fallback
results, source, msg = manager.search_with_best_source("Rosa rugosa")
print(f"Found results from: {source}")
```

### Example 2: Robust Data Retrieval

```python
from api.data_source_manager import DataSourceManager
from database.db_manager import TaxonomyDatabase

manager = DataSourceManager()

# Get taxon with full hierarchy (tries multiple sources)
taxon, lineage, source = manager.get_taxon_with_hierarchy(
    identifier=505310,  # TSN or GBIF ID
    source='ITIS'       # Or None for automatic
)

if taxon and lineage:
    # Store in database
    with TaxonomyDatabase("plants.db") as db:
        db.create_schema()
        for taxon_item in lineage:
            db.insert_taxon(taxon_item.to_dict())
    print(f"✓ Stored from {source}")
else:
    print("✗ All sources failed")
```

### Example 3: Custom Logging

```python
from utils.logger import setup_logging
import logging

# Setup with custom configuration
setup_logging(
    log_level=logging.DEBUG,
    log_file="my_app.log",
    console=True
)

# Use in your code
from utils.logger import get_logger
logger = get_logger('my_module')

logger.info("Starting operation")
logger.debug("Detailed debug info")
logger.warning("Something unusual happened")
logger.error("Operation failed")
```

## Error Handling Guide

### Common Errors and Solutions

#### Connection Timeout
```
Error: Request timed out after 3 attempts
Solution: Check internet connection, try again later
```

#### ITIS/GBIF Down
```
Error: Failed to connect to ITIS after 3 attempts
Auto-fix: System automatically tries GBIF as fallback
```

#### No Results Found
```
Error: No results found from any data source
Possible causes:
  - Species name misspelled
  - Species not in databases
  - All sources unavailable
```

## Configuration

### Retry Settings

Modify retry behavior in client initialization:

```python
from api.itis_client import ITISClient

# Custom retry configuration
client = ITISClient(
    max_retries=5,      # Try up to 5 times
    retry_delay=2.0,    # Start with 2 second delay
    timeout=60          # 60 second timeout
)
```

### Logging Levels

Control verbosity:

```bash
# Minimal output
python demo_enhanced.py

# Verbose output
python demo_enhanced.py --verbose

# Or in code:
setup_quick_logging(verbose=True)  # DEBUG level
setup_quick_logging(verbose=False) # INFO level
```

## Enhanced Interactive Mode

```bash
python demo_enhanced.py --interactive --verbose
```

New commands:
- `test` - Test all data source connections
- `verbose` - Toggle verbose logging on/off
- All original commands still work

## Logging Output Examples

### Console Output (Color-Coded)
```
INFO - plant_taxonomy.api.manager - DataSourceManager initialized (primary: ITIS)
INFO - plant_taxonomy.api.itis - Testing ITIS connection...
INFO - plant_taxonomy.api.itis - ✓ ITIS connection successful
WARNING - plant_taxonomy.api.itis - Request timeout (attempt 1/3)
ERROR - plant_taxonomy.api.itis - ✗ ITIS connection failed
```

### Log File Output
```
2025-01-17 15:30:12 - INFO - plant_taxonomy.api.manager - DataSourceManager initialized
2025-01-17 15:30:14 - DEBUG - plant_taxonomy.api.itis - Request to searchByScientificName
2025-01-17 15:30:14 - DEBUG - plant_taxonomy.api.itis - Parameters: {'srchKey': 'Quercus'}
2025-01-17 15:30:16 - INFO - plant_taxonomy.api.itis - Found 15 results
```

## Testing

### Connection Test
```bash
python demo_enhanced.py
```
First step tests all data sources and reports status.

### Offline Test
```bash
python test_offline.py
```
Tests all features without internet connection.

## Performance

- **Retry logic**: Exponential backoff prevents hammering failed services
- **Connection pooling**: Reuses HTTP connections for efficiency
- **Caching**: Database serves as local cache
- **Fallback**: Reduces failed operations by trying alternatives

## Troubleshooting

### No logs directory

The system creates `logs/` automatically. If you see errors, create it manually:
```bash
mkdir logs
```

### Cannot import logger

Make sure you're running from project directory:
```bash
cd plant_taxonomy_db_enhanced
python demo_enhanced.py
```

### All sources failing

1. Check internet connection
2. Try with verbose logging: `python demo_enhanced.py --verbose`
3. Check log file in `logs/` directory
4. Test specific source:
   ```python
   from api.itis_client import ITISClient
   client = ITISClient()
   client.test_connection()
   ```

## Comparison: Original vs Enhanced

| Feature | Original | Enhanced |
|---------|----------|----------|
| Data Sources | ITIS only | ITIS + GBIF |
| Error Handling | Basic try/catch | Retry + fallback |
| Logging | Print statements | Comprehensive logging |
| Error Messages | Generic | Specific + solutions |
| Retry Logic | None | Exponential backoff |
| Connection Test | No | Yes |
| Offline Mode | Yes | Yes |

## Next Steps

1. **Test with your species**: Try adding plants you're researching
2. **Customize logging**: Adjust verbosity for your needs
3. **Add more sources**: Extend with Tropicos, WFO, etc.
4. **Build GUI**: Use logging for progress indicators

## License

Released under the [MIT licence](LICENSE).

## Acknowledgments

- ITIS for taxonomic data
- GBIF for biodiversity information
- Enhanced logging and error handling patterns
