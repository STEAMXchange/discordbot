# 🎮 SteamXQuality Development Playground Guide

## 🚀 Quick Start

### **Complete Playground (Recommended)**
```bash
# Run the comprehensive playground
python test_playground.py

# Or start with everything loaded
python -i test_playground.py
```

### **Backend Only**
```bash
# Test backend functionality
python backend/test.py

# Or start Python with backend loaded
python -i backend/test.py
```

### **Bot Only**
```bash
# Test bot functionality  
python bot/test.py

# Or start Python with bot loaded
python -i bot/test.py
```

## 🎯 What You Get

### **Backend Playground (`backend/test.py`)**
- ✅ Google Sheets integration testing
- ✅ Project management functions
- ✅ Writer/Designer assignment testing
- ✅ Data model exploration
- ✅ Safe testing with dry-run options

### **Bot Playground (`bot/test.py`)**
- ✅ Discord bot utilities testing
- ✅ Thread management simulation
- ✅ QC helper functions testing
- ✅ Mock Discord objects for testing
- ✅ Workflow simulation

### **Complete Playground (`test_playground.py`)**
- ✅ Everything from both modules
- ✅ Full system integration testing
- ✅ Performance benchmarking
- ✅ End-to-end workflow demos
- ✅ Quick experiments and examples

## 🧪 Example Usage

### **Backend Testing**
```python
# Start the playground
python -i backend/test.py

# Try some functions
>>> demo_basic_functions()
>>> demo_project_operations("000001")
>>> demo_assignment_system("Science")

# Test assignments (dry run)
>>> test_assignment("000001", dry_run=True)

# Get recommendations
>>> recommendations = get_assignment_recommendations("000001")
>>> print(recommendations)
```

### **Bot Testing**
```python
# Start the playground
python -i bot/test.py

# Try bot functions
>>> demo_bot_utils()
>>> demo_qc_helpers()
>>> test_thread_management()

# Simulate QC workflow
>>> simulate_qc_workflow()
```

### **Complete Testing**
```python
# Start the complete playground
python -i test_playground.py

# Run comprehensive tests
>>> full_system_test()
>>> demo_complete_workflow()
>>> performance_test()

# Quick experiments
>>> quick_experiments()
```

## 🎪 Available Functions

### **Backend Functions**
- `demo_basic_functions()` - Test basic functionality
- `demo_project_operations(project_id)` - Test project operations
- `demo_assignment_system(topic)` - Test assignment system
- `test_assignment(pid, dry_run=True)` - Test assignments safely
- `quick_test()` - Run all backend tests

### **Bot Functions**
- `demo_bot_utils()` - Test bot utilities
- `demo_qc_helpers()` - Test QC functions
- `test_thread_management()` - Test thread operations
- `simulate_qc_workflow()` - Simulate complete workflow
- `quick_test()` - Run all bot tests

### **Complete Functions**
- `full_system_test()` - Test entire system
- `demo_complete_workflow()` - End-to-end demo
- `performance_test()` - Performance benchmarks
- `quick_experiments()` - Quick examples
- `interactive_help()` - Show all available functions

## 💡 Pro Tips

### **Safe Testing**
```python
# Always use dry_run for assignments
test_assignment("000001", dry_run=True)

# Get recommendations without assigning
recommendations = get_assignment_recommendations("000001")
```

### **Exploring Data**
```python
# Check available topics
topics = get_steam_topics()

# Explore column mappings
print(PROJECT_COLUMNS.PROJECT_NAME)  # "B"
print(DESIGNER_COLUMNS.KPI)          # "K"

# Check QC configuration
print(EXPECTED_FONTS)
print(EXPECTED_COLORS)
```

### **Performance Testing**
```python
# Time your operations
import time
start = time.time()
writers = get_best_writers("Science")
end = time.time()
print(f"Time: {end - start:.3f}s")
```

### **Mock Testing**
```python
# Create mock Discord objects
mock_objects = demo_mock_discord_objects()
user = mock_objects["user"]
thread = mock_objects["thread"]
```

## 🔧 Troubleshooting

### **Import Errors**
```bash
# Make sure you're in the project root
cd /path/to/steamxquality

# Check Python path
python -c "import sys; print(sys.path)"
```

### **Google Sheets Errors**
- Check your `steamxquality-d4784ddb6b40.json` credentials file
- Verify `PROJECT_SHEET_ID` and `MANAGEMENT_SHEET_ID` in environment
- Test with: `get_project_row("000001")`

### **Bot Errors**
- Check `DISCORD_BOT_TOKEN` environment variable
- Bot functions work without Discord connection
- Thread management uses local JSON database

## 🎨 Customization

### **Add Your Own Tests**
```python
def my_custom_test():
    """My custom test function."""
    print("🧪 Running my custom test...")
    
    # Your test code here
    result = get_project_info("000001")
    
    if result:
        print("✅ Test passed!")
        return True
    else:
        print("❌ Test failed!")
        return False

# Add to quick_test results
results.append(("My Custom Test", my_custom_test()))
```

### **Environment Setup**
```bash
# Copy environment template
cp env.example .env

# Edit your configuration
# DISCORD_BOT_TOKEN=your_token_here
# PROJECT_SHEET_ID=your_sheet_id
# MANAGEMENT_SHEET_ID=your_management_sheet_id
```

## 🎯 Development Workflow

1. **Start with Complete Playground**: `python -i test_playground.py`
2. **Run System Test**: `full_system_test()`
3. **Try Workflow Demo**: `demo_complete_workflow()`
4. **Experiment**: Use `interactive_help()` to explore
5. **Test Your Changes**: Add custom test functions
6. **Performance Check**: `performance_test()` before deployment

## 🚀 Next Steps

- Use the playground to understand the system
- Test your changes safely with dry-run options  
- Add your own test functions as you develop
- Use performance testing to optimize
- Integrate with your IDE for better development experience

Happy coding! 🎮✨
