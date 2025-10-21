#!/usr/bin/env python
"""
ななこ言語のCLIインターフェース
使用方法: python -m nanako.nanako_cli [ファイル名]
"""

import sys
from .nanako import NanakoRuntime, NanakoError
import csv
import json
import traceback

# バージョン情報をインポート
try:
    from . import __version__
except ImportError:
    __version__ = "unknown"

def main():
    env = {}
    try:
        # バージョン表示の処理
        if len(sys.argv) > 1 and sys.argv[1] in ['--version', '-v', '-V']:
            print(f"Nanako (ななこ) version {__version__}")
            sys.exit(0)

        # ヘルプ表示の処理
        if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
            print(f"Nanako (ななこ) version {__version__}")
            print("\n使用方法:")
            print("  python -m nanako.nanako_cli [ファイル名]")
            print("  nanako [ファイル名]                  # インストール後")
            print("\nオプション:")
            print("  --version, -v, -V    バージョン情報を表示")
            print("  --help, -h           このヘルプメッセージを表示")
            print("\nファイル形式:")
            print("  .nanako    Nanakoプログラムファイル")
            print("  .csv       CSVデータファイル（環境変数として読み込み）")
            print("  .json      JSONデータファイル（環境変数として読み込み）")
            print("\n例:")
            print("  python -m nanako.nanako_cli examples/01basic.nanako")
            print("  python -m nanako.nanako_cli data.csv program.nanako")
            print("  python -m nanako.nanako_cli                    # インタラクティブモード")
            sys.exit(0)

        run_interactive = True
        for file in sys.argv[1:]:
            if file.endswith('.json'):
                try:
                    env.update(load_env_from_json(file))
                except Exception as e:
                    print(f"エラー ({file}): {e}", file=sys.stderr)
                    sys.exit(1)
            elif file.endswith('.csv'):
                try:
                    env.update(read_csv_as_dict_of_lists(file))
                except Exception as e:
                    print(f"エラー ({file}): {e}", file=sys.stderr)
                    sys.exit(1)
            elif file.endswith('.nanako'):
                try:
                    env = run_file(file, env)
                    run_interactive = False
                except NanakoError as e:
                    # Nanakoの構文エラーや実行時エラー
                    print(f"\nエラーが発生しました: {file}", file=sys.stderr)
                    # エラー詳細を表示
                    if hasattr(e, 'args') and len(e.args) > 1:
                        msg, details = e.args[0], e.args[1]
                        if isinstance(details, tuple) and len(details) >= 4:
                            source, line, col, snippet = details
                            print(f"  行 {line}, 列 {col}: {msg}", file=sys.stderr)
                            print(f"  >>> {snippet}", file=sys.stderr)
                        else:
                            print(f"  {msg}", file=sys.stderr)
                    else:
                        print(f"  {e}", file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    print(f"\nエラーが発生しました: {file}", file=sys.stderr)
                    traceback.print_exc()
                    sys.exit(1)

        if run_interactive:
            env = interactive_mode(env)
        runtime = NanakoRuntime()
        print(runtime.stringfy_as_json(env))
    except KeyboardInterrupt:
        print("\n終了します", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        traceback.print_exc()
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

def run_file(filename, env):
    """ファイルを実行"""
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()
    runtime = NanakoRuntime()
    # ファイル名情報を持ったままexecする
    env = runtime.exec(code, env)
    return env

def interactive_mode(env):
    """インタラクティブモード"""
    print(f"Nanako (ななこ) version {__version__}")
    print("終了するには 'quit' または 'exit' を入力してください")
        
    while True:
        try:
            code = input(">>> ")
            if code.lower() in ['quit', 'exit']:
                break
            
            if code.strip():    
                runtime = NanakoRuntime()
                if code == "":
                    print(runtime.stringfy_as_json(env))
                else:
                    env = runtime.exec(code, env)
        except SyntaxError as e:
            # tracebackでフォーマット
            formatted = traceback.format_exception_only(SyntaxError, e)
            print("".join(formatted).strip())
        except KeyboardInterrupt:
            print("\n終了します")
            break
        except EOFError:
            print("\n終了します")
            break
    return env

def load_env_from_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # 文字列で整数配列に変換できるものは変換
    def try_convert(val):
        if isinstance(val, str):
            arr = [ord(c) for c in val]
            return arr
        if isinstance(val, bool):
            return int(val)
        elif isinstance(val, dict):
            return {k: try_convert(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [try_convert(x) for x in val]
        else:
            return val
    return {k: try_convert(v) for k, v in data.items()}

def read_csv_as_dict_of_lists(filename):
    """
    CSVファイルを読み込み、一行目をキー、各列の値をリストとして辞書で返す
    """
    result = {}
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for key in reader.fieldnames:
            result[key] = []
        for row in reader:
            for key in reader.fieldnames:
                result[key].append(row[key])
    return result

try:
    from IPython.core.magic import register_cell_magic

    @register_cell_magic
    def nanako(line, cell):
        """
        Jupyter用セルマジック: %%nanako
        セル内のななこ言語コードを実行し、環境を表示
        """
        try:
            runtime = NanakoRuntime()
            env = runtime.exec(cell)
            print(runtime.stringfy_as_json(env))
        except Exception as e:
            print(f"エラー: {e}")
except NameError:
    pass
except ImportError:
    pass

if __name__ == "__main__":
    main()