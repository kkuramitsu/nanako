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
        print(dump_dict_as_json(env))
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
    print("ななこ言語インタラクティブモード")
    print("終了するには 'quit' または 'exit' を入力してください")
        
    while True:
        try:
            code = input(">>> ")
            if code.lower() in ['quit', 'exit']:
                break
            
            if code.strip():
                if code == "":
                    print(dump_dict_as_json(env))
                else:
                    runtime = NanakoRuntime()
                    env = runtime.exec(code, env)        
        except KeyboardInterrupt:
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

def convert_array_to_string_if_printable(arr):
    """
    配列の要素が全て正の整数かつprintableな文字なら文字列に変換し、そうでなければそのまま返す
    """
    if (
        isinstance(arr, list)
        and all(isinstance(x, int) and x > 0 and chr(x).isprintable() for x in arr)
    ):
        try:
            return ''.join(chr(x) for x in arr)
        except Exception:
            return arr
    return arr

def is_json_serializable(x):
    try:
        json.dumps(x)
        return True
    except Exception:
        return False

def process_value(v):
    if isinstance(v, list):
        # 1次元配列のみ変換
        if all(not isinstance(x, (list, dict)) for x in v):
            return convert_array_to_string_if_printable(v)
        else:
            # 多次元配列や辞書が含まれる場合は再帰的に処理
            return [process_value(x) for x in v if is_json_serializable(process_value(x))]
    elif isinstance(v, dict):
        return {k: process_value(val) for k, val in v.items() if is_json_serializable(process_value(val))}
    else:
        return v

def dump_dict_as_json(d):
    """
    辞書をJSON形式で安全に変換する。
    1次元配列はconvert_array_to_string_if_printableで文字列化。
    JSONに変換できない要素は除外。
    """

    processed = {k: process_value(v) for k, v in d.items() if is_json_serializable(process_value(v))}
    return json.dumps(processed, ensure_ascii=False, indent=2)


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
            print(dump_dict_as_json(env))
        except Exception as e:
            print(f"エラー: {e}")
except NameError:
    pass
except ImportError:
    pass

if __name__ == "__main__":
    main()