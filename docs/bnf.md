# Nanakoの構文仕様

Nanakoの構文をEBNF(拡張BNF)記法で定義します。

## 記法の説明

- `::=` : 定義
- `|` : 選択
- `[ ]` : 省略可能（0回または1回）
- `{ }` : 繰り返し（0回以上）
- `( )` : グループ化
- `" "` : リテラル文字列
- `/* */` : コメント

## プログラム構造

```ebnf
program ::= { statement }

statement ::= assignment
            | increment
            | decrement
            | append
            | if_statement
            | loop_statement
            | break_statement
            | return_statement
            | test_statement
            | expression_statement
            | comment
```

## 文 (Statements)

### 代入文

```ebnf
assignment ::= variable "=" expression
             | variable "[" expression "]" "=" expression
             | variable "を" expression "とする"
             | variable "[" expression "]" "を" expression "とする"
```

### インクリメント・デクリメント

```ebnf
increment ::= variable "を増やす"
            | variable "[" expression "]" "を増やす"

decrement ::= variable "を減らす"
            | variable "[" expression "]" "を減らす"
```

### 配列追加

```ebnf
append ::= variable "[" "?" "]" "=" expression
         | variable "の末尾に" expression "を追加する"
```

### 条件分岐

```ebnf
if_statement ::= "もし" expression comparison_operator expression "ならば" "、"? block
                 [ "そうでなければ" "、"? block ]

comparison_operator ::= "が"
                      | "が" ( "以上" | "以下" | "以外" | "未満" )
                      | "が" ( "より大きい" | "より小さい" )
```

### ループ

```ebnf
loop_statement ::= expression "回" "、"? ( "くり返す" | "繰り返す" ) block
```

### Break文

```ebnf
break_statement ::= ( "くり返しを抜ける" | "繰り返しを抜ける" )
```

### Return文

```ebnf
return_statement ::= expression "が答え"
```

### テスト文

```ebnf
test_statement ::= ">>>" expression newline expected_value

expected_value ::= expression
```

### 式文

```ebnf
expression_statement ::= expression
```

### コメント

```ebnf
comment ::= "#" { any_character } newline
```

## 式 (Expressions)

```ebnf
expression ::= null_literal
             | number_literal
             | string_literal
             | array_literal
             | function_literal
             | function_call
             | variable
             | minus_expression
             | array_length
```

### リテラル

```ebnf
null_literal ::= "?" | "？" | "null"

number_literal ::= [ "-" ] digit { digit }

string_literal ::= '"' { character } '"'
                 | '"' { character } '"'

array_literal ::= "[" [ expression { "," expression } [ "," ] ] "]"
                | "【" [ expression { "," expression } [ "," ] ] "】"
```

### 関数

```ebnf
function_literal ::= "入力" parameter_list "に対し" "て"? "、"? block

parameter_list ::= identifier { ( "," | "、" | "，" | "､" ) identifier }

function_call ::= identifier "(" [ expression { "," expression } ] ")"
                | identifier "（" [ expression { "," expression } ] "）"
```

### 変数とアクセス

```ebnf
variable ::= identifier [ array_access ]

array_access ::= ( "[" | "【" ) expression ( "]" | "】" ) { ( "[" | "【" ) expression ( "]" | "】" ) }

identifier ::= ( letter | japanese_char ) { letter | japanese_char | digit }
```

### その他の式

```ebnf
minus_expression ::= "-" expression

array_length ::= "|" variable "|"
```

## ブロック

```ebnf
block ::= ( "{" | "｛" ) { statement } ( "}" | "｝" )
```

## 字句要素

```ebnf
digit ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
        | "０" | "１" | "２" | "３" | "４" | "５" | "６" | "７" | "８" | "９"

letter ::= "a" ... "z" | "A" ... "Z"

japanese_char ::= /* ひらがな、カタカナ、漢字 */

character ::= /* 任意のUnicode文字（ダブルクォート以外） */

whitespace ::= " " | "\t" | "　"

newline ::= "\n" | "\r\n"

comma ::= "," | "、" | "，" | "､"
```

## 制約事項

### サポートされている機能
- 整数演算（加減算のみ）
- 配列（多次元配列可）
- 文字列（Unicode配列として扱う）
- 関数（再帰可）
- 条件分岐
- ループ（break文サポート）
- doctest

### サポートされていない機能
- 浮動小数点数
- 中置演算子（`x + y` など）
- for文型の反復子
- 論理演算子（`and`, `or`, `not`）
- ビット演算
- 例外処理
- インポート/モジュール
- クラス/オブジェクト指向
- 辞書/ハッシュマップ

## 例

### 変数と演算

```nanako
x = 10
xを増やす
xを減らす
```

### 配列

```nanako
arr = [1, 2, 3]
arr[0] = 10
arr[?] = 4
length = |arr|
```

### 条件分岐

```nanako
もし xが5ならば、{
    yを増やす
}
そうでなければ、{
    yを減らす
}
```

### ループ

```nanako
10回、くり返す {
    xを増やす
}

?回、くり返す {
    もし xが100以上ならば、{
        くり返しを抜ける
    }
    xを増やす
}
```

### 関数

```nanako
足し算 = 入力 x, y に対し、{
    y回、くり返す {
        xを増やす
    }
    xが答え
}

result = 足し算(3, 5)
```

### doctest

```nanako
x = 42
>>> x
42
```

