import math
import re

_FLOAT_RE = re.compile(r"^\d+([,.]\d+)?$")
_INT_PREFIX_RE = re.compile(r"^[+-]?\d+")
_PARSE_FLOAT_RE = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
_OPS = ("===", "!==", "==", "!=", "<=", ">=", "&&", "||")


def calculate_formula(formula, values):
    text = str(formula or "").strip()
    if not text:
        return None
    try:
        prepared = _substitute(text, values)
        value = _Parser(prepared).parse()
        return _result_text(value)
    except (ArithmeticError, TypeError, ValueError):
        return None


def _substitute(formula, values):
    def repl(match):
        field_id = int(match.group(1))
        return _substituted_value(values.get(field_id, ""))

    text = re.sub(r"\{(\d+)\}", repl, formula)
    text = text.replace("[_direction_hospital_]", "0")
    text = text.replace("[_age_]", "")
    text = text.replace("[_sex_]", "")
    return text


def _substituted_value(value):
    original = _orig_value(value)
    if not _FLOAT_RE.match(original):
        return original
    number = float(original.replace(",", ".")) or 0
    if not math.isfinite(number):
        number = 0
    return _number_literal(number)


def _orig_value(value):
    text = "" if value is None else str(value)
    if not text:
        return ""
    prefix = _INT_PREFIX_RE.match(text.strip())
    if prefix and int(prefix.group(0)) == 0:
        return "0"
    return text.strip()


def _number_literal(number):
    if number == int(number) and abs(number) < 1e15:
        return str(int(number))
    return str(number)


def _result_text(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if not _truthy(value):
        return "0"
    return _string(value)


def _truthy(value):
    if value is None or value is False:
        return False
    if isinstance(value, (int, float)) and (math.isnan(value) or value == 0):
        return False
    if value == "":
        return False
    return True


def _string(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        return _number_literal(float(value))
    return "" if value is None else str(value)


def _number(value):
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = "" if value is None else str(value).strip()
    if text == "":
        return 0.0
    try:
        return float(text)
    except ValueError:
        return float("nan")


def _parse_float(value):
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    match = _PARSE_FLOAT_RE.match("" if value is None else str(value).strip())
    if not match:
        return float("nan")
    return float(match.group(0))


def _parse_int(value, radix=10):
    base = int(_number(radix))
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if math.isnan(value) or math.isinf(value):
            return float("nan")
        return float(int(value))
    text = "" if value is None else str(value).strip()
    match = re.match(r"^[+-]?[0-9a-zA-Z]+", text)
    if not match or base < 2 or base > 36:
        return float("nan")
    try:
        return float(int(match.group(0), base))
    except ValueError:
        return float("nan")


def _round(value):
    number = _number(value)
    if math.isnan(number) or math.isinf(number):
        return number
    return float(math.floor(number + 0.5))


def _eq(left, right):
    if isinstance(left, bool) or isinstance(right, bool):
        return _eq(_number(left) if isinstance(left, bool) else left, _number(right) if isinstance(right, bool) else right)
    if _is_number(left) and _is_number(right):
        if math.isnan(left) or math.isnan(right):
            return False
        return float(left) == float(right)
    if _is_number(left) and isinstance(right, str):
        return _eq(left, _number(right))
    if isinstance(left, str) and _is_number(right):
        return _eq(_number(left), right)
    return str(left) == str(right)


def _strict_eq(left, right):
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left is right
    if _is_number(left) and _is_number(right):
        if math.isnan(left) or math.isnan(right):
            return False
        return float(left) == float(right)
    return type(left) is type(right) and left == right


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _rel(left, right, op):
    if isinstance(left, str) and isinstance(right, str):
        pair = (left, right)
    else:
        pair = (_number(left), _number(right))
        if math.isnan(pair[0]) or math.isnan(pair[1]):
            return False
    if op == "<":
        return pair[0] < pair[1]
    if op == ">":
        return pair[0] > pair[1]
    if op == "<=":
        return pair[0] <= pair[1]
    return pair[0] >= pair[1]


def _add(left, right):
    if isinstance(left, str) or isinstance(right, str):
        return _string(left) + _string(right)
    return _number(left) + _number(right)


def _div(left, right):
    numerator = _number(left)
    denominator = _number(right)
    if denominator == 0:
        if numerator == 0 or math.isnan(numerator):
            return float("nan")
        return float("inf") if numerator > 0 else float("-inf")
    return numerator / denominator


def _tokenize(text):
    tokens = []
    index = 0
    size = len(text)
    while index < size:
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if char in "'\"":
            quote = char
            index += 1
            chars = []
            while index < size and text[index] != quote:
                if text[index] == "\\" and index + 1 < size:
                    chars.append(text[index + 1])
                    index += 2
                    continue
                chars.append(text[index])
                index += 1
            if index >= size:
                raise ValueError("string")
            index += 1
            tokens.append(("str", "".join(chars)))
            continue
        if char.isdigit() or (char == "." and index + 1 < size and text[index + 1].isdigit()):
            start = index
            index += 1
            while index < size and (text[index].isdigit() or text[index] == "."):
                index += 1
            tokens.append(("num", float(text[start:index])))
            continue
        if char.isalpha() or char == "_":
            start = index
            index += 1
            while index < size and (text[index].isalnum() or text[index] == "_"):
                index += 1
            tokens.append(("ident", text[start:index]))
            continue
        matched = False
        for op in _OPS:
            if text.startswith(op, index):
                tokens.append(("op", op))
                index += len(op)
                matched = True
                break
        if matched:
            continue
        if char in "+-*/%<>?:().,":
            tokens.append(("op", char))
            index += 1
            continue
        raise ValueError(char)
    tokens.append(("eof", None))
    return tokens


class _Parser:
    def __init__(self, text):
        self.tokens = _tokenize(text)
        self.index = 0

    def parse(self):
        value = self._ternary()
        if self._peek()[0] != "eof":
            raise ValueError("trailing")
        return value

    def _peek(self):
        return self.tokens[self.index]

    def _pop(self):
        token = self.tokens[self.index]
        self.index += 1
        return token

    def _accept(self, op):
        token = self._peek()
        if token[0] == "op" and token[1] == op:
            self._pop()
            return True
        return False

    def _expect(self, op):
        if not self._accept(op):
            raise ValueError(op)

    def _ident(self):
        token = self._pop()
        if token[0] != "ident":
            raise ValueError("ident")
        return token[1]

    def _ternary(self):
        condition = self._or()
        if not self._accept("?"):
            return condition
        yes = self._ternary()
        self._expect(":")
        no = self._ternary()
        return yes if _truthy(condition) else no

    def _or(self):
        value = self._and()
        while self._accept("||"):
            right = self._and()
            value = value if _truthy(value) else right
        return value

    def _and(self):
        value = self._equality()
        while self._accept("&&"):
            right = self._equality()
            value = right if _truthy(value) else value
        return value

    def _equality(self):
        value = self._comparison()
        while True:
            if self._accept("==="):
                value = _strict_eq(value, self._comparison())
            elif self._accept("!=="):
                value = not _strict_eq(value, self._comparison())
            elif self._accept("=="):
                value = _eq(value, self._comparison())
            elif self._accept("!="):
                value = not _eq(value, self._comparison())
            else:
                return value

    def _comparison(self):
        value = self._add()
        while True:
            op = next((item for item in ("<=", ">=", "<", ">") if self._accept(item)), None)
            if not op:
                return value
            value = _rel(value, self._add(), op)

    def _add(self):
        value = self._mul()
        while True:
            if self._accept("+"):
                value = _add(value, self._mul())
            elif self._accept("-"):
                value = _number(value) - _number(self._mul())
            else:
                return value

    def _mul(self):
        value = self._unary()
        while True:
            if self._accept("*"):
                value = _number(value) * _number(self._unary())
            elif self._accept("/"):
                value = _div(value, self._unary())
            elif self._accept("%"):
                value = _number(value) % _number(self._unary())
            else:
                return value

    def _unary(self):
        if self._accept("+"):
            return _number(self._unary())
        if self._accept("-"):
            return -_number(self._unary())
        if self._accept("!"):
            return not _truthy(self._unary())
        return self._postfix()

    def _postfix(self):
        value = self._primary()
        while True:
            if self._accept("."):
                name = self._ident()
                self._expect("(")
                value = self._method(value, name, self._args())
                continue
            if isinstance(value, tuple) and value[0] == "ident" and self._accept("("):
                value = self._call(value[1], self._args())
                continue
            return value

    def _primary(self):
        token = self._peek()
        if token[0] == "num":
            self._pop()
            return token[1]
        if token[0] == "str":
            self._pop()
            return token[1]
        if token[0] == "ident":
            self._pop()
            return ("ident", token[1])
        if self._accept("("):
            value = self._ternary()
            self._expect(")")
            return value
        raise ValueError("primary")

    def _args(self):
        if self._accept(")"):
            return []
        args = []
        while True:
            args.append(self._ternary())
            if self._accept(")"):
                return args
            self._expect(",")

    def _call(self, name, args):
        if name == "Number" and len(args) == 1:
            return _number(args[0])
        if name == "String" and len(args) == 1:
            return _string(args[0])
        if name == "parseInt" and args:
            radix = args[1] if len(args) > 1 else 10
            return _parse_int(args[0], radix)
        raise ValueError(name)

    def _method(self, owner, name, args):
        if owner == ("ident", "Number") and name == "parseFloat" and len(args) == 1:
            return _parse_float(args[0])
        if owner == ("ident", "Number") and name == "parseInt" and args:
            radix = args[1] if len(args) > 1 else 10
            return _parse_int(args[0], radix)
        if owner == ("ident", "Math") and name == "min" and args:
            return _math_span(args, min)
        if owner == ("ident", "Math") and name == "max" and args:
            return _math_span(args, max)
        if owner == ("ident", "Math") and name == "round" and len(args) == 1:
            return _round(args[0])
        if owner == ("ident", "Math") and name == "abs" and len(args) == 1:
            return abs(_number(args[0]))
        if owner == ("ident", "Math") and name == "ceil" and len(args) == 1:
            return _finite_math(args[0], math.ceil)
        if owner == ("ident", "Math") and name == "floor" and len(args) == 1:
            return _finite_math(args[0], math.floor)
        if name == "toFixed" and args:
            return _to_fixed(owner, args[0])
        raise ValueError(name)


def _math_span(args, fn):
    numbers = [_number(arg) for arg in args]
    if any(math.isnan(number) for number in numbers):
        return float("nan")
    return float(fn(numbers))


def _finite_math(value, fn):
    number = _number(value)
    if math.isnan(number) or math.isinf(number):
        return number
    return float(fn(number))


def _to_fixed(value, digits):
    number = _number(value)
    places = int(_number(digits))
    if math.isnan(number):
        return "NaN"
    if math.isinf(number):
        return "Infinity" if number > 0 else "-Infinity"
    return f"{number:.{places}f}"
