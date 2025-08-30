# Legacy Files Archive

This folder contains the original files that were replaced by the new modular structure.

## 📅 Archive Date
Created: $(date)

## 📁 Archived Files

### **Original Monolithic Files**
- `sheets.py` - Original 400+ line sheets integration file
- `qc.py` - Original Discord bot main file
- `utils.py` - Original bot utilities

### **Intermediate Refactor Files**
- `sheets_clean.py` - Clean API version of sheets.py
- `sheet_models.py` - Extracted data models
- `sheet_helpers.py` - Extracted helper functions
- `assignment_engine.py` - Extracted assignment logic
- `qc_helpers.py` - Extracted QC helper functions

### **Original Commands**
- `commands/` - Original command structure

## 🔄 **Replacement Mapping**

| Old File | New Location | Status |
|----------|-------------|--------|
| `sheets.py` | `backend/sheets_api.py` | ✅ Replaced |
| `sheet_models.py` | `backend/models.py` | ✅ Replaced |
| `sheet_helpers.py` | `backend/helpers.py` | ✅ Replaced |
| `assignment_engine.py` | `backend/assignment.py` | ✅ Replaced |
| `qc.py` | `bot/qc_main.py` | ✅ Replaced |
| `qc_helpers.py` | `bot/qc_helpers.py` | ✅ Replaced |
| `utils.py` | `bot/utils.py` | ✅ Replaced |
| `commands/` | `bot/commands/` | ✅ Replaced |

## ⚠️ **Important Notes**

- These files are kept for reference only
- **DO NOT** import from these files in new code
- Use the new modular structure in `backend/` and `bot/`
- These files may be removed in future versions

## 🚀 **New Usage**

Instead of:
```python
import sheets
from utils import BotUtils
```

Use:
```python
from backend import get_project_info, assign_writer_to_project
from bot.utils import BotUtils
```

## 🗑️ **Safe to Delete**

These files can be safely deleted once you're confident the new structure works properly:

```bash
rm -rf legacy/
```
