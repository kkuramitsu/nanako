// Nanako (ななこ) - JavaScript Implementation
// An educational programming language for the generative AI era.

// Polyfill for Number.isInteger if not available
if (!Number.isInteger) {
    Number.isInteger = function(value) {
        return typeof value === 'number' && 
               isFinite(value) && 
               Math.floor(value) === value;
    };
}

// Utils
function errorDetails(text, pos) {
    let line = 1;
    let col = 1;
    let start = 0;
    for (let i = 0; i < pos && i < text.length; i++) {
        if (text[i] === '\n') {
            line++;
            col = 1;
            start = i + 1;
        } else {
            col++;
        }
    }
    const end = text.indexOf('\n', start);
    const lineText = end === -1 ? text.slice(start) : text.slice(start, end);
    return { text, line, col, lineText };
}

// Runtime
class NanakoRuntime {
    constructor() {
        this.incrementCount = 0;
        this.decrementCount = 0;
        this.compareCount = 0;
        this.callFrames = []; // {funcName, args, pos}
        this.shouldStop = false;
        this.timeout = 0;
        this.startTime = 0;
    }

    pushCallFrame(funcName, args, pos) {
        this.callFrames.push({ funcName, args, pos });
    }

    popCallFrame() {
        this.callFrames.pop();
    }

    updateVariable(name, env, source, pos) {
        // JavaScript版では何もしない
    }

    print(value, source, pos) {
        const details = errorDetails(source, pos);
        console.log(`>>> ${details.lineText.trim()}\n${value}`);
    }

    start(timeout = 30) {
        this.shouldStop = false;
        this.timeout = timeout;
        this.startTime = Date.now();
    }

    checkExecution(errorDetails) {
        // 手動停止フラグのチェック
        if (this.shouldStop) {
            throw new NanakoError('プログラムが手動で停止されました', errorDetails);
        }

        // タイムアウトチェック
        if (this.timeout > 0 && (Date.now() - this.startTime) > this.timeout * 1000) {
            throw new NanakoError(`タイムアウト(${this.timeout}秒)になりました`, errorDetails);
        }
    }

    exec(code, env = null, timeout = 30) {
        if (env === null) {
            env = {};
        }
        const parser = new NanakoParser();
        const program = parser.parse(code);
        this.start(timeout);
        program.evaluate(this, env);
        return env;
    }
}

class NanakoError extends SyntaxError {
    constructor(message, details) {
        super(message);
        this.details = details;
    }
}

class ReturnBreakException extends Error {
    constructor(value = null) {
        super();
        this.value = value;
    }
}

// AST Node Classes
class ASTNode {
    constructor(source = "", pos = 0) {
        this.source = source;
        this.pos = pos;
    }

    evaluate(runtime, env) {
        throw new Error("Abstract method");
    }
}

// Statement classes
class Statement extends ASTNode {
    semicolon(lang = "js") {
        return lang === "py" ? "" : ";";
    }
}

// Expression classes
class Expression extends ASTNode {}

class Program extends Statement {
    constructor(statements, source = "", pos = 0) {
        super(source, pos);
        this.statements = statements;
    }

    evaluate(runtime, env) {
        for (const statement of this.statements) {
            statement.evaluate(runtime, env);
        }
    }

    emit(lang = "js", indent = "") {
        const lines = [];
        for (const statement of this.statements) {
            const code = statement.emit(lang, indent);
            if (code.trim()) {
                lines.push(code);
            }
        }
        return lines.join('\n');
    }
}

class Block extends Statement {
    constructor(statements, source = "", pos = 0) {
        super(source, pos);
        this.statements = statements;
    }

    evaluate(runtime, env) {
        for (const statement of this.statements) {
            statement.evaluate(runtime, env);
        }
    }

    emit(lang = "js", indent = "") {
        const lines = [];
        for (const statement of this.statements) {
            const code = statement.emit(lang, indent + "    ");
            if (code.trim()) {
                lines.push(code);
            }
        }
        return lines.join('\n');
    }
}

class NullValue extends Expression {
    constructor(source = "", pos = 0) {
        super(source, pos);
    }

    evaluate(runtime, env) {
        return null;
    }

    emit(lang = "js", indent = "") {
        return lang === "py" ? "None" : "null";
    }
}

class Number extends Expression {
    constructor(value = 0.0, source = "", pos = 0) {
        super(source, pos);
        this.value = parseFloat(value);
    }

    evaluate(runtime, env) {
        return this.value;
    }

    emit(lang = "js", indent = "") {
        return Number.isInteger(this.value) ? this.value.toString() : this.value.toString();
    }
}

class Abs extends Expression {
    constructor(element, source = "", pos = 0) {
        super(source, pos);
        this.element = element;
    }

    evaluate(runtime, env) {
        const value = this.element.evaluate(runtime, env);
        if (typeof value === 'number') {
            return Math.abs(value);
        }
        if (Array.isArray(value)) {
            return value.length;
        }
        return 0;
    }

    emit(lang = "js", indent = "") {
        if (lang === "py") {
            return `len(${this.element.emit(lang, indent)})`;
        }
        return `(${this.element.emit(lang, indent)}).length`;
    }
}

class Minus extends Expression {
    constructor(element, source = "", pos = 0) {
        super(source, pos);
        this.element = element;
    }

    evaluate(runtime, env) {
        const value = this.element.evaluate(runtime, env);
        if (typeof value !== 'number') {
            throw new NanakoError("マイナス記号（-）は数値にのみ使用できます。文字列や配列には使えません。", errorDetails(this.source, this.pos));
        }
        return -value;
    }

    emit(lang = "js", indent = "") {
        return `-${this.element.emit(lang, indent)}`;
    }
}

class ArrayList extends Expression {
    constructor(elements, source = "", pos = 0) {
        super(source, pos);
        this.elements = elements;
    }

    evaluate(runtime, env) {
        return this.elements.map(element => element.evaluate(runtime, env));
    }

    emit(lang = "js", indent = "") {
        const elements = this.elements.map(element => element.emit(lang, indent));
        return `[${elements.join(', ')}]`;
    }
}

class StringLiteral extends Expression {
    constructor(stringArray, source = "", pos = 0) {
        super(source, pos);
        this.stringArray = stringArray;
    }

    evaluate(runtime, env) {
        // 文字列を文字コードの配列に変換
        return this.stringArray;
    }

    emit(lang = "js", indent = "") {
        const str = String.fromCharCode(...this.stringArray);
        if (lang === "py") {
            return `"${str.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
        }
        return `"${str.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
    }
}

class Function extends Expression {
    constructor(parameters, body, source = "", pos = 0) {
        super(source, pos);
        this.parameters = parameters;
        this.body = body;
    }

    evaluate(runtime, env) {
        return this;
    }

    emit(lang = "js", indent = "") {
        const params = this.parameters.join(', ');
        const body = this.body.emit(lang, indent + "    ");
        if (lang === "py") {
            return `def ${this.name}(${params}):\n${body}`;
        }
        return `function(${params}) {\n${body}\n${indent}}`;
    }
}

class FuncCall extends Expression {
    constructor(name, args, source = "", pos = 0) {
        super(source, pos);
        this.name = name;
        this.arguments = args;
    }

    evaluate(runtime, env) {
        if (!(this.name in env)) {
            throw new NanakoError(`関数 '${this.name}' が見つかりません。関数を呼び出す前に定義してください。`, errorDetails(this.source, this.pos));
        }
        const func = env[this.name];
        if (func.parameters.length !== this.arguments.length) {
            throw new NanakoError(`関数 '${this.name}' の引数の数が間違っています。${func.parameters.length}個の引数が必要ですが、${this.arguments.length}個渡されました。`, errorDetails(this.source, this.pos));
        }

        const newEnv = { ...env };
        const args = [];
        for (let i = 0; i < func.parameters.length; i++) {
            const value = this.arguments[i].evaluate(runtime, env);
            newEnv[func.parameters[i]] = value;
            args.push(value);
        }
        try {
            runtime.pushCallFrame(this.name, args, this.pos);
            func.body.evaluate(runtime, newEnv);
        } catch (e) {
            if (e instanceof ReturnBreakException) {
                runtime.popCallFrame();
                return e.value;
            }
            throw e;
        }
        runtime.popCallFrame();
        return null;
    }

    emit(lang = "js", indent = "") {
        const args = this.arguments.map(arg => arg.emit(lang, indent)).join(', ');
        return `${this.name}(${args})`;
    }
}

class Variable extends Expression {
    constructor(name, indices = null, source = "", pos = 0) {
        super(source, pos);
        this.name = name;
        this.indices = indices;
    }

    getValueIndex(runtime, env) {
        if (!(this.name in env)) {
            throw new NanakoError(`変数 '${this.name}' が定義されていません。変数を使う前に値を代入してください。`, errorDetails(this.source, this.pos));
        }

        let value = env[this.name];
        if (this.indices && this.indices.length > 0) {
            for (let i = 0; i < this.indices.length; i++) {
                const index = this.indices[i].evaluate(runtime, env);
                if (typeof index !== 'number' && index !== null) {
                    throw new NanakoError("配列の添え字には数値を使ってください。文字列や他の型は使えません。", errorDetails(this.indices[i].source, this.indices[i].pos));
                }
                if (i === this.indices.length - 1) {
                    return { value, index: Math.floor(index) };
                }
                value = value[Math.floor(index)];
            }
        }
        return { value, index: -1 };
    }

    evaluate(runtime, env) {
        const { value, index } = this.getValueIndex(runtime, env);
        if (index === -1) {
            return value;
        }
        if (!Array.isArray(value)) {
            throw new NanakoError(`変数 '${this.name}' は配列ではありません。配列の要素にアクセスするには、まず配列を作成してください。`, errorDetails(this.source, this.pos));
        }
        if (index === null) {
            // ランダムに選ぶ
            return value[Math.floor(Math.random() * value.length)];
        }
        if (index >= value.length || index < 0) {
            throw new NanakoError(`配列の添え字が範囲外です。この配列の要素は0番から${value.length - 1}番まです。`, errorDetails(this.source, this.pos));
        }
        return value[index];
    }

    emit(lang = "js", indent = "") {
        if (!this.indices || this.indices.length === 0) {
            return this.name;
        }
        const indices = [];
        for (const index of this.indices) {
            const indexCode = index.emit(lang, indent);
            indices.push(`[${indexCode === "null" || indexCode === "None" ? "null" : indexCode}]`);
        }
        return this.name + indices.join('');
    }
}

class Assignment extends Statement {
    constructor(variable, expression, source = "", pos = 0) {
        super(source, pos);
        this.variable = variable;
        this.expression = expression;
    }

    evaluate(runtime, env) {
        const value = this.expression.evaluate(runtime, env);
        if (!(this.variable.name in env) && this.variable.indices === null) {
            env[this.variable.name] = 0;
        }
        const { value: varValue, index } = this.variable.getValueIndex(runtime, env);
        if (index === null) {
            // 特別な処理: var[?] = value の場合
            varValue.push(value);
        } else if (index === -1) {
            env[this.variable.name] = value;
        } else {
            varValue[index] = value;
        }
    }

    emit(lang = "js", indent = "") {
        const variable = this.variable.emit(lang, indent);
        const expression = this.expression.emit(lang, indent);
        if (variable.endsWith('[null]') || variable.endsWith('[None]')) {
            return `${indent}${variable.replace(/\[null\]$|\[None\]$/, '')}.push(${expression})${this.semicolon(lang)}`;
        }
        return `${indent}${variable} = ${expression}${this.semicolon(lang)}`;
    }
}

class Increment extends Statement {
    constructor(variable, source = "", pos = 0) {
        super(source, pos);
        this.variable = variable;
    }

    evaluate(runtime, env) {
        const { value: varValue, index } = this.variable.getValueIndex(runtime, env);
        if (index === -1) {
            if (typeof env[this.variable.name] !== 'number') {
                throw new NanakoError(`変数 '${this.variable.name}' は数値ではないので増やすことができません。数値を代入してから増やしてください。`, errorDetails(this.source, this.pos));
            }
            env[this.variable.name] += 1;
        } else {
            if (typeof varValue[index] !== 'number') {
                throw new NanakoError("配列の要素が数値ではないので増やすことができません。数値の要素のみ増やせます。", errorDetails(this.source, this.pos));
            }
            varValue[index] += 1;
        }
        runtime.incrementCount += 1;
    }

    emit(lang = "js", indent = "") {
        const variable = this.variable.emit(lang, indent);
        return `${indent}${variable} += 1${this.semicolon(lang)}`;
    }
}

class Decrement extends Statement {
    constructor(variable, source = "", pos = 0) {
        super(source, pos);
        this.variable = variable;
    }

    evaluate(runtime, env) {
        const { value: varValue, index } = this.variable.getValueIndex(runtime, env);
        if (index === -1) {
            if (typeof env[this.variable.name] !== 'number') {
                throw new NanakoError(`変数 '${this.variable.name}' は数値ではないので減らすことができません。数値を代入してから減らしてください。`, errorDetails(this.source, this.pos));
            }
            env[this.variable.name] -= 1;
        } else {
            if (typeof varValue[index] !== 'number') {
                throw new NanakoError("配列の要素が数値ではないので減らすことができません。数値の要素のみ減らせます。", errorDetails(this.source, this.pos));
            }
            varValue[index] -= 1;
        }
        runtime.decrementCount += 1;
    }

    emit(lang = "js", indent = "") {
        const variable = this.variable.emit(lang, indent);
        return `${indent}${variable} -= 1${this.semicolon(lang)}`;
    }
}

class IfStatement extends Statement {
    constructor(left, operator, right, thenBlock, elseBlock = null, source = "", pos = 0) {
        super(source, pos);
        this.left = left;
        this.operator = operator; // "以上", "以下", "より大きい", "より小さい", "以外", "未満", ""
        this.right = right;
        this.thenBlock = thenBlock;
        this.elseBlock = elseBlock;
    }

    evaluate(runtime, env) {
        const leftValue = this.left.evaluate(runtime, env);
        const rightValue = this.right.evaluate(runtime, env);
        let result;
        if (this.operator === "以上") {
            result = leftValue >= rightValue;
        } else if (this.operator === "以下") {
            result = leftValue <= rightValue;
        } else if (this.operator === "より大きい") {
            result = leftValue > rightValue;
        } else if (this.operator === "より小さい") {
            result = leftValue < rightValue;
        } else if (this.operator === "以外") {
            result = leftValue !== rightValue;
        } else if (this.operator === "未満") {
            result = leftValue < rightValue;
        } else {
            result = leftValue === rightValue;
        }
        runtime.compareCount += 1;
        if (result) {
            this.thenBlock.evaluate(runtime, env);
        } else if (this.elseBlock) {
            this.elseBlock.evaluate(runtime, env);
        }
    }

    emit(lang = "js", indent = "") {
        const left = this.left.emit(lang, indent);
        const right = this.right.emit(lang, indent);
        let op;
        if (this.operator === "以上") op = ">=";
        else if (this.operator === "以下") op = "<=";
        else if (this.operator === "より大きい") op = ">";
        else if (this.operator === "より小さい" || this.operator === "未満") op = "<";
        else if (this.operator === "以外") op = "!=";
        else op = "==";

        const condition = `${left} ${op} ${right}`;
        const thenBody = this.thenBlock.emit(lang, indent + "    ");
        
        if (lang === "py") {
            let result = `${indent}if ${condition}:\n${thenBody}`;
            if (this.elseBlock) {
                const elseBody = this.elseBlock.emit(lang, indent + "    ");
                result += `\n${indent}else:\n${elseBody}`;
            }
            return result;
        } else {
            let result = `${indent}if (${condition}) {\n${thenBody}\n${indent}}`;
            if (this.elseBlock) {
                const elseBody = this.elseBlock.emit(lang, indent + "    ");
                result += ` else {\n${elseBody}\n${indent}}`;
            }
            return result;
        }
    }
}

class LoopStatement extends Statement {
    constructor(count, body, source = "", pos = 0) {
        super(source, pos);
        this.count = count;
        this.body = body;
    }

    evaluate(runtime, env) {
        let loopCount = this.count.evaluate(runtime, env);
        const details = errorDetails(this.source, this.pos);
        if (loopCount === null) {
            while (true) {
                runtime.checkExecution(details);
                this.body.evaluate(runtime, env);
            }
        }
        if (Array.isArray(loopCount)) {
            loopCount = loopCount.length;
        }
        for (let i = 0; i < Math.abs(Math.floor(loopCount)); i++) {
            runtime.checkExecution(details);
            this.body.evaluate(runtime, env);
        }
    }

    emit(lang = "js", indent = "") {
        const count = this.count.emit(lang, indent);
        const body = this.body.emit(lang, indent + "    ");
        
        if (lang === "py") {
            return `${indent}for _ in range(${count}):\n${body}`;
        } else {
            return `${indent}for (let i = 0; i < ${count}; i++) {\n${body}\n${indent}}`;
        }
    }
}

class ReturnStatement extends Statement {
    constructor(expression, source = "", pos = 0) {
        super(source, pos);
        this.expression = expression;
    }

    evaluate(runtime, env) {
        const value = this.expression.evaluate(runtime, env);
        throw new ReturnBreakException(value);
    }

    emit(lang = "js", indent = "") {
        const expr = this.expression.emit(lang, indent);
        return `${indent}return ${expr}${this.semicolon(lang)}`;
    }
}

class ExpressionStatement extends Statement {
    constructor(expression, source = "", pos = 0) {
        super(source, pos);
        this.expression = expression;
    }

    evaluate(runtime, env) {
        const value = this.expression.evaluate(runtime, env);
        runtime.print(value, this.source, this.pos);
        return value;
    }

    emit(lang = "js", indent = "") {
        const expr = this.expression.emit(lang, indent);
        if (lang === "py") {
            return `${indent}print(${expr})`;
        } else {
            return `${indent}console.log(${expr})${this.semicolon(lang)}`;
        }
    }
}

class DocTest extends Statement {
    constructor(expression, answer, pos = 0) {
        super("", pos);
        this.expression = expression;
        this.answer = answer;
    }

    evaluate(runtime, env) {
        const value = this.expression.evaluate(runtime, env);
        const answerValue = this.answer.evaluate(runtime, env);
        if (value !== answerValue) {
            throw new NanakoError(`テストに失敗: ${value}`, errorDetails(this.source, this.pos));
        }
    }

    emit(lang = "js", indent = "") {
        const expr = this.expression.emit(lang, indent);
        const answer = this.answer.emit(lang, indent);
        if (lang === "py") {
            return `${indent}assert ${expr} == ${answer}`;
        } else {
            return `${indent}console.assert(${expr} === ${answer})${this.semicolon(lang)}`;
        }
    }
}

class NanakoParser {
    constructor() {
        this.text = "";
        this.pos = 0;
        this.length = 0;
    }

    parse(text) {
        this.text = this.normalize(text);
        this.pos = 0;
        this.length = this.text.length;
        return this.parseProgram();
    }

    normalize(text) {
        // 全角文字を半角に変換
        text = text.replace(/"/g, '"').replace(/"/g, '"');
        return text.replace(/[０-９Ａ-Ｚａ-ｚ]/g, function(match) {
            return String.fromCharCode(match.charCodeAt(0) - 0xFEE0);
        });
    }

    errorDetails(pos) {
        return errorDetails(this.text, pos);
    }

    parseProgram() {
        const statements = [];
        this.consumeWhitespace(true);
        while (this.pos < this.length) {
            try {
                const stmt = this.parseStatement();
                if (stmt) {
                    statements.push(stmt);
                }
                this.consumeWhitespace(true);
            } catch (e) {
                console.error(e);
                this.consumeUntilEol();
            }
        }
        return new Program(statements);
    }

    parseStatement(text = null) {
        if (text !== null) {
            this.text = text;
            this.pos = 0;
            this.length = text.length;
        }

        this.consumeWhitespace(true);
        const savedPos = this.pos;

        let stmt = this.parseIfStatement();
        if (!stmt) {
            stmt = this.parseLoopStatement();
        }
        if (!stmt) {
            stmt = this.parseReturn();
        }
        if (!stmt) {
            stmt = this.parseDocTest();
        }
        if (!stmt) {
            stmt = this.parseAssignment();
        }
        if (stmt) {
            stmt.source = this.text;
            stmt.pos = savedPos;
            return stmt;
        }
        throw new SyntaxError("Expected statement");
    }

    parseDocTest() {
        const savedPos = this.pos;
        if (!this.consumeString(">>>")) {
            this.pos = savedPos;
            return null;
        }

        this.consumeWhitespace();
        const expression = this.parseExpression();
        if (expression === null) {
            throw new SyntaxError("`>>>` の後には式が必要です");
        }
        this.consumeEol();
        const answerExpression = this.parseExpression();
        if (answerExpression === null) {
            throw new SyntaxError("`>>>` の次の行には正解の値が必要です");
        }
        this.consumeEol();
        return new DocTest(expression, answerExpression);
    }

    parseAssignment() {
        const savedPos = this.pos;

        const variable = this.parseVariable();
        if (variable === null) {
            this.pos = savedPos;
            return null;
        }

        this.consumeWhitespace();

        if (this.consumeString("を")) {
            this.consumeWhitespace();
            if (this.consumeString("増やす")) {
                this.consumeEol();
                return new Increment(variable);
            }
            if (this.consumeString("減らす")) {
                this.consumeEol();
                return new Decrement(variable);
            }

            const expression = this.parseExpression();
            if (expression === null) {
                throw new SyntaxError("Expected expression");
            }

            // オプションの "とする"
            this.consumeWhitespace();
            this.consumeString("とする");
            this.consumeEol();
            return new Assignment(variable, expression);
        }

        // "="
        const savedPos2 = this.pos;
        if (this.consumeString("=")) {
            this.consumeWhitespace();
            const expression = this.parseExpression();

            if (expression === null) {
                throw new SyntaxError("Expected expression");
            }

            this.consumeEol();
            return new Assignment(variable, expression);
        }

        throw new SyntaxError("Expected '='");
    }

    parseIfStatement() {
        const savedPos = this.pos;

        if (!this.consumeString("もし")) {
            this.pos = savedPos;
            return null;
        }
        this.consumeCma();

        const left = this.parseExpression();
        if (!this.consumeString("が")) {
            throw new SyntaxError("Expected 'が'");
        }

        this.consumeCma();
        const right = this.parseExpression();
        this.consumeWhitespace();

        // 比較演算子
        let operator = "";
        for (const op of ["以上", "以下", "より大きい", "より小さい", "以外", "未満"]) {
            if (this.consumeString(op)) {
                operator = op;
                break;
            }
        }

        this.consumeWhitespace();
        if (!this.consumeString("ならば")) {
            throw new SyntaxError("Expected 'ならば'");
        }
        this.consumeCma();

        const thenBlock = this.parseBlock();
        if (thenBlock === null) {
            throw new SyntaxError("Expected block after 'ならば'");
        }
        this.consumeEol();

        // else節（オプション）
        const elseBlock = this.parseElseStatement();
        return new IfStatement(left, operator, right, thenBlock, elseBlock);
    }

    parseElseStatement() {
        const savedPos = this.pos;
        this.consumeWhitespace();
        if (!this.consumeString("そうでなければ")) {
            this.pos = savedPos;
            return null;
        }
        this.consumeCma();
        const block = this.parseBlock();
        if (block === null) {
            throw new SyntaxError("Expected block after 'そうでなければ'");
        }
        this.consumeEol();
        return block;
    }

    parseLoopStatement() {
        const savedPos = this.pos;
        const count = this.parseExpression();
        if (count === null) {
            this.pos = savedPos;
            return null;
        }
        if (!this.consumeString("回")) {
            this.pos = savedPos;
            return null;
        }
        this.consumeCma();
        if (!this.consumeString("くり返す")) {
            throw new SyntaxError("Expected 'くり返す'");
        }

        const body = this.parseBlock();
        if (body === null) {
            throw new SyntaxError("Expected loop body");
        }
        this.consumeEol();
        return new LoopStatement(count, body);
    }

    parseReturn() {
        const savedPos = this.pos;
        const expression = this.parseExpression();
        if (expression && this.consumeString("が答え")) {
            this.consumeEol();
            return new ReturnStatement(expression);
        }
        this.pos = savedPos;
        return null;
    }

    parseExpression(text = null) {
        if (text !== null) {
            this.text = text;
            this.pos = 0;
            this.length = text.length;
        }
        this.consumeWhitespace();
        const savedPos = this.pos;
        let expression = this.parseInteger();
        if (!expression) {
            expression = this.parseString();
        }
        if (!expression) {
            expression = this.parseAbs();
        }
        if (!expression) {
            expression = this.parseMinus();
        }
        if (!expression) {
            expression = this.parseFunction();
        }
        if (!expression) {
            expression = this.parseArrayList();
        }
        if (!expression) {
            expression = this.parseNull();
        }
        if (!expression) {
            expression = this.parseFuncCall();
        }
        if (!expression) {
            expression = this.parseVariable();
        }

        if (expression) {
            if (this.consume("+", "-", "*", "/", "%")) {
                throw new SyntaxError("中置記法は使えないよ");
            }
            expression.pos = savedPos;
            expression.source = this.text;
            return expression;
        }

        return null;
    }

    parseInteger() {
        const savedPos = this.pos;
        if (!this.consumeDigit()) {
            this.pos = savedPos;
            return null;
        }

        // 数字
        while (this.consumeDigit()) {
            // continue
        }

        const valueStr = this.text.slice(savedPos, this.pos);
        try {
            const value = parseInt(valueStr);
            this.consumeWhitespace();
            return new Number(value, this.text, savedPos);
        } catch (e) {
            this.pos = savedPos;
            return null;
        }
    }

    parseString() {
        const savedPos = this.pos;

        // ダブルクォート開始
        if (!this.consumeString('"')) {
            this.pos = savedPos;
            return null;
        }

        // 文字列内容を読み取り
        const stringContent = [];
        while (this.pos < this.length && this.text[this.pos] !== '"') {
            const char = this.text[this.pos];
            if (char === '\\' && this.pos + 1 < this.length) {
                // エスケープシーケンスの処理
                this.pos++;
                const nextChar = this.text[this.pos];
                if (nextChar === 'n') {
                    stringContent.push('\n'.charCodeAt(0));
                } else if (nextChar === 't') {
                    stringContent.push('\t'.charCodeAt(0));
                } else if (nextChar === '\\') {
                    stringContent.push('\\'.charCodeAt(0));
                } else if (nextChar === '"') {
                    stringContent.push('"'.charCodeAt(0));
                } else {
                    stringContent.push(nextChar.charCodeAt(0));
                }
            } else {
                stringContent.push(char.charCodeAt(0));
            }
            this.pos++;
        }

        // ダブルクォート終了
        if (!this.consumeString('"')) {
            this.pos = savedPos;
            throw new SyntaxError("閉じていない文字列");
        }

        this.consumeWhitespace();
        return new StringLiteral(stringContent, this.text, savedPos);
    }

    parseMinus() {
        const savedPos = this.pos;

        // マイナス符号（オプション）
        if (!this.consumeString("-")) {
            this.pos = savedPos;
            return null;
        }
        this.consumeWhitespace();
        const element = this.parseExpression();
        if (element === null) {
            throw new SyntaxError("Expected expression after '-'");
        }
        this.consumeWhitespace();
        return new Minus(element, this.text, savedPos);
    }

    parseAbs() {
        const savedPos = this.pos;
        if (!this.consumeString("|")) {
            this.pos = savedPos;
            return null;
        }

        this.consumeWhitespace();
        const element = this.parseExpression();
        if (element === null) {
            throw new SyntaxError("Expected expression after '|'");
        }
        this.consumeWhitespace();
        if (!this.consumeString("|")) {
            throw new SyntaxError("Expected closing '|'");
        }
        this.consumeWhitespace();
        return new Abs(element, this.text, savedPos);
    }

    parseFunction() {
        const savedPos = this.pos;
        // "λ" または "入力"
        if (!this.consumeString("λ") && !this.consumeString("入力")) {
            this.pos = savedPos;
            return null;
        }

        this.consumeWhitespace();

        // パラメータ
        const parameters = [];
        while (true) {
            const identifier = this.parseIdentifier();
            if (identifier === null) {
                throw new SyntaxError("Expected identifier");
            }
            if (parameters.includes(identifier)) {
                throw new SyntaxError(`Duplicate parameter '${identifier}'`);
            }
            parameters.push(identifier);
            this.consumeWhitespace();
            if (!this.consumeString(",")) {
                break;
            }
            this.consumeWhitespace();
        }

        if (parameters.length === 0) {
            throw new SyntaxError("Expected parameter");
        }

        this.consumeWhitespace();
        if (!this.consumeString("に対し")) {
            throw new SyntaxError("Expected 'に対し'");
        }
        this.consumeString("て");
        this.consumeCma();
        const body = this.parseBlock();

        if (body === null) {
            throw new SyntaxError("Expected function body");
        }
        this.consumeWhitespace();
        return new Function(parameters, body, this.text, savedPos);
    }

    parseFuncCall() {
        const savedPos = this.pos;
        const name = this.parseIdentifier();
        if (name === null) {
            this.pos = savedPos;
            return null;
        }
        this.consumeWhitespace();

        if (!this.consumeString("(")) {
            this.pos = savedPos;
            return null;
        }

        this.consumeWhitespace();

        const args = [];
        while (true) {
            const expression = this.parseExpression();
            if (expression === null) {
                throw new SyntaxError("Expected expression in function call");
            }
            args.push(expression);
            this.consumeWhitespace();
            if (this.consumeString(")")) {
                break;
            }
            if (!this.consumeString(",")) {
                throw new SyntaxError("Expected ',' or ')' in function call");
            }
            this.consumeWhitespace();
        }

        this.consumeWhitespace();
        return new FuncCall(name, args, this.text, savedPos);
    }

    parseArrayList() {
        const savedPos = this.pos;
        // "[" で始まる
        if (!this.consumeString("[")) {
            this.pos = savedPos;
            return null;
        }

        const elements = [];
        const savedPos2 = this.pos;
        while (true) {
            this.consumeWhitespace();
            if (this.consumeString("]")) {
                break;
            }
            const expression = this.parseExpression();
            if (expression === null) {
                throw new SyntaxError("ここには式が来るはずです");
            }
            elements.push(expression);
            this.consumeWhitespace();
            if (this.consumeString("]")) {
                break;
            }
            if (!this.consumeString(",")) {
                throw new SyntaxError("閉じ`]`がないよ");
            }
        }

        this.consumeWhitespace();
        return new ArrayList(elements, this.text, savedPos);
    }

    parseNull() {
        const savedPos = this.pos;
        if (this.consume("null", "?", "？")) {
            this.consumeWhitespace();
            return new NullValue(this.text, savedPos);
        }
        return null;
    }

    parseVariable() {
        const savedPos = this.pos;
        const name = this.parseIdentifier();
        if (name === null) {
            return null;
        }
        const indices = [];

        this.consumeWhitespace();
        while (this.consumeString("[")) {
            this.consumeWhitespace();
            const index = this.parseExpression();
            indices.push(index);
            if (!this.consumeString("]")) {
                throw new SyntaxError("閉じ`]`が必要だよ");
            }
            this.consumeWhitespace();
        }
        return new Variable(name, indices.length === 0 ? null : indices, this.text, savedPos);
    }

    parseBlock() {
        this.consumeWhitespace();
        if (!this.consumeString("{")) {
            throw new SyntaxError("Expected opening '{'");
        }
        this.consumeUntilEol();
        const indentDepth = this.consumeWhitespace();
        let foundClosingBrace = false;
        const statements = [];
        while (this.pos < this.length) {
            this.consumeWhitespace();
            if (this.consumeString("}")) {
                foundClosingBrace = true;
                break;
            }
            const stmt = this.parseStatement();
            if (stmt) {
                statements.push(stmt);
            }
        }

        if (!foundClosingBrace) {
            throw new SyntaxError("Expected closing '}'");
        }

        this.consumeWhitespace();
        return new Block(statements);
    }

    parseIdentifier() {
        const savedPos = this.pos;
        if (!this.consumeAlpha()) {
            this.pos = savedPos;
            return null;
        }

        while (this.notIdentifierWords() && this.consumeAlpha()) {
            // continue
        }

        while (this.consumeDigit()) {
            // continue
        }

        return this.text.slice(savedPos, this.pos);
    }

    notIdentifierWords() {
        // 除外キーワードチェック
        const remaining = this.text.slice(this.pos);
        for (const kw of ["くり返す", "を", "回", "とする", "が", "ならば", "に対し"]) {
            if (remaining.startsWith(kw)) {
                return false;
            }
        }
        return true;
    }

    consumeAlpha() {
        if (this.pos >= this.length) {
            return false;
        }
        const char = this.text[this.pos];
        if (char.match(/[a-zA-Z_]/) || 
                (char >= '\u4e00' && char <= '\u9fff') ||  // 漢字
                (char >= '\u3040' && char <= '\u309f') ||  // ひらがな
                (char >= '\u30a0' && char <= '\u30ff') ||  // カタカナ
                char === 'ー') {
            this.pos++;
            return true;
        }
        return false;
    }

    consume(...strings) {
        for (const string of strings) {
            if (this.consumeString(string)) {
                return true;
            }
        }
        return false;
    }

    consumeString(string) {
        if (this.text.slice(this.pos).startsWith(string)) {
            this.pos += string.length;
            return true;
        }
        return false;
    }

    consumeDigit() {
        if (this.pos >= this.length) {
            return false;
        }
        if (this.text[this.pos].match(/\d/)) {
            this.pos++;
            return true;
        }
        return false;
    }

    consumeWhitespace(includeNewline = false) {
        const WS = includeNewline ? " 　\t\n\r" : " 　\t";
        let c = 0;
        while (this.pos < this.length) {
            if (this.text[this.pos] === '#' || this.text[this.pos] === '＃') {
                this.pos++;
                this.consumeUntilEol();
            } else if (WS.includes(this.text[this.pos])) {
                this.pos++;
                c++;
            } else {
                break;
            }
        }
        return c;
    }

    consumeCma() {
        this.consume("、", "，", ",");
        this.consumeWhitespace();
    }

    consumeEol() {
        this.consumeWhitespace();
        if (this.pos < this.length && this.text[this.pos] === '\n') {
            this.pos++;
        } else if (this.pos >= this.length) {
            // ファイル終端
        } else {
            // EOLが見つからない場合でもエラーにしない
        }
    }

    consumeUntilEol() {
        while (this.pos < this.length && this.text[this.pos] !== '\n') {
            this.pos++;
        }
        if (this.pos < this.length) {
            this.pos++;
        }
    }
}

// Export for Node.js if in Node environment
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        NanakoRuntime,
        NanakoParser,
        NanakoError,
        ReturnBreakException,
        // AST nodes
        ASTNode,
        Statement,
        Expression,
        Program,
        Block,
        NullValue,
        Number,
        Abs,
        Minus,
        ArrayList,
        StringLiteral,
        Function,
        FuncCall,
        Variable,
        Assignment,
        Increment,
        Decrement,
        IfStatement,
        LoopStatement,
        ReturnStatement,
        DocTest
    };
}