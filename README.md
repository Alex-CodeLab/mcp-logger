# MCP Logger

Reusable MCP logging service with SQLite backend. Enables agents and applications to write and read logs from a shared location.

## Installation

```bash
git clone https://github.com/madeonawave/mcp-logger.git
cd mcp-logger
uv tool install -e .
```

## Usage

### 1. Start the MCP server

```bash
mcp-logger
```

### 2. Configure in OpenCode

```json
{
  "mcp": {
    "logger": {
      "type": "local",
      "command": ["mcp-logger"],
      "enabled": true
    }
  }
}
```

### 3. Use the tools

**Write a log:**
```
log_write message="Starting build" level="info" repo="my-project" source="agent"
```

**Read latest logs:**
```
log_read n=20
```

**Search logs:**
```
log_search search="error" level="error"
```

## Use in Your Code

### Python Logging Compatible API

```python
import sys
sys.path.insert(0, "/path/to/mcp-logger/src")
from logger import getLogger, INFO

# Get logger - repo defaults to logger name
logger = getLogger("my-project")

# Use like standard logging
logger.info("Build started")
logger.info("Build finished", metadata={"duration": "2m"})
logger.error("Build failed", metadata={"exit_code": 1})
logger.warning("Warning message")
logger.debug("Debug info")

# Override repo per call
logger.info("Message", repo="other-project")

# Format args work too
logger.info("Processing %s items", "10")
```

### Alternative: Copy logger.py to your project

```bash
cp /path/to/mcp-logger/src/logger.py ./logger.py
```

Then:
```python
from logger import getLogger

logger = getLogger("my-project")
logger.info("Hello")
```

### Drop-in replacement for stdlib logging

```python
# Replace standard logging with this logger
from logger import logging

logging.basicConfig(level=logging.INFO, repo="my-project")
logger = logging.getLogger("my-project")
logger.info("Works like standard logging!")
```

## Database

Default location: `~/.lxer/logs.db`

Schema:
```sql
logs (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    level TEXT,      -- debug, info, warning, error
    message TEXT,
    repo TEXT,
    source TEXT,    -- agent or application
    metadata TEXT   -- optional JSON
)
```