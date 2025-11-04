# PythonユーザのためのNanako入門

Nanakoは、教育用のプログラミング言語です。
日本語ベースの文法、限られた言語仕様により、プログラミングの基礎やアルゴリズムの基礎を体験できるように開発されています。
この文書ではPythonユーザのための最短の習得点をまとめます。

## 基本文法の比較

### 変数と代入

```python
# Python
x = 10
x += 1
x -= 1
```

```nanako
# Nanako
x = 10
xを増やす
xを減らす
```

### 配列

```python
# Python
arr = [1, 2, 3]
arr[0] = 10
arr.append(4)
length = len(arr)
```

```nanako
# Nanako
arr = [1, 2, 3]
arr[0] = 10
arr[?] = 4              # または: arrの末尾に4を追加する
length = |arr|
```

### 条件分岐

```python
# Python
if x == 5:
    y = 1
elif x >= 10:
    y = 2
else:
    y = 3
```

```nanako
# Nanako
もし xが5ならば、{
    y = 1
}
そうでなければ、{
    もし xが10以上ならば、{
        y = 2
    }
    そうでなければ、{
        y = 3
    }
}
```

比較演算子：
- `xが5ならば` → `x == 5`
- `xが5以外ならば` → `x != 5`
- `xが5以上ならば` → `x >= 5`
- `xが5以下ならば` → `x <= 5`
- `xが5より大きいならば` → `x > 5`
- `xが5より小さいならば` / `xが5未満ならば` → `x < 5`

### ループ

```python
# Python
for i in range(10):
    print(i)

# 無限ループ
while True:
    if condition:
        break
```

```nanako
# Nanako
10回、くり返す {
    # 処理
}

# 無限ループ
?回、くり返す {
    もし 条件ならば、{
        くり返しを抜ける
    }
}
```

### 関数

```python
# Python
def add(x, y):
    return x + y

result = add(3, 5)
```

```nanako
# Nanako
足し算 = 入力 x, y に対し、{
    y回、くり返す {
        xを増やす
    }
    xが答え
}

result = 足し算(3, 5)
```

## Nanakoの特徴的な制約

### できること
- 整数演算のみ（加減算のみ、乗除算は自分で実装）
- 配列操作（多次元配列可）
- 文字列（Unicode配列として扱う）
- 再帰関数
- doctest（`>>>` で期待値を記述）

### できないこと
- 小数（浮動小数点数）
- 中置演算子（`x + y` は不可）
- for文のような反復子（`N回、くり返す`のみ）
- 文字列連結（配列として操作）
- 辞書/オブジェクト
- クラス/継承
- 例外処理
- インポート/モジュール

## 実行方法

```bash
# インストール
pip install nanako

# 実行
nanako program.nanako

# インタラクティブモード
nanako

# CSVデータを読み込んで実行
nanako data.csv program.nanako
```

## Webエディタ

`html/nanako_editor.html` をブラウザで開くと、Monaco Editorベースのオンラインエディタが使えます。
- コードの実行
- JavaScript/Pythonへのトランスパイル
- 実行履歴のダウンロード機能

## サンプルコード

`examples/` ディレクトリに以下のサンプルがあります：

- `01basic.nanako` - 基本操作
- `02array.nanako` - 配列操作
- `03loop.nanako` - ループ
- `04function.nanako` - 関数定義
- `07gcd.nanako` - 最大公約数
- `08fibonacci.nanako` - フィボナッチ数列
- `09bubblesort.nanako` - バブルソート
- `09quicksort.nanako` - クイックソート
- `09lifegame.nanako` - ライフゲーム

## まとめ

Nanakoは最小限の構文でアルゴリズムの本質を学ぶための言語です。
制約があることで、基本的なアルゴリズムを自分で実装する必要があり、教育的価値が高まります。

