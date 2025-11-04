// Nanako (ななこ) - JavaScript Implementation
// An educational programming language for the generative AI era.

// Version
const NANAKO_VERSION = "0.3.1";

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
    return { text, line, col, pos, lineText };
}

function transformArray(values) {
    if (Array.isArray(values)) {
        return new NanakoArray(values);
    }
    if (typeof values === 'string') {
        return new NanakoArray(values);
    }
    if (values && typeof values === 'object' && !Array.isArray(values) && !(values instanceof NanakoArray) && !(values instanceof ASTNode)) {
        try {
            for (const [key, value] of Object.entries(values)) {
                values[key] = transformArray(value);
            }
            return values;
        } catch (e) {
            console.warn('transformArray failed on object:', values, e);
            return values;
        }
    }
    return values;
}

function stringfyAsJson(env) {
    const lines = ["{"];
    const indent = "    ";
    for (const [key, value] of Object.entries(env)) {
        const keyStr = `${indent}"${key}":`;
        if (typeof value === 'number') {
            lines.push(`${keyStr} ${Math.floor(value)},`);
        } else if (value instanceof NanakoArray) {
            const content = value.emit("js", indent);
            lines.push(`${keyStr} ${content},`);
        } else if (value === null) {
            lines.push(`${keyStr} null,`);
        }
    }
    if (lines.length > 1) {
        lines[lines.length - 1] = lines[lines.length - 1].slice(0, -1);
    }
    lines.push("}");
    return lines.join('\n');
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
        this.interactiveMode = false;
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

    print(value, source, pos, endPos) {
        const details = errorDetails(source, pos);
        if (this.interactiveMode) {
            console.log(`${value}`);
        } else {
            console.log(`>>> ${details.lineText.trim()}   #(${details.line}行目)\n${value}`);
        }
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
        } else {
            env = transformArray(env);
        }
        const parser = new NanakoParser();
        const program = parser.parse(code);
        this.start(timeout);
        program.evaluate(this, env);
        return env;
    }

    transformArray(value) {
        return transformArray(value);
    }

    stringfyAsJson(env) {
        env = this.transformArray(env);
        return stringfyAsJson(env);
    }
}

class NanakoArray {
    constructor(values) {
        if (typeof values === 'string') {
            this.elements = Array.from(values, ch => ch.charCodeAt(0));
            this.isStringView = true;
        } else if (Array.isArray(values)) {
            this.elements = values.map(v => transformArray(v));
            this.isStringView = false;
        } else {
            // Handle non-array, non-string values
            this.elements = [];
            this.isStringView = false;
        }
    }

    emit(lang = "js", indent = "") {
        if (this.isStringView) {
            const chars = [];
            for (const code of this.elements) {
                chars.push(String.fromCharCode(code));
            }
            const content = chars.join('').replace(/\\/g, '\\\\').replace(/\n/g, '\\n').replace(/\t/g, '\\t').replace(/"/g, '\\"');
            return '"' + content + '"';
        }
        if (this.elements.length === 0) {
            return "[]";
        }
        if (this.elements[0] instanceof NanakoArray) {
            const lines = ["["];
            for (const element of this.elements) {
                const line = element.emit(lang, indent + "  ");
                lines.push(`    ${indent}${line},`);
            }
            lines[lines.length - 1] = lines[lines.length - 1].slice(0, -1);
            lines.push(`${indent}]`);
            return lines.join('\n');
        }
        const elements = [];
        for (const element of this.elements) {
            elements.push(String(element));
        }
        return "[" + elements.join(", ") + "]";
    }

    toString() {
        return this.emit("js", "");
    }

    equals(other) {
        if (other instanceof NanakoArray) {
            if (this.elements.length !== other.elements.length) {
                return false;
            }
            for (let i = 0; i < this.elements.length; i++) {
                const a = this.elements[i];
                const b = other.elements[i];
                if (a instanceof NanakoArray && b instanceof NanakoArray) {
                    if (!a.equals(b)) {
                        return false;
                    }
                } else if (a !== b) {
                    return false;
                }
            }
            return true;
        }
        return false;
    }
}

class NanakoError extends SyntaxError {
    constructor(message, details) {
        super(message);
        this.details = details;
        if (details && typeof details === 'object') {
            this.line = details.line;
            this.col = details.col;
            this.pos = details.pos;
        }
    }
}

class BreakBreakException extends Error {
    constructor() {
        super();
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
    constructor() {
        this.source = "";
        this.pos = 0;
        this.endPos = 0;
    }

    errorDetails() {
        return errorDetails(this.source, this.pos);
    }

    evaluate(runtime, env) {
        throw new Error("Abstract method");
    }

    emit(lang = "js", indent = "") {
        throw new Error("Abstract method");
    }
}

// Statement classes
class StatementNode extends ASTNode {
    semicolon(lang = "js") {
        return lang === "py" ? "" : ";";
    }
}

// Expression classes
class ExpressionNode extends ASTNode {}

class ProgramNode extends StatementNode {
    constructor(statements) {
        super();
        this.statements = Array.isArray(statements) ? statements : [];
    }

    evaluate(runtime, env) {
        if (Array.isArray(this.statements)) {
            for (const statement of this.statements) {
                statement.evaluate(runtime, env);
            }
        }
    }

    emit(lang = "js", indent = "") {
        const lines = [];
        if (Array.isArray(this.statements)) {
            for (const statement of this.statements) {
                lines.push(statement.emit(lang, indent));
            }
        }
        return lines.join("\n");
    }
}

class BlockNode extends StatementNode {
    constructor(statements) {
        super();
        this.statements = Array.isArray(statements) ? statements : [];
    }

    evaluate(runtime, env) {
        if (Array.isArray(this.statements)) {
            for (const statement of this.statements) {
                statement.evaluate(runtime, env);
            }
        }
    }

    emit(lang = "js", indent = "") {
        const lines = [];
        if (Array.isArray(this.statements)) {
            for (const statement of this.statements) {
                lines.push(statement.emit(lang, indent + "    "));
            }
        }
        if (lang === "py") {
            if (lines.length === 0) {
                lines.push(`${indent}pass`);
            }
        } else {
            lines.push(`${indent}}`);
        }
        return lines.join("\n");
    }
}

class NullNode extends ExpressionNode {
    evaluate(runtime, env) {
        return null;
    }

    emit(lang = "js", indent = "") {
        return lang === "py" ? "None" : "null";
    }
}

class NumberNode extends ExpressionNode {
    constructor(value = 0) {
        super();
        this.value = parseInt(value);
    }

    evaluate(runtime, env) {
        return this.value;
    }

    emit(lang = "js", indent = "") {
        return String(this.value);
    }
}

class LenNode extends ExpressionNode {
    constructor(element) {
        super();
        this.element = element;
    }

    evaluate(runtime, env) {
        const value = this.element.evaluate(runtime, env);
        if (value instanceof NanakoArray) {
            return value.elements.length;
        }
        throw new NanakoError(`配列じゃないね？ ❌${value}`, this.element.errorDetails());
    }

    emit(lang = "js", indent = "") {
        if (lang === "py") {
            return "len(" + this.element.emit(lang, indent) + ")";
        }
        return "(" + this.element.emit(lang, indent) + ").length";
    }
}

class MinusNode extends ExpressionNode {
    constructor(element) {
        super();
        this.element = element;
    }

    evaluate(runtime, env) {
        const value = this.element.evaluate(runtime, env);
        if (typeof value !== 'number') {
            throw new NanakoError("数ではないよ", this.errorDetails());
        }
        return -value;
    }

    emit(lang = "js", indent = "") {
        return `-${this.element.emit(lang, indent)}`;
    }
}

class ArrayNode extends ExpressionNode {
    constructor(elements) {
        super();
        this.elements = elements;
    }

    evaluate(runtime, env) {
        const arrayContent = this.elements.map(element => element.evaluate(runtime, env));
        return new NanakoArray(arrayContent);
    }

    emit(lang = "js", indent = "") {
        const elements = [];
        if (Array.isArray(this.elements)) {
            for (const element of this.elements) {
                elements.push(element.emit(lang, indent));
            }
        }
        return "[" + elements.join(", ") + "]";
    }
}

class StringNode extends ExpressionNode {
    constructor(content) {
        super();
        this.value = new NanakoArray(content);
    }

    evaluate(runtime, env) {
        return this.value;
    }

    emit(lang = "js", indent = "") {
        return this.value.emit(lang, indent);
    }
}

class FunctionNode extends ExpressionNode {
    constructor(parameters, body) {
        super();
        this.name = "<lambda>";
        this.parameters = parameters;
        this.body = body;
    }

    evaluate(runtime, env) {
        return this;
    }

    emit(lang = "js", indent = "") {
        // Debug parameters
        // console.log("FunctionNode emit - parameters:", this.parameters, "type:", typeof this.parameters, "isArray:", Array.isArray(this.parameters));
        // console.log("FunctionNode emit - body:", this.body, "type:", typeof this.body);
        
        const params = Array.isArray(this.parameters) ? this.parameters.join(", ") : (this.parameters || "");
        
        let body = "";
        if (this.body) {
            body = this.body.emit(lang, indent);
        }
                
        if (lang === "py") {
            if (this.name && this.name !== "<lambda>") {
                // Named function definition
                return `def ${this.name}(${params}):\n${body}\n`;
            }
            // Anonymous lambda function
            return `lambda ${params}: (${body.trim()})`;
        }
        // JavaScript function
        // if (this.name && this.name !== "<lambda>") {
        //     return `function ${this.name}(${params}) {\n${body}\n}`;
        // }
        return `function (${params}) {\n${body}`;
    }
}

class FuncCallNode extends ExpressionNode {
    constructor(name, args) {
        super();
        this.name = name;
        this.arguments = args;
    }

    evaluate(runtime, env) {
        if (!(this.name in env)) {
            throw new NanakoError(`関数 '${this.name}' が見つかりません`, this.errorDetails());
        }
        const func = env[this.name];
        if (func.parameters.length !== this.arguments.length) {
            throw new NanakoError("引数の数が一致しません", this.errorDetails());
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
        const args = [];
        if (Array.isArray(this.arguments)) {
            for (const argument of this.arguments) {
                args.push(argument.emit(lang, indent));
            }
        }
        const params = args.join(", ");
        return `${this.name}(${params})`;
    }
}

class VariableNode extends ExpressionNode {
    constructor(name, indices = null) {
        super();
        this.name = name;
        this.indices = indices;
    }

    evaluate(runtime, env) {
        if (!(this.name in env)) {
            throw new NanakoError(`知らない変数だよ！ '${this.name}'`, this.errorDetails());
        }
        let value = env[this.name];
        if (this.indices === null || this.indices.length === 0) {
            return value;
        }

        let array = env[this.name];
        for (const index of this.indices) {
            if (!(array instanceof NanakoArray)) {
                throw new NanakoError(`配列ではありません: ❌${array}`, this.errorDetails());
            }
            const indexValue = index.evaluate(runtime, env);
            if (typeof indexValue === 'number') {
                const idx = Math.floor(indexValue);
                if (0 <= idx && idx < array.elements.length) {
                    array = array.elements[idx];
                    continue;
                }
            }
            throw new NanakoError(`配列の添え字は0から${array.elements.length - 1}の間ですよ: ❌${indexValue}`, index.errorDetails());
        }
        return array;
    }

    evaluateWith(runtime, env, value) {
        if (this.indices === null || this.indices.length === 0) {
            env[this.name] = value;
            return;
        }

        if (!(this.name in env)) {
            throw new NanakoError(`知らない変数だよ！ '${this.name}'`, this.errorDetails());
        }

        let array = env[this.name];
        for (let i = 0; i < this.indices.length; i++) {
            if (!(array instanceof NanakoArray)) {
                throw new NanakoError(`配列ではありません: ❌${array}`, this.errorDetails());
            }
            const indexValue = this.indices[i].evaluate(runtime, env);
            if (typeof indexValue === 'number') {
                const idx = Math.floor(indexValue);
                if (idx < 0 || idx >= array.elements.length) {
                    break;
                }
                if (i === this.indices.length - 1) {
                    array.elements[idx] = value;
                    return;
                }
                array = array.elements[idx];
            } else if (indexValue === null) {
                if (i === this.indices.length - 1) {
                    array.elements.push(value);
                    return;
                }
            }
            break;
        }
        throw new NanakoError(`配列の添え字は0から${array.elements.length - 1}の間ですよ: ❌${indexValue}`, this.indices[0].errorDetails());
    }

    emit(lang = "js", indent = "") {
        if (this.indices === null || this.indices.length === 0) {
            return this.name;
        }
        const indices = [];
        if (Array.isArray(this.indices)) {
            for (const index of this.indices) {
                indices.push(`[${index.emit(lang, indent)}]`);
            }
        }
        const indicesStr = indices.join('');
        return `${this.name}${indicesStr}`;
    }
}

class AssignmentNode extends StatementNode {
    constructor(variable, expression) {
        super();
        this.variable = variable;
        this.expression = expression;
        if (expression instanceof FunctionNode) {
            expression.name = variable.name;
        }
    }

    evaluate(runtime, env) {
        const value = this.expression.evaluate(runtime, env);
        this.variable.evaluateWith(runtime, env, value);
        runtime.updateVariable(this.variable.name, env, this.source, this.pos);
    }

    emit(lang = "js", indent = "") {
        const variable = this.variable.emit(lang, indent);
        const expression = this.expression.emit(lang, indent);
        if (variable.endsWith('[null]') || variable.endsWith('[None]')) {
            if (lang === "py") {
                return `${indent}${variable.slice(0, -6)}.append(${expression})`;
            }
            if (lang === "js") {
                return `${indent}${variable.slice(0, -6)}.push(${expression})${this.semicolon(lang)}`;
            }
        }
        if (this.expression instanceof FunctionNode) {
            // Python function definition: def funcname(args): body
            if (lang === "py") {
                return `${indent}${expression}`;
            }
            return `${indent}${variable} = ${expression}\n`;
        }
        return `${indent}${variable} = ${expression}${this.semicolon(lang)}`;
    }
}

class IncrementNode extends StatementNode {
    constructor(variable) {
        super();
        this.variable = variable;
    }

    evaluate(runtime, env) {
        const value = this.variable.evaluate(runtime, env);
        if (typeof value !== 'number') {
            throw new NanakoError(`数じゃないよ: ❌${value}`, this.variable.errorDetails());
        }
        this.variable.evaluateWith(runtime, env, value + 1);
        runtime.incrementCount += 1;
    }

    emit(lang = "js", indent = "") {
        const variable = this.variable.emit(lang, indent);
        return `${indent}${variable} += 1${this.semicolon(lang)}`;
    }
}

class DecrementNode extends StatementNode {
    constructor(variable) {
        super();
        this.variable = variable;
    }

    evaluate(runtime, env) {
        const value = this.variable.evaluate(runtime, env);
        if (typeof value !== 'number') {
            throw new NanakoError(`数じゃないよ: ❌${value}`, this.variable.errorDetails());
        }
        this.variable.evaluateWith(runtime, env, value - 1);
        runtime.decrementCount += 1;
    }

    emit(lang = "js", indent = "") {
        const variable = this.variable.emit(lang, indent);
        return `${indent}${variable} -= 1${this.semicolon(lang)}`;
    }
}

class AppendNode extends StatementNode {
    constructor(variable, expression) {
        super();
        this.variable = variable;
        this.expression = expression;
    }

    evaluate(runtime, env) {
        const array = this.variable.evaluate(runtime, env);
        if (!(array instanceof NanakoArray)) {
            throw new NanakoError(`配列じゃないね？ ❌${array}`, this.variable.errorDetails());
        }
        const value = this.expression.evaluate(runtime, env);
        array.elements.push(value);
    }

    emit(lang = "js", indent = "") {
        const variable = this.variable.emit(lang, indent);
        const expression = this.expression.emit(lang, indent);
        if (lang === "py") {
            return `${indent}${variable}.append(${expression})`;
        }
        if (lang === "js") {
            return `${indent}${variable}.push(${expression})${this.semicolon(lang)}`;
        }
        return `${indent}${variable}.append(${expression})`;
    }
}

class IfNode extends StatementNode {
    constructor(left, operator, right, thenBlock, elseBlock = null) {
        super();
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
        if (this.operator === "以上") {
            op = ">=";
        } else if (this.operator === "以下") {
            op = "<=";
        } else if (this.operator === "より大きい") {
            op = ">";
        } else if (this.operator === "より小さい") {
            op = "<";
        } else if (this.operator === "以外") {
            op = "!=";
        } else if (this.operator === "未満") {
            op = "<";
        } else {
            op = "==";
        }
        const lines = [];
        if (lang === "py") {
            lines.push(`${indent}if ${left} ${op} ${right}:`);
        } else {
            lines.push(`${indent}if(${left} ${op} ${right}) {`);
        }
        lines.push(this.thenBlock.emit(lang, indent));
        if (this.elseBlock) {
            if (lang === "py") {
                lines.push(`${indent}else:`);
            } else {
                lines.push(`${indent}else {`);
            }
            lines.push(this.elseBlock.emit(lang, indent));
        }
        return lines.join("\n");
    }
}

class LoopNode extends StatementNode {
    constructor(count, body) {
        super();
        this.count = count;
        this.body = body;
    }

    evaluate(runtime, env) {
        const loopCount = this.count.evaluate(runtime, env);
        const details = errorDetails(this.source, this.pos);
        if (loopCount === null) {
            try {
                while (true) {
                    runtime.checkExecution(details);
                    this.body.evaluate(runtime, env);
                }
            } catch (e) {
                if (e instanceof BreakBreakException) {
                    return;
                }
                throw e;
            }
        }
        if (Array.isArray(loopCount)) {
            throw new NanakoError(`配列の長さでは？`, details);
        }
        if (loopCount < 0) {
            throw new NanakoError(`負のループ回数: ${loopCount}`, details);
        }
        try {
            for (let i = 0; i < Math.floor(loopCount); i++) {
                runtime.checkExecution(details);
                this.body.evaluate(runtime, env);
            }
        } catch (e) {
            if (e instanceof BreakBreakException) {
                return;
            }
            throw e;
        }
    }

    emit(lang = "js", indent = "") {
        const lines = [];
        if (this.count instanceof NullNode) {
            if (lang === "py") {
                lines.push(`${indent}while True:`);
            } else {
                lines.push(`${indent}while(true) {`);
            }
        } else {
            const count = this.count.emit(lang, indent);
            if (lang === "py") {
                lines.push(`${indent}for _ in range(${count}):`);
            } else {
                const i = `i${Math.floor(indent.length / 4)}`;
                lines.push(`${indent}for(var ${i} = 0; ${i} < ${count}; ${i}++) {`);
            }
        }

        lines.push(this.body.emit(lang, indent));
        return lines.join("\n");
    }
}

class BreakNode extends StatementNode {
    constructor() {
        super();
    }

    evaluate(runtime, env) {
        throw new BreakBreakException();
    }

    emit(lang = "js", indent = "") {
        return `${indent}break${this.semicolon(lang)}`;
    }
}

class ReturnNode extends StatementNode {
    constructor(expression) {
        super();
        this.expression = expression;
    }

    evaluate(runtime, env) {
        const value = this.expression.evaluate(runtime, env);
        throw new ReturnBreakException(value);
    }

    emit(lang = "js", indent = "") {
        return `${indent}return ${this.expression.emit(lang, indent)}${this.semicolon(lang)}`;
    }
}

class ExpressionStatementNode extends StatementNode {
    constructor(expression) {
        super();
        this.expression = expression;
    }

    evaluate(runtime, env) {
        const value = this.expression.evaluate(runtime, env);
        const e = this.expression;
        runtime.print(value, e.source, e.pos, e.endPos);
        return value;
    }

    emit(lang = "js", indent = "") {
        return `${indent}${this.expression.emit(lang, indent)}${this.semicolon(lang)}`;
    }
}

class TestNode extends StatementNode {
    constructor(expression, answer) {
        super();
        this.expression = expression;
        this.answer = answer;
    }

    evaluate(runtime, env) {
        const value = this.expression.evaluate(runtime, env);
        const answerValue = this.answer.evaluate(runtime, env);
        if (value !== answerValue) {
            throw new NanakoError(`テストに失敗: ${value}`, this.errorDetails());
        }
    }

    emit(lang = "js", indent = "") {
        const expression = this.expression.emit(lang, indent);
        const answer = this.answer.emit(lang, indent);
        if (lang === "js") {
            return `${indent}console.assert(${expression} == ${answer})${this.semicolon(lang)}`;
        }
        return `${indent}assert (${expression} == ${answer})${this.semicolon(lang)}`;
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
        text = text.replace(/"/g, '"').replace(/"/g, '"');
        // 全角文字を半角に変換する
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
            const stmt = this.parseStatement();
            if (stmt) {
                statements.push(stmt);
            }
            this.consumeWhitespace(true);
        }
        return new ProgramNode(statements);
    }

    parseStatement(text = null) {
        if (text !== null) {
            this.text = this.normalize(text);
            this.pos = 0;
            this.length = text.length;
        }

        // 文をパース
        this.consumeWhitespace(true);
        const savedPos = this.pos;

        let stmt = this.parseIfStatement();
        if (!stmt) {
            stmt = this.parseLoopStatement();
        }
        if (!stmt) {
            stmt = this.parseDoctest();
        }
        if (!stmt) {
            stmt = this.parseAssignment();
        }
        if (!stmt) {
            stmt = this.parseReturn();
        }
        if (!stmt) {
            stmt = this.parseBreak();
        }
        if (stmt) {
            stmt.source = this.text;
            stmt.pos = savedPos;
            stmt.endPos = this.pos;
            this.consumeEol();
            return stmt;
        }
        throw new NanakoError(`ななこの知らない書き方！`, this.errorDetails(savedPos));
    }

    parseDoctest() {
        // ドキュテストをパース
        const savedPos = this.pos;
        if (!this.consumeString(">>>")) {
            this.pos = savedPos;
            return null;
        }

        this.consumeWhitespace();
        const expression = this.parseExpression();
        if (expression === null) {
            throw new NanakoError("`>>>` の後にはテストする式が必要です", this.errorDetails(this.pos));
        }
        this.consumeEol();
        const answerExpression = this.parseExpression();
        if (answerExpression === null) {
            throw new NanakoError("`>>>` の次の行には正解が必要です", this.errorDetails(this.pos));
        }
        return new TestNode(expression, answerExpression);
    }

    parseAssignment() {
        // 代入文をパース
        const savedPos = this.pos;

        const variable = this.parseVariable(true);  // definitionContext = true
        if (variable === null) {
            this.pos = savedPos;
            return null;
        }

        this.consumeWhitespace();

        // "の末尾に" 構文
        if (this.consume("の末尾に")) {
            this.consumeCma();
            const expression = this.parseExpression();
            if (expression === null) {
                throw new NanakoError("ここに何か忘れてません？", this.errorDetails(this.pos));
            }
            this.consumeWhitespace();
            this.consumeString("を");
            this.consumeCma();
            this.consume("追加する");
            return new AppendNode(variable, expression);
        }

        if (this.consumeString("を")) {
            this.consumeWhitespace();
            if (this.consumeString("増やす")) {
                return new IncrementNode(variable);
            }
            if (this.consumeString("減らす")) {
                return new DecrementNode(variable);
            }

            const expression = this.parseExpression();
            if (expression === null) {
                throw new NanakoError("ここに何か忘れてません？", this.errorDetails(this.pos));
            }

            // オプションの "とする"
            this.consumeWhitespace();
            this.consumeString("とする");
            return new AssignmentNode(variable, expression);
        }

        // "="
        if (this.consume("=", "＝")) {
            this.consumeWhitespace();
            const expression = this.parseExpression();
            if (expression === null) {
                throw new NanakoError("ここに何か忘れてません？", this.errorDetails(this.pos));
            }

            return new AssignmentNode(variable, expression);
        }

        this.pos = savedPos;
        return null;
    }

    parseIfStatement() {
        // if文をパース
        const savedPos = this.pos;

        if (!this.consumeString("もし")) {
            this.pos = savedPos;
            return null;
        }
        this.consumeCma();

        const left = this.parseExpression();
        if (!left) {
            throw new NanakoError("何と比較したいの？", this.errorDetails(this.pos));
        }

        if (!this.consumeString("が")) {
            throw new NanakoError("`が`が必要", this.errorDetails(this.pos));
        }

        this.consumeCma();
        const right = this.parseExpression();
        if (!right) {
            throw new NanakoError("何と比較したいの？", this.errorDetails(this.pos));
        }
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
            throw new NanakoError("`ならば`が必要", this.errorDetails(this.pos));
        }
        this.consumeCma();

        const thenBlock = this.parseBlock();
        if (thenBlock === null) {
            throw new NanakoError("「もし、ならば」どうするの？ { }で囲んでね！", this.errorDetails(this.pos));
        }

        // else節（オプション）
        const elseBlock = this.parseElseStatement();
        return new IfNode(left, operator, right, thenBlock, elseBlock);
    }

    parseElseStatement() {
        // else文をパース
        const savedPos = this.pos;
        this.consumeWhitespace(true);
        if (!this.consumeString("そうでなければ")) {
            this.pos = savedPos;
            return null;
        }
        this.consumeCma();
        const block = this.parseBlock();
        if (block === null) {
            throw new NanakoError("「そうでなければ」どうするの？ { }で囲んでね！", this.errorDetails(this.pos));
        }
        return block;
    }

    parseLoopStatement() {
        // ループ文をパース
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
        if (!this.consume("くり返す", "繰り返す")) {
            throw new NanakoError("`くり返す`が必要", this.errorDetails(this.pos));
        }

        const body = this.parseBlock();
        if (body === null) {
            throw new NanakoError("何をくり返すの？ { }で囲んでね！", this.errorDetails(this.pos));
        }
        return new LoopNode(count, body);
    }

    parseReturn() {
        const savedPos = this.pos;
        const expression = this.parseExpression();
        if (expression) {
            if (this.consumeString("が答え")) {
                return new ReturnNode(expression);
            }
            this.consumeWhitespace();
            if (this.pos >= this.length || this.text[this.pos] === '\n') {
                return new ExpressionStatementNode(expression);
            }
        }
        this.pos = savedPos;
        return null;
    }

    parseBreak() {
        const savedPos = this.pos;
        if (this.consume("くり返しを抜ける", "繰り返しを抜ける")) {
            return new BreakNode();
        }
        this.pos = savedPos;
        return null;
    }

    parseExpression(text = null) {
        if (text !== null) {
            this.text = this.normalize(text);
            this.pos = 0;
            this.length = text.length;
        }

        // 式をパース
        this.consumeWhitespace();
        const savedPos = this.pos;
        let expression = this.parseInteger();
        if (!expression) {
            expression = this.parseString();
        }
        if (!expression) {
            expression = this.parseLen();
        }
        if (!expression) {
            expression = this.parseMinus();
        }
        if (!expression) {
            expression = this.parseFunction();
        }
        if (!expression) {
            expression = this.parseArraylist();
        }
        if (!expression) {
            expression = this.parseNull();
        }
        if (!expression) {
            expression = this.parseFunccall();
        }
        if (!expression) {
            expression = this.parseVariable();
        }

        if (expression) {
            if (this.consume("+", "-", "*", "/", "%", "＋", "ー", "＊", "／", "％", "×", "÷")) {
                throw new NanakoError("ななこは中置記法を使えないよ！", this.errorDetails(this.pos));
            }
            expression.source = this.text;
            expression.pos = savedPos;
            expression.endPos = this.pos;
            this.consumeWhitespace();
            return expression;
        }

        return null;
    }

    parseInteger() {
        // 整数をパース
        const savedPos = this.pos;
        if (!this.consumeDigit()) {
            this.pos = savedPos;
            return null;
        }

        // 数字
        while (this.consumeDigit()) {
            // continue
        }

        if (this.consume(".")) {
            throw new NanakoError("ななこは小数を使えないよ！", this.errorDetails(this.pos));
        }

        const valueStr = this.text.slice(savedPos, this.pos);
        try {
            const value = parseInt(valueStr);
            return new NumberNode(value);
        } catch (e) {
            this.pos = savedPos;
            return null;
        }
    }

    parseString() {
        // 文字列リテラルをパース
        const savedPos = this.pos;

        // ダブルクォート開始
        if (!this.consume('"', '"', '"')) {
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
                    stringContent.push('\n');
                } else if (nextChar === 't') {
                    stringContent.push('\t');
                } else if (nextChar === '\\') {
                    stringContent.push('\\');
                } else if (nextChar === '"') {
                    stringContent.push('"');
                } else {
                    stringContent.push(nextChar);
                }
            } else {
                stringContent.push(char);
            }
            this.pos++;
        }

        // ダブルクォート終了
        if (!this.consume('"', '"', '"')) {
            this.pos = savedPos;
            throw new NanakoError("閉じ`\"`を忘れないで", this.errorDetails(savedPos));
        }

        // 文字コードを取り出す
        if (this.consume("[", "【")) {
            this.consumeWhitespace();
            const number = this.parseInteger();
            if (number === null) {
                throw new NanakoError("添え字を忘れているよ", this.errorDetails(this.pos));
            }
            this.consumeWhitespace();
            if (!this.consume("]", "】")) {
                throw new NanakoError("閉じ`]`を忘れないで", this.errorDetails(this.pos));
            }
            if (stringContent.length === 0) {
                throw new NanakoError("空の文字列に添え字は使えません", this.errorDetails(this.pos));
            }
            const index = number.value;
            if (!(0 <= index && index < stringContent.length)) {
                throw new NanakoError(`添え字は0から${stringContent.length-1}の間ですよ: ❌${index}`, this.errorDetails(this.pos));
            }
            return new NumberNode(stringContent[index].charCodeAt(0));
        }

        return new StringNode(stringContent.join(''));
    }

    parseMinus() {
        // 整数をパース
        const savedPos = this.pos;

        // マイナス符号（オプション）
        if (!this.consume("-", "ー")) {
            this.pos = savedPos;
            return null;
        }
        this.consumeWhitespace();
        const element = this.parseExpression();
        if (element === null) {
            throw new NanakoError("`-`の次に何か忘れてない？", this.errorDetails(this.pos));
        }
        return new MinusNode(element);
    }

    parseLen() {
        // 絶対値または長さをパース
        const savedPos = this.pos;
        if (!this.consume("|", "｜")) {
            this.pos = savedPos;
            return null;
        }

        this.consumeWhitespace();
        const element = this.parseExpression();
        if (element === null) {
            throw new NanakoError("`|`の次に何か忘れてない？", this.errorDetails(this.pos));
        }
        this.consumeWhitespace();
        if (!this.consume("|", "｜")) {
            throw new NanakoError("閉じ`|`を忘れないで", this.errorDetails(this.pos));
        }
        return new LenNode(element);
    }

    parseFunction() {
        // 関数をパース
        const savedPos = this.pos;
        // "λ" または "入力"
        if (!this.consume("入力", "λ")) {
            this.pos = savedPos;
            return null;
        }

        this.consumeWhitespace();

        // パラメータ
        const parameters = [];
        while (true) {
            const identifier = this.parseIdentifier(true);  // definitionContext = true
            if (identifier === null) {
                throw new NanakoError("変数名が必要", this.errorDetails(this.pos));
            }
            if (parameters.includes(identifier)) {
                throw new NanakoError(`同じ変数名を使っているよ: ❌'${identifier}'`, this.errorDetails(this.pos));
            }
            parameters.push(identifier);
            this.consumeWhitespace();
            if (!this.consume(",", "、", "，", "､")) {
                break;
            }
            this.consumeWhitespace();
        }

        if (parameters.length === 0) {
            throw new NanakoError("ひとつは変数名が必要", this.errorDetails(this.pos));
        }

        this.consumeWhitespace();
        if (!this.consumeString("に対し")) {
            throw new NanakoError("`に対し`が必要", this.errorDetails(this.pos));
        }
        this.consumeString("て");
        this.consumeCma();
        const body = this.parseBlock();

        if (body === null) {
            throw new NanakoError("関数の本体は？ { }で囲んでね！", this.errorDetails(this.pos));
        }
        return new FunctionNode(parameters, body);
    }

    parseFunccall() {
        // 関数呼び出しをパース
        const savedPos = this.pos;
        const name = this.parseIdentifier();
        if (name === null) {
            this.pos = savedPos;
            return null;
        }
        this.consumeWhitespace();

        if (!this.consume("(", "（")) {
            this.pos = savedPos;
            return null;
        }

        this.consumeWhitespace();

        const args = [];
        while (true) {
            const expression = this.parseExpression();
            if (expression === null) {
                throw new NanakoError("関数なら引数を忘れないで", this.errorDetails(this.pos));
            }
            args.push(expression);
            this.consumeWhitespace();
            if (this.consume(")", "）")) {
                break;
            }
            if (!this.consume(",", "、", "，", "､")) {
                throw new NanakoError("閉じ`)`を忘れないで", this.errorDetails(this.pos));
            }
            this.consumeWhitespace();
        }

        return new FuncCallNode(name, args);
    }

    parseArraylist() {
        // 配列をパース
        const savedPos = this.pos;
        // "[" で始まる
        if (!this.consume("[", "【")) {
            this.pos = savedPos;
            return null;
        }

        const elements = [];
        const savedPos2 = this.pos;
        while (true) {
            this.consumeWhitespace(true);  // include newlines
            if (this.consume("]", "】")) {
                break;
            }
            const expression = this.parseExpression();
            if (expression === null) {
                throw new NanakoError("値を忘れてます", this.errorDetails(this.pos));
            }
            elements.push(expression);
            this.consumeWhitespace(true);  // include newlines
            if (this.consume("]", "】")) {
                break;
            }
            if (!this.consume(",", "、", "，", "､")) {
                throw new NanakoError("閉じ`]`を忘れないで", this.errorDetails(savedPos2));
            }
        }

        return new ArrayNode(elements);
    }

    parseNull() {
        // null値をパース
        if (this.consume("null", "?", "？")) {
            return new NullNode();
        }
        return null;
    }

    parseVariable(definitionContext = false) {
        // 変数をパース
        const name = this.parseIdentifier(definitionContext);
        if (name === null) {
            return null;
        }

        const indices = [];

        while (this.consume("[", "【")) {
            this.consumeWhitespace();
            const index = this.parseExpression();
            indices.push(index);
            if (!this.consume("]", "】")) {
                throw new NanakoError("閉じ `]`を忘れないで", this.errorDetails(this.pos));
            }
        }

        if (indices.length === 0) {
            return new VariableNode(name, null);
        }
        return new VariableNode(name, indices);
    }

    parseBlock() {
        // ブロックをパース
        this.consumeWhitespace();
        const savedPos = this.pos;
        if (!this.consume("{", "｛")) {
            this.pos = savedPos;
            return null;
        }
        
        // Check if this is a single-line block by looking ahead for closing brace on same line
        const afterOpenBrace = this.pos;
        let isSingleLine = false;
        let tempPos = this.pos;
        
        // Look ahead on the same line to see if there's a closing brace
        while (tempPos < this.length && this.text[tempPos] !== '\n') {
            if (this.text[tempPos] === '}' || this.text[tempPos] === '｝') {
                isSingleLine = true;
                break;
            }
            tempPos++;
        }
        
        if (!isSingleLine) {
            // Multi-line block: skip to end of line and handle indentation
            this.consumeUntilEol();
        }
        
        const indentDepth = this.consumeWhitespace();
        let foundClosingBrace = false;
        const statements = [];

        while (this.pos < this.length) {
            this.consumeWhitespace(true);
            if (this.consume("}", "｝")) {
                foundClosingBrace = true;
                break;
            }
            const stmt = this.parseStatement();
            if (stmt) {
                statements.push(stmt);
            }
        }

        if (!foundClosingBrace) {
            throw new NanakoError("閉じ `}`を忘れないで", this.errorDetails(savedPos));
        }

        return new BlockNode(statements);
    }

    parseIdentifier(definitionContext = false) {
        // 識別子をパース
        const savedPos = this.pos;

        if (definitionContext) {
            // 定義時のコンテキスト: より広範な文字を変数名として受け入れる
            while (this.pos < this.length) {
                const char = this.text[this.pos];
                if (" \t\n\r,=[](){}#　＝＃、，､【】（）｛｝".includes(char)) {
                    break;
                }
                if ("にをの".includes(char)) {
                    const remaining = this.text.slice(this.pos);
                    if (remaining.startsWith("に対し") || remaining.startsWith("を増やす") ||
                        remaining.startsWith("を減らす") || remaining.startsWith("の末尾に")) {
                        break;
                    }
                }
                this.pos++;
            }
            const name = this.text.slice(savedPos, this.pos).trim();
            if (name.length > 0) {
                return name;
            }
            return null;
        }

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

        const name = this.text.slice(savedPos, this.pos);
        if (name.length > 0) {
            return name;
        }
        return null;
    }

    notIdentifierWords() {
        // 除外キーワードチェック
        const remaining = this.text.slice(this.pos);
        for (const kw of ["くり返す", "を", "回", "とする", "が", "ならば", "に対し", "を増やす", "を減らす", "の末尾に"]) {
            if (remaining.startsWith(kw)) {
                return false;
            }
        }
        return true;
    }

    consumeAlpha() {
        if (this.pos < this.length) {
            const char = this.text[this.pos];
            if ((char.match(/[a-zA-Z_]/) ||
                (char >= '\u4e00' && char <= '\u9fff') ||  // 漢字
                (char >= '\u3040' && char <= '\u309f') ||  // ひらがな
                (char >= '\u30a0' && char <= '\u30ff') ||  // カタカナ
                char === 'ー')) {
                this.pos++;
                return true;
            }
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
        this.consume("、", "，", "､", ",");
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
        // 改行まで読み飛ばす
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
        NanakoArray,
        NanakoError,
        ReturnBreakException,
        // AST nodes
        ASTNode,
        StatementNode,
        ExpressionNode,
        ProgramNode,
        BlockNode,
        NullNode,
        NumberNode,
        LenNode,
        MinusNode,
        ArrayNode,
        StringNode,
        FunctionNode,
        FuncCallNode,
        VariableNode,
        AssignmentNode,
        IncrementNode,
        DecrementNode,
        IfNode,
        LoopNode,
        ReturnNode,
        ExpressionStatementNode,
        TestNode
    };
}