# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Nanako (ななこ) is an educational programming language designed for the generative AI era. It demonstrates Turing completeness using minimal operations and teaches programming fundamentals through constrained computation.

## Key Architecture Components

### Core Language Implementation (`nanako.py`)
- **NanakoRuntime**: Execution environment with operation counting and timeout handling
- **AST Nodes**: Abstract syntax tree classes inheriting from `ASTNode`
  - Statements: `Assignment`, `Increment`, `Decrement`, `IfStatement`, `LoopStatement`, `ReturnStatement`
  - Expressions: `Number`, `Variable`, `Function`, `FuncCall`, `ArrayList`, `StringLiteral`
- **NanakoParser**: Recursive descent parser with Japanese language support
- **Error Handling**: Custom `NanakoError` with source position tracking

### Language Constraints
- **Limited Operations**: Only increment, decrement, absolute value, negation
- **Zero Comparisons Only**: Conditional statements compare against zero using operators (以上, 以下, より大きい, etc.)
- **Fixed Loops**: N-times repetition or array-length-based iteration
- **Japanese Syntax**: Natural language constructs like `xを増やす` (increment x), `5回、くり返す` (repeat 5 times)

## Common Development Commands

### Running Programs
```bash
python run_nanako.py examples/basic.nanako     # Execute a nanako file
python run_nanako.py                           # Interactive mode
python run_nanako.py data.csv program.nanako   # Load CSV data and run program
```

### Testing
```bash
python -m pytest test_nanako.py               # Run full test suite
python test_nanako.py                         # Direct test execution
```

### Example Programs
- `examples/basic.nanako`: Basic increment/decrement operations
- `examples/string_example.nanako`: String manipulation examples
- `examples/loop.nanako`: Loop control examples

## Implementation Notes

### Variable Management
Variables are stored in environment dictionaries (`env`) passed through evaluation calls. Array access uses bracket notation with special `?` index for random access or append operations.

### Function Calls
Functions create new environment scopes. Return values use `ReturnBreakException` for control flow, following the pattern `expression が答え` (expression is the answer).

### String Handling
Strings are internally represented as arrays of Unicode code points, enabling character manipulation through array operations.

### Runtime Execution
The runtime includes operation counters (`increment_count`, `decrement_count`, `compare_count`) and call frame tracking for debugging and educational analysis.

## File Structure

### Python Implementation
- `nanako/nanako.py`: Core interpreter implementation
- `run_nanako.py`: Command-line runner with file execution and interactive mode
- `test_nanako.py`: Comprehensive test suite using pytest
- `setup.py` & `pyproject.toml`: PyPI packaging configuration (version 0.1.1)

### JavaScript/Web Implementation
- `html/nanako.js`: JavaScript port of Nanako interpreter with AST emit functionality
- `html/nanako_editor.html`: Web-based Monaco Editor integration with:
  - Real-time code execution and error highlighting
  - Dark/light theme toggle
  - Tabbed interface for execution results, JavaScript, and Python code generation
  - Auto-save and restore functionality for user code
  - 50:50 editor/output layout with resizable panels

### Documentation & Data
- `data.csv`: Sample data file for CSV integration
- `TUTORIAL.md`: Step-by-step language tutorial
- `memo.txt`: Language specification notes
- `CLAUDE.md`: This file - development guidance for Claude Code

## Web Editor Features

### AST Code Generation
The JavaScript implementation includes `emit()` methods on all AST nodes that generate equivalent code in JavaScript or Python:
- `ast.emit("js")`: Generates JavaScript code
- `ast.emit("py")`: Generates Python code

### Monaco Editor Integration
- Full syntax highlighting for Nanako language
- Error position tracking with line highlighting
- Keyboard shortcuts (Ctrl+Enter to execute)
- Fallback textarea editor for compatibility

## Development Workflow

### Making Changes to the Web Editor
When updating the web implementation:
1. Modify `html/nanako.js` for core language changes
2. Update `html/nanako_editor.html` for UI/editor features
3. Test with example files in `examples/` directory
4. Ensure both Monaco Editor and fallback editor work correctly

### Version Management
- Python version is maintained in `nanako/__init__.py`, `setup.py`, and `pyproject.toml`
- JavaScript version should be kept in sync with Python implementation
- Both implementations share the same AST structure and language semantics