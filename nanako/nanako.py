from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
import random, time

## utils 

def error_details(text, pos):
    line = 1
    col = 1
    start = 0
    for i, char in enumerate(text):
        if i == pos:
            break
        if char == '\n':
            line += 1
            col = 1
            start = i + 1
        else:
            col += 1
    end = text.find('\n', start)
    if end == -1:
        end = len(text)
    return text, line, col, text[start:end]

## Runtime

class NanakoRuntime(object):
    increment_count: int
    decrement_count: int
    compare_count: int
    call_frames: List[tuple]  # (func_name, args, pos)
    
    def __init__(self):
        self.increment_count = 0
        self.decrement_count = 0
        self.compare_count = 0
        self.call_frames = []  # (func_name, args, pos)
        self.shouldStop = False
        self.timeout = 0 
    
    def push_call_frame(self, func_name: str, args: List[Any], pos: int):
        self.call_frames.append((func_name, args, pos))
    
    def pop_call_frame(self):
        self.call_frames.pop()

    def start(self, timeout = 30):
        self.shouldStop = False
        self.timeout = timeout
        self.startTime = time.time()

    def checkExecution(self, error_details: tuple):

        # 手動停止フラグのチェック
        if self.shouldStop:
            raise NanakoError('プログラムが手動で停止されました', error_details)

        # タイムアウトチェック
        if self.timeout > 0 and (time.time() - self.startTime) > self.timeout:
            raise NanakoError(f'タイムアウト({self.timeout}秒)になりました', error_details)

    def exec(self, code, env=None, timeout=30):
        if env is None:
            env = {}
        parser = NanakoParser()
        program = parser.parse(code)
        self.start(timeout)
        program.evaluate(self, env)
        return env

class NanakoError(SyntaxError):
    def __init__(self, message: str, details):
        super().__init__(message, details)


class ReturnBreakException(Exception):
    def __init__(self, value=None):
        self.value = value


# AST Node Classes
@dataclass
class ASTNode(ABC):
    source: str
    pos: int

    @abstractmethod
    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]) -> Any:
        pass
    

# Statement classes
@dataclass
class Statement(ASTNode):
    pass

# Expression classes
@dataclass
class Expression(ASTNode):
    pass

@dataclass
class Program(Statement):
    statements: List[Statement]

    def __init__(self, statements: List[Statement], source="", pos=0):
        self.statements = statements
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        for statement in self.statements:
            statement.evaluate(runtime, env)


@dataclass
class Block(Statement):
    statements: List[Statement]

    def __init__(self, statements: List[Statement], source="", pos=0):
        self.statements = statements
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        for statement in self.statements:
            statement.evaluate(runtime, env)

@dataclass
class NullValue(Expression):
    
    def __init__(self, source="", pos=0):
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        return None

@dataclass
class Number(Expression):
    value: float

    def __init__(self, value: float = 0.0, source="", pos=0):
        self.value = float(value)
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        return self.value

@dataclass
class Abs(Expression):
    element: Expression

    def __init__(self, element: Expression, source="", pos=0):
        self.element = element
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        value = self.element.evaluate(runtime, env)
        if isinstance(value, int):
            return abs(value)
        if isinstance(value, list):
            return len(value)
        return 0

@dataclass
class Minus(Expression):
    element: Expression

    def __init__(self, element: Expression, source="", pos=0):
        self.element = element
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        value = self.element.evaluate(runtime, env)
        if not isinstance(value, (int, float)):
            raise NanakoError("数値ではないよ", error_details(self.source, self.pos))
        return -value

@dataclass
class ArrayList(Expression):
    elements: List[Expression]

    def __init__(self, elements: List[Expression], source="", pos=0):
        self.elements = elements
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        return [element.evaluate(runtime, env) for element in self.elements]


@dataclass
class StringLiteral(Expression):

    def __init__(self, string_array: List[int], source="", pos=0):
        self.string_array = string_array
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        # 文字列を文字コードの配列に変換
        return self.string_array

@dataclass
class Function(Expression):
    parameters: List[str]
    body: Block

    def __init__(self, parameters: List[str], body: Block, source="", pos=0):
        self.parameters = parameters
        self.body = body
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        return self

@dataclass
class FuncCall(Expression):
    name: str
    arguments: List[Expression]

    def __init__(self, name: str, arguments: List[Expression], source="", pos=0):
        self.name = name
        self.arguments = arguments
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        if self.name in env:
            function = env[self.name]
        if len(function.parameters) != len(self.arguments):
            raise NanakoError("引数の数がパラメータの数と一致しません", error_details(self.source, self.pos))

        new_env = env.copy()
        arguments = []
        for parameter, argument in zip(function.parameters, self.arguments):
            value = argument.evaluate(runtime, env)
            new_env[parameter] = value
            arguments.append(value)
        try:
            runtime.push_call_frame(self.name, arguments, self.pos)
            function.body.evaluate(runtime, new_env)
        except ReturnBreakException as e:
            runtime.pop_call_frame()
            return e.value
        return None


@dataclass
class Variable(Expression):
    name: str
    indices: List[Expression]  # 配列アクセス用

    def __init__(self, name: str, indices: Optional[List[Expression]] = None, source="", pos=0):
        self.name = name
        self.indices = indices
        self.source = source
        self.pos = pos 

    def get_valueindex(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        if self.name in env:
            value = env[self.name]
        else:
            raise NanakoError(f"未定義の変数 '{self.name}' です", error_details(self.source, self.pos))

        if isinstance(self.indices, list) and len(self.indices) > 0:
            for i, index_expression in enumerate(self.indices):
                index = index_expression.evaluate(runtime, env)
                if not isinstance(index, (int, float, NullValue)):
                    raise NanakoError(f"配列の添え字は数にして", error_details(index_expression.source, index_expression.pos))
                if i == len(self.indices) - 1:
                    if isinstance(index, float):
                        index = int(index)
                    return value, index
                value = value[int(index)]
        return value, -1

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        value, index = self.get_valueindex(runtime, env)
        if index == -1:
            return value
        if not isinstance(value, list):
            raise NanakoError(f"これは配列ではありません", error_details(self.source, self.pos))
        if index is None:
            # ランダムに選ぶ
            return random.choice(value)    
        if index >= len(value):
            raise NanakoError(f"この配列の添え字は0から{len(value)-1}の間ですよ", error_details(self.source, self.pos))
        return value[index]

@dataclass
class Assignment(Statement):
    variable: Variable
    expression: Expression

    def __init__(self, variable: Variable, expression: Expression, source="", pos=0):
        self.variable = variable
        self.expression = expression
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        value = self.expression.evaluate(runtime, env)
        if self.variable.name not in env and self.variable.indices is None:
            env[self.variable.name] = 0
        var_value, index = self.variable.get_valueindex(runtime, env)
        if index is None:
            # 特別な処理: var[?] = value の場合
            var_value.append(value)
        elif index == -1:
            env[self.variable.name] = value
        else:
            var_value[index] = value

@dataclass
class Increment(Statement):
    variable: Variable

    def __init__(self, variable: Variable, source="", pos=0):
        self.variable = variable
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        var_value, index = self.variable.get_valueindex(runtime, env)
        if index == -1:
            if not isinstance(env[self.variable.name], (int,float)):
                raise NanakoError(f"`{self.variable.name}`は数値じゃないから増やせないよ", error_details(self.source, self.pos))
            env[self.variable.name] += 1
        else:
            if not isinstance(var_value[index], (int,float)):
                raise NanakoError(f"数値じゃないから増やせないよ", error_details(self.source, self.pos))
            var_value[index] += 1
        runtime.increment_count += 1

@dataclass
class Decrement(Statement):
    variable: Variable

    def __init__(self, variable: Variable, source="", pos=0):
        self.variable = variable
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        var_value, index = self.variable.get_valueindex(runtime, env)
        if index == -1:
            if not isinstance(env[self.variable.name], (int, float)):
                raise NanakoError(f"`{self.variable.name}`は数値じゃないから減らせないよ", error_details(self.source, self.pos))
            env[self.variable.name] -= 1
        else:
            if not isinstance(var_value[index], (int, float)):
                raise NanakoError("数値じゃないから減らせないよ", error_details(self.source, self.pos))
            var_value[index] -= 1
        runtime.decrement_count += 1

@dataclass
class IfStatement(Statement):
    condition: Expression
    operator: str  # "以上", "以下", "より大きい", "より小さい", "以外", "未満", ""
    then_block: Block
    else_block: Optional[Block] = None

    def __init__(self, condition: Expression, operator: str, then_block: Block, else_block: Optional[Block] = None, source="", pos=0):
        self.condition = condition
        self.operator = operator
        self.then_block = then_block
        self.else_block = else_block
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        cond_value = self.condition.evaluate(runtime, env)
        base_value = 0
        if self.operator == "以上":
            result = cond_value >= base_value
        elif self.operator == "以下":
            result = cond_value <= base_value
        elif self.operator == "より大きい":
            result = cond_value > base_value
        elif self.operator == "より小さい":
            result = cond_value < base_value
        elif self.operator == "以外":
            result = cond_value != base_value
        elif self.operator == "未満":
            result = cond_value < base_value
        else:
            result = cond_value == base_value
        runtime.compare_count += 1
        if result:
            self.then_block.evaluate(runtime, env)
        elif self.else_block:
            self.else_block.evaluate(runtime, env)

@dataclass
class LoopStatement(Statement):
    count: Expression
    body: Block

    def __init__(self, count: Expression, body: Block, source="", pos=0):
        self.count = count
        self.body = body
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        loop_count = self.count.evaluate(runtime, env)
        details = error_details(self.source, self.pos)
        if loop_count is None:
            while True:
                runtime.checkExecution(details)
                self.body.evaluate(runtime, env)            
        if isinstance(loop_count, list):
            loop_count = len(loop_count)
        for _ in range(abs(int(loop_count))):
            runtime.checkExecution(details)
            self.body.evaluate(runtime, env)


@dataclass
class ReturnStatement(Statement):
    expression: Expression

    def __init__(self, expression: Expression, source="", pos=0):
        self.expression = expression
        self.source = source
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        value = self.expression.evaluate(runtime, env)
        raise ReturnBreakException(value)


@dataclass
class DocTest(Statement):
    expression: Expression
    answer: Expression

    def __init__(self, expression: Expression, answer: Expression, pos=0):
        self.expression = expression
        self.answer = answer
        self.source = ""
        self.pos = pos

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        value = self.expression.evaluate(runtime, env)
        answer_value = self.answer.evaluate(runtime, env)
        if value != answer_value:
            raise NanakoError(f"テストに失敗: {value}", error_details(self.source, self.pos))


class NanakoParser(object):
    
    def parse(self, text) -> Program:
        self.text = text
        self.pos = 0
        self.length = len(text)
        return self.parse_program()
    
    def error_details(self, pos):
        return error_details(self.text, pos)

    def parse_program(self) -> Program:
        statements = []
        self.consume_whitespace(include_newline=True)
        while self.pos < self.length:
            try:
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
                self.consume_whitespace(include_newline=True)
            except SyntaxError as e:
                print(e)
                self.consume_until_eol()
        return Program(statements)
    
    def parse_statement(self, text = None) -> Optional[Statement]:
        if text is not None:
            self.text = text
            self.pos = 0
            self.length = len(text)

        """文をパース"""
        self.consume_whitespace(include_newline=True)
        saved_pos = self.pos

        stmt = self.parse_if_statement()
        if not stmt:
            stmt = self.parse_loop_statement()
        if not stmt:
            stmt = self.parse_return()
        if not stmt:
            stmt = self.parse_doctest()
        if not stmt:
            stmt = self.parse_assignment()
        if stmt:
            stmt.source = self.text
            stmt.pos = saved_pos
            return stmt
        raise SyntaxError(f"Expected statement", error_details(self.text, saved_pos))

    def parse_doctest(self) -> Statement:
        """ドキュテストをパース"""
        saved_pos = self.pos
        if not self.consume_string(">>>"):
            self.pos = saved_pos
            return None
        
        self.consume_whitespace()
        expression = self.parse_expression()
        if expression is None:
            raise SyntaxError(f"`>>>` の後には式が必要です", error_details(self.text, self.pos))
        self.consume_eol()
        answer_expression = self.parse_expression()
        if expression is None:
            raise SyntaxError(f"`>>>` の次の行には正解の値が必要です", error_details(self.text, self.pos))
        self.consume_eol()
        return DocTest(expression, answer_expression)

    def parse_assignment(self) -> Assignment:
        """代入文をパース"""
        saved_pos = self.pos

        variable = self.parse_variable()
        if variable is None:
            self.pos = saved_pos
            return None
        
        self.consume_whitespace()

        if self.consume_string("を"):
            self.consume_whitespace()
            if self.consume_string("増やす"):
                self.consume_eol()
                return Increment(variable)
            if self.consume_string("減らす"):
                self.consume_eol()
                return Decrement(variable)

            expression = self.parse_expression()
            if expression is None:
                raise SyntaxError(f"Expected expression", error_details(self.text, self.pos))

            # オプションの "とする"
            self.consume_whitespace()
            self.consume_string("とする")
            self.consume_eol()
            return Assignment(variable, expression)

        # "="
        saved_pos = self.pos
        if self.consume_string("="):
            self.consume_whitespace()
            expression = self.parse_expression()
            
            if expression is None:
                raise SyntaxError(f"Expected expression", error_details(self.text, self.pos))

            self.consume_eol()
            return Assignment(variable, expression)

        raise SyntaxError(f"Expected '=", error_details(self.text, saved_pos))
    
    def parse_if_statement(self) -> IfStatement:
        """if文をパース"""
        saved_pos = self.pos

        if not self.consume_string("もし"):
            self.pos = saved_pos
            return None
        self.consume_cma()
        
        condition = self.parse_expression()
        if not self.consume_string("が"):
            raise SyntaxError(f"Expected 'が'", error_details(self.text, self.pos))

        self.consume_cma()
        if not self.consume_string("0"):
            raise SyntaxError(f"Expected '0'", error_details(self.text, self.pos))
        self.consume_whitespace()
        
        # 比較演算子
        operator = ""
        for op in ["以上", "以下", "より大きい", "より小さい", "以外", "未満"]:
            if self.consume_string(op):
                operator = op
                break
        
        self.consume_whitespace()
        if not self.consume_string("ならば"):
            raise SyntaxError(f"Expected 'ならば'", error_details(self.text, self.pos))
        self.consume_cma()

        then_block = self.parse_block()
        if then_block is None:
            raise SyntaxError(f"Expected block after 'ならば'", error_details(self.text, self.pos))
        self.consume_eol()
        
        # else節（オプション）
        else_block = self.parse_else_statement()
        return IfStatement(condition, operator, then_block, else_block)
    
    def parse_else_statement(self) -> Block:
        """else文をパース"""
        saved_pos = self.pos
        self.consume_whitespace()
        if not self.consume_string("そうでなければ"):
            self.pos = saved_pos
            return None
        self.consume_cma()
        block = self.parse_block()
        if block is None:
            raise SyntaxError(f"Expected block after 'そうでなければ'", error_details(self.text, self.pos))
        self.consume_eol()
        return block

    def parse_loop_statement(self) -> LoopStatement:
        """ループ文をパース"""
        saved_pos = self.pos
        count = self.parse_expression()
        if count is None:
            self.pos = saved_pos
            return None
        if not self.consume_string("回"):
            self.pos = saved_pos
            return None
        self.consume_cma()
        if not self.consume_string("くり返す"):
            raise SyntaxError(f"Expected 'くり返す'", error_details(self.text, self.pos))

        body = self.parse_block()
        if body is None:
            raise SyntaxError(f"Expected loop body", error_details(self.text, self.pos))
        self.consume_eol()
        return LoopStatement(count, body)
    
    def parse_return(self) -> ReturnStatement:
        saved_pos = self.pos
        expression = self.parse_expression()
        if expression and self.consume_string("が答え"):
            self.consume_eol()
            return ReturnStatement(expression)
        self.pos = saved_pos
        return None
    
    def parse_expression(self, text=None) -> Expression:
        if text is not None:
            self.text = text
            self.pos = 0
            self.length = len(text)
        """式をパース"""
        self.consume_whitespace()
        saved_pos = self.pos
        expression = self.parse_integer()
        if not expression:
            expression = self.parse_string()
        if not expression:
            expression = self.parse_abs()
        if not expression:
            expression = self.parse_minus()
        if not expression:
            expression = self.parse_function()
        if not expression:
            expression = self.parse_arraylist()
        if not expression:
            expression = self.parse_null()
        if not expression:
            expression = self.parse_funccall()
        if not expression:
            expression = self.parse_variable()

        if expression:
            if self.consume("+", "-", "*", "/", "%"):
                raise SyntaxError("中置記法は使えないよ", error_details(self.text, self.pos))
            expression.pos = saved_pos
            return expression

        return None
                    

    def parse_integer(self) -> Number:
        """整数をパース"""
        saved_pos = self.pos
        if not self.consume_digit():
            self.pos = saved_pos
            return None    
        
        # 数字
        while self.consume_digit():
            pass
        
        value_str = self.text[saved_pos:self.pos]
        try:
            value = int(value_str)
            self.consume_whitespace()
            return Number(value)
        except ValueError:
            self.pos = saved_pos
            return None

    def parse_string(self) -> StringLiteral:
        """文字列リテラルをパース"""
        saved_pos = self.pos
        
        # ダブルクォート開始
        if not self.consume_string('"'):
            self.pos = saved_pos
            return None
            
        # 文字列内容を読み取り
        string_content = []
        while self.pos < self.length and self.text[self.pos] != '"':
            char = self.text[self.pos]
            if char == '\\' and self.pos + 1 < self.length:
                # エスケープシーケンスの処理
                self.pos += 1
                next_char = self.text[self.pos]
                if next_char == 'n':
                    string_content.append(ord('\n'))
                elif next_char == 't':
                    string_content.append(ord('\t'))
                elif next_char == '\\':
                    string_content.append(ord('\\'))
                elif next_char == '"':
                    string_content.append(ord('"'))
                else:
                    string_content.append(ord(next_char))
            else:
                string_content.append(ord(char))
            self.pos += 1
        
        # ダブルクォート終了
        if not self.consume_string('"'):
            self.pos = saved_pos
            raise SyntaxError(f"閉じていない文字列", error_details(self.text, self.pos))

        self.consume_whitespace()
        return StringLiteral(string_content)

    def parse_minus(self) -> Minus:
        """整数をパース"""
        saved_pos = self.pos
        
        # マイナス符号（オプション）
        if not self.consume_string("-"):
            self.pos = saved_pos
            return None
        self.consume_whitespace()
        element = self.parse_expression()
        if element is None:
            raise SyntaxError(f"Expected expression after '-'", error_details(self.text, self.pos))
        self.consume_whitespace()
        return Minus(element)        

    def parse_abs(self) -> Abs:
        """絶対値または長さをパース"""
        saved_pos = self.pos
        if not self.consume_string("|"):
            self.pos = saved_pos
            return None
        
        self.consume_whitespace()
        element = self.parse_expression()
        if element is None:
            raise SyntaxError(f"Expected expression after '|'", error_details(self.text, self.pos))
        self.consume_whitespace()
        if not self.consume_string("|"):
            raise SyntaxError(f"Expected closing '|'", error_details(self.text, self.pos))
        self.consume_whitespace()
        return Abs(element)

    def parse_function(self) -> Function:
        """関数をパース"""
        saved_pos = self.pos
        # "λ" または "入力"
        if not (self.consume_string("λ") or self.consume_string("入力")):
            self.pos = saved_pos
            return None

        self.consume_whitespace()
        
        # パラメータ
        parameters = []
        while True:
            identifier = self.parse_identifier()
            if identifier is None:
                raise SyntaxError(f"Expected identifier", error_details(self.text, self.pos))
            if identifier in parameters:
                raise SyntaxError(f"Duplicate parameter '{identifier}'", error_details(self.text, self.pos))
            parameters.append(identifier)
            self.consume_whitespace()
            if not self.consume_string(","):
                break
            self.consume_whitespace()
        
        if len(parameters) == 0:
            raise SyntaxError(f"Expected parameter", error_details(self.text, self.pos))

        self.consume_whitespace()
        if not self.consume_string("に対し"):
            raise SyntaxError(f"Expected 'に対し'", error_details(self.text, self.pos))
        self.consume_string("て")
        self.consume_cma()
        body = self.parse_block()
        
        if body is None:
            raise SyntaxError(f"Expected function body", error_details(self.text, self.pos))
        self.consume_whitespace()
        return Function(parameters, body)
    
    def parse_funccall(self) -> FuncCall:
        """関数呼び出しをパース"""
        saved_pos = self.pos
        name = self.parse_identifier()
        if name is None:
            self.pos = saved_pos
            return None
        self.consume_whitespace()

        if not self.consume_string("("):
            self.pos = saved_pos
            return None

        self.consume_whitespace()
        
        arguments = []
        while True:
            expression = self.parse_expression()
            if expression is None:
                raise SyntaxError(f"Expected expression in function call", error_details(self.text, self.pos))
            arguments.append(expression)
            self.consume_whitespace()
            if self.consume_string(")"):
                break
            if not self.consume_string(","):
                raise SyntaxError(f"Expected ',' or ')' in function call", error_details(self.text, self.pos))
            self.consume_whitespace()

        self.consume_whitespace()
        return FuncCall(name, arguments)
    
    def parse_arraylist(self) -> ArrayList:
        """配列をパース"""
        saved_pos = self.pos
         # "[" で始まる
        if not self.consume_string("["):
            self.pos = saved_pos
            return None
        
        elements = []
        saved_pos = self.pos
        while True:
            self.consume_whitespace()
            if self.consume_string("]"):
                break
            expression = self.parse_expression()
            if expression is None:
                raise SyntaxError(f"ここには式が来るはずです", error_details(self.text, self.pos))
            elements.append(expression)
            self.consume_whitespace()
            if self.consume_string("]"):
                break
            if not self.consume_string(","):
                raise SyntaxError(f"閉じ`]`がないよ", error_details(self.text, saved_pos))

        self.consume_whitespace()
        return ArrayList(elements)
    
    def parse_null(self) -> NullValue:
        """null値をパース"""
        if self.consume("null", "?", "？"):
            self.consume_whitespace()
            return NullValue()
        return None

    def parse_variable(self) -> Variable:
        """変数をパース"""
        name = self.parse_identifier()
        indices = []
        
        self.consume_whitespace()
        while self.consume_string("["):
            self.consume_whitespace()
            index = self.parse_expression()
            indices.append(index)
            if not self.consume_string("]"):
                raise SyntaxError(f"閉じ`]`が必要だよ", error_details(self.text, self.pos))
            self.consume_whitespace()
        if len(indices) == 0:
            indices = None
        return Variable(name, indices)
    
    def parse_block(self) -> Block:
        """ブロックをパース"""
        self.consume_whitespace()
        if not self.consume_string("{"):
            raise SyntaxError(f"Expected opening '{{'", error_details(self.text, self.pos))
        self.consume_until_eol()
        indent_depth = self.consume_whitespace()
        found_closing_brace = False
        statements = []
        while self.pos < self.length:
            self.consume_whitespace()
            if self.consume_string("}"):
                found_closing_brace = True
                break
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)

        if not found_closing_brace:
            raise SyntaxError(f"Expected closing '}}'", error_details(self.text, self.pos))

        self.consume_whitespace()
        return Block(statements)
    
    def parse_identifier(self) -> str:
        """識別子をパース"""
        saved_pos = self.pos
        if not self.consume_alpha():
            self.pos = saved_pos
            return None

        while self.not_identifier_words() and self.consume_alpha():
            pass

        while self.consume_digit():
            pass
        
        return self.text[saved_pos:self.pos]
    
    def not_identifier_words(self) -> bool:
        # 除外キーワードチェック
        remaining = self.text[self.pos:]
        for kw in ["くり返す", "を", "回", "とする", "が", "ならば", "に対し"]:
            if remaining.startswith(kw):
                return False
        return True
    
    def consume_alpha(self) -> bool:
        if self.pos >= self.length:
            return False
        char = self.text[self.pos]
        if (char.isalpha() or char == '_' or 
                '\u4e00' <= char <= '\u9fff' or  # 漢字
                '\u3040' <= char <= '\u309f' or  # ひらがな
                '\u30a0' <= char <= '\u30ff' or  # カタカナ
                char == 'ー'):
            self.pos += 1
            return True
        return False

    def consume(self, *strings) -> bool:
        for string in strings:
            if self.consume_string(string):
                return True
        return False

    def consume_string(self, string: str) -> bool:
        if self.text[self.pos:].startswith(string):
            self.pos += len(string)
            return True
        return False
    
    def consume_digit(self) -> bool:
        if self.pos >= self.length:
            return False
        if self.text[self.pos].isdigit():
            self.pos += 1
            return True
        return False

    
    def consume_whitespace(self, include_newline: bool = False):
        if include_newline:
            WS = " 　\t\n\r"
        else:
            WS = " 　\t"
        c = 0
        while self.pos < self.length:
            if self.text[self.pos] in '#＃':
                self.pos += 1
                self.consume_until_eol()
            elif self.text[self.pos] in WS:
                self.pos += 1
                c += 1
            else:
                break
        return c
    
    def consume_cma(self):
        self.consume_string("、")
        self.consume_whitespace()
    
    def consume_eol(self):
        self.consume_whitespace()
        if self.pos < self.length and self.text[self.pos] == '\n':
            self.pos += 1
        elif self.pos >= self.length:
            pass  # ファイル終端
        else:
            # EOLが見つからない場合でもエラーにしない
            pass
    
    def consume_until_eol(self):
        """改行まで読み飛ばす"""
        while self.pos < self.length and self.text[self.pos] != '\n':
            self.pos += 1
        if self.pos < self.length:
            self.pos += 1

