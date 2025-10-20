#!/usr/bin/env python
"""
ななこ言語のメインランナー
使用方法: python run_nanako.py [ファイル名]
"""

import sys
from .nanako import NanakoRuntime
import csv
import json
import traceback

def main():
    env = {}
    try:            
        run_interactive = True
        for file in sys.argv[1:]:
            if file.endswith('.json'):
                env.update(load_env_from_json(file))
            elif file.endswith('.csv'):
                env.update(read_csv_as_dict_of_lists(file))
            elif file.endswith('.nanako'):
                env = run_file(file, env)
                run_interactive = False

        if run_interactive:
            env = interactive_mode(env)
        runtime = NanakoRuntime()
        print(runtime.stringfy_as_json(env))
    except Exception as e:
        traceback.print_exc()
        print(f"エラー: {e}")

def run_file(filename, env):
    """ファイルを実行"""
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()  
    runtime = NanakoRuntime()
    env = runtime.exec(code, env)
    return env

def interactive_mode(env):
    """インタラクティブモード"""
    print("ななこ言語")
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