import pytest
from nanako import NanakoParser, NanakoRuntime, ReturnBreakException, NanakoError

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

    def test_parse_variable_index(self):
        """変数のインデックスアクセスのパースをテスト"""
        expression = self.parser.parse_expression('x[0]')
        self.env['x'] = [1, 2, 3]
        result = expression.evaluate(self.runtime, self.env)
        assert result == 1

    def test_parse_variable_index_error(self):
        """変数のインデックスアクセスのパースをテスト"""
        with pytest.raises(SyntaxError) as e:
            expression = self.parser.parse_expression('x[3]')
            self.env['x'] = [1, 2, 3]
            result = expression.evaluate(self.runtime, self.env)
        print(e.value)
        assert "配列" in str(e.value)

    def test_parse_japanese_variable_index(self):
        """日本語の変数名のパースをテスト"""
        expression = self.parser.parse_expression('変数[0]')
        self.env['変数'] = [1, 2, 3]
        result = expression.evaluate(self.runtime, self.env)
        assert result == 1

    def test_parse_variable_index2(self):
        """変数のインデックスアクセスのパースをテスト"""
        expression = self.parser.parse_expression('x[1][1]')
        self.env['x'] = [[1, 2], [3, 4]]
        result = expression.evaluate(self.runtime, self.env)
        assert result == 4

    def test_parse_japanese_variable_index2(self):
        """日本語の変数名のパースをテスト"""
        expression = self.parser.parse_expression('変数[1][1]')
        self.env['変数'] = [[1, 2], [3, 4]]
        result = expression.evaluate(self.runtime, self.env)
        assert result == 4

    def test_parse_abs(self):
        """絶対値のパースをテスト"""
        expression = self.parser.parse_expression('|x|')
        self.env['x'] = -1
        result = expression.evaluate(self.runtime, self.env)
        assert result == 1

    def test_parse_abs_list(self):
        """絶対値のパースをテスト"""
        expression = self.parser.parse_expression('|x|')
        self.env['x'] = [1, 2]
        result = expression.evaluate(self.runtime, self.env)
        assert result == 2

    def test_parse_string(self):
        """文字列リテラル '"AB"' のパースをテスト"""
        expression = self.parser.parse_expression('"AB"')
        result = expression.evaluate(self.runtime, self.env)
        assert result == [65, 66]

    def test_parse_zenkaku_string(self):
        """文字列リテラル '“AB”' のパースをテスト"""
        expression = self.parser.parse_expression('“AB”') #変換ミス防止のため全角引用符
        result = expression.evaluate(self.runtime, self.env)
        assert result == [65, 66]

    def test_parse_string_literal_empty(self):
        """空文字列のパースをテスト"""
        expression = self.parser.parse_expression('""')
        result = expression.evaluate(self.runtime, self.env)
        assert result == []

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
        assert result == [1, 2, 3]

    def test_parse_array_literal_trailing_comma(self):
        """配列リテラルのパースをテスト"""
        expression = self.parser.parse_expression('[1, 2, 3,]')
        result = expression.evaluate(self.runtime, self.env)
        assert result == [1, 2, 3]

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
        assert result == [[1, 2], [3, 4]]

    def test_parse_array_literal_string(self):
        """文字列配列のパースをテスト"""
        expression = self.parser.parse_expression('["AB", "CD"]')
        result = expression.evaluate(self.runtime, self.env)
        assert result == [[65, 66], [67, 68]]

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

    def test_parse_assignment_error(self):
        """代入文のパースをテスト"""
        with pytest.raises(SyntaxError) as e:
            statement = self.parser.parse_statement('x = ')
            statement.evaluate(self.runtime, self.env)
        assert "忘" in str(e.value)


    def test_parse_japanese_assignment(self):
        """代入文のパースをテスト"""
        statement = self.parser.parse_statement('xを1とする')
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 1

    def test_parse_japanese_assignment_ja(self):
        """代入文のパースをテスト"""
        statement = self.parser.parse_statement('変数を1とする')
        statement.evaluate(self.runtime, self.env)
        assert self.env['変数'] == 1

    def test_parse_assignment_array(self):
        """代入文のパースをテスト"""
        statement = self.parser.parse_statement('x[0] = 1')
        self.env['x'] = [0]
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == [1]

    def test_parse_assignment_array_ja(self):
        """代入文のパースをテスト"""
        statement = self.parser.parse_statement('変数[0] = 1')
        self.env['変数'] = [0]
        statement.evaluate(self.runtime, self.env)
        assert self.env['変数'] == [1]

    def test_parse_japanese_assignment_array(self):
        """代入文のパースをテスト"""
        statement = self.parser.parse_statement('x[0]を1とする')
        self.env['x'] = [0]
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == [1]

    def test_parse_japanese_assignment_array_ja(self):
        """代入文のパースをテスト"""
        statement = self.parser.parse_statement('変数[0]を1とする')
        self.env['変数'] = [0]
        statement.evaluate(self.runtime, self.env)
        assert self.env['変数'] == [1]

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
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == [2, 1]

    def test_parse_decrement_element(self):
        """デクリメントのパースをテスト"""
        statement = self.parser.parse_statement('x[0]を減らす')
        self.env['x'] = [1, 1]
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == [0, 1]

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

    def test_parse_if_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0ならば、 {
                xを1とする
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
                xを1とする
            } そうでなければ、 {
                xを2とする
            }''')
        self.env['x'] = 0
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 1

    def test_parse_if_false_else_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0ならば、 {
                xを1とする
            } 
            そうでなければ、 {
                xを2とする
            }''')
        self.env['x'] = 1
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 2

    def test_parse_if_not_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0以外ならば、 {
                xを0とする
            }''')
        self.env['x'] = 1
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 0

    def test_parse_if_gte_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0以上ならば、 {
                xを-1とする
            }''')
        self.env['x'] = 0
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == -1

    def test_parse_if_gt_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0より大きいならば、 {
                xを-1とする
            }''')
        self.env['x'] = 1
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == -1

    def test_parse_if_gt_false_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0より大きいならば、 {
                xを-1とする
            }''')
        self.env['x'] = 0
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 0

    def test_parse_if_lte_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0以下ならば、 {
                xを1とする
            }''')
        self.env['x'] = 0
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 1

    def test_parse_if_lt_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0より小さいならば、 {
                xを1とする
            }''')
        self.env['x'] = -1
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 1

    def test_parse_if_lt_false_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0より小さいならば、 {
                xを1とする
            }''')
        self.env['x'] = 0
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 0

    def test_parse_if_lt2_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0未満ならば、 {
                xを1とする
            }''')
        self.env['x'] = -1
        statement.evaluate(self.runtime, self.env)
        assert self.env['x'] == 1

    def test_parse_if_lt2_false_statement(self):
        """if文のパースをテスト"""
        statement = self.parser.parse_statement('''
            もしxが0未満ならば、 {
                xを1とする
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
# GCD
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



if __name__ == '__main__':
    # pytest を直接実行
    pytest.main([__file__, "-v"])
    

