#!/usr/bin/env python3
"""WOLFE: a readable, standard-library-only port of the C neural field.

The declarations construct all connections. No checkpoint, optimizer, remote API,
embedding service, or tool execution is involved. The C implementation is the
primary body; this file exposes the same computation for inspection.

    model = Wolfe('tools.json', 'examples.jsonl')
    result = model.call('set a timer for thirty seconds', reasoning=True)

Set reasoning='compact' for a short evidence view. With an explicit state
path, model.correct(record) saves a bounded correction and rebuilds the field.

Internal source positions count UTF-8 bytes, exactly as in wolfe.c.
"""
from dataclasses import dataclass, field
import json
import math
import os
import pathlib
import sys
import time

MAX_TOOLS, MAX_PROPERTIES, MAX_EXAMPLES = 64, 16, 2048
MAX_WORDS, MAX_TOKENS, DIMENSIONS, ITERATIONS = 4096, 96, 96, 6
MAX_TEXT, MAX_FILE, MAX_VALUES = 2048, 4 * 1024 * 1024, 32
MAX_CORRECTIONS = 32
MASK64, FNV_OFFSET, FNV_PRIME = (1 << 64) - 1, 1469598103934665603, 1099511628211
FILLERS = set(b'a an the please could would can you i me my we our to of for is are be it this that some with and then now just kindly want need like'.split())
SMALL_NUMBERS = dict(zip(b'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety'.split(), list(range(20)) + list(range(20, 100, 10))))
SPACE = b' \t\r\n\v\f'


def hash_bytes(value, data):
    for byte in data:
        value = ((value ^ byte) * FNV_PRIME) & MASK64
    return value


def clamp(value, low, high):
    return max(low, min(high, value))


def sigmoid(value):
    return 1.0 / (1.0 + math.exp(-clamp(value, -40, 40)))


def dot(left, right):
    return sum(a * b for a, b in zip(left, right))


def normalize(vector):
    norm = math.sqrt(dot(vector, vector))
    if norm > 1e-12:
        for index in range(DIMENSIONS):
            vector[index] /= norm


def project(vector, word, scale):
    """Three signed hash projections; uint64 overflow is deliberate."""
    value = hash_bytes(FNV_OFFSET, word)
    for _ in range(3):
        vector[value % DIMENSIONS] += scale if (value >> 20) & 1 else -scale
        value = (value * 6364136223846793005 + 1) & MASK64


def ascii_alnum(byte):
    return 48 <= byte <= 57 or 65 <= byte <= 90 or 97 <= byte <= 122


@dataclass
class Token:
    word: bytes
    start: int
    end: int
    slot: bool = False
    id: int = -1
    quoted: bool = False


def tokenize(text):
    data = text.encode('utf-8') if isinstance(text, str) else text
    if len(data) >= MAX_TEXT:
        raise ValueError('text exceeds 2047 bytes')
    tokens, index = [], 0
    quoted = False
    while index < len(data):
        begin, slot = index, False
        byte = data[index]
        if byte == 123 and b'}' in data[index + 1:]:
            slot = True
            begin = index = index + 1
            while data[index] != 125:
                index += 1
        elif ascii_alnum(byte) or byte >= 128 or (byte in b'-+' and index + 1 < len(data) and 48 <= data[index + 1] <= 57):
            index += 1
            while index < len(data):
                byte = data[index]
                if ascii_alnum(byte) or byte >= 128 or (byte in b".'" and index + 1 < len(data) and ascii_alnum(data[index + 1])):
                    index += 1
                else:
                    break
        else:
            if byte == 34 and (index == 0 or data[index - 1] != 92):
                quoted = not quoted
            index += 1
            continue
        if len(tokens) >= MAX_TOKENS:
            raise ValueError('text exceeds 96 tokens')
        if index - begin >= 96:
            raise ValueError('token exceeds 95 bytes')
        tokens.append(Token(data[begin:index].lower(), begin, index, slot, quoted=quoted))
        if slot:
            index += 1
    return Tokens(tokens, len(data))


class Tokens(list):
    """Tokens plus the byte boundary of their request or selected clause."""
    def __init__(self, values=(), limit=0):
        super().__init__(values)
        self.limit = limit


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON object key')
            result[key] = value
        return result

    def invalid_constant(_):
        raise ValueError('malformed JSON')

    if isinstance(text, bytes):
        try:
            text = text.decode('utf-8')
        except UnicodeError as error:
            raise ValueError('invalid UTF-8') from error
    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=invalid_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError('malformed JSON') from error
    count = 0

    def inspect(item, depth=0):
        nonlocal count
        count += 1
        if depth > 32 or count > 32768:
            raise ValueError('JSON resource limit or missing value')
        if isinstance(item, str):
            if '\0' in item:
                raise ValueError('embedded NUL in JSON string')
            item.encode('utf-8')
        elif isinstance(item, dict):
            for key, child in item.items():
                inspect(key, depth + 1)
                inspect(child, depth + 1)
        elif isinstance(item, list):
            for child in item:
                inspect(child, depth + 1)
    try:
        inspect(value)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('malformed JSON') from error
    return value


def read_file(path):
    try:
        data = pathlib.Path(path).read_bytes()
    except OSError as error:
        raise ValueError(f'cannot open {path}') from error
    if len(data) > MAX_FILE:
        raise ValueError('file exceeds 4 MiB limit or cannot seek')
    if b'\0' in data:
        raise ValueError('embedded NUL in file')
    return data


def bounded_string(value, capacity, error):
    if not isinstance(value, str) or len(value.encode('utf-8')) >= capacity:
        raise ValueError(error)
    return value


def numeric(value):
    if type(value) not in (float, int):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def scalar_text(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


@dataclass
class Property:
    name: str
    type: str
    description: str = ''
    required: bool = False
    minimum: object = None
    maximum: object = None
    values: list = field(default_factory=list)
    aliases: dict = field(default_factory=dict)
    units: dict = field(default_factory=dict)
    default: object = None
    has_default: bool = False

    def valid(self, value):
        if self.type == 'string':
            ok = isinstance(value, str)
        elif self.type == 'boolean':
            ok = type(value) is bool
        else:
            ok = numeric(value)
            if ok:
                ok = ((self.type != 'integer' or math.floor(value) == value)
                      and (self.minimum is None or value >= self.minimum)
                      and (self.maximum is None or value <= self.maximum))
        return ok and (not self.values or any(type(value) is type(item) and value == item or numeric(value) and numeric(item) and value == item for item in self.values))


@dataclass
class Tool:
    name: str
    description: str
    properties: list


@dataclass
class Example:
    text: str
    tool: int
    tokens: list
    arguments: dict = field(default_factory=dict)
    synthetic: bool = False
    corrected: bool = False


@dataclass
class Word:
    word: bytes
    df: int = 0
    idf: float = 0
    vector: list = field(default_factory=lambda: [0.0] * DIMENSIONS)


@dataclass
class Candidate:
    field: float = 0
    neural: float = 0
    keyword: float = 0
    prophecy: float = 0
    evidence: float = 0
    best: int = -1


class Wolfe:
    """Build the model directly from editable tool schemas and JSONL examples."""
    def __init__(self, tools='tools.json', examples='examples.jsonl', state=None):
        self.tools_path, self.examples_path = tools, examples
        self.identity = FNV_OFFSET
        self.tools, self.examples, self.words = [], [], []
        self.vocabulary = {}
        self._relation_cache = {}
        self._load_tools(tools)
        self._load_examples(examples)
        self.base_examples = [(example.text, example.tool, dict(example.arguments)) for example in self.examples]
        self.corrections = []
        self.signatures = [[0.0] * DIMENSIONS for _ in range(len(self.tools) + 1)]
        self.accepted = [0] * (len(self.tools) + 1)
        self.rejected = [0] * (len(self.tools) + 1)
        self.state_path = state
        if state:
            self.load_state(state, rebuild=False)
        self._append_corrections()
        self._build_field()

    def _load_tools(self, path):
        data = read_file(path)
        self.identity = hash_bytes(self.identity, data)
        root = strict_json(data)
        definitions = root if isinstance(root, list) else root.get('tools') if isinstance(root, dict) else None
        if not isinstance(definitions, list):
            raise ValueError('tools must be a JSON array or an object containing tools')
        for definition in definitions:
            if len(self.tools) >= MAX_TOOLS:
                raise ValueError('tool limit: 64')
            if not isinstance(definition, dict):
                raise ValueError('tool requires an object')
            definition = definition.get('function', definition)
            if not isinstance(definition, dict):
                raise ValueError('function must be an object')
            name = bounded_string(definition.get('name'), 96, 'tool requires a nonempty name under 96 bytes')
            if not name:
                raise ValueError('tool requires a nonempty name under 96 bytes')
            if any(tool.name == name for tool in self.tools):
                raise ValueError('duplicate tool name')
            description = bounded_string(definition.get('description', ''), MAX_TEXT, 'tool description too long')
            properties = []
            schema = definition.get('parameters', definition.get('input_schema'))
            if schema is not None:
                if not isinstance(schema, dict) or schema.get('type') != 'object':
                    raise ValueError('parameters must be an object schema')
                for key in schema:
                    if key not in ('type', 'properties', 'required', 'additionalProperties', 'description', 'title', '$schema'):
                        raise ValueError('unsupported schema keyword: ' + key)
                definitions_p = schema.get('properties', {})
                if not isinstance(definitions_p, dict):
                    raise ValueError('properties must be an object')
                for prop_name, declaration in definitions_p.items():
                    if len(properties) >= MAX_PROPERTIES:
                        raise ValueError('property limit: 16 per tool')
                    bounded_string(prop_name, 64, 'invalid or duplicate property name')
                    if not isinstance(declaration, dict) or declaration.get('type') not in ('string', 'number', 'integer', 'boolean'):
                        raise ValueError('only flat string, number, integer, boolean properties are supported')
                    for key in declaration:
                        if key not in ('type', 'enum', 'default', 'description', 'title', 'minimum', 'maximum', 'x-unit', 'x-aliases'):
                            raise ValueError('unsupported schema keyword: ' + key)
                    prop = Property(prop_name, declaration['type'])
                    prop.description = bounded_string(declaration.get('description', ''), 256, 'property description too long')
                    for key in ('minimum', 'maximum'):
                        if key in declaration:
                            if not numeric(declaration[key]):
                                raise ValueError(f'invalid {key}')
                            setattr(prop, key, declaration[key])
                    if prop.minimum is not None and prop.maximum is not None and prop.minimum > prop.maximum:
                        raise ValueError('minimum exceeds maximum')
                    if 'enum' in declaration:
                        values = declaration['enum']
                        if not isinstance(values, list):
                            raise ValueError('enum must be an array')
                        for value in values:
                            if len(prop.values) >= MAX_VALUES or len(scalar_text(value).encode('utf-8')) >= 256:
                                raise ValueError('enum limit exceeded')
                            previous = prop.values
                            prop.values = []
                            valid = prop.valid(value)
                            prop.values = previous
                            if not valid:
                                raise ValueError('enum value type mismatch')
                            prop.values.append(value)
                    aliases = declaration.get('x-aliases', {})
                    if not isinstance(aliases, dict):
                        raise ValueError('x-aliases must be an object')
                    for key, names in aliases.items():
                        if key not in [scalar_text(value) for value in prop.values]:
                            if prop.type == 'boolean' and key in ('true', 'false') and len(prop.values) < MAX_VALUES:
                                prop.values.append(key == 'true')
                            else:
                                raise ValueError('alias key must name an enum value or boolean')
                        if not isinstance(names, list):
                            raise ValueError('alias key must name an enum value or boolean')
                        if len(names) > MAX_VALUES:
                            raise ValueError('alias limit exceeded')
                        prop.aliases[key] = [bounded_string(alias, 128, 'alias limit exceeded') for alias in names]
                    units = declaration.get('x-unit', {})
                    if not isinstance(units, dict) or ('x-unit' in declaration and prop.type not in ('number', 'integer')):
                        raise ValueError('x-unit requires a numeric property and object')
                    for key, factor in units.items():
                        if len(prop.units) >= MAX_VALUES:
                            raise ValueError('unit limit exceeded')
                        bounded_string(key, 64, 'unit limit exceeded')
                        if not numeric(factor) or factor <= 0:
                            raise ValueError('unit factor must be positive')
                        prop.units[key.encode('utf-8')] = factor
                    if 'default' in declaration:
                        if not prop.valid(declaration['default']):
                            raise ValueError('invalid property default')
                        prop.has_default, prop.default = True, declaration['default']
                    properties.append(prop)
                required = schema.get('required', [])
                if not isinstance(required, list):
                    raise ValueError('required must be an array')
                for key in required:
                    matching = [prop for prop in properties if prop.name == key]
                    if not matching:
                        raise ValueError('required names unknown property')
                    matching[0].required = True
            self.tools.append(Tool(name, description, properties))
        if not self.tools:
            raise ValueError('at least one tool is required')

    def _add_example(self, text, tool, synthetic=False, arguments=None):
        if len(self.examples) >= MAX_EXAMPLES:
            raise ValueError('example limit: 2048')
        bounded_string(text, MAX_TEXT, 'example text too long')
        self.examples.append(Example(text, tool, tokenize(text), arguments or {}, synthetic))

    def _load_examples(self, path):
        data = read_file(path)
        self.identity = hash_bytes(self.identity, data)
        names = [tool.name for tool in self.tools]
        for line in data.splitlines():
            if not line.strip():
                continue
            example = strict_json(line)
            if not isinstance(example, dict) or 'tool' not in example:
                raise ValueError('each example requires tool (name or null)')
            if example['tool'] is None:
                tool = len(self.tools)
            elif example['tool'] in names:
                tool = names.index(example['tool'])
            else:
                raise ValueError('example names unknown tool')
            text = bounded_string(example.get('text'), MAX_TEXT, 'invalid example text or resource limit')
            arguments = example.get('arguments', {})
            if not isinstance(arguments, dict):
                raise ValueError('example arguments must be an object')
            for name, value in arguments.items():
                props = {} if tool == len(self.tools) else {prop.name: prop for prop in self.tools[tool].properties}
                if name not in props:
                    raise ValueError('example argument names unknown property')
                if len(scalar_text(value).encode('utf-8')) >= MAX_TEXT:
                    raise ValueError('example argument too long')
                placeholder = isinstance(value, str) and value.startswith('{') and value.endswith('}')
                if not placeholder and not props[name].valid(value):
                    raise ValueError('example argument violates schema')
            self._add_example(text, tool, arguments=arguments)
        if not self.examples:
            raise ValueError('examples file is empty')

    def weight(self, token):
        if token.slot:
            return 0.0
        if token.quoted:
            return .015
        if token.word in FILLERS:
            return 0.12
        return self.words[token.id].idf if token.id >= 0 else 1.0

    def _derive_slots(self, example):
        if example.tool >= len(self.tools):
            return
        for prop in self.tools[example.tool].properties:
            if prop.name not in example.arguments:
                continue
            value = scalar_text(example.arguments[prop.name])
            if value.startswith('{'):
                continue
            literal = tokenize(value)
            if not literal:
                continue
            for k in range(len(example.tokens) - len(literal) + 1):
                if all(not example.tokens[k + z].slot and example.tokens[k + z].word == token.word for z, token in enumerate(literal)):
                    first = example.tokens[k]
                    first.slot, first.word = True, prop.name.encode('utf-8')
                    first.end = example.tokens[k + len(literal) - 1].end
                    del example.tokens[k + 1:k + len(literal)]
                    break

    def _build_field(self):
        for example in self.examples:
            self._derive_slots(example)
        for index, tool in enumerate(self.tools):
            self._add_example(tool.name.replace('_', ' '), index, True)
            if tool.description:
                self._add_example(tool.description, index, True)
        for example in self.examples:
            seen = set()
            for token in example.tokens:
                if token.slot:
                    continue
                if token.word not in self.vocabulary:
                    if len(self.words) >= MAX_WORDS:
                        raise ValueError('vocabulary exceeds 4096 words')
                    self.vocabulary[token.word] = len(self.words)
                    self.words.append(Word(token.word))
                token.id = self.vocabulary[token.word]
                if token.id not in seen:
                    self.words[token.id].df += 1
                seen.add(token.id)
        for word in self.words:
            word.idf = 1.0 + math.log((len(self.examples) + 1.0) / (word.df + 1.0))
            project(word.vector, word.word, 1.0)
        # Hebbian association: nearby corpus tokens supply context projections.
        for example in self.examples:
            for j, token in enumerate(example.tokens):
                if token.id < 0:
                    continue
                word = self.words[token.id]
                for k, neighbour in enumerate(example.tokens):
                    if k != j and neighbour.id >= 0 and neighbour.word not in FILLERS:
                        proximity = 1.0 / (1.0 + abs(j - k))
                        project(word.vector, neighbour.word, .30 * proximity / math.sqrt(word.df))
        for word in self.words:
            normalize(word.vector)
        for example in self.examples:
            signature = self.signatures[example.tool]
            for token in example.tokens:
                if token.id >= 0:
                    weight = self.weight(token)
                    for d, value in enumerate(self.words[token.id].vector):
                        signature[d] += value * weight
        for signature in self.signatures:
            normalize(signature)

    @staticmethod
    def morphology(left, right):
        if len(left) < 4 or len(right) < 4:
            return 0.0
        common = sum(left[i:i + 3] in right for i in range(len(left) - 2))
        return .35 * common / (len(left) + len(right) - 4 - common)

    def relation(self, left, right):
        if left.slot or right.slot:
            return 0.0
        if bool(left.quoted) != bool(right.quoted):
            return .01
        if left.word == right.word:
            return 1.0
        key = (left.word, right.word)
        if key not in self._relation_cache:
            lexical = self.morphology(left.word, right.word)
            context = clamp(dot(self.words[left.id].vector, self.words[right.id].vector), 0, 1) if left.id >= 0 and right.id >= 0 else 0
            self._relation_cache[key] = max(lexical, .32 * context)
        return self._relation_cache[key]

    @staticmethod
    def _negative_clause(tokens):
        """Clause polarity is an input feature; quoted argument text is literal."""
        for i, token in enumerate(tokens):
            if token.quoted or token.slot:
                continue
            if token.word == b'not' and i + 1 < len(tokens) and tokens[i + 1].word == b'only':
                continue
            if token.word in (b'not', b'never', b"don't", b'dont'):
                return True
        return False

    def _prefix_words(self, tokens):
        # Topic fillers still carry grammatical roles in the ordered prefix.
        result = []
        roles = (b'am', b'was', b'were', b'have', b'has', b'had', b'no', b'longer', b'he', b'she', b'they', b"i'd")
        ignored = (b'a', b'an', b'the', b'please', b'just', b'kindly', b'for', b'to', b'of', b'with')
        for token in tokens:
            if token.quoted or token.slot:
                break
            if token.word not in FILLERS and token.word not in roles:
                if token.word not in self.vocabulary:
                    continue
                break
            if token.word not in ignored:
                if token.word == b'you' and any(word in (b'want', b'need', b'like') for word in result):
                    continue
                result.append(token.word)
        return result

    def _prefix_agreement(self, query, example):
        left, right = self._prefix_words(query), self._prefix_words(example)
        if not left:
            return 1.0
        position = matched = 0
        groups = ((b'can', b'could', b'would'), (b'want', b'need', b'like'), (b'i', b"i'd"))
        for word in left:
            for index in range(position, len(right)):
                if word == right[index] or any(word in group and right[index] in group for group in groups):
                    matched += 1
                    position = index + 1
                    break
        overlap = matched / max(1.0, len(left) + len(right) - matched)
        return .30 + .70 * overlap * overlap

    def _example_scores(self, query, example):
        matched = total = query_match = query_total = keyword_match = keyword_total = sequence = sequence_total = attention = 0.0
        for word in example.tokens:
            weight = self.weight(word)
            if not weight:
                continue
            best = max((self.relation(word, token) for token in query), default=0)
            literal = any(word.word == token.word for token in query)
            matched += weight * best
            total += weight
            keyword_match += weight * literal
            keyword_total += weight
            attention += weight * best * best
        for word in query:
            weight = self.weight(word) * (.10 if word.id < 0 else 1.0)
            best = max((self.relation(word, token) for token in example.tokens), default=0)
            query_match += weight * best
            query_total += weight
        for left, right in zip(example.tokens, example.tokens[1:]):
            weight = min(self.weight(left), self.weight(right))
            if weight <= .12:
                continue
            best = max((self.relation(left, a) * self.relation(right, b) for a, b in zip(query, query[1:])), default=0)
            sequence += weight * best
            sequence_total += weight
        field_score = .78 * matched / total + .22 * query_match / max(query_total, 1e-9) if total else 0
        neural_attention = .78 * attention / total + .22 * query_match / max(query_total, 1e-9) if total else 0
        order = sequence / sequence_total if sequence_total else 0
        keyword = keyword_match / keyword_total if keyword_total else 0
        if example.synthetic:
            field_score *= .80
            neural_attention *= .80
            keyword *= .80
        if self._negative_clause(query) != self._negative_clause(example.tokens):
            field_score *= .25
            neural_attention *= .25
            order *= .25
        return field_score, neural_attention, order, keyword

    def _score(self, query, mode):
        count = len(self.tools) + 1
        candidates = [Candidate() for _ in range(count)]
        drive, mass, embedding = [0.0] * count, [0.0] * count, [0.0] * DIMENSIONS
        for token in query:
            token.id = self.vocabulary.get(token.word, -1)
            if token.id >= 0:
                weight = self.weight(token)
                for d, value in enumerate(self.words[token.id].vector):
                    embedding[d] += value * weight
        normalize(embedding)
        if mode == 'keyword':
            for index, example in enumerate(self.examples):
                hit = total = 0.0
                for token in example.tokens:
                    weight = self.weight(token)
                    if not weight:
                        continue
                    total += weight
                    if any(not word.quoted and token.word == word.word for word in query):
                        hit += weight
                if total:
                    value = hit / total * (.8 if example.synthetic else 1.0)
                    candidate = candidates[example.tool]
                    if value > candidate.keyword:
                        candidate.keyword, candidate.best = value, index
            return candidates, []
        roles = [0.0] * count
        role_examples = [0] * count
        for example in self.examples:
            if not example.synthetic:
                role_examples[example.tool] += 1
                roles[example.tool] = max(roles[example.tool], self._prefix_agreement(query, example.tokens))
        for i, examples in enumerate(role_examples):
            if not examples:
                roles[i] = 1.0
        roles[len(self.tools)] = 1.0
        for index, example in enumerate(self.examples):
            field_score, attention, order, keyword = self._example_scores(query, example)
            field_score *= roles[example.tool]
            attention *= roles[example.tool]
            order *= roles[example.tool]
            evidence = .90 * attention + .10 * order
            candidate = candidates[example.tool]
            if field_score > candidate.field:
                candidate.field = field_score
                if mode == 'field':
                    candidate.best = index
            if mode == 'field':
                continue
            candidate.keyword = max(candidate.keyword, keyword)
            if evidence > candidate.evidence:
                candidate.evidence, candidate.prophecy, candidate.best = evidence, order, index
            activation = math.exp(10.0 * evidence)
            drive[example.tool] += activation * evidence
            mass[example.tool] += activation
        if mode == 'field':
            return candidates, []
        state = []
        for i, candidate in enumerate(candidates):
            attended = drive[i] / mass[i] if mass[i] else 0
            drive[i] = .88 * candidate.evidence + .12 * attended
            state.append(sigmoid(8.0 * (drive[i] - .53)))
        trajectory = []
        # Recurrent attractors (destiny) competitively settle example attention.
        for _ in range(ITERATIONS):
            total = sum(state)
            context = embedding[:]
            for d in range(DIMENSIONS):
                for i in range(count):
                    context[d] += .45 * state[i] * state[i] * self.signatures[i][d] / max(total, 1e-9)
            normalize(context)
            following = []
            for i in range(count):
                attraction = max(0, dot(context, self.signatures[i]))
                competitors = (total - state[i]) / max(1, len(self.tools))
                following.append(sigmoid(7.0 * (drive[i] - .53) + .80 * state[i] + .22 * attraction - .45 * competitors))
            state = following
            trajectory.append(state)
        for i, candidate in enumerate(candidates):
            total = self.accepted[i] + self.rejected[i]
            reliability = .9 + .1 * (self.accepted[i] + 1.0) / (total + 2.0) if total else 1.0
            candidate.neural = state[i] * reliability
        return candidates, trajectory

    @staticmethod
    def _phrase_at(query, position, phrase):
        phrase = tokenize(phrase)
        if not phrase or position + len(phrase) > len(query):
            return None
        if all(token.word == query[position + i].word for i, token in enumerate(phrase)):
            return position + len(phrase)
        return None

    def _enum_value(self, prop, query, begin, end):
        found, at, until = None, 0, 0
        for index, value in enumerate(prop.values):
            phrase = scalar_text(value)
            for i in range(begin, end):
                for alias in [phrase] + prop.aliases.get(phrase, []):
                    finish = self._phrase_at(query, i, alias)
                    if finish is not None and finish <= end:
                        if found is not None and found != index:
                            return None
                        found, at, until = index, i, finish
        return (prop.values[found], at, until) if found is not None else None

    @staticmethod
    def _numeric_atom(query, index, end):
        word, finish = query[index].word, index + 1
        try:
            value = float(word)
        except ValueError:
            small = SMALL_NUMBERS.get(word, -1)
            if small < 0:
                if word in (b'a', b'an'):
                    value = 1.0
                elif word == b'half':
                    value = .5
                else:
                    return None
            else:
                value = float(small)
            if small >= 20 and index + 1 < end:
                ones = SMALL_NUMBERS.get(query[index + 1].word, -1)
                if 0 < ones < 10:
                    value += ones
                    finish += 1
            if finish < end and query[finish].word == b'hundred':
                value *= 100
                finish += 1
        return (value, finish) if math.isfinite(value) else None

    def _parse_number(self, prop, query, start, end):
        found, total, at, until = 0, 0.0, 0, 0
        # Unit-bearing quantities take priority over unrelated bare numbers.
        if prop.units:
            index = 0
            while index < len(query):
                atom = self._numeric_atom(query, index, len(query))
                if atom:
                    value, finish = atom
                    if finish < len(query) and query[finish].word in prop.units:
                        factor = prop.units[query[finish].word]
                        finish += 1
                        if [token.word for token in query[finish:finish + 3]] == [b'and', b'a', b'half']:
                            value += .5
                            finish += 3
                        if not found:
                            at = index
                        total += value * factor
                        until = finish
                        found += 1
                        index = finish - 1
                index += 1
            if found:
                return total, at, until
        index = start
        while index < end:
            atom = self._numeric_atom(query, index, end)
            if atom and query[index].word not in (b'a', b'an'):
                if found:
                    return None
                total, finish = atom
                at, until, found = index, finish, 1
                index = finish - 1
            index += 1
        return (total, at, until) if found else None

    @staticmethod
    def _align_template(example, query, tool):
        pattern = example.tokens
        budget = 25000
        best = None
        best_score = -1e30

        def visit(pi, qi, begins, ends, literals, score, matched, first, last):
            nonlocal budget, best, best_score
            budget -= 1
            if budget < 0:
                return
            if pi == len(pattern):
                if matched and score > best_score:
                    best = (begins[:], ends[:], literals[:], score, matched, first, last)
                    best_score = score
                return
            token = pattern[pi]
            if token.slot:
                captures = [len(query)] if pi + 1 == len(pattern) else range(qi, len(query) + 1)
                for end in captures:
                    begins[pi], ends[pi] = qi, end
                    visit(pi + 1, end, begins, ends, literals, score, matched, first, last)
                return
            for k in range(qi, len(query)):
                if bool(token.quoted) == bool(query[k].quoted) and token.word == query[k].word:
                    weight = .1 if token.word in FILLERS else 1.0
                    following = literals[:]
                    following[pi] = k
                    visit(pi + 1, k + 1, begins[:], ends[:], following, score + weight - .035 * (k - qi), matched + 1, k if first < 0 else first, k + 1)
            visit(pi + 1, qi, begins[:], ends[:], literals[:], score - (.05 if token.word in FILLERS else .85), matched, first, last)

        visit(0, 0, [-1] * len(pattern), [-1] * len(pattern), [-1] * len(pattern), 0.0, 0, -1, 0)
        if best_score < .5:
            return None
        begins, ends, literals, score, matched, first, last = best
        slots, bound = {}, {}
        names = {prop.name.encode('utf-8') for prop in tool.properties}
        for i, token in enumerate(pattern):
            if token.slot and token.word in names:
                name = token.word.decode('utf-8')
                slots[name] = (begins[i], ends[i])
                bound[name] = i > 0 and not pattern[i - 1].slot and literals[i - 1] >= 0
        anchors = sum(not token.slot for token in pattern)
        return {'slots': slots, 'bound': bound, 'score': score, 'selection_score': score + .08 * anchors,
                'matched': matched, 'first': first, 'last': last}

    def _frame_word(self, winner, word):
        return any(token.word == word and not token.slot
                   for example in self.examples if example.tool == winner and not example.synthetic
                   for token in example.tokens)

    def _frame_related(self, winner, prop, word):
        if word in FILLERS or self._frame_word(winner, word):
            return True
        query = Token(word, 0, 0, id=self.vocabulary.get(word, -1))
        for example in self.examples:
            if example.tool == winner and not example.synthetic:
                if any(not token.slot and self.relation(query, token) >= .08 for token in example.tokens):
                    return True
        for token in tokenize(prop.description):
            token.id = self.vocabulary.get(token.word, -1)
            if self.relation(query, token) >= .08:
                return True
        return False

    def _string_span(self, data, query, tool, prop, begin, end):
        winner = self.tools.index(tool)
        while end > begin and not query[end - 1].quoted and query[end - 1].word in (b'please', b'kindly'):
            end -= 1
        # Polite request suffixes are not part of an unquoted argument.
        if end - begin > 2 and not query[end - 2].quoted and not query[end - 1].quoted and query[end - 2].word == b'for' and query[end - 1].word in (b'me', b'us'):
            end -= 2
        i = begin
        while i < end:
            for other in tool.properties:
                if other is prop:
                    continue
                for value in other.values:
                    if not query[i].quoted and self._phrase_at(query, i, scalar_text(value)) is not None:
                        end = i
                        while end > begin and (query[end - 1].word in FILLERS or query[end - 1].word in (b'in', b'using')):
                            end -= 1
            i += 1
        start = query[begin].start if begin < end else len(data)
        finish = query.limit if end == len(query) else query[end].start
        while start > 0 and data[start - 1] in b"\"'":
            start -= 1
        quotes = [i for i in range(start, finish) if data[i] == 34 and (i == 0 or data[i - 1] != 92)]
        if len(quotes) >= 2:
            first, second = quotes[:2]
            introduction = all(self._frame_related(winner, prop, token.word) for token in query[begin:end] if token.start < first)
            tail = all(byte in SPACE + b'.!?,;' for byte in data[second + 1:finish])
            if introduction and tail:
                return begin, end, first + 1, second
        for i in range(start, finish):
            if data[i] == 58 and not (i > 0 and i + 1 < len(data) and 48 <= data[i - 1] <= 57 and 48 <= data[i + 1] <= 57):
                start = i + 1
                break
        while start < finish and data[start] in SPACE:
            start += 1
        while finish > start and data[finish - 1] in SPACE + b'.!?':
            finish -= 1
        if finish - start >= 2 and (data[start], data[finish - 1]) in ((34, 34), (39, 39)):
            start, finish = start + 1, finish - 1
        while finish > start and data[finish - 1] in b',;':
            finish -= 1
        return begin, end, start, finish

    def _string_candidates(self, data, query, winner, prop, field_score):
        """Compete distinct source spans against an explicit absent-value candidate."""
        tool = self.tools[winner]
        candidates = [{'start': -1, 'end': -1, 'score': 1.0}]
        for example in self.examples:
            if example.tool != winner or example.synthetic:
                continue
            alignment = self._align_template(example, query, tool)
            if not alignment or prop.name not in alignment['slots']:
                continue
            begin, end = alignment['slots'][prop.name]
            if begin < 0 or begin >= end:
                continue
            begin, end, start, finish = self._string_span(data, query, tool, prop, begin, end)
            if finish <= start:
                continue
            total = sum(.1 if token.word in FILLERS else 1.0 for token in example.tokens if not token.slot)
            content = [token for token in query[begin:end] if token.start >= start and token.end <= finish]
            quoted = any(token.quoted for token in content)
            novel = quoted or any(token.word not in FILLERS and not self._frame_word(winner, token.word) for token in content)
            content_words = sum(token.word not in FILLERS for token in content)
            if alignment['bound'][prop.name] and not content_words:
                novel = True
            score = ((1.0 if alignment['bound'][prop.name] else .15)
                     + .6 * clamp(alignment['score'] / max(1.0, total), 0.0, 1.0)
                     + .4 * bool(novel) + .05 * alignment['score'])
            if quoted:
                score += .25
            if not novel and end - begin <= 2 and not quoted:
                score -= .8
            previous = next((item for item in candidates[1:] if item['start'] == start and item['end'] == finish), None)
            if previous is not None:
                previous['score'] = max(previous['score'], score)
            elif len(candidates) < MAX_TOKENS:
                candidates.append({'start': start, 'end': finish, 'score': score})
        # The corpus can supply a preposition binding a fronted comma-delimited value.
        if len(query) > 2 and not query[0].quoted:
            binder = any(token.slot and token.word == prop.name.encode('utf-8')
                         and (example.tokens[i - 1].word in FILLERS or example.tokens[i - 1].word == b'in')
                         and example.tokens[i - 1].word == query[0].word
                         for example in self.examples if example.tool == winner and not example.synthetic
                         for i, token in enumerate(example.tokens) if i > 0)
            cut = next((i + 1 for i in range(1, len(query) - 1)
                        if b',' in data[query[i].end:query[i + 1].start]), -1) if binder else -1
            if cut > 1 and len(candidates) < MAX_TOKENS:
                candidates.append({'start': query[1].start, 'end': query[cut - 1].end,
                                   'score': 1.25 + .4 * field_score})
        chosen, second = 0, -1
        for i in range(1, len(candidates)):
            if candidates[i]['score'] > candidates[chosen]['score']:
                second, chosen = chosen, i
            elif second < 0 or candidates[i]['score'] > candidates[second]['score']:
                second = i
        diagnostics = {'evidence': round(candidates[chosen]['score'], 6),
                       'alternative': round(candidates[second]['score'], 6) if second >= 0 else 0.0,
                       'candidates': len(candidates)}
        if not chosen:
            return None, diagnostics
        start, finish = candidates[chosen]['start'], candidates[chosen]['end']
        value = data[start:finish].decode('utf-8')
        if not 0 < finish - start < MAX_TEXT or len(json.dumps(value, ensure_ascii=False).encode('utf-8')) >= MAX_TEXT:
            return None, diagnostics
        return {'value': value, 'source': 'input', 'span': [start, finish]}, diagnostics

    def _extract(self, text, query, winner, field_score, missing_diagnostics=None):
        tool, best, best_example = self.tools[winner], None, None
        for example in self.examples:
            if example.tool != winner or example.synthetic:
                continue
            alignment = self._align_template(example, query, tool)
            if alignment and (best is None or alignment['selection_score'] > best['selection_score']):
                best, best_example = alignment, example
        captures, complete = {}, True
        data = text.encode('utf-8')
        for prop in tool.properties:
            begin, end = best['slots'].get(prop.name, (0, len(query))) if best else (0, len(query))
            extracted = None
            capture = None
            diagnostics = None
            if prop.values:
                extracted = self._enum_value(prop, query, begin, end)
            elif prop.type in ('number', 'integer'):
                extracted = self._parse_number(prop, query, begin, end)
                if extracted is None and sum(item.type in ('number', 'integer') for item in tool.properties) == 1:
                    extracted = self._parse_number(prop, query, 0, len(query))
            elif prop.type == 'boolean':
                for i in range(begin, end):
                    if query[i].word in (b'true', b'false'):
                        extracted = (query[i].word == b'true', i, i + 1)
                        break
            elif prop.type == 'string':
                capture, diagnostics = self._string_candidates(data, query, winner, prop, field_score)
            if extracted:
                value, at, until = extracted
                if prop.type in ('number', 'integer'):
                    value = json.loads(format(value, '.17g'))
                capture = {'value': value, 'source': 'input', 'span': [query[at].start, query[until - 1].end]}
            if capture and not prop.valid(capture['value']):
                capture = None
            if capture is None and best_example and prop.name in best_example.arguments:
                value = best_example.arguments[prop.name]
                rendered = scalar_text(value)
                if not rendered.startswith('{'):
                    for i in range(len(query)):
                        finish = self._phrase_at(query, i, rendered)
                        if finish is not None:
                            capture = {'value': value, 'source': 'example value observed in input', 'span': [query[i].start, query[finish - 1].end]}
                            break
            if capture is None and prop.has_default:
                capture = {'value': prop.default, 'source': 'schema default', 'span': [0, 0]}
            for example in self.examples:
                if example.corrected and example.tool == winner and example.text == text and prop.name in example.arguments:
                    capture = {'value': example.arguments[prop.name], 'source': 'correction', 'span': [0, 0]}
                    diagnostics = {'evidence': 1.0, 'alternative': 0.0, 'candidates': 2}
            if capture and prop.valid(capture['value']):
                capture.update(diagnostics or {'evidence': 1.0, 'alternative': 0.0, 'candidates': 2})
                captures[prop.name] = capture
            elif prop.required:
                complete = False
                if missing_diagnostics is not None:
                    missing_diagnostics.append({'name': prop.name, **(diagnostics or
                        {'evidence': 1.0, 'alternative': 0.0, 'candidates': 1})})
        return captures, complete

    @staticmethod
    def _rank(candidates, mode):
        scores = [getattr(candidate, mode) for candidate in candidates]
        winner = max(range(len(scores)), key=scores.__getitem__)
        second = max((i for i in range(len(scores)) if i != winner), key=scores.__getitem__, default=-1)
        return winner, second, scores[winner], scores[second] if second >= 0 else -1

    @staticmethod
    def _explicit_continuation(data, query, index):
        if index <= 0 or index >= len(query) or query[index].quoted:
            return False
        if query[index].word not in (b'also', b'additionally', b'then', b'next'):
            return False
        return any(data[k] in b'.;!?' for k in range(query[index - 1].end, query[index].start))

    def _scope_content(self, data, query, mode):
        for i in range(1, len(query)):
            colon = any(data[k] == 58 and not (k > 0 and k + 1 < len(data) and 48 <= data[k - 1] <= 57 and 48 <= data[k + 1] <= 57) for k in range(query[i - 1].end, query[i].start))
            if colon and not query[i].quoted:
                begin = 0
                for k in range(1, i):
                    if query[k].quoted:
                        continue
                    for position in range(query[k - 1].end, query[k].start):
                        if data[position] in b'.;!?' and not (data[position] == 46 and position > 0
                                and position + 1 < len(data) and 48 <= data[position - 1] <= 57 and 48 <= data[position + 1] <= 57):
                            begin = k
                candidates, _ = self._score(query[begin:i], mode)
                winner, _, best, runner = self._rank(candidates, mode)
                if winner < len(self.tools) and best > .70 and best - runner > .07:
                    if any(prop.type == 'string' and not prop.values for prop in self.tools[winner].properties):
                        stop = next((k for k in range(i + 1, len(query)) if self._explicit_continuation(data, query, k)), len(query))
                        for token in query[i:stop]:
                            if not token.quoted:
                                token.quoted = 2
                        return

    def _clause_choice(self, data, query, candidates, trajectory, mode, winner):
        cuts = [0]
        for i in range(1, len(query)):
            if query[i].quoted or (query[i - 1].quoted and not self._explicit_continuation(data, query, i)):
                continue
            split = query[i].word in (b'and', b'then')
            if split and query[i].word == b'and' and i + 1 < len(query):
                if self._numeric_atom(query, i + 1, len(query)) is not None:
                    split = False
            for j in range(query[i - 1].end, query[i].start):
                if data[j] in b'.;:' and not (data[j] == 46 and j > 0 and j + 1 < len(data) and 48 <= data[j - 1] <= 57 and 48 <= data[j + 1] <= 57):
                    split = True
            if split:
                cuts.append(i)
        if len(cuts) < 2:
            return 0, None
        cuts.append(len(query))
        chosen, positives, different, saved = -1, 0, False, None
        for begin, end in zip(cuts, cuts[1:]):
            while begin < end and query[begin].word in (b'and', b'then', b'also', b'additionally', b'next'):
                begin += 1
            if begin >= end:
                continue
            subquery = Tokens(query[begin:end], query[end].start if end < len(query) else query.limit)
            subcandidates, subtrajectory = self._score(subquery, mode)
            selected, _, best, runner = self._rank(subcandidates, mode)
            if selected < len(self.tools) and best > .65 and best - runner > .07 and (mode != 'neural' or subcandidates[selected].evidence > .57):
                _, complete = self._extract(data.decode('utf-8'), subquery, selected, subcandidates[selected].field)
                if not complete:
                    continue
                if chosen >= 0 and chosen != selected:
                    different = True
                positives += 1
                chosen = selected
                saved = subquery, subcandidates, subtrajectory, selected, best, best - runner
        if positives > 1 and (different or self.tools[chosen].properties):
            return 2, None
        if positives >= 1 and (chosen != winner or candidates[chosen].evidence < .52):
            return 1, saved
        return 0, None

    def call(self, text, reasoning=False, mode='neural'):
        """Return at most one validated call; never execute the selected tool."""
        if reasoning not in (False, True, 2, 'compact'):
            raise ValueError('reasoning must be false, true or compact')
        if mode not in ('neural', 'field', 'keyword'):
            raise ValueError('unknown mode')
        bounded_string(text, MAX_TEXT, 'text exceeds 2047 bytes')
        # This cache is disposable arithmetic, never accumulated experience.
        self._relation_cache.clear()
        query = tokenize(text)
        data = text.encode('utf-8')
        self._scope_content(data, query, mode)
        candidates, trajectory = self._score(query, mode)
        winner, second, best, runner = self._rank(candidates, mode)
        confidence, margin = clamp(best, 0, 1), best - runner
        status, captures, missing_diagnostics = 'call', {}, []
        split, saved = self._clause_choice(data, query, candidates, trajectory, mode, winner)
        if split == 1:
            query, candidates, trajectory, winner, confidence, margin = saved
            best, second, runner = confidence, -1, 0
        insufficient = (mode == 'neural' and (candidates[winner].field < .50 or candidates[winner].evidence < .52)
                        or mode == 'field' and best < .50
                        or mode == 'keyword' and best < .55)
        ambiguous = (second >= 0 and ((mode == 'neural' and best - runner < .065 and runner > .52 and candidates[winner].evidence - candidates[second].evidence < .08)
                                     or (mode != 'neural' and best - runner < .065 and runner > .45)))
        if split == 2:
            status = 'ambiguous'
        elif not query or winner == len(self.tools) or insufficient:
            status = 'no_call'
        elif ambiguous:
            status = 'ambiguous'
        else:
            captures, complete = self._extract(text, query, winner, candidates[winner].field, missing_diagnostics)
            if not complete:
                status = 'missing_arguments'
        scores = [getattr(candidate, mode) for candidate in candidates]
        result = {'calls': [], 'status': status, 'confidence': round(confidence, 6)}
        if status == 'call':
            result['calls'] = [{'name': self.tools[winner].name, 'arguments': {name: capture['value'] for name, capture in captures.items()}}]
        elif status == 'missing_arguments':
            result['tool'] = self.tools[winner].name
            result['missing'] = [prop.name for prop in self.tools[winner].properties if prop.required and prop.name not in captures]
        if reasoning:
            explain = {'mode': mode, 'iterations': ITERATIONS if mode == 'neural' else 0, 'margin': round(margin, 6), 'score_kind': 'activation, not calibrated probability', 'candidates': [], 'evidence': [], 'arguments': [], 'missing_arguments': missing_diagnostics if status == 'missing_arguments' else [], 'trajectory': []}
            for i, candidate in enumerate(candidates):
                item = {'tool': self.tools[i].name if i < len(self.tools) else None, 'score': round(scores[i], 6), 'field': round(candidate.field, 6), 'prophecy': round(candidate.prophecy, 6)}
                if candidate.best >= 0:
                    item['example'] = self.examples[candidate.best].text
                explain['candidates'].append(item)
            if candidates[winner].best >= 0:
                pattern = self.examples[candidates[winner].best].tokens
                for token in query:
                    strength, related = 0.0, None
                    for other in pattern:
                        value = self.relation(token, other)
                        if value > strength:
                            strength, related = value, other.word
                    if strength > .30 and token.word not in FILLERS:
                        explain['evidence'].append({'text': token.word.decode('utf-8'), 'relation': related.decode('utf-8'), 'strength': round(strength, 6), 'span': [token.start, token.end]})
            for name, capture in captures.items():
                explain['arguments'].append({'name': name, **capture})
            if mode == 'neural':
                explain['trajectory'] = [round(state[winner], 6) for state in trajectory]
            if reasoning == 2 or reasoning == 'compact':
                explain = {'mode': mode, 'score_kind': explain['score_kind'],
                           'winner': self.tools[winner].name if winner < len(self.tools) else None,
                           'evidence': [item['text'] for item in explain['evidence'][:8]],
                           'arguments': explain['arguments'], 'margin': round(margin, 6)}
            result['reasoning'] = explain
        self._relation_cache.clear()
        return result

    def _validate_correction(self, record):
        """A correction is an explicit complete answer, never a prediction."""
        if not isinstance(record, dict) or any(key not in ('text', 'tool', 'arguments') for key in record):
            raise ValueError('correction must contain only text, tool and arguments')
        if len(json.dumps(record, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')) > 65535:
            raise ValueError('correction exceeds 65535 bytes')
        text = bounded_string(record.get('text'), MAX_TEXT, 'invalid correction text')
        if not text or 'tool' not in record:
            raise ValueError('correction requires nonempty text and tool')
        tokens = tokenize(text)
        if not tokens:
            raise ValueError('correction requires nonempty text and tool')
        names = [tool.name for tool in self.tools]
        name = record['tool']
        if name is not None and (not isinstance(name, str) or name not in names):
            raise ValueError('correction names unknown tool')
        if name is not None and 'arguments' not in record:
            raise ValueError('correction requires complete arguments')
        arguments = record.get('arguments', {})
        if not isinstance(arguments, dict):
            raise ValueError('correction arguments must be an object')
        properties = [] if name is None else self.tools[names.index(name)].properties
        known = {prop.name: prop for prop in properties}
        for key, value in arguments.items():
            if key not in known:
                raise ValueError('correction argument names unknown property')
            if len(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')) >= MAX_TEXT or not known[key].valid(value):
                raise ValueError('correction argument violates schema')
        if any(prop.required and prop.name not in arguments for prop in properties):
            raise ValueError('correction is missing required arguments')
        return {'text': text, 'tool': name, 'arguments': dict(arguments)}

    def _append_corrections(self):
        names = [tool.name for tool in self.tools]
        corrected = {record['text'] for record in self.corrections}
        self.examples = [example for example in self.examples if example.text not in corrected]
        for record in self.corrections:
            winner = names.index(record['tool']) if record['tool'] is not None else len(self.tools)
            self._add_example(record['text'], winner, arguments=record['arguments'])
            self.examples[-1].corrected = True
            for token in self.examples[-1].tokens:
                token.slot = False

    def _rebuild_field(self):
        # Rebuild from the unchanged declarative source plus bounded corrections.
        # Slot derivation mutates tokens, so restore their source representation.
        self.examples = []
        for text, tool, arguments in self.base_examples:
            self._add_example(text, tool, arguments=arguments)
        self.words, self.vocabulary, self._relation_cache = [], {}, {}
        self.signatures = [[0.0] * DIMENSIONS for _ in range(len(self.tools) + 1)]
        self._append_corrections()
        self._build_field()

    def load_state(self, path, rebuild=True):
        if not pathlib.Path(path).exists():
            return
        state = strict_json(read_file(path))
        if not isinstance(state, dict) or state.get('identity') != f'{self.identity:016x}':
            raise ValueError('state identity does not match tools and examples; delete state to reset')
        if not numeric(state.get('version')) or state['version'] not in (1, 2):
            raise ValueError('unsupported state version')
        if not isinstance(state.get('tools'), dict):
            raise ValueError('invalid state tools')
        names = [tool.name for tool in self.tools]
        accepted, rejected = [0] * len(self.accepted), [0] * len(self.rejected)
        for name, counters in state['tools'].items():
            if name not in names:
                raise ValueError('state names unknown tool')
            if not isinstance(counters, dict):
                raise ValueError('invalid bounded state counters')
            values = [counters.get('accepted'), counters.get('rejected')]
            if any(not numeric(value) or value < 0 or value > 65535 or math.floor(value) != value for value in values):
                raise ValueError('invalid bounded state counters')
            i = names.index(name)
            accepted[i], rejected[i] = map(int, values)
        records = state.get('corrections', []) if state['version'] == 1 else state.get('corrections')
        if not isinstance(records, list) or len(records) > MAX_CORRECTIONS:
            raise ValueError('invalid bounded corrections')
        if state['version'] == 1 and 'corrections' in state:
            raise ValueError('version 1 state cannot contain corrections')
        corrections = [self._validate_correction(record) for record in records]
        if len({record['text'] for record in corrections}) != len(corrections):
            raise ValueError('duplicate correction text in state')
        self.accepted, self.rejected, self.corrections = accepted, rejected, corrections
        if rebuild:
            self._rebuild_field()

    def _save_state(self, path):
        state = {'version': 2, 'identity': f'{self.identity:016x}',
                 'tools': {tool.name: {'accepted': self.accepted[i], 'rejected': self.rejected[i]} for i, tool in enumerate(self.tools)},
                 'corrections': self.corrections}
        if len(os.fsencode(path)) + 5 >= 4096:
            raise ValueError('state path too long')
        temporary = str(path) + '.tmp'
        try:
            pathlib.Path(temporary).write_text(json.dumps(state, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n', encoding='utf-8')
            os.replace(temporary, path)
        except OSError as error:
            try:
                pathlib.Path(temporary).unlink(missing_ok=True)
            except OSError:
                pass
            raise ValueError('state write failed') from error

    def correct(self, record, path=None):
        """Persist one explicit correction and rebuild; no optimizer is involved."""
        path = path or self.state_path
        if not path:
            raise ValueError('correction requires --state')
        record = self._validate_correction(record)
        # Build and save a candidate before replacing the live model.
        fresh = Wolfe(self.tools_path, self.examples_path)
        if fresh.identity != self.identity:
            raise ValueError('definitions changed; reload model before correcting')
        fresh.accepted, fresh.rejected = self.accepted[:], self.rejected[:]
        fresh.corrections = [dict(item, arguments=dict(item['arguments'])) for item in self.corrections]
        existing = next((i for i, item in enumerate(fresh.corrections) if item['text'] == record['text']), None)
        if existing is None:
            if len(fresh.corrections) == MAX_CORRECTIONS:
                del fresh.corrections[0]
            fresh.corrections.append(record)
        else:
            fresh.corrections[existing] = record
        fresh._rebuild_field()
        fresh.state_path = path
        fresh._save_state(path)
        self.__dict__.update(fresh.__dict__)
        return {'status': 'corrected', 'corrections': len(self.corrections)}

    def feedback(self, result, kind, path=None):
        path = path or self.state_path
        if kind not in ('accepted', 'rejected'):
            raise ValueError('feedback must be accepted or rejected')
        if not path:
            raise ValueError('feedback requires --state')
        if result['status'] != 'call':
            raise ValueError('feedback requires a complete call')
        winner = [tool.name for tool in self.tools].index(result['calls'][0]['name'])
        previous = self.accepted[winner], self.rejected[winner]
        if self.accepted[winner] + self.rejected[winner] >= 65535:
            self.accepted[winner] //= 2
            self.rejected[winner] //= 2
        (self.accepted if kind == 'accepted' else self.rejected)[winner] += 1
        try:
            self._save_state(path)
        except (ValueError, OSError):
            self.accepted[winner], self.rejected[winner] = previous
            raise


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    begun = time.process_time()
    options = {'tools': 'tools.json', 'examples': 'examples.jsonl', 'state': None, 'feedback': None, 'mode': 'neural', 'correct': None}
    batch = reasoning = stats = False
    positional = []
    index = 0
    try:
        while index < len(argv):
            arg = argv[index]
            if arg in ('--help', '-h'):
                print('WOLFE — Weightless Ontological Language Function Engine\nUsage: python3 wolfe.py [--tools PATH] [--examples PATH] [--reasoning | --reasoning-compact] [--mode neural|field|keyword] [--batch] [--state PATH] [--feedback accepted|rejected] [--correct PATH] [--stats] [query]\nNo tools are executed. A request emits at most one validated call.')
                return 0
            if arg in ('--reasoning', '--explain'):
                reasoning = True
            elif arg == '--reasoning-compact':
                reasoning = 2
            elif arg == '--batch':
                batch = True
            elif arg == '--stats':
                stats = True
            elif arg in ('--tools', '--examples', '--state', '--feedback', '--mode', '--correct'):
                index += 1
                if index == len(argv):
                    raise ValueError('missing option value')
                options[arg[2:]] = argv[index]
            elif arg.startswith('--'):
                raise ValueError('unknown option: ' + arg)
            else:
                positional.append(arg)
            index += 1
        text = ' '.join(positional)
        if len(text.encode('utf-8')) + 2 >= MAX_TEXT:
            raise ValueError('query too long')
        if options['mode'] not in ('neural', 'field', 'keyword'):
            raise ValueError('unknown mode')
        if options['feedback'] and options['feedback'] not in ('accepted', 'rejected'):
            raise ValueError('feedback must be accepted or rejected')
        if options['feedback'] and not options['state']:
            raise ValueError('feedback requires --state')
        if batch and text:
            raise ValueError('--batch cannot take a positional query')
        if batch and options['feedback']:
            raise ValueError('batch feedback must not implicitly mark every request; use individual requests')
        if options['correct'] and not options['state']:
            raise ValueError('correction requires --state')
        if options['correct'] and (batch or text or options['feedback']):
            raise ValueError('--correct cannot be combined with query, batch or feedback')
        model = Wolfe(options['tools'], options['examples'], options['state'])
        if options['correct']:
            data = read_file(options['correct'])
            if len(data) > 65535:
                raise ValueError('correction exceeds 65535 bytes')
            record = strict_json(data)
            result = model.correct(record)
            print(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
            return 0
    except (ValueError, OSError, UnicodeError) as error:
        print('WOLFE: ' + str(error), file=sys.stderr)
        return 2
    if stats:
        print(json.dumps({'tools': len(model.tools), 'examples': len(model.examples), 'vocabulary': len(model.words), 'field_dimensions': DIMENSIONS, 'iterations': ITERATIONS, 'startup_cpu_ms': round(1000 * (time.process_time() - begun), 3), 'identity': f'{model.identity:016x}', 'pretrained_parameters': 0}), file=sys.stderr)

    def emit(value):
        print(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False), flush=True)

    exit_code = 0
    lines = sys.stdin.buffer if batch else [None]
    for line in lines:
        try:
            if batch:
                if len(line) >= 16383 and not line[:16383].endswith(b'\n'):
                    raise ValueError('batch line exceeds 16382 bytes')
                row = strict_json(line)
                text = bounded_string(row.get('text') if isinstance(row, dict) else None, MAX_TEXT, 'batch item requires text under 2048 bytes')
            elif not text:
                data = sys.stdin.buffer.readline(MAX_TEXT)
                if not data:
                    print('provide a query or --batch', file=sys.stderr)
                    return 2
                if len(data) >= MAX_TEXT - 1 and not data.endswith(b'\n'):
                    print('query too long', file=sys.stderr)
                    return 2
                text = data.decode('utf-8')
            result = model.call(text, reasoning, options['mode'])
            if options['feedback']:
                model.feedback(result, options['feedback'], options['state'])
            emit(result)
        except (ValueError, OSError, UnicodeError) as error:
            emit({'calls': [], 'status': 'error', 'error': str(error)})
            exit_code = 1
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
