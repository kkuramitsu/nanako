# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Nanako (ななこ) は、最小構成の構文に基づく教育プログラミング言語です。
生成AI時代の教育用プログラミング言語として、日本語ベースの直感的な構文を提供します。

## ファイル構成

### Python 実装

Python版がNanakoのマスター実装です。必要に応じて人手メンテしています。

- `nanako/nanako.py`: パーサと抽象構文木、評価器
- `nanako/run_nanako.py`: CLIインターフェース（エラーハンドリング含む）
- `nanako/test_nanako.py`: テストコード（101テスト、4テストクラス）

`setup.py` & `pyproject.toml`: PyPI packaging configuration

### JS 実装

原則、Web ブラウザ上で実装するための nanako.py から移植されたものです。

- `html/nanako.js`: Python版 nanako.py の移植
- `html/nanako.test.js`: テストコード（74テスト、Jest使用）
- `html/nanako_editor.html`: Webブラウザ上の実行環境

### サンプルコード

Nanako のサンプルコードは `examples/` ディレクトリにあります。

- `examples/*.nanako`: 14個のサンプルファイル
  - 基本構文、配列、文字列、条件分岐、ループ、関数
  - アルゴリズム例：GCD、フィボナッチ、バブルソート、クイックソート、ライフゲーム、ROT13

## Key Architecture Components

### Core Language Implementation (`nanako.py`)

- **NanakoRuntime**: Execution environment with operation counting and timeout handling
  - Operation counters: `increment_count`, `decrement_count`, `compare_count`
  - Call frame tracking for debugging
  - Timeout protection (default: 30 seconds)

- **AST Nodes**: Abstract syntax tree classes inheriting from `ASTNode`
  - Statements: `AssignmentNode`, `AppendNode`, `IncrementNode`, `DecrementNode`, `IfNode`, `LoopNode`, `BreakNode`, `ReturnNode`, `TestNode`, `ExpressionStatementNode`
  - Expressions: `NumberNode`, `VariableNode`, `FunctionNode`, `FuncCallNode`, `ArrayNode`, `StringNode`, `NullNode`, `MinusNode`, `ArrayLenNode`
  - All nodes have `evaluate()` and `emit()` methods

- **NanakoParser**: Recursive descent parser with Japanese language support
  - Context-aware identifier parsing (定義時と参照時で異なる挙動)
  - Keyword detection: `に対し`, `を増やす`, `を減らす`, `の末尾に`, `くり返しを抜ける`

- **Error Handling**: Custom `NanakoError` with source position tracking
  - Line number, column number, code snippet
  - Enhanced CLI error reporting with filename display

## Common Development Commands

### Running Programs
```bash
# CLI実行（setup.py install不要）
python3 -m nanako.run_nanako examples/01basic.nanako    # Execute a nanako file
python3 -m nanako.run_nanako                            # Interactive mode
python3 -m nanako.run_nanako data.csv program.nanako    # Load CSV data and run program

# インストール後
nanako examples/01basic.nanako                          # After pip install
```

### Testing
```bash
# 全テスト実行（101テスト）
python3 -m pytest nanako/test_nanako.py -v

# テストクラス別実行
python3 -m pytest nanako/test_nanako.py::TestNanakoParser -v       # パーサーテスト (65)
python3 -m pytest nanako/test_nanako.py::TestNanako -v             # 実行テスト (9)
python3 -m pytest nanako/test_nanako.py::TestNanakoEmitCode -v     # コード生成テスト (2)
python3 -m pytest nanako/test_nanako.py::TestNanakoExamples -v     # サンプルファイルテスト (16)
python3 -m pytest nanako/test_nanako.py::TestNanakoCLI -v          # CLIテスト (8)

# 個別テスト実行
python3 -m pytest nanako/test_nanako.py::TestNanakoExamples::test_individual_example[01basic.nanako] -v

# JavaScriptテスト実行（74テスト）
cd html && npm test
```

## Implementation Notes

### Variable Management
Variables are stored in environment dictionaries (`env`) passed through evaluation calls.
- Array access uses bracket notation: `配列[0]`, `配列[i]`
- Special `?` index for append operations: `配列[?] = 値`
- Context-aware identifier parsing enables Japanese variable names like `残りの回数`, `近い要素がある`

### Array Append Operation
Two syntax options for appending to arrays:
1. `配列[?] = 値` (AssignmentNode with null index)
2. `配列の末尾に値を追加する` (AppendNode - dedicated statement)

### Function Calls
Functions create new environment scopes. Return values use `ReturnBreakException` for control flow.
- Pattern: `expression が答え` (expression is the answer)
- Call frame tracking for debugging

### Loop Control Flow
Loops support break statements using `BreakBreakException` for control flow.
- Pattern: `くり返しを抜ける` or `繰り返しを抜ける` (break from loop)
- Works with both infinite loops (`?回、くり返す`) and counted loops (`N回、くり返す`)
- Example:
  ```nanako
  10回、くり返す {
      もし yが5ならば、{
          くり返しを抜ける
      }
      yを増やす
  }
  ```

### String Handling
Strings are internally represented as `NanakoArray` of Unicode code points.
- Enables character manipulation through array operations
- Example: `"AB"` → `[65, 66]`

### Runtime Execution
- Operation counters for educational analysis: `increment_count`, `decrement_count`, `compare_count`
- Timeout protection prevents infinite loops
- Call frame tracking for stack trace

## Additional Notes: JavaScript/Web Implementation

- `html/nanako.js`: JavaScript port of Nanako interpreter with AST emit functionality
- `html/nanako_editor.html`: Web-based Monaco Editor integration with:
  - Real-time code execution and error highlighting
  - Dark/light theme toggle
  - Tabbed interface for execution results, JavaScript, and Python code generation
  - 50:50 editor/output layout with resizable panels
  - Selected examples are insert into the editor
  - Output: NanakoRuntime.print(), NanakoRuntime stats, and NanakoRuntime.stringfy_as_json()

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

### Making Changes to Python Implementation
1. **Update `nanako/nanako.py`** for core language changes
   - Add new AST nodes if needed
   - Implement both `evaluate()` and `emit()` methods
   - Update `NanakoParser` if new syntax is added

2. **Update `nanako/test_nanako.py`** with corresponding tests
   - Add parser tests in `TestNanakoParser`
   - Add execution tests in `TestNanako`
   - Add emit tests in `TestNanakoEmitCode`
   - Update example files if needed

3. **Run tests to verify changes**
   ```bash
   python3 -m pytest nanako/test_nanako.py -v
   ```

### Making Changes to the Web Editor
When updating the web implementation:
1. Modify `html/nanako.js` for core language changes (port from Python)
2. Update `html/nanako_editor.html` for UI/editor features
3. Test both Monaco Editor and fallback textarea editor
4. Ensure code generation (`emit()`) works for both JS and Python

### Testing Strategy
The Python test suite (101 tests) covers:
1. **Parser tests (65)**: All syntax variations and error cases
2. **Execution tests (9)**: Complex programs (functions, recursion, algorithms, loop control)
3. **Code generation tests (2)**: JS/Python emit functionality
4. **Example file tests (16)**: All `examples/*.nanako` files
5. **CLI tests (8)**: Command-line interface including error reporting

The JavaScript test suite (74 tests) covers:
1. **Parser tests (60)**: All syntax variations and error cases
2. **Execution tests (9)**: Complex programs matching Python test suite
3. **Code generation tests (2)**: JS/Python emit functionality

### Known Issues
Some example files have known errors (tracked in `TestNanakoExamples.KNOWN_ERRORS`):
- `06sum.nanako`: Missing helper function
- `09quicksort.nanako`: Variable scope issue
- `09rot13.nanako`: Array append syntax issue

### Version Management
- Python version is maintained in `nanako/__init__.py`, `setup.py`, and `pyproject.toml`
- JavaScript version should be kept in sync with Python implementation
- Both implementations share the same AST structure and language semantics

## Recent Improvements (2025-10/11)

### Version 0.2.2 - Break Statement Support
- Added `BreakNode` AST node for loop control flow
- Added `BreakBreakException` for control flow handling
- Syntax: `くり返しを抜ける` or `繰り返しを抜ける`
- Works with both infinite loops and counted loops
- Implemented in both Python and JavaScript versions
- Added comprehensive test cases (Python: 101 tests, JavaScript: 74 tests)
- Example:
  ```nanako
  10回、くり返す {
      もし yが5ならば、{
          くり返しを抜ける
      }
      yを増やす
  }
  ```

### Context-Aware Identifier Parsing
- Improved parsing of Japanese variable names
- Distinguishes between definition and reference contexts
- Handles variables like `残りの回数`, `近い要素がある`, `配列の末尾に`

### AppendNode Statement
- New dedicated AST node for array append operations
- Syntax: `配列の末尾に値を追加する`
- Complements existing `配列[?] = 値` syntax

### Enhanced Error Reporting
- CLI now displays filename on all errors
- NanakoError shows line number, column number, and code snippet
- Improved debugging experience for educational use

### Comprehensive Test Suite
- Python: 101 tests covering all aspects of the language
- JavaScript: 74 tests matching Python implementation
- Automated testing of all example files
- CLI functionality tests (no installation required)

