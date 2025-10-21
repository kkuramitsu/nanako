from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
import time

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

    def update_variable(self, name: str, env: Dict[str, Any], source: str, pos: int):
        pass

    def print(self, value, source: str, pos: int, end_pos: int):
        source, line, col, snipet = error_details(source, pos)
        print(f">>> {snipet.strip()}\n{value}")

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
        else:
            env = transform_array(env)
        parser = NanakoParser()
        program = parser.parse(code)
        self.start(timeout)
        program.evaluate(self, env)
        return env
    
    def transform_array(self, value: Any):
        return transform_array(value)

    def stringfy_as_json(self, env:Dict[str, Any]):
        env = self.transform_array(env)
        return stringfy_as_json(env)


class NanakoArray(object):
    elements: List[Any]
    is_string_view: bool

    def __init__(self, values: Any):
        if isinstance(values, str):
            self.elements = [ord(ch) for ch in values]
            self.is_string_view = True
        else:
            self.elements = [transform_array(v) for v in values]
            self.is_string_view = False


    def emit(self, lang="js", indent:str = "") -> str:
        if self.is_string_view:
            chars = []
            for code in self.elements:
                chars.append(chr(code))
                content = ''.join(chars).replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t').replace('"', '\\"')
            return '"' + content + '"'
        if len(self.elements) == 0:
            return "[]"
        if isinstance(self.elements[0], NanakoArray):
            lines = ["["]
            for element in self.elements:
                line = element.emit(lang, indent + "  ")
                lines.append(f"    {indent}{line},")
            lines[-1] = lines[-1][:-1]
            lines.append(f"{indent}]")
            return '\n'.join(lines)
        elements = []
        for element in self.elements:
            elements.append(str(element))
        return "[" + ", ".join(elements) + "]"

    def __str__(self):
        return self.emit("js", "")

    def __repr__(self):
        return self.emit("js", "")

def transform_array(values):
    if isinstance(values, (list, tuple)):
        return NanakoArray(values)
    if isinstance(values, str):
        return NanakoArray(str)
    if isinstance(values, dict):
        for key, value in values.items():
            values[key] = transform_array(value)
        return values
    return values

def stringfy_as_json(env: Dict[str, Any]):
    lines = ["{"]
    indent = "    "
    for key, value in env.items():
        key = f"{indent}\"{key}\":"
        if isinstance(value, (int, float)):
            lines.append(f"{key} {int(value)},")
        if isinstance(value, NanakoArray):
            content = value.emit("js", indent)
            lines.append(f"{key} {content},")
        if value is None:
            lines.append(f"{key} null,")
    if len(lines)>1:
        lines[-1] = lines[-1][:-1]
    lines.append("}")
    return '\n'.join(lines)

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


class NanakoError(SyntaxError):
    def __init__(self, message: str, details):
        super().__init__(message, details)


class ReturnBreakException(RuntimeError):
    def __init__(self, value=None):
        self.value = value


@dataclass
class ASTNode(ABC):
    source: str
    pos: int
    end_pos: int

    def __init__(self):
        self.source = ""
        self.pos = 0
        self.end_pos = 0

    def error_details(self):
        return error_details(self.source, self.pos)

    @abstractmethod
    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]) -> Any:
        pass
    
    @abstractmethod
    def emit(self, lang="js", indent:str = "") -> str:
        pass

# StatementNode classes
@dataclass
class StatementNode(ASTNode):
    def __init__(self):
        super().__init__()

    def semicolon(self, lang="js") -> str:
        if lang == "py":
            return ""
        return ";"

# ExpressionNode classes
@dataclass
class ExpressionNode(ASTNode):

    def __init__(self):
        super().__init__()

    pass

@dataclass
class ProgramNode(StatementNode):
    statements: List[StatementNode]

    def __init__(self, statements: List[StatementNode]):
        super().__init__()
        self.statements = statements

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        for statement in self.statements:
            statement.evaluate(runtime, env)

    def emit(self, lang="js", indent:str = "") -> str:
        lines = []
        for statement in self.statements:
            lines.append(statement.emit(lang, indent))
        return "\n".join(lines)

@dataclass
class BlockNode(StatementNode):
    statements: List[StatementNode]

    def __init__(self, statements: List[StatementNode]):
        super().__init__()
        self.statements = statements

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        for statement in self.statements:
            statement.evaluate(runtime, env)

    def emit(self, lang="js", indent:str = "") -> str:
        lines = []
        for statement in self.statements:
            lines.append(statement.emit(lang, indent+"    "))
        if lang == "py":
            if len(lines) == 0:
                lines.append(f"{indent}pass")
        else:
            lines.append(f"{indent}}}")
        return "\n".join(lines)


@dataclass
class NullNode(ExpressionNode):
    
    def __init__(self):
        super().__init__()

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        return None

    def emit(self, lang="js", indent:str = "") -> str:
        if lang == "py":
            return "None"
        return "null"

@dataclass
class NumberNode(ExpressionNode):
    value: int

    def __init__(self, value: int = 0):
        super().__init__()
        self.value = int(value)

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        return self.value

    def emit(self, lang="js", indent:str = "") -> str:
        return str(self.value)


@dataclass
class ArrayLenNode(ExpressionNode):
    element: ExpressionNode

    def __init__(self, element: ExpressionNode):
        super().__init__()
        self.element = element

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        value = self.element.evaluate(runtime, env)
        if isinstance(value, NanakoArray):
            return len(value.elements)
        raise NanakoError(f"配列じゃないね？ ❌{value}", self.element.error_details())

    def emit(self, lang="js", indent:str = "") -> str:
        if lang == "py":
            return "len(" + self.element.emit(lang, indent) + ")"
        return "(" + self.element.emit(lang, indent) + ").length"

@dataclass
class MinusNode(ExpressionNode):
    element: ExpressionNode

    def __init__(self, element: ExpressionNode):
        super().__init__()
        self.element = element

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        value = self.element.evaluate(runtime, env)
        if not isinstance(value, (int, float)):
            raise NanakoError("数ではないよ", error_details(self.source, self.pos))
        return -value

    def emit(self, lang="js", indent:str = "") -> str:
        return f"-{self.element.emit(lang, indent)}"

@dataclass
class ArrayNode(ExpressionNode):
    elements: List[Any] 

    def __init__(self, elements: List[Any]):
        super().__init__()
        self.elements = elements

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        array_content = [element.evaluate(runtime, env) for element in self.elements]
        return NanakoArray(array_content)

    def emit(self, lang="js", indent:str = "") -> str:
        elements = []
        for element in self.elements:
            elements.append(element.emit(lang, indent))
        return "[" + ", ".join(elements) + "]"

@dataclass
class StringNode(ExpressionNode):
    value: List[Any] 

    def __init__(self, content: str):
        super().__init__()
        self.value = NanakoArray(content)

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        return self.value

    def emit(self, lang="js", indent:str = "") -> str:
        return self.value.emit(lang, indent)


@dataclass
class FunctionNode(ExpressionNode):
    name: str
    parameters: List[str]
    body: BlockNode

    def __init__(self, parameters: List[str], body: BlockNode):
        super().__init__()
        self.name = "<lambda>"
        self.parameters = parameters
        self.body = body

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        return self

    def emit(self, lang="js", indent:str = "") -> str:
        params = ", ".join(self.parameters)
        body = self.body.emit(lang, indent)
        if lang == "py":
            return f"def {self.name}({params}):\n{body}"
        return f"function ({params}) {{\n{body}"

@dataclass
class FuncCallNode(ExpressionNode):
    name: str
    arguments: List[ExpressionNode]

    def __init__(self, name: str, arguments: List[ExpressionNode]):
        super().__init__()
        self.name = name
        self.arguments = arguments

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        if not self.name in env:
            funcnames = [n for n, v in env.items() if isinstance(v, FunctionNode)]
            raise NanakoError(f"関数の定義忘れていない？: ❌{self.name} 🔍{funcnames}", error_details(self.source, self.pos))
        function = env[self.name]
        if not isinstance(function, FunctionNode):
            raise NanakoError(f"関数ではありません: ❌{self.name}", error_details(self.source, self.pos))
        if len(function.parameters) != len(self.arguments):
            raise NanakoError("引数の数が一致しません", error_details(self.source, self.pos))

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

    def emit(self, lang="js", indent:str = "") -> str:
        arguments = []
        for argument in self.arguments:
            arguments.append(argument.emit(lang, indent))
        params = ", ".join(arguments)
        return f"{self.name}({params})"

@dataclass
class VariableNode(ExpressionNode):
    name: str
    indices: List[ExpressionNode]  # 配列アクセス用

    def __init__(self, name: str, indices: Optional[List[ExpressionNode]] = None):
        super().__init__()
        self.name = name
        self.indices = indices

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        if self.name in env:
            value = env[self.name]
        else:
            raise NanakoError(f"知らない変数だよ！ '{self.name}'", self.error_details())
        if self.indices is None or len(self.indices) == 0:
            return value
        
        array = env[self.name]
        for index in self.indices:
            if not isinstance(array, NanakoArray):
                raise NanakoError(f"配列ではありません: ❌{array}", self.error_details())
            index_value = index.evaluate(runtime, env)
            if isinstance(index_value, (int, float)):
                index_value = int(index_value)
                if 0<= index_value < len(array.elements):
                    array = array.elements[index_value]
                    continue
            raise NanakoError(f"配列の添え字は0から{len(array.elements)-1}の間ですよ: ❌{index_value}", index.error_details())
        return array

    def evaluate_with(self, runtime: NanakoRuntime, env: Dict[str, Any], value):
        if self.indices is None or len(self.indices) == 0:
            env[self.name] = value
            return       

        if self.name in env:
            array = env[self.name]
        else:
            raise NanakoError(f"知らない変数だよ！ '{self.name}'", self.error_details())

        for i, index in enumerate(self.indices):
            if not isinstance(array, NanakoArray):
                raise NanakoError(f"配列ではありません: ❌{array}", self.error_details())
            index_value = index.evaluate(runtime, env)
            if isinstance(index_value, (int, float)):
                index_value = int(index_value)
                if index_value < 0 or index_value >= len(array.elements):
                    break
                if i == len(self.indices) - 1:
                    array.elements[index_value] = value
                    return None
                array = array.elements[index_value]
            elif index_value is None:
                if i == len(self.indices) - 1:
                    array.elements.append(value)
                    return None
            break
        raise NanakoError(f"配列の添え字は0から{len(array.elements)-1}の間ですよ: ❌{index_value}", index.error_details())

    def emit(self, lang="js", indent:str = "") -> str:
        if self.indices is None or len(self.indices) == 0:
            return self.name
        indices = []
        for index in self.indices:
            indices.append(f"[{index.emit(lang, indent)}]")
        indices_str = "".join(indices)
        return f"{self.name}{indices_str}"

@dataclass
class AssignmentNode(StatementNode):
    variable: VariableNode
    expression: ExpressionNode

    def __init__(self, variable: VariableNode, expression: ExpressionNode):
        super().__init__()
        self.variable = variable
        self.expression = expression
        if isinstance(expression, FunctionNode):
            expression.name = variable.name

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        value = self.expression.evaluate(runtime, env)
        self.variable.evaluate_with(runtime, env, value)
        runtime.update_variable(self.variable.name, env, self.source, self.pos)

    def emit(self, lang="js", indent:str = "") -> str:
        variable = self.variable.emit(lang, indent)
        expression = self.expression.emit(lang, indent)
        if variable.endswith('[null]') or variable.endswith('[None]'):
            if lang == "py":
                return f'{indent}{variable[:-6]}.append({expression})'
            if lang == "js":
                return f'{indent}{variable[:-6]}.push({expression}){self.semicolon(lang)}'            
        if lang == "py" and isinstance(self.expression, FunctionNode):
            return f"{indent}{expression}"
        return f"{indent}{variable} = {expression}{self.semicolon(lang)}"

@dataclass
class AppendNode(StatementNode):
    variable: VariableNode
    expression: ExpressionNode

    def __init__(self, variable: VariableNode, expression: ExpressionNode):
        super().__init__()
        self.variable = variable
        self.expression = expression

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        array = self.variable.evaluate(runtime, env)
        if not isinstance(array, NanakoArray):
            raise NanakoError(f"配列じゃないね？ ❌{array}", self.variable.error_details())
        value = self.expression.evaluate(runtime, env)
        array.elements.append(value)

    def emit(self, lang="js", indent:str = "") -> str:
        variable = self.variable.emit(lang, indent)
        expression = self.expression.emit(lang, indent)
        if lang == "py":
            return f'{indent}{variable}.append({expression})'
        if lang == "js":
            return f'{indent}{variable}.push({expression}){self.semicolon(lang)}'
        return f'{indent}{variable}.append({expression})'

@dataclass
class IncrementNode(StatementNode):
    variable: VariableNode

    def __init__(self, variable: VariableNode):
        super().__init__()
        self.variable = variable

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        value = self.variable.evaluate(runtime, env)
        if not isinstance(value, (int, float)):
            raise NanakoError(f"数じゃないよ: ❌{value}", self.variable.error_details())
        self.variable.evaluate_with(runtime, env, value + 1)
        runtime.increment_count += 1
    
    def emit(self, lang="js", indent:str = "") -> str:
        variable = self.variable.emit(lang, indent)
        return f"{indent}{variable} += 1{self.semicolon(lang)}"

@dataclass
class DecrementNode(StatementNode):
    variable: VariableNode

    def __init__(self, variable: VariableNode):
        super().__init__()
        self.variable = variable

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        value = self.variable.evaluate(runtime, env)
        if not isinstance(value, (int, float)):
            raise NanakoError(f"数じゃないよ: ❌{value}", self.variable.error_details())
        self.variable.evaluate_with(runtime, env, value - 1)
        runtime.decrement_count += 1

    def emit(self, lang="js", indent:str = "") -> str:
        variable = self.variable.emit(lang, indent)
        return f"{indent}{variable} -= 1{self.semicolon(lang)}"

@dataclass
class IfNode(StatementNode):
    left: ExpressionNode
    operator: str  # "以上", "以下", "より大きい", "より小さい", "以外", "未満", ""
    right: ExpressionNode
    then_block: BlockNode
    else_block: Optional[BlockNode] = None

    def __init__(self, left: ExpressionNode, operator: str, right: ExpressionNode, then_block: BlockNode, else_block: Optional[BlockNode] = None):
        super().__init__()
        self.left = left
        self.operator = operator
        self.right = right
        self.then_block = then_block
        self.else_block = else_block

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        left_value = self.left.evaluate(runtime, env)
        right_value = self.right.evaluate(runtime, env)
        if self.operator == "以上":
            result = left_value >= right_value
        elif self.operator == "以下":
            result = left_value <= right_value
        elif self.operator == "より大きい":
            result = left_value > right_value
        elif self.operator == "より小さい":
            result = left_value < right_value
        elif self.operator == "以外":
            result = left_value != right_value
        elif self.operator == "未満":
            result = left_value < right_value
        else:
            result = left_value == right_value
        runtime.compare_count += 1
        if result:
            self.then_block.evaluate(runtime, env)
        elif self.else_block:
            self.else_block.evaluate(runtime, env)

    def emit(self, lang="js", indent:str = "") -> str:
        left = self.left.emit(lang, indent)
        right = self.right.emit(lang, indent)
        if self.operator == "以上":
            op = ">="
        elif self.operator == "以下":
            op = "<="
        elif self.operator == "より大きい":
            op = ">"
        elif self.operator == "より小さい":
            op = "<"
        elif self.operator == "以外":
            op = "!="
        elif self.operator == "未満":
            op = "<"
        else:
            op = "=="
        lines = []
        if lang == "py":
            lines.append(f"{indent}if {left} {op} {right}:")
        else:
            lines.append(f"{indent}if({left} {op} {right}) {{")
        lines.append(self.then_block.emit(lang, indent))
        if self.else_block:
            if lang == "py":
                lines.append(f"{indent}else:")
            else:
                lines.append(f"{indent}else {{")
            lines.append(self.else_block.emit(lang, indent))
        return "\n".join(lines)

@dataclass
class LoopNode(StatementNode):
    count: ExpressionNode
    body: BlockNode

    def __init__(self, count: ExpressionNode, body: BlockNode):
        super().__init__()
        self.count = count
        self.body = body

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        loop_count = self.count.evaluate(runtime, env)
        details = error_details(self.source, self.pos)
        if loop_count is None:
            while True:
                runtime.checkExecution(details)
                self.body.evaluate(runtime, env)            
        if isinstance(loop_count, list):
            raise NanakoError(f"配列の長さでは？", details)
        if loop_count < 0:
            raise NanakoError(f"負のループ回数: {loop_count}", details)
        for _ in range(int(loop_count)):
            runtime.checkExecution(details)
            self.body.evaluate(runtime, env)

    def emit(self, lang="js", indent:str = "") -> str:
        lines = []
        if isinstance(self.count, NullNode):
            if lang == "py":
                lines.append(f"{indent}while True:")
            else:
                lines.append(f"{indent}while(true) {{")
        else:
            count = self.count.emit(lang, indent)
            if lang == "py":
                lines.append(f"{indent}for _ in range({count}):")
            else:
                i = f"i{len(indent)//4}"
                lines.append(f"{indent}for(var {i} = 0; {i} < {count}; {i}++) {{")

        lines.append(self.body.emit(lang, indent))
        return "\n".join(lines)



@dataclass
class ReturnNode(StatementNode):
    expression: ExpressionNode

    def __init__(self, expression: ExpressionNode):
        super().__init__()
        self.expression = expression

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        value = self.expression.evaluate(runtime, env)
        raise ReturnBreakException(value)

    def emit(self, lang="js", indent:str = "") -> str: 
        return f"{indent}return {self.expression.emit(lang, indent)}{self.semicolon(lang)}"

@dataclass
class ExpressionStatementNode(StatementNode):
    expression: ExpressionNode

    def __init__(self, expression: ExpressionNode):
        super().__init__()
        self.expression = expression

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        value = self.expression.evaluate(runtime, env)
        e = self.expression
        runtime.print(value, e.source, e.pos, e.end_pos)
        return value

    def emit(self, lang="js", indent:str = "") -> str:
        return f"{indent}{self.expression.emit(lang, indent)}{self}"

@dataclass
class TestNode(StatementNode):
    expression: ExpressionNode
    answer: ExpressionNode

    def __init__(self, expression: ExpressionNode, answer: ExpressionNode):
        super().__init__()
        self.expression = expression
        self.answer = answer

    def evaluate(self, runtime: NanakoRuntime, env: Dict[str, Any]):
        value = self.expression.evaluate(runtime, env)
        answer_value = self.answer.evaluate(runtime, env)
        if value != answer_value:
            raise NanakoError(f"テストに失敗: {value}", error_details(self.source, self.pos))

    def emit(self, lang="js", indent:str = "") -> str:
        expression = self.expression.emit(lang, indent)
        answer = self.answer.emit(lang, indent)
        if lang == "js":
            return f"{indent}console.assert({expression} == {answer}){self.semicolon(lang)}"
        return f"{indent}assert ({expression} == {answer}){self.semicolon(lang)}"

class NanakoParser(object):
    variables: List[str]

    def __init__(self):
        self.init_text("")

    def init_text(self, text: str, reset_variables: bool = True):
        self.text = self.normalize(text)
        self.pos = 0
        self.length = len(text)
        if reset_variables:
            self.variables = []

    def normalize(self, text: str) -> str:
        text = text.replace('“”', '"').replace('”', '"')
        """全角文字を半角に変換する"""
        return text.translate(str.maketrans("０-９Ａ-Ｚａ-ｚ", "0-9A-Za-z"))
    
    def add_variable(self, name: str):
        if name not in self.variables:
            self.variables.append(name)
        self.variables.sort(key=lambda x: -len(x))

    def parse(self, text) -> ProgramNode:
        self.init_text(text)
        return self.parse_program()

    def error_details(self, pos):
        return error_details(self.text, pos)

    def parse_program(self) -> ProgramNode:
        statements = []
        self.consume_whitespace(include_newline=True)
        while self.pos < self.length:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.consume_whitespace(include_newline=True)
        return ProgramNode(statements)
    
    def parse_statement(self, text = None) -> Optional[StatementNode]:
        if text is not None:
            self.init_text(text)

        """文をパース"""
        self.consume_whitespace(include_newline=True)
        saved_pos = self.pos

        stmt = self.parse_IfNode()
        if not stmt:
            stmt = self.LoopNode()
        if not stmt:
            stmt = self.parse_TestNode()
        if not stmt:
            stmt = self.parse_AssignmentNode()
        if not stmt:
            stmt = self.parse_ReturnNode()
        if stmt:
            stmt.source = self.text
            stmt.pos = saved_pos
            stmt.end_pos = self.pos
            self.consume_whitespace(include_newline=True)
            return stmt
        raise SyntaxError(f"ななこの知らない書き方だね！", error_details(self.text, saved_pos))

    def parse_TestNode(self) -> StatementNode:
        """テストケースをパース"""
        saved_pos = self.pos
        if not self.consume_string(">>>"):
            self.pos = saved_pos
            return None
        
        self.consume_whitespace()
        expression = self.parse_expression()
        if expression is None:
            raise SyntaxError(f"`>>>` の後にはテストする式が必要です", error_details(self.text, self.pos))
        self.consume_eol()
        answer_expression = self.parse_expression()
        if answer_expression is None:
            raise SyntaxError(f"`>>>` の次の行には正解が必要です", error_details(self.text, self.pos))
        return TestNode(expression, answer_expression)

    def parse_AssignmentNode(self) -> AssignmentNode:
        """代入文をパース"""
        saved_pos = self.pos

        variable : VariableNode = self.parse_VariableNode(definition_context=True)
        if variable is None:
            self.pos = saved_pos
            return None
        
        self.consume_whitespace()

        if self.consume("の末尾に"):
            self.consume_comma()
            expression = self.parse_expression()
            if expression is None:
                raise SyntaxError(f"ここに何か忘れてません？", error_details(self.text, self.pos))
            self.consume_whitespace()
            self.consume_string("を")
            self.consume_comma()
            self.consume("追加する")
            return AppendNode(variable, expression)

        if self.consume_string("を"):
            self.consume_whitespace()
            if self.consume_string("増やす"):
                return IncrementNode(variable)
            if self.consume_string("減らす"):
                return DecrementNode(variable)
            raise SyntaxError(f"`増やす`か`減らす`かどちら？", error_details(self.text, self.pos))

        # "="
        if self.consume("=", "＝"):
            self.consume_whitespace()
            expression = self.parse_expression()
            if expression is None:
                raise SyntaxError(f"ここに何か忘れてません？", error_details(self.text, self.pos))

            self.add_variable(variable.name)
            return AssignmentNode(variable, expression)
                
        self.pos = saved_pos
        return None
    
    def parse_IfNode(self) -> IfNode:
        """if文をパース"""
        saved_pos = self.pos

        if not self.consume_string("もし"):
            self.pos = saved_pos
            return None
        self.consume_comma()
        
        left = self.parse_expression()
        if not left:
            raise SyntaxError(f"何と比較したいの？", error_details(self.text, self.pos))

        if not self.consume_string("が"):
            raise SyntaxError(f"`が`が必要", error_details(self.text, self.pos))

        self.consume_comma()
        right = self.parse_expression()
        if not right:
            raise SyntaxError(f"何と比較したいの？", error_details(self.text, self.pos))
        self.consume_whitespace()
        
        # 比較演算子
        operator = ""
        for op in ["以上", "以下", "より大きい", "より小さい", "以外", "未満"]:
            if self.consume_string(op):
                operator = op
                break
        
        self.consume_whitespace()
        if not self.consume_string("ならば"):
            raise SyntaxError("`ならば`が必要", error_details(self.text, self.pos))
        self.consume_comma()

        then_block = self.parse_block()
        if then_block is None:
            raise SyntaxError("「もし〜ならば」どうするの？ { }で囲んでね！", error_details(self.text, self.pos))
        
        # else節（オプション）
        else_block = self.parse_else_statement()
        return IfNode(left, operator, right, then_block, else_block)
    
    def parse_else_statement(self) -> BlockNode:
        """else文をパース"""
        saved_pos = self.pos
        self.consume_whitespace(include_newline=True)
        if not self.consume_string("そうでなければ"):
            self.pos = saved_pos
            return None
        self.consume_comma()
        block = self.parse_block()
        if block is None:
            raise SyntaxError("「そうでなければ」どうするの？ { }で囲んでね！", error_details(self.text, self.pos))
        return block

    def LoopNode(self) -> LoopNode:
        """ループ文をパース"""
        saved_pos = self.pos
        count = self.parse_expression()
        if count is None:
            self.pos = saved_pos
            return None
        if not self.consume_string("回"):
            self.pos = saved_pos
            return None
        self.consume_comma()
        if not self.consume("くり返す", "繰り返す"):
            raise SyntaxError(f"`くり返す`が必要", error_details(self.text, self.pos))

        body = self.parse_block()
        if body is None:
            raise SyntaxError("何をくり返すの？ { }で囲んでね！", error_details(self.text, self.pos))
        return LoopNode(count, body)
    
    def parse_ReturnNode(self) -> ReturnNode:
        saved_pos = self.pos
        expression = self.parse_expression()
        if expression:
            if self.consume_string("が答え"):
                return ReturnNode(expression)
            self.consume_whitespace()
            if self.pos >= self.length or self.text[self.pos] == '\n':
                return ExpressionStatementNode(expression)
        self.pos = saved_pos
        return None

    def parse_expression(self, text=None) -> ExpressionNode:
        if text is not None:
            self.init_text(text, reset_variables=False)
            
        """式をパース"""
        self.consume_whitespace()
        saved_pos = self.pos
        expression = self.parse_NumberNode()
        if not expression:
            expression = self.parse_StringNode()
        if not expression:
            expression = self.parse_ArrayLenNode()
        if not expression:
            expression = self.parse_MinusNode()
        if not expression:
            expression = self.parse_FunctionNode()
        if not expression:
            expression = self.parse_ArrayNode()
        if not expression:
            expression = self.parse_NullNode()
        if not expression:
            expression = self.parse_FuncCallNode()
        if not expression:
            expression = self.parse_VariableNode()

        if expression:
            if self.consume("+", "-", "*", "/", "%", "＋", "ー", "＊", "／", "％", "×", "÷"):
                raise SyntaxError("ななこは中置記法を使えないよ！", error_details(self.text, self.pos))
            expression.source = self.text
            expression.pos = saved_pos
            expression.end_pos = self.pos
            self.consume_whitespace()
            return expression

        return None
                    

    def parse_NumberNode(self) -> NumberNode:
        """整数をパース"""
        saved_pos = self.pos
        if not self.consume_digit():
            self.pos = saved_pos
            return None    
        
        # 数字
        while self.consume_digit():
            pass
        
        if self.consume("."):
            raise SyntaxError("ななこは小数を使えないよ！", error_details(self.text, self.pos))

        value_str = self.text[saved_pos:self.pos]
        try:
            value = int(value_str)
            return NumberNode(value)
        except ValueError:
            self.pos = saved_pos
            return None

    def parse_StringNode(self) -> ArrayNode:
        """文字列リテラルをパース"""
        saved_pos = self.pos
        
        # ダブルクォート開始
        if not self.consume('"', "“", "”"):
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
                    string_content.append('\n')
                elif next_char == 't':
                    string_content.append('\t')
                elif next_char == '\\':
                    string_content.append('\\')
                elif next_char == '"':
                    string_content.append('"')
                else:
                    string_content.append(next_char)
            else:
                string_content.append(char)
            self.pos += 1

        # ダブルクォート終了
        if not self.consume('"', "“", "”"):
            self.pos = saved_pos
            raise SyntaxError(f"閉じ`\"`を忘れないで", error_details(self.text, saved_pos))

        return StringNode(''.join(string_content))

    def parse_MinusNode(self) -> MinusNode:
        """整数をパース"""
        saved_pos = self.pos
        
        # マイナス符号（オプション）
        if not self.consume("-", "ー"):
            self.pos = saved_pos
            return None
        self.consume_whitespace()
        element = self.parse_expression()
        if element is None:
            raise SyntaxError(f"`-`の次に何か忘れてない？", error_details(self.text, self.pos))
        return MinusNode(element)        

    def parse_ArrayLenNode(self) -> ArrayLenNode:
        """絶対値または長さをパース"""
        saved_pos = self.pos
        if not self.consume("|", "｜"):
            self.pos = saved_pos
            return None
        
        self.consume_whitespace()
        element = self.parse_expression()
        if element is None:
            raise SyntaxError(f"`|`の次に何か忘れてない？", error_details(self.text, self.pos))
        self.consume_whitespace()
        if not self.consume("|", "｜"):
            raise SyntaxError(f"閉じ`|`を忘れないで", error_details(self.text, self.pos))
        return ArrayLenNode(element)

    def parse_FunctionNode(self) -> FunctionNode:
        """関数をパース"""
        saved_pos = self.pos
        # "λ" または "入力"
        if not self.consume("入力", "λ"):
            self.pos = saved_pos
            return None

        self.consume_whitespace()
        
        # パラメータ
        parameters = []
        while True:
            name = self.parse_name(definition_context=True)
            if name is None:
                raise SyntaxError(f"変数名が必要", error_details(self.text, self.pos))
            if name in parameters:
                raise SyntaxError(f"同じ変数名を使っているよ: ❌'{name}'", error_details(self.text, self.pos))
            parameters.append(name)
            self.consume_whitespace()
            if not self.consume(",", "、"):
                break
            self.consume_whitespace()
        
        if len(parameters) == 0:
            raise SyntaxError(f"ひとつは変数名が必要", error_details(self.text, self.pos))

        self.consume_whitespace()
        if not self.consume_string("に対し"):
            raise SyntaxError(f"`に対し`が必要", error_details(self.text, self.pos))
        self.consume_string("て")
        self.consume_comma()
        saved_variables = self.variables.copy()
        self.variables = self.variables + parameters
        body = self.parse_block()
        self
        
        if body is None:
            raise SyntaxError("関数の本体は？ { }で囲んでね！", error_details(self.text, self.pos))
        return FunctionNode(parameters, body)
    
    def parse_FuncCallNode(self) -> FuncCallNode:
        """関数呼び出しをパース"""
        saved_pos = self.pos
        name = self.parse_name()
        if name is None:
            self.pos = saved_pos
            return None
        self.consume_whitespace()

        if not self.consume("(", "（"):
            self.pos = saved_pos
            return None

        self.consume_whitespace()
        
        arguments = []
        while True:
            expression = self.parse_expression()
            if expression is None:
                raise SyntaxError(f"関数なら引数を忘れないで", error_details(self.text, self.pos))
            arguments.append(expression)
            self.consume_whitespace()
            if self.consume(")", "）"):
                break
            if not self.consume(",", "、", "，"):
                raise SyntaxError(f"閉じ`)`を忘れないで", error_details(self.text, self.pos))
            self.consume_whitespace()

        return FuncCallNode(name, arguments)
    
    def parse_ArrayNode(self) -> ArrayNode:
        """配列をパース"""
        saved_pos = self.pos
         # "[" で始まる
        if not self.consume("[", "【"):
            self.pos = saved_pos
            return None
        
        elements = []
        saved_pos = self.pos
        while True:
            self.consume_whitespace(include_newline=True)
            if self.consume("]", "】"):
                break
            expression = self.parse_expression()
            if expression is None:
                raise SyntaxError(f"値を忘れてます", error_details(self.text, self.pos))
            elements.append(expression)
            self.consume_whitespace(include_newline=True)
            if self.consume("]", "】"):
                break
            if not self.consume(",", "、", "，"):
                raise SyntaxError(f"閉じ`]`を忘れないで", error_details(self.text, saved_pos))

        return ArrayNode(elements)
    
    def parse_NullNode(self) -> NullNode:
        """null値をパース"""
        if self.consume("null", "?", "？"):
            return NullNode()
        return None

    def parse_VariableNode(self, definition_context = False) -> VariableNode:
        """変数をパース"""
        name = self.parse_name(definition_context=definition_context)
        if name is None:
            return None

        indices = []
        
        while self.consume("[", "【"):
            self.consume_whitespace()
            index = self.parse_expression()
            indices.append(index)
            if not self.consume("]", "】"):
                raise SyntaxError(f"閉じ `]`を忘れないで", error_details(self.text, self.pos))

        if len(indices) == 0:
            indices = None
        return VariableNode(name, indices)
    
    def parse_block(self) -> BlockNode:
        """ブロックをパース"""
        self.consume_whitespace()
        saved_pos = self.pos
        if not self.consume("{", "｛"):
            self.pos = saved_pos
            return None
        self.consume_until_eol()
        indent_depth = self.consume_whitespace()
        found_closing_brace = False
        statements = []
        while self.pos < self.length:
            self.consume_whitespace()
            if self.consume("}", "｝"):
                found_closing_brace = True
                break
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)

        if not found_closing_brace:
            raise SyntaxError("閉じ `}`を忘れないで", error_details(self.text, saved_pos))

        return BlockNode(statements)

    def parse_name(self, definition_context: bool = False) -> str:
        """識別子をパース"""
        saved_pos = self.pos
        if definition_context:
            while self.pos < self.length:
                char = self.text[self.pos]
                if char in " \t\n\r,=[](){}#　＝＃、，【】（）｛｝":
                    break
                if char in "にをの":
                    remaining = self.text[self.pos:]
                    if remaining.startswith("に対し") or remaining.startswith("を増やす") or remaining.startswith("を減らす") or remaining.startswith("の末尾に"):
                        break
                self.pos += 1
            name = self.text[saved_pos:self.pos].strip()
            if len(name) > 0:
                return name
            return None

        if self.consume(*self.variables):
            return self.text[saved_pos:self.pos]
        elif not self.consume_alpha():
            self.pos = saved_pos
            return None

        while (not self.is_keywords()) and self.consume_alpha():
            pass

        while self.consume_digit():
            pass
        
        name = self.text[saved_pos:self.pos]
        if len(name) > 0:
            return name
        return None
    
    def is_keywords(self) -> bool:
        # 除外キーワードチェック
        remaining = self.text[self.pos:]
        for kw in ["を", "とする", "が", "ならば", "に対し", "の末尾に", "を増やす"]:
            if remaining.startswith(kw):
                return True
        return False
    
    def consume_alpha(self) -> bool:
        if self.pos < self.length:
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
        c = 0
        while self.pos < self.length:
            if self.text[self.pos] in " 　\t\r":
                self.pos += 1
                c += 1
                continue
            if include_newline and self.text[self.pos] in '#＃':
                self.consume_until_eol()
                c = 0
                continue
            if include_newline and self.text[self.pos] == '\n':
                self.pos += 1
                c = 0
            else:
                break
        return c
    
    def consume_comma(self):
        self.consume("、", "，", ",")
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

