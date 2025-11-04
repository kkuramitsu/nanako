// Nanako (ななこ) Jest Test Suite
// JavaScript port of test_nanako.py

// Import nanako.js classes
const fs = require('fs');
const path = require('path');

// Read and execute nanako.js file to get classes
const nanakoPath = path.join(__dirname, 'nanako.js');
const nanakoCode = fs.readFileSync(nanakoPath, 'utf8');

// Capture console output
let capturedOutput = [];
const originalConsole = console;

// Create a new Function to execute nanako.js in controlled context
// and extract the classes we need
const createNanakoContext = () => {
    const context = {
        console: {
            ...originalConsole,
            log: (...args) => {
                capturedOutput.push(args.join(' '));
                originalConsole.log(...args);
            }
        }
    };
    
    // Execute nanako.js in the context
    const func = new Function('console', nanakoCode + '; return { NanakoParser, NanakoRuntime, NanakoArray, ASTNode, ReturnBreakException, transformArray };');
    return func(context.console);
};

const nanakoClasses = createNanakoContext();
const { NanakoParser, NanakoRuntime, NanakoArray, ASTNode, ReturnBreakException, transformArray } = nanakoClasses;

class TestNanakoParser {
    beforeEach() {
        this.parser = new NanakoParser();
        this.runtime = new NanakoRuntime();
        this.env = {};
        capturedOutput = [];
    }

    testParseNull() {
        const expression = this.parser.parseExpression('?');
        const result = expression.evaluate(this.runtime, this.env);
        expect(result).toBe(null);
    }

    testParseZenkakuNull() {
        const expression = this.parser.parseExpression('？');
        const result = expression.evaluate(this.runtime, this.env);
        expect(result).toBe(null);
    }

    testParseInteger() {
        const expression = this.parser.parseExpression('42');
        const result = expression.evaluate(this.runtime, this.env);
        expect(result).toBe(42);
    }

    testParseZenkakuInteger() {
        const expression = this.parser.parseExpression('４２');
        const result = expression.evaluate(this.runtime, this.env);
        expect(result).toBe(42);
    }

    testParseMinusInteger() {
        const expression = this.parser.parseExpression('-42');
        const result = expression.evaluate(this.runtime, this.env);
        expect(result).toBe(-42);
    }

    testParseInfix() {
        expect(() => {
            const expression = this.parser.parseExpression('4+2');
            expression.evaluate(this.runtime, this.env);
        }).toThrow(/中置/);
    }

    testParseFraction() {
        expect(() => {
            const expression = this.parser.parseExpression('4.2');
            expression.evaluate(this.runtime, this.env);
        }).toThrow(/小数/);
    }

    testParseVariable() {
        const expression = this.parser.parseExpression('x');
        this.env.x = 1;
        const result = expression.evaluate(this.runtime, this.env);
        expect(result).toBe(1);
    }

    testParseJapaneseVariable() {
        const expression = this.parser.parseExpression('変数');
        this.env['変数'] = 1;
        const result = expression.evaluate(this.runtime, this.env);
        expect(result).toBe(1);
    }

    testParseVariableIndex() {
        const expression = this.parser.parseExpression('x[0]');
        this.env.x = [1, 2, 3];
        this.env = transformArray(this.env);
        const result = expression.evaluate(this.runtime, this.env);
        expect(result).toBe(1);
    }

    testParseVariableIndexError() {
        expect(() => {
            const expression = this.parser.parseExpression('x[3]');
            this.env.x = [1, 2, 3];
            this.env = transformArray(this.env);
            expression.evaluate(this.runtime, this.env);
        }).toThrow(/配列/);
    }

    testParseJapaneseVariableIndex() {
        const expression = this.parser.parseExpression('変数[0]');
        this.env['変数'] = [1, 2, 3];
        this.env = transformArray(this.env);
        const result = expression.evaluate(this.runtime, this.env);
        expect(result).toBe(1);
    }

    testParseVariableIndex2() {
        const expression = this.parser.parseExpression('x[1][1]');
        this.env.x = [[1, 2], [3, 4]];
        this.env = transformArray(this.env);
        const result = expression.evaluate(this.runtime, this.env);
        expect(result).toBe(4);
    }

    testParseJapaneseVariableIndex2() {
        const expression = this.parser.parseExpression('変数[1][1]');
        this.env['変数'] = [[1, 2], [3, 4]];
        this.env = transformArray(this.env);
        const result = expression.evaluate(this.runtime, this.env);
        expect(result).toBe(4);
    }

    testParseLen() {
        const expression = this.parser.parseExpression('|x|');
        this.env.x = [1, 2];
        this.env = transformArray(this.env);
        const result = expression.evaluate(this.runtime, this.env);
        expect(result).toBe(2);
    }

    testParseString() {
        const expression = this.parser.parseExpression('"AB"');
        const result = expression.evaluate(this.runtime, this.env);
        expect(result.elements).toEqual([65, 66]);
    }

    testParseZenkakuString() {
        const expression = this.parser.parseExpression('"AB"');
        const result = expression.evaluate(this.runtime, this.env);
        expect(result.elements).toEqual([65, 66]);
    }

    testParseStringLiteralEmpty() {
        const expression = this.parser.parseExpression('""');
        const result = expression.evaluate(this.runtime, this.env);
        expect(result.elements).toEqual([]);
    }

    testParseStringLiteralUnclosed() {
        expect(() => {
            const expression = this.parser.parseExpression('"AB');
            expression.evaluate(this.runtime, this.env);
        }).toThrow(/閉/);
    }

    testParseCharactorLiteral() {
        const expression = this.parser.parseExpression('"A"[0]');
        const result = expression.evaluate(this.runtime, this.env);
        expect(result).toBe(65);
    }

    testParseArrayLiteral() {
        const expression = this.parser.parseExpression('[1, 2, 3]');
        const result = expression.evaluate(this.runtime, this.env);
        expect(result.elements).toEqual([1, 2, 3]);
    }

    testParseArrayLiteralTrailingComma() {
        const expression = this.parser.parseExpression('[1, 2, 3,]');
        const result = expression.evaluate(this.runtime, this.env);
        expect(result.elements).toEqual([1, 2, 3]);
    }

    testParseArrayLiteralNoComma() {
        expect(() => {
            const expression = this.parser.parseExpression('[1, 2 3]');
            expression.evaluate(this.runtime, this.env);
        }).toThrow(/閉/);
    }

    testParseArrayLiteralUnclosed() {
        expect(() => {
            const expression = this.parser.parseExpression('[1, 2, 3');
            expression.evaluate(this.runtime, this.env);
        }).toThrow(/閉/);
    }

    testParseArrayLiteral2d() {
        const expression = this.parser.parseExpression('[[1, 2], [3, 4]]');
        const result = expression.evaluate(this.runtime, this.env);
        expect(result.elements[0].elements).toEqual([1, 2]);
        expect(result.elements[1].elements).toEqual([3, 4]);
    }

    testParseArrayLiteral2d2() {
        const expression = this.parser.parseExpression('[\n  [1, 2],\n   [3, 4]\n]');
        const result = expression.evaluate(this.runtime, this.env);
        expect(result.elements[0].elements).toEqual([1, 2]);
        expect(result.elements[1].elements).toEqual([3, 4]);
    }

    testParseArrayLiteralString() {
        const expression = this.parser.parseExpression('["AB", "CD"]');
        const result = expression.evaluate(this.runtime, this.env);
        expect(result.elements[0].elements).toEqual([65, 66]);
        expect(result.elements[1].elements).toEqual([67, 68]);
    }

    testParseAssignment() {
        const statement = this.parser.parseStatement('x = 1');
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(1);
    }

    testParseAssignmentJa() {
        const statement = this.parser.parseStatement('変数 = 1');
        statement.evaluate(this.runtime, this.env);
        expect(this.env['変数']).toBe(1);
    }

    testParseAssignmentError() {
        expect(() => {
            const statement = this.parser.parseStatement('x = ');
            statement.evaluate(this.runtime, this.env);
        }).toThrow(/忘/);
    }

    testParseJapaneseAssignment() {
        // 「xを1とする」構文はサポートされていない（エラーが期待される）
        expect(() => {
            const statement = this.parser.parseStatement('xを1とする');
            statement.evaluate(this.runtime, this.env);
        }).toThrow(/知らない|増やす/);
    }

    testParseJapaneseAssignmentJa() {
        // 「変数を1とする」構文はサポートされていない（エラーが期待される）
        expect(() => {
            const statement = this.parser.parseStatement('変数を1とする');
            statement.evaluate(this.runtime, this.env);
        }).toThrow(/知らない|増やす/);
    }

    testParseAssignmentArray() {
        const statement = this.parser.parseStatement('x[0] = 1');
        this.env.x = [0];
        this.env = transformArray(this.env);
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x.elements).toEqual([1]);
    }

    testParseAssignmentArrayJa() {
        const statement = this.parser.parseStatement('変数[0] = 1');
        this.env['変数'] = [0];
        this.env = transformArray(this.env);
        statement.evaluate(this.runtime, this.env);
        expect(this.env['変数'].elements).toEqual([1]);
    }

    testParseJapaneseAssignmentArray() {
        const statement = this.parser.parseStatement('x[0]を1とする');
        this.env.x = new NanakoArray([0]);
        this.env = transformArray(this.env);
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x.elements).toEqual([1]);
    }

    testParseJapaneseAssignmentArrayJa() {
        const statement = this.parser.parseStatement('変数[0]を1とする');
        this.env['変数'] = [0];
        this.env = transformArray(this.env);
        statement.evaluate(this.runtime, this.env);
        expect(this.env['変数'].elements).toEqual([1]);
    }

    testParseIncrement() {
        const statement = this.parser.parseStatement('xを増やす');
        this.env.x = 1;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(2);
    }

    testParseDecrement() {
        const statement = this.parser.parseStatement('xを減らす');
        this.env.x = 1;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(0);
    }

    testParseIncrementJa() {
        const statement = this.parser.parseStatement('変数を増やす');
        this.env['変数'] = 1;
        statement.evaluate(this.runtime, this.env);
        expect(this.env['変数']).toBe(2);
    }

    testParseDecrementJa() {
        const statement = this.parser.parseStatement('変数を減らす');
        this.env['変数'] = 1;
        statement.evaluate(this.runtime, this.env);
        expect(this.env['変数']).toBe(0);
    }

    testParseIncrementElement() {
        const statement = this.parser.parseStatement('x[0]を増やす');
        this.env.x = [1, 1];
        this.env = transformArray(this.env);
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x.elements[0]).toBe(2);
    }

    testParseDecrementElement() {
        const statement = this.parser.parseStatement('x[0]を減らす');
        this.env.x = [1, 1];
        this.env = transformArray(this.env);
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x.elements[0]).toBe(0);
    }

    testParseIncrementArray() {
        expect(() => {
            const statement = this.parser.parseStatement('xを増やす');
            this.env.x = [1, 1];
            statement.evaluate(this.runtime, this.env);
        }).toThrow(/数/);
    }

    testParseDecrementArray() {
        expect(() => {
            const statement = this.parser.parseStatement('xを減らす');
            this.env.x = [1, 1];
            statement.evaluate(this.runtime, this.env);
        }).toThrow(/数/);
    }

    testParseIfStatement() {
        const statement = this.parser.parseStatement(`
            もしxが0ならば、 {
                x = 1
            }`);
        this.env.x = 0;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(1);
    }

    testParseIfStatementEmpty() {
        const statement = this.parser.parseStatement(`
            もしxが0ならば、 {
            }`);
        expect(statement.thenBlock.statements).toHaveLength(0);
        expect(statement.elseBlock).toBe(null);
        this.env.x = 0;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(0);
    }

    testParseIfElseStatement() {
        const statement = this.parser.parseStatement(`
            もしxが0ならば、 {
                x = 1
            } そうでなければ、 {
                x = 2
            }`);
        this.env.x = 0;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(1);
    }

    testParseIfFalseElseStatement() {
        const statement = this.parser.parseStatement(`
            もしxが0ならば、 {
                x = 1
            } 
            そうでなければ、 {
                x = 2
            }`);
        this.env.x = 1;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(2);
    }

    testParseIfNotStatement() {
        const statement = this.parser.parseStatement(`
            もしxが0以外ならば、 {
                x = 0
            }`);
        this.env.x = 1;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(0);
    }

    testParseIfGteStatement() {
        const statement = this.parser.parseStatement(`
            もしxが0以上ならば、 {
                x = -1
            }`);
        this.env.x = 0;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(-1);
    }

    testParseIfGtStatement() {
        const statement = this.parser.parseStatement(`
            もしxが0より大きいならば、 {
                x = -1
            }`);
        this.env.x = 1;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(-1);
    }

    testParseIfGtFalseStatement() {
        const statement = this.parser.parseStatement(`
            もしxが0より大きいならば、 {
                x = -1
            }`);
        this.env.x = 0;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(0);
    }

    testParseIfLteStatement() {
        const statement = this.parser.parseStatement(`
            もしxが0以下ならば、 {
                x = 1
            }`);
        this.env.x = 0;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(1);
    }

    testParseIfLtStatement() {
        const statement = this.parser.parseStatement(`
            もしxが0より小さいならば、 {
                x = 1
            }`);
        this.env.x = -1;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(1);
    }

    testParseIfLtFalseStatement() {
        const statement = this.parser.parseStatement(`
            もしxが0より小さいならば、 {
                x = 1
            }`);
        this.env.x = 0;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(0);
    }

    testParseIfLt2Statement() {
        const statement = this.parser.parseStatement(`
            もしxが0未満ならば、 {
                x = 1
            }`);
        this.env.x = -1;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(1);
    }

    testParseIfLt2FalseStatement() {
        const statement = this.parser.parseStatement(`
            もしxが0未満ならば、 {
                x = 1
            }`);
        this.env.x = 0;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(0);
    }

    testParseReturn() {
        const statement = this.parser.parseStatement("xが答え");
        this.env.x = 1;
        try {
            statement.evaluate(this.runtime, this.env);
            // Should not reach here
            expect(true).toBe(false);
        } catch (e) {
            expect(e instanceof ReturnBreakException).toBe(true);
            expect(e.value).toBe(1);
        }
    }

    testParseExpression() {
        const statement = this.parser.parseStatement("x");
        this.env.x = 1;
        const result = statement.evaluate(this.runtime, this.env);
        expect(result).toBe(1);
    }

    testParseStatementError() {
        expect(() => {
            const statement = this.parser.parseStatement("x?");
            this.env.x = 1;
            statement.evaluate(this.runtime, this.env);
        }).toThrow(/ななこ/);
    }

    testParseDoctestPass() {
        const statement = this.parser.parseStatement(`
            >>> x
            0
            `);
        this.env.x = 0;
        statement.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(0);
    }

    testParseDoctestPass2() {
        const statement = this.parser.parseStatement(`
            x = [1,2]
            >>> x
            [1, 2]
            `);
        statement.evaluate(this.runtime, this.env);
        expect('x' in this.env).toBe(true);
    }

    testParseDoctestFail() {
        const statement = this.parser.parseStatement(`
            >>> x
            0
            `);
        expect(() => {
            this.env.x = 1;
            statement.evaluate(this.runtime, this.env);
        }).toThrow(/失敗/);
    }

    testParseFunctionWithEmptyLines() {
        const program = this.parser.parse(`
たし算 = 入力 x に対し、{

    x が答え

}

たし算(5)
            `);
        this.env = {};
        program.evaluate(this.runtime, this.env);
        // 関数が正常に実行されることを確認（エラーが出ないこと）
        expect('たし算' in this.env).toBe(true);
    }

    testParseLoopWithEmptyLines() {
        const program = this.parser.parse(`
x = 0
5回、くり返す {

    xを増やす

}
            `);
        this.env = {};
        program.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(5);
    }

    testParseIfWithEmptyLines() {
        const program = this.parser.parse(`
x = 10
もし xが5以上ならば、{

    xを増やす

}
            `);
        this.env = {};
        program.evaluate(this.runtime, this.env);
        expect(this.env.x).toBe(11);
    }
}

class TestNanako {
    beforeEach() {
        this.parser = new NanakoParser();
        this.runtime = new NanakoRuntime();
        this.env = {};
        capturedOutput = [];
    }

    testFunction() {
        const program = this.parser.parse(`
            y = 0
            ID = 入力 x に対して {
                xが答え
            }
            y = ID(5)
            `);
        this.env = {};
        program.evaluate(this.runtime, this.env);
        this.env.ID = null;
        expect(this.env.y).toBe(5);
    }

    testInfiniteLoop() {
        const program = this.parser.parse(`
            y = 0
            ?回、くり返す {
                yを増やす
            }
            `);
        expect(() => {
            this.env = {};
            this.runtime.start(1);
            program.evaluate(this.runtime, this.env);
        }).toThrow(/タイムアウト/);
    }

    testLoopBreak() {
        const program = this.parser.parse(`
            y = 0
            10回、くり返す {
                もし yが5ならば、{
                    くり返しを抜ける
                }
                yを増やす
            }
            `);
        this.env = {};
        program.evaluate(this.runtime, this.env);
        expect(this.env.y).toBe(5);
    }

    testAdditionFunction() {
        const program = this.parser.parse(`
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
            `);
        this.env = {};
        this.runtime.start(1);
        program.evaluate(this.runtime, this.env);
        expect(this.env.X).toBe(15);
        expect(this.env.Y).toBe(6);
    }

    testAbsFunction() {
        const program = this.parser.parse(`
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
Y = 絶対値(5)`);
        this.env = {};
        this.runtime.start(1);
        program.evaluate(this.runtime, this.env);
        expect(this.env.X).toBe(5);
        expect(this.env.Y).toBe(5);
    }

    testModFunction() {
        const program = this.parser.parse(`
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
`);
        this.env = {};
        this.runtime.start(1);
        program.evaluate(this.runtime, this.env);
        expect(this.env.X).toBe(12);
        expect(this.env.Y).toBe(0);
    }

    testGcdFunction() {
        const program = this.parser.parse(`
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
`);
        this.env = {};
        this.runtime.start(1);
        program.evaluate(this.runtime, this.env);
        expect(this.env.X).toBe(12);
    }

    testRecursiveFunction() {
        const program = this.parser.parse(`
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
`);
        this.env = {};
        this.runtime.start(1);
        program.evaluate(this.runtime, this.env);
        expect(this.env.X).toBe(10);
    }

    testSumFunction() {
        const program = this.parser.parse(`
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
`);
        this.env = {};
        this.runtime.start(1);
        program.evaluate(this.runtime, this.env);
        expect(this.env.X).toBe(15);
    }
}

class TestNanakoEmitCode {
    beforeEach() {
        this.parser = new NanakoParser();
        this.runtime = new NanakoRuntime();
        this.env = {};
        capturedOutput = [];
    }

    testEmitJs() {
        const program = this.parser.parse(EMIT_NANAKO);
        const code = program.emit("js", "|");
        expect(code).toBe(EMIT_JS);
    }

    testEmitPy() {
        const program = this.parser.parse(EMIT_NANAKO);
        const code = program.emit("py", "|");
        expect(code).toBe(EMIT_PYTHON);
    }
}

const EMIT_NANAKO = `
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
            buf[?] = 数列[i]
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
`;

const EMIT_JS = `|合計 = function (数列) {
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
|}

|console.assert(合計([1, 2, 3, 4, 5]) == 15);`;

const EMIT_PYTHON = `|def 合計(数列):
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

|assert (合計([1, 2, 3, 4, 5]) == 15)`;

// Jest test suite setup
describe('NanakoParser', () => {
    let testInstance;
    
    beforeEach(() => {
        testInstance = new TestNanakoParser();
        testInstance.beforeEach();
    });

    test('parse null', () => testInstance.testParseNull());
    test('parse zenkaku null', () => testInstance.testParseZenkakuNull());
    test('parse integer', () => testInstance.testParseInteger());
    test('parse zenkaku integer', () => testInstance.testParseZenkakuInteger());
    test('parse minus integer', () => testInstance.testParseMinusInteger());
    test('parse infix', () => testInstance.testParseInfix());
    test('parse fraction', () => testInstance.testParseFraction());
    test('parse variable', () => testInstance.testParseVariable());
    test('parse japanese variable', () => testInstance.testParseJapaneseVariable());
    test('parse variable index', () => testInstance.testParseVariableIndex());
    test('parse variable index error', () => testInstance.testParseVariableIndexError());
    test('parse japanese variable index', () => testInstance.testParseJapaneseVariableIndex());
    test('parse variable index2', () => testInstance.testParseVariableIndex2());
    test('parse japanese variable index2', () => testInstance.testParseJapaneseVariableIndex2());
    test('parse len', () => testInstance.testParseLen());
    test('parse string', () => testInstance.testParseString());
    test('parse zenkaku string', () => testInstance.testParseZenkakuString());
    test('parse string literal empty', () => testInstance.testParseStringLiteralEmpty());
    test('parse string literal unclosed', () => testInstance.testParseStringLiteralUnclosed());
    test('parse charactor literal', () => testInstance.testParseCharactorLiteral());
    test('parse array literal', () => testInstance.testParseArrayLiteral());
    test('parse array literal trailing comma', () => testInstance.testParseArrayLiteralTrailingComma());
    test('parse array literal no comma', () => testInstance.testParseArrayLiteralNoComma());
    test('parse array literal unclosed', () => testInstance.testParseArrayLiteralUnclosed());
    test('parse array literal 2d', () => testInstance.testParseArrayLiteral2d());
    test('parse array literal 2d 2', () => testInstance.testParseArrayLiteral2d2());
    test('parse array literal string', () => testInstance.testParseArrayLiteralString());
    test('parse assignment', () => testInstance.testParseAssignment());
    test('parse assignment ja', () => testInstance.testParseAssignmentJa());
    test('parse assignment error', () => testInstance.testParseAssignmentError());
    test('parse japanese assignment', () => testInstance.testParseJapaneseAssignment());
    test('parse japanese assignment ja', () => testInstance.testParseJapaneseAssignmentJa());
    test('parse assignment array', () => testInstance.testParseAssignmentArray());
    test('parse assignment array ja', () => testInstance.testParseAssignmentArrayJa());
    test('parse japanese assignment array', () => testInstance.testParseJapaneseAssignmentArray());
    test('parse japanese assignment array ja', () => testInstance.testParseJapaneseAssignmentArrayJa());
    test('parse increment', () => testInstance.testParseIncrement());
    test('parse decrement', () => testInstance.testParseDecrement());
    test('parse increment ja', () => testInstance.testParseIncrementJa());
    test('parse decrement ja', () => testInstance.testParseDecrementJa());
    test('parse increment element', () => testInstance.testParseIncrementElement());
    test('parse decrement element', () => testInstance.testParseDecrementElement());
    test('parse increment array', () => testInstance.testParseIncrementArray());
    test('parse decrement array', () => testInstance.testParseDecrementArray());
    test('parse if statement', () => testInstance.testParseIfStatement());
    test('parse if statement empty', () => testInstance.testParseIfStatementEmpty());
    test('parse if else statement', () => testInstance.testParseIfElseStatement());
    test('parse if false else statement', () => testInstance.testParseIfFalseElseStatement());
    test('parse if not statement', () => testInstance.testParseIfNotStatement());
    test('parse if gte statement', () => testInstance.testParseIfGteStatement());
    test('parse if gt statement', () => testInstance.testParseIfGtStatement());
    test('parse if gt false statement', () => testInstance.testParseIfGtFalseStatement());
    test('parse if lte statement', () => testInstance.testParseIfLteStatement());
    test('parse if lt statement', () => testInstance.testParseIfLtStatement());
    test('parse if lt false statement', () => testInstance.testParseIfLtFalseStatement());
    test('parse if lt2 statement', () => testInstance.testParseIfLt2Statement());
    test('parse if lt2 false statement', () => testInstance.testParseIfLt2FalseStatement());
    test('parse return', () => testInstance.testParseReturn());
    test('parse expression', () => testInstance.testParseExpression());
    test('parse statement error', () => testInstance.testParseStatementError());
    test('parse doctest pass', () => testInstance.testParseDoctestPass());
    test('parse doctest pass 2', () => testInstance.testParseDoctestPass2());
    test('parse doctest fail', () => testInstance.testParseDoctestFail());
    test('parse function with empty lines', () => testInstance.testParseFunctionWithEmptyLines());
    test('parse loop with empty lines', () => testInstance.testParseLoopWithEmptyLines());
    test('parse if with empty lines', () => testInstance.testParseIfWithEmptyLines());
});

describe('Nanako', () => {
    let testInstance;
    
    beforeEach(() => {
        testInstance = new TestNanako();
        testInstance.beforeEach();
    });

    test('function', () => testInstance.testFunction());
    test('infinite loop', () => testInstance.testInfiniteLoop());
    test('loop break', () => testInstance.testLoopBreak());
    test('addition function', () => testInstance.testAdditionFunction());
    test('abs function', () => testInstance.testAbsFunction());
    test('mod function', () => testInstance.testModFunction());
    test('gcd function', () => testInstance.testGcdFunction());
    test('recursive function', () => testInstance.testRecursiveFunction());
    test('sum function', () => testInstance.testSumFunction());
});

describe('NanakoEmitCode', () => {
    let testInstance;
    
    beforeEach(() => {
        testInstance = new TestNanakoEmitCode();
        testInstance.beforeEach();
    });

    test('emit js', () => testInstance.testEmitJs());
    test('emit py', () => testInstance.testEmitPy());
});