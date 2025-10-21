import pytest
import glob
import os
from pathlib import Path
from nanako import NanakoParser, NanakoRuntime, NanakoArray, NanakoError

class TestNanakoParser:
    """NanakoParser のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される初期化"""
        self.parser = NanakoParser()
        self.runtime = NanakoRuntime()
        self.env = {}

    def test_parse_null(self):
        """nullリテラルのパースをテスト"""
        expression = self.parser.parse_expression('?')
        result = expression.evaluate(self.runtime, self.env)
        assert result == None

    def test_parse_zenkaku_null(self):
        """nullリテラルのパースをテスト"""
        expression = self.parser.parse_expression('？')
        result = expression.evaluate(self.runtime, self.env)
        assert result == None

    def test_parse_integer(self):
        """整数リテラルのパースをテスト"""
        expression = self.parser.parse_expression('42')
        result = expression.evaluate(self.runtime, self.env)
        assert result == 42

    def test_parse_zenkaku_integer(self):
        """整数リテラルのパースをテスト"""
        expression = self.parser.parse_expression('４２')
        result = expression.evaluate(self.runtime, self.env)
        assert result == 42

    def test_parse_minus_integer(self):
        """整数リテラルのパースをテスト"""
        expression = self.parser.parse_expression('-42')
        result = expression.evaluate(self.runtime, self.env)
        assert result == -42

    def test_parse_infix(self):
        """中置記法をテスト"""
        with pytest.raises(SyntaxError) as e:
            expression = self.parser.parse_expression('4+2')
            result = expression.evaluate(self.runtime, self.env)
            assert result == 6
        print(e.value)
        assert "中置" in str(e.value)

    def test_parse_fraction(self):
        """少数をテスト"""
        with pytest.raises(SyntaxError) as e:
            expression = self.parser.parse_expression('4.2')
            result = expression.evaluate(self.runtime, self.env)
            assert result == 4.2
        assert "小数" in str(e.value)


    def test_parse_variable(self):
        """変数のパースをテスト"""
        expression = self.parser.parse_expression('x')
        self.env['x'] = 1
        result = expression.evaluate(self.runtime, self.env)
        assert result == 1

    def test_parse_japanese_variable(self):
        """日本語の変数名のパースをテスト"""
        expression = self.parser.parse_expression('変数')
        self.env['変数'] = 1
        result = expression.evaluate(self.runtime, self.env)
        assert result == 1

    def test_parse_japanese_variable2(self):
        """日本語の変数名のパースをテスト"""
        self.parser.variables.append('近い要素がある')
        expression = self.parser.parse_expression('近い要素がある')
        self.env['近い要素がある'] = 1
        result = expression.evaluate(self.runtime, self.env)
        assert result == 1

    def test_parse_japanese_variable3(self):
        """日本語の変数名のパースをテスト"""
        self.parser.variables.append('残りの回数')
        expression = self.parser.parse_expression('残りの回数')
        self.env['残りの回数'] = 1
        result = expression.evaluate(self.runtime, self.env)
        assert result == 1

    def test_parse_japanese_variable4(self):
        """日本語の変数名のパースをテスト"""
        expression = self.parser.parse_expression('配列の末尾に要素を追加する')
        self.env['配列'] = 1
        result = expression.evaluate(self.runtime, self.env)
        assert result == 1

    def test_parse_japanese_variable5(self):
        """日本語の変数名のパースをテスト"""
        expression = self.parser.parse_expression('文字列ROT13')
        self.env['文字列ROT13'] = 1
        result = expression.evaluate(self.runtime, self.env)
        assert result == 1

    def test_parse_japanese_variable5(self):
        """日本語の変数名のパースをテスト"""
        expression = self.parser.parse_expression('差分に対し')
        self.env['差分'] = 1
        result = expression.evaluate(self.runtime, self.env)
        assert result == 1

    def test_parse_variable_index(self):
        """変数のインデックスアクセスのパースをテスト"""
        expression = self.parser.parse_expression('x[0]')
        self.env['x'] = [1, 2, 3]
        self.env = self.runtime.transform_array(self.env)
        result = expression.evaluate(self.runtime, self.env)
        assert result == 1

    def test_parse_variable_index_error(self):
        """変数のインデックスアクセスのパースをテスト"""
        with pytest.raises(SyntaxError) as e:
            expression = self.parser.parse_expression('x[3]')
            self.env['x'] = [1, 2, 3]
            self.env = self.runtime.transform_array(self.env)
            result = expression.evaluate(self.runtime, self.env)
        print(e.value)
        assert "配列" in str(e.value)

    def test_parse_japanese_variable_index(self):
        """日本語の変数名のパースをテスト"""
        expression = self.parser.parse_expression('変数[0]')
        self.env['変数'] = [1, 2, 3]
        self.env = self.runtime.transform_array(self.env)
        result = expression.evaluate(self.runtime, self.env)
        assert result == 1

    def test_parse_variable_index2(self):
        """変数のインデックスアクセスのパースをテスト"""
        expression = self.parser.parse_expression('x[1][1]')
        self.env['x'] = [[1, 2], [3, 4]]
        self.env = self.runtime.transform_array(self.env)
        result = expression.evaluate(self.runtime, self.env)
        assert result == 4

    def test_parse_japanese_variable_index2(self):
        """日本語の変数名のパースをテスト"""
        expression = self.parser.parse_expression('変数[1][1]')
        self.env['変数'] = [[1, 2], [3, 4]]
        self.env = self.runtime.transform_array(self.env)
        result = expression.evaluate(self.runtime, self.env)
        assert result == 4

    def test_parse_len(self):
        """絶対値のパースをテスト"""
        expression = self.parser.parse_expression('|x|')
        self.env['x'] = [1, 2]
        self.env = self.runtime.transform_array(self.env)
        result = expression.evaluate(self.runtime, self.env)
        assert result == 2

    def test_parse_string(self):
        """文字列リテラル '"AB"' のパースをテスト"""
        expression = self.parser.parse_expression('"AB"')
        result = expression.evaluate(self.runtime, self.env)
        assert result.elements == [65, 66]

    def test_parse_zenkaku_string(self):
        """文字列リテラル '“AB”' のパースをテスト"""
        expression = self.parser.parse_expression('“AB”') #変換ミス防止のため全角引用符
        result = expression.evaluate(self.runtime, self.env)
        assert result.elements == [65, 66]

    def test_parse_string_literal_empty(self):
        """空文字列のパースをテスト"""
        expression = self.parser.parse_expression('""')
        result = expression.evaluate(self.runtime, self.env)
        assert result.elements == []

    def test_parse_string_literal_unclosed(self):
        """未閉じ文字列のパースをテスト"""
        with pytest.raises(SyntaxError) as e:
            expression = self.parser.parse_expression('"AB')
            result = expression.evaluate(self.runtime, self.env)
        print(e.value)
        assert "閉" in str(e.value)

    def test_parse_array_literal(self):
        """配列リテラルのパースをテスト"""
        expression = self.parser.parse_expression('[1, 2, 3]')
        result = expression.evaluate(self.runtime, self.env)
        assert result.elements == [1, 2, 3]

    def test_parse_array_literal_trailing_comma(self):
        """配列リテラルのパースをテスト"""
        expression = self.parser.parse_expression('[1, 2, 3,]')
        result = expression.evaluate(self.runtime, self.env)
        assert result.elements == [1, 2, 3]

    def test_parse_array_literal_no_comma(self):
        """未閉じ配列リテラルのパースをテスト"""
        with pytest.raises(SyntaxError) as e:
            expression = self.parser.parse_expression('[1, 2 3]')
            result = expression.evaluate(self.runtime, self.env)
        print(e.value)
        assert "閉" in str(e.value)

    def test_parse_array_literal_unclosed(self):
        """未閉じ配列リテラルのパースをテスト"""
        with pytest.raises(SyntaxError) as e:
            expression = self.parser.parse_expression('[1, 2, 3')
            result = expression.evaluate(self.runtime, self.env)
        print(e.value)
        assert "閉" in str(e.value)

    def test_parse_array_literal_2d(self):
        """2次元配列のパースをテスト"""
        expression = self.parser.parse_expression('[[1, 2], [3, 4]]')
        result = expression.evaluate(self.runtime, self.env)
        assert result.elements[0].elements == [1, 2]
        assert result.elements[1].elements == [3, 4]

    def test_parse_array_literal_string(self):
        """文字列配列のパースをテスト"""
        expression = self.parser.parse_expression('["AB", "CD"]')
        result = expression.evaluate(self.runtime, self.env)
        assert result.elements[0].elements == [65, 66]
        assert result.elements[1].elements == [67, 68]

    def test_parse_assignment(self):
        """代入文のパースをテスト"""
        statement = self.parser.parse_statement('x = 1')
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 1

    def test_parse_assignment_ja(self):
        """代入文のパースをテスト"""
        statement = self.parser.parse_statement('変数 = 1')
        statement.evaluate(self.runtime, self.env)
        assert self.env['変数'] == 1

    def test_parse_assignment_1(self):
        """代入文のパースをテスト"""
        statement = self.parser.parse_statement('残りの回数 = 1')
        statement.evaluate(self.runtime, self.env)
        assert self.env['残りの回数'] == 1

    def test_parse_assignment_2(self):
        """代入文のパースをテスト"""
        statement = self.parser.parse_statement('近い要素がある = 1')
        statement.evaluate(self.runtime, self.env)
        assert self.env['近い要素がある'] == 1

    def test_parse_assignment_error(self):
        """代入文のパースをテスト"""
        with pytest.raises(SyntaxError) as e:
            statement = self.parser.parse_statement('x = ')
            statement.evaluate(self.runtime, self.env)
        assert "忘" in str(e.value)


    def test_parse_japanese_assignment(self):
        """代入文のパースをテスト"""
        with pytest.raises(SyntaxError) as e:
             statement = self.parser.parse_statement('xを1とする')
             statement.evaluate(self.runtime, self.env)
        assert "知らない" in str(e.value) or "増やす" in str(e.value)

    def test_parse_japanese_assignment_ja(self):
        """代入文のパースをテスト"""
        with pytest.raises(SyntaxError) as e:
             statement = self.parser.parse_statement('変数を1とする')
             statement.evaluate(self.runtime, self.env)
        assert "知らない" in str(e.value) or "増やす" in str(e.value)

    def test_parse_assignment_array(self):
        """代入文のパースをテスト"""
        statement = self.parser.parse_statement('x[0] = 1')
        self.env['x'] = [0]
        self.env = self.runtime.transform_array(self.env)
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'].elements == [1]

    def test_parse_assignment_array_ja(self):
        """代入文のパースをテスト"""
        statement = self.parser.parse_statement('変数[0] = 1')
        self.env['変数'] = [0]
        self.env = self.runtime.transform_array(self.env)
        statement.evaluate(self.runtime, self.env)
        assert self.env['変数'].elements == [1]

    # def test_parse_japanese_assignment_array(self):
    #     """代入文のパースをテスト"""
    #     statement = self.parser.parse_statement('x[0]を1とする')
    #     self.env['x'] = NanakoArray([0])
    #     self.env = self.runtime.transform_array(self.env)
    #     statement.evaluate(self.runtime, self.env)
    #     assert self.env['x'].elements == [1]

    # def test_parse_japanese_assignment_array_ja(self):
    #     """代入文のパースをテスト"""
    #     statement = self.parser.parse_statement('変数[0]を1とする')
    #     self.env['変数'] = [0]
    #     self.env = self.runtime.transform_array(self.env)
    #     statement.evaluate(self.runtime, self.env)
    #     assert self.env['変数'].elements == [1]

    def test_parse_increment(self):
        """インクリメントのパースをテスト"""
        statement = self.parser.parse_statement('xを増やす')
        self.env['x'] = 1
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 2

    def test_parse_decrement(self):
        """デクリメントのパースをテスト"""
        statement = self.parser.parse_statement('xを減らす')
        self.env['x'] = 1
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 0

    def test_parse_increment_ja(self):
        """インクリメントのパースをテスト"""
        statement = self.parser.parse_statement('変数を増やす')
        self.env['変数'] = 1
        statement.evaluate(self.runtime, self.env)
        assert self.env['変数'] == 2

    def test_parse_decrement_ja(self):
        """デクリメントのパースをテスト"""
        statement = self.parser.parse_statement('変数を減らす')
        self.env['変数'] = 1
        statement.evaluate(self.runtime, self.env)
        assert self.env['変数'] == 0

    def test_parse_increment_element(self):
        """インクリメントのパースをテスト"""
        statement = self.parser.parse_statement('x[0]を増やす')
        self.env['x'] = [1, 1]
        self.env = self.runtime.transform_array(self.env)
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'].elements[0] == 2

    def test_parse_decrement_element(self):
        """デクリメントのパースをテスト"""
        statement = self.parser.parse_statement('x[0]を減らす')
        self.env['x'] = [1, 1]
        self.env = self.runtime.transform_array(self.env)
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'].elements[0] == 0

    def test_parse_increment_array(self):
        """インクリメントのパースをテスト"""
        with pytest.raises(SyntaxError) as e:
            statement = self.parser.parse_statement('xを増やす')
            self.env['x'] = [1, 1]
            statement.evaluate(self.runtime, self.env)
        assert "数" in str(e.value)

    def test_parse_decrement_array(self):
        """デクリメントのパースをテスト"""
        with pytest.raises(SyntaxError) as e:
            statement = self.parser.parse_statement('xを減らす')
            self.env['x'] = [1, 1]
            statement.evaluate(self.runtime, self.env)
        assert "数" in str(e.value)

    def test_parse_append_number(self):
        """アペンドのパースをテスト"""
        with pytest.raises(SyntaxError) as e:
            statement = self.parser.parse_statement('xの末尾に1を追加する')
            self.env['x'] = 1
            statement.evaluate(self.runtime, self.env)
        assert "配列" in str(e.value)

    def test_parse_append_array(self):
        """アペンドのパースをテスト"""
        statement = self.parser.parse_statement('xの末尾に1を追加する')
        self.env['x'] = []
        self.env = self.runtime.transform_array(self.env)
        statement.evaluate(self.runtime, self.env)
        assert len(self.env['x'].elements) == 1
        assert self.env['x'].elements[0] == 1

    def test_parse_if_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0ならば、 {
                x=1
            }''')
        self.env['x'] = 0
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 1

    def test_parse_if_statement_empty(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0ならば、 {
            }''')
        assert len(statement.then_block.statements) == 0
        assert statement.else_block is None
        self.env['x'] = 0
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 0

    def test_parse_if_else_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0ならば、 {
                x=1
            } そうでなければ、 {
                x=2
            }''')
        self.env['x'] = 0
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 1

    def test_parse_if_false_else_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0ならば、 {
                x=1
            } 
            そうでなければ、 {
                x=2
            }''')
        self.env['x'] = 1
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 2

    def test_parse_if_not_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0以外ならば、 {
                x=0
            }''')
        self.env['x'] = 1
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 0

    def test_parse_if_gte_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0以上ならば、 {
                x=-1
            }''')
        self.env['x'] = 0
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == -1

    def test_parse_if_gt_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0より大きいならば、 {
                x=-1
            }''')
        self.env['x'] = 1
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == -1

    def test_parse_if_gt_false_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0より大きいならば、 {
                x=-1
            }''')
        self.env['x'] = 0
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 0

    def test_parse_if_lte_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0以下ならば、 {
                x=1
            }''')
        self.env['x'] = 0
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 1

    def test_parse_if_lt_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0より小さいならば、 {
                x=1
            }''')
        self.env['x'] = -1
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 1

    def test_parse_if_lt_false_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0より小さいならば、 {
                x=1
            }''')
        self.env['x'] = 0
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 0

    def test_parse_if_lt2_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0未満ならば、 {
                x=1
            }''')
        self.env['x'] = -1
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 1

    def test_parse_if_lt2_false_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0未満ならば、 {
                x=1
            }''')
        self.env['x'] = 0
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 0

    def test_parse_return(self):
        """リターン文のパースをテスト"""
        statement = self.parser.parse_statement("xが答え")
        with pytest.raises(RuntimeError) as e:
            self.env['x'] = 1
            statement.evaluate(self.runtime, self.env)
        assert e.value.value == 1

    def test_parse_expression(self):
        """リターン文のパースをテスト"""
        statement = self.parser.parse_statement("x")
        self.env['x'] = 1
        result = statement.evaluate(self.runtime, self.env)
        assert result == 1

    def test_parse_statement_error(self):
        """不正な構文をテスト"""
        with pytest.raises(SyntaxError) as e:
            statement = self.parser.parse_statement("x?")
            self.env['x'] = 1
            statement.evaluate(self.runtime, self.env)
        assert "ななこ" in str(e.value)


    def test_parse_doctest_pass(self):
        """doctest"""
        statement = self.parser.parse_statement('''
            >>> x
            0
            ''')
        self.env['x'] = 0
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 0

    def test_parse_doctest_fail(self):
        """doctest"""
        statement = self.parser.parse_statement('''
            >>> x
            0
            ''')
        with pytest.raises(SyntaxError) as e:
            self.env['x'] = 1
            statement.evaluate(self.runtime, self.env)
            assert self.env['x'] == 1
        assert "失敗" in str(e.value)

class TestNanako:
    """Nanako のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される初期化"""
        self.parser = NanakoParser()
        self.runtime = NanakoRuntime()
        self.env = {}


    def test_function(self):
        """ループのパースをテスト"""
        program = self.parser.parse('''
            y = 0
            ID = 入力 x に対して {
                xが答え
            }
            y = ID(5)
            ''')
        self.env = {}
        program.evaluate(self.runtime, self.env)
        self.env['ID'] = None
        print(self.env)
        assert self.env['y'] == 5

    def test_infinite_loop(self):
        """無限関数のテスト"""
        program = self.parser.parse('''
            y = 0
            ?回、くり返す {
                yを増やす
            }
            ''')
        with pytest.raises(SyntaxError) as e:
            self.env = {}
            self.runtime.start(timeout=1)
            program.evaluate(self.runtime, self.env)
        print(e.value)
        assert "タイムアウト" in str(e.value)

    def test_addition_function(self):
        """足し算関数のテスト"""
        program = self.parser.parse('''
足し算 = 入力 X, Y に対し {
    Y回、くり返す {
        Xを増やす
    }
    Xが答え
}

# 次はどうなるでしょうか？
X = 足し算(10, 5)

# 次はどうなるのでしょうか？
Y = 足し算(足し算(1, 2), 3)
            ''')
        self.env = {}
        self.runtime.start(timeout=1)
        program.evaluate(self.runtime, self.env)
        assert self.env['X'] == 15
        assert self.env['Y'] == 6

    def test_abs_function(self):
        """絶対値関数のテスト"""
        program = self.parser.parse('''
絶対値 = 入力 X に対し {
    もしXが0より小さいならば、{
        -Xが答え
    }
    そうでなければ {
        Xが答え
    }
}

# 次はどうなるでしょうか？
X = 絶対値(-5)
Y = 絶対値(5)''')
        self.env = {}
        self.runtime.start(timeout=1)
        program.evaluate(self.runtime, self.env)
        assert self.env['X'] == 5
        assert self.env['Y'] == 5

    def test_mod_function(self):
        """剰余関数のテスト"""
        program = self.parser.parse('''
あまり = 入力 X, Y に対し {
    X回、くり返す {
        R = 0
        Y回、くり返す {
            もしXが0ならば、{
                Rが答え
            }
            Rを増やす
            Xを減らす
        }
    }
}

# 次はどうなるでしょうか？
X = あまり(60, 48)
Y = あまり(48, 12)
''')
        self.env = {}
        self.runtime.start(timeout=1)
        program.evaluate(self.runtime, self.env)
        assert self.env['X'] == 12
        assert self.env['Y'] == 0

    def test_gcd_function(self):
        """最大公約数関数のテスト"""
        program = self.parser.parse('''
# GCD

最大公約数 = 入力 X, Y に対し {
    Y回、くり返す {
        R = あまり(X, Y)
        もしRが0ならば、{
            Yが答え
        }
        X = Y
        Y = R
    }
}
                                    
あまり = 入力 X, Y に対し {
    X回、くり返す {
        R = 0
        Y回、くり返す {
            もしXが0ならば、{
                Rが答え
            }
            Rを増やす
            Xを減らす
        }
    }
}

# 次はどうなるでしょうか？
X = 最大公約数(60, 48)
''')
        self.env = {}
        self.runtime.start(timeout=1)
        program.evaluate(self.runtime, self.env)
        assert self.env['X'] == 12

    def test_recursive_function(self):
        """再帰関数のテスト"""
        program = self.parser.parse('''
# 再帰関数による総和

足し算 = 入力 X, Y に対し {
    Y回、くり返す {
        Xを増やす
    }
    Xが答え
}

減らす = 入力 X に対し {
    Xを減らす
    Xが答え
}
                                    
総和 = 入力 n に対し {
    もし n が 1 ならば、{
        1が答え
    }
    そうでなければ、{
        足し算(総和(減らす(n)), n)が答え
    }
}

X = 総和(4)
''')
        self.env = {}
        self.runtime.start(timeout=1)
        program.evaluate(self.runtime, self.env)
        assert self.env['X'] == 10

    def test_sum_function(self):
        """合計のテスト"""
        program = self.parser.parse('''
# 数列の合計

足し算 = 入力 X, Y に対し {
    Y回、くり返す {
        Xを増やす
    }
    Xが答え
}

合計 = 入力 数列 に対し {
    i = 0
    sum = 0
    |数列|回、くり返す {
        sum = 足し算(sum, 数列[i])
        iを増やす
    }
    sumが答え
}

X = 合計([1, 2, 3, 4, 5])
''')
        self.env = {}
        self.runtime.start(timeout=1)
        program.evaluate(self.runtime, self.env)
        assert self.env['X'] == 15


class TestNanakoEmitCode:
    """Nanako のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される初期化"""
        self.parser = NanakoParser()
        self.runtime = NanakoRuntime()
        self.env = {}

    def test_emit_js(self):
        """コード変換のテスト"""
        program = self.parser.parse(EMIT_NANAKO)
        code = program.emit("js", "|")
        print(code)
        assert code == EMIT_JS

    def test_emit_py(self):
        """コード変換のテスト"""
        program = self.parser.parse(EMIT_NANAKO)
        code = program.emit("py", "|")
        print(code)
        assert code == EMIT_PYTHON

EMIT_NANAKO = """
合計 = 入力 数列 に対し {
    i = 0
    sum = 0
    buf = []
    |数列|回、くり返す {
        sum = 足し算(sum, 数列[i])
        もしsumが10より大きいならば、{
            buf[0] = 数列[i]
        }
        そうでなければ、{
            bufの末尾に数列[i]を追加する
        }
        ?回くり返す {
            sum = -sum
        }
        iを増やす
    }
    sumが答え
}
                                    
>>> 合計([1, 2, 3, 4, 5])
15
"""

EMIT_JS = """\
|合計 = function (数列) {
|    i = 0;
|    sum = 0;
|    buf = [];
|    for(var i1 = 0; i1 < (数列).length; i1++) {
|        sum = 足し算(sum, 数列[i]);
|        if(sum > 10) {
|            buf[0] = 数列[i];
|        }
|        else {
|            buf.push(数列[i]);
|        }
|        while(true) {
|            sum = -sum;
|        }
|        i += 1;
|    }
|    return sum;
|};
|console.assert(合計([1, 2, 3, 4, 5]) == 15);"""

EMIT_PYTHON = """\
|def 合計(数列):
|    i = 0
|    sum = 0
|    buf = []
|    for _ in range(len(数列)):
|        sum = 足し算(sum, 数列[i])
|        if sum > 10:
|            buf[0] = 数列[i]
|        else:
|            buf.append(数列[i])
|        while True:
|            sum = -sum
|        i += 1
|    return sum
|assert (合計([1, 2, 3, 4, 5]) == 15)"""

class TestNanakoExamples:
    """examples/*.nanako のテストクラス

    このテストクラスは、examplesディレクトリ内のすべての.nanakoファイルが
    正常にパース・実行できることを検証します。

    テストの種類:
    1. test_all_examples_parse_successfully: すべてのファイルがパース可能か一括確認
    2. test_all_examples_execute_without_error: すべてのファイルが実行可能か一括確認
    3. test_individual_example: 各ファイルを個別にテスト（失敗箇所の特定が容易）

    既知のエラーがあるファイルは KNOWN_ERRORS に登録し、スキップします。
    これにより、新規エラーと既知のエラーを区別できます。
    """

    # 既知のエラーがあるファイル（修正予定）
    # サンプルファイルのバグや未実装機能により一時的にエラーになるファイル
    KNOWN_ERRORS = {
        # 全てのサンプルファイルが正常に動作するようになりました
    }

    def setup_method(self):
        """各テストメソッドの前に実行される初期化"""
        self.parser = NanakoParser()
        self.runtime = NanakoRuntime()

    def get_example_files(self):
        """examplesディレクトリのすべての.nanakoファイルを取得"""
        # test_nanako.pyの親ディレクトリからexamplesを探す
        test_dir = Path(__file__).parent
        project_root = test_dir.parent
        examples_dir = project_root / "examples"

        if not examples_dir.exists():
            return []

        # すべての.nanakoファイルを取得してソート
        example_files = sorted(examples_dir.glob("*.nanako"))
        return example_files

    def test_all_examples_parse_successfully(self):
        """すべてのexampleファイルがパースできることを確認"""
        example_files = self.get_example_files()

        if len(example_files) == 0:
            pytest.skip("No example files found")

        errors = []
        known_errors = []

        for filepath in example_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    code = f.read()
                # パースのみ実行
                program = self.parser.parse(code)
                assert program is not None, f"{filepath.name}: プログラムがNoneです"
            except Exception as e:
                error_msg = f"{filepath.name}: {str(e)[:100]}"
                if filepath.name in self.KNOWN_ERRORS:
                    known_errors.append(f"{error_msg} (既知のエラー: {self.KNOWN_ERRORS[filepath.name]})")
                else:
                    errors.append(error_msg)

        # 新規エラーのみ失敗とする
        if errors:
            pytest.fail(f"以下のファイルでパースエラーが発生しました:\n" + "\n".join(errors))

        # 既知のエラーは警告として表示
        if known_errors:
            print(f"\n既知のエラー（修正予定）:\n" + "\n".join(known_errors))

    def test_all_examples_execute_without_error(self):
        """すべてのexampleファイルがエラーなく実行できることを確認（既知のエラーは除外）"""
        example_files = self.get_example_files()

        if len(example_files) == 0:
            pytest.skip("No example files found")

        errors = []
        known_errors = []
        successful = []

        for filepath in example_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    code = f.read()

                # 新しいruntimeとenvで実行
                runtime = NanakoRuntime()
                env = {}
                runtime.exec(code, env, timeout=5)
                successful.append(filepath.name)

            except Exception as e:
                error_msg = f"{filepath.name}: {str(e)[:100]}"
                if filepath.name in self.KNOWN_ERRORS:
                    known_errors.append(f"{error_msg} (既知: {self.KNOWN_ERRORS[filepath.name]})")
                else:
                    errors.append(error_msg)

        # 統計情報を表示
        print(f"\n実行成功: {len(successful)}/{len(example_files)} ファイル")

        # 新規エラーのみ失敗とする
        if errors:
            pytest.fail(f"以下のファイルで実行エラーが発生しました:\n" + "\n".join(errors))

        # 既知のエラーは警告として表示
        if known_errors:
            print(f"既知のエラー（修正予定）: {len(known_errors)}件")

    @pytest.mark.parametrize("example_file", [
        pytest.param(f, id=f.name)
        for f in sorted(Path(__file__).parent.parent.joinpath("examples").glob("*.nanako"))
        if Path(__file__).parent.parent.joinpath("examples").exists()
    ])
    def test_individual_example(self, example_file):
        """個別のexampleファイルをテスト（失敗したファイルを特定しやすくする）"""
        # 既知のエラーはスキップ
        if example_file.name in self.KNOWN_ERRORS:
            pytest.skip(f"既知のエラー: {self.KNOWN_ERRORS[example_file.name]}")

        with open(example_file, 'r', encoding='utf-8') as f:
            code = f.read()

        # パース
        program = self.parser.parse(code)
        assert program is not None, f"パースに失敗しました"

        # 実行
        runtime = NanakoRuntime()
        env = {}
        runtime.exec(code, env, timeout=5)

        # 実行が完了すればOK（特定の結果を期待しない）


class TestNanakoCLI:
    """nanako CLIコマンドのテストクラス

    setup.pyのconsole_scriptsをインストールせずにCLI機能をテストします。
    python -m nanako.nanako_cli の形式で直接実行してテストします。
    """

    def get_nanako_command(self):
        """nanakoコマンドのパスを取得"""
        # プロジェクトルートを取得
        test_dir = Path(__file__).parent
        project_root = test_dir.parent

        # python -m nanako.nanako_cli として実行
        return ["python3", "-m", "nanako.nanako_cli"]

    def test_cli_runs_without_args(self):
        """引数なしで実行（インタラクティブモード起動確認）"""
        import subprocess

        cmd = self.get_nanako_command()

        # インタラクティブモードは標準入力を期待するので、
        # quitを送って即座に終了させる
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = proc.communicate(input="quit\n", timeout=2)

        # エラーなく終了することを確認
        assert proc.returncode == 0 or "Nanako" in stdout or "version" in stdout

    def test_cli_runs_example_file(self):
        """exampleファイルを実行できることを確認"""
        import subprocess

        test_dir = Path(__file__).parent
        project_root = test_dir.parent
        example_file = project_root / "examples" / "01basic.nanako"

        if not example_file.exists():
            pytest.skip("Example file not found")

        cmd = self.get_nanako_command() + [str(example_file)]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        # 正常終了を確認
        assert proc.returncode == 0, f"stderr: {proc.stderr}"

        # JSONフォーマットの出力があることを確認
        assert "{" in proc.stdout and "}" in proc.stdout

    def test_cli_with_csv_file(self):
        """CSVファイルを読み込んで実行できることを確認"""
        import subprocess

        test_dir = Path(__file__).parent
        project_root = test_dir.parent
        csv_file = project_root / "data.csv"

        if not csv_file.exists():
            pytest.skip("CSV file not found")

        cmd = self.get_nanako_command() + [str(csv_file)]

        # Popenを使用してstdinを制御
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # stdin に quit を送信
        stdout, stderr = proc.communicate(input="quit\n", timeout=5)

        # 正常終了を確認（CSVを読み込んでインタラクティブモードに入る）
        assert proc.returncode == 0 or "Nanako" in stdout or "version" in stdout

    def test_run_nanako_main_function(self):
        """nanako_cli.mainを直接呼び出してテスト（モジュールAPIとして）"""
        import sys
        from io import StringIO
        from nanako.nanako_cli import run_file

        test_dir = Path(__file__).parent
        project_root = test_dir.parent
        example_file = project_root / "examples" / "01basic.nanako"

        if not example_file.exists():
            pytest.skip("Example file not found")

        # run_file関数を直接呼び出し
        env = {}
        result_env = run_file(str(example_file), env)

        # 実行結果の環境に変数が設定されていることを確認
        assert isinstance(result_env, dict)
        assert "x" in result_env or "y" in result_env

    def test_csv_loader_function(self):
        """CSV読み込み関数を直接テスト"""
        from nanako.nanako_cli import read_csv_as_dict_of_lists

        test_dir = Path(__file__).parent
        project_root = test_dir.parent
        csv_file = project_root / "data.csv"

        if not csv_file.exists():
            pytest.skip("CSV file not found")

        # CSV読み込み関数を直接呼び出し
        result = read_csv_as_dict_of_lists(str(csv_file))

        # 辞書が返されることを確認
        assert isinstance(result, dict)

        # 各カラムがリストになっていることを確認
        for key, value in result.items():
            assert isinstance(value, list)

    def test_json_loader_function(self):
        """JSON読み込み関数を直接テスト"""
        import tempfile
        import json
        from nanako.nanako_cli import load_env_from_json

        # テスト用のJSONファイルを作成
        test_data = {
            "x": 10,
            "name": "test",
            "list": [1, 2, 3]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name

        try:
            # JSON読み込み関数を直接呼び出し
            result = load_env_from_json(temp_file)

            # データが正しく読み込まれることを確認
            assert isinstance(result, dict)
            assert "x" in result
            assert result["x"] == 10
        finally:
            # 一時ファイルを削除
            import os
            os.unlink(temp_file)

    def test_cli_error_displays_filename(self):
        """エラー発生時にファイル名が表示されることを確認"""
        import subprocess
        import tempfile

        # エラーを起こすNanakoコードを含む一時ファイルを作成
        test_code = """# テスト用エラーファイル
y
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nanako', delete=False) as f:
            f.write(test_code)
            temp_file = f.name

        try:
            cmd = self.get_nanako_command() + [temp_file]

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            # エラーで終了することを確認
            assert proc.returncode != 0

            # エラー出力にファイル名が含まれることを確認
            stderr = proc.stderr
            assert temp_file in stderr or "test_" in stderr, f"ファイル名が表示されていません: {stderr}"

            # NanakoErrorの場合は行番号も表示されることを確認
            if "知らない変数" in stderr:
                assert "行" in stderr, f"行番号が表示されていません: {stderr}"
                assert "列" in stderr, f"列番号が表示されていません: {stderr}"

        finally:
            # 一時ファイルを削除
            import os
            os.unlink(temp_file)

    def test_cli_python_error_displays_filename(self):
        """Python例外発生時にファイル名が表示されることを確認"""
        import subprocess
        import tempfile

        # 一時的なエラーファイルを作成
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.nanako', delete=False, encoding='utf-8')
        error_code = """
# 存在しない関数を呼び出してエラーを発生させる
結果 = 存在しない関数(123)
"""
        temp_file.write(error_code)
        temp_file.close()

        try:
            cmd = self.get_nanako_command() + [temp_file.name]

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            # エラーで終了することを確認
            assert proc.returncode != 0

            # エラー出力にファイル名が含まれることを確認
            stderr = proc.stderr
            assert temp_file.name in stderr or os.path.basename(temp_file.name) in stderr, f"ファイル名が表示されていません: {stderr}"
            assert "エラーが発生しました" in stderr, f"エラーメッセージが表示されていません: {stderr}"
        finally:
            os.unlink(temp_file.name)

    def test_cli_version_display(self):
        """--versionフラグでバージョンが表示されることを確認"""
        import subprocess

        cmd = self.get_nanako_command() + ["--version"]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        # 正常終了を確認
        assert proc.returncode == 0

        # バージョン情報が表示されることを確認
        output = proc.stdout
        assert "Nanako" in output, f"バージョン情報が表示されていません: {output}"
        assert "version" in output, f"バージョン番号が表示されていません: {output}"

    def test_cli_help_display(self):
        """--helpフラグでヘルプが表示されることを確認"""
        import subprocess

        cmd = self.get_nanako_command() + ["--help"]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        # 正常終了を確認
        assert proc.returncode == 0

        # ヘルプ情報が表示されることを確認
        output = proc.stdout
        assert "使用方法" in output, f"使用方法が表示されていません: {output}"
        assert "オプション" in output, f"オプションが表示されていません: {output}"
        assert "version" in output, f"バージョン情報が含まれていません: {output}"


if __name__ == '__main__':
    # pytest を直接実行
    pytest.main([__file__, "-v"])
    

