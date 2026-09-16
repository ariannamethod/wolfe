/* WOLFE — Weightless Ontological Language Function Engine.
 * C99, libc + libm. No checkpoint, optimizer, network, or tool execution.
 *
 * The corpus constructs an associative neural field. Token units have sparse
 * lexical input and dense, corpus-derived context vectors. Attention activates
 * example units, which excite tool attractors. Corpus bigrams provide ordered
 * predictive input (prophecy); recurrent tool units retain and competitively
 * settle the attractor (destiny). Those settled units choose the tool.
 * PostGPT/Q are the architectural ancestors, not linked dependencies.
 * Numeric connections are calculated from declarations, never optimized.
 * Templates only bind arguments AFTER selection. They do not select tools.
 */
#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <ctype.h>
#include <math.h>
#include <errno.h>
#include <limits.h>
#include <time.h>
#include <float.h>
#include <stdarg.h>
#define NT 64
#define NP 16
#define NE 2048
#define NV 4096
#define NW 96
#define ND 96
#define NS 2048
#define NJ 32768
#define NVAL 32
#define MAX_FILE (4u*1024u*1024u)
#define ITERATIONS 6
#define NCORRECTIONS 32
#define CORRECTION_BYTES 65536
static char error_message[256];

static int fail(const char *s) {
    snprintf(error_message, sizeof error_message, "%s", s);
    return 0;
}

static void copy(char *d, size_t n, const char *s) {
    if (n) {
        size_t z = strlen(s);
        if (z >= n) z = n - 1;
        memcpy(d, s, z);
        d[z] = 0;
    }
}

static uint64_t hash_bytes(uint64_t h, const char *s, size_t n) {
    size_t i;
    for (i = 0; i < n; i++) {
        h ^= (unsigned char) s[i];
        h *= UINT64_C(1099511628211);
    }
    return h;
}

static uint64_t hash(const char *s) {
    return hash_bytes(UINT64_C(1469598103934665603), s, strlen(s));
}

static double clamp(double x, double lo, double hi) {
    return x < lo ? lo : x > hi ? hi : x;
}

/* A strict bounded JSON tree. Sibling links skip nested values. */
typedef struct {
    int type, start, end, child, next;
} JT;

typedef struct {
    const char *s;
    size_t n, p;
    JT *t;
    int used, depth;
} JP;

enum {
    JOBJ = 1,
    JARR,
    JSTR,
    JNUM,
    JBOOL,
    JNULL
};

static void ws(JP *j) {
    while (j->p < j->n && strchr(" \t\r\n", j->s[j->p])) j->p++;
}

static int parse_value(JP *j);

static int hexval(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static int parse_string(JP *j) {
    size_t start = ++j->p;
    while (j->p < j->n) {
        unsigned char c = (unsigned char) j->s[j->p++];
        if (c == '"') return (int) start;
        if (c < 32) return -1;
        if (c == '\\') {
            size_t k;
            if (j->p >= j->n) return -1;
            c = (unsigned char) j->s[j->p++];
            if (c == 'u') {
                for (k = 0; k < 4; k++) if (j->p >= j->n || hexval(j->s[j->p++]) < 0) return -1;
            } else if (!strchr("\"\\/bfnrt", c)) return -1;
        }
    }
    return -1;
}

static int parse_value(JP *j) {
    int id, last = -1;
    size_t start;
    char c;
    ws(j);
    if (j->p >= j->n || j->used >= NJ || j->depth++ > 32) {
        fail("JSON resource limit or missing value");
        return -1;
    }
    id = j->used++;
    j->t[id].child = j->t[id].next = -1;
    j->t[id].start = (int) j->p;
    c = j->s[j->p];
    if (c == '{' || c == '[') {
        char end = c == '{' ? '}' : ']';
        j->t[id].type = c == '{' ? JOBJ : JARR;
        j->p++;
        ws(j);
        if (j->p < j->n && j->s[j->p] == end) j->p++;
        else for (;;) {
            int v;
            if (c == '{') {
                ws(j);
                if (j->p >= j->n || j->s[j->p] != '"') return -1;
                v = parse_value(j);
                if (v < 0) return -1;
                if (last < 0) j->t[id].child = v;
                else j->t[last].next = v;
                last = v;
                ws(j);
                if (j->p >= j->n || j->s[j->p++] != ':') return -1;
            }
            v = parse_value(j);
            if (v < 0) return -1;
            if (last < 0) j->t[id].child = v;
            else j->t[last].next = v;
            last = v;
            ws(j);
            if (j->p >= j->n) return -1;
            if (j->s[j->p] == end) {
                j->p++;
                break;
            }
            if (j->s[j->p++] != ',') return -1;
        }
    } else if (c == '"') {
        j->t[id].type = JSTR;
        if (parse_string(j) < 0) return -1;
    } else if (c == 't' && j->n - j->p >= 4 && !memcmp(j->s + j->p, "true", 4)) {
        j->t[id].type = JBOOL;
        j->p += 4;
    } else if (c == 'f' && j->n - j->p >= 5 && !memcmp(j->s + j->p, "false", 5)) {
        j->t[id].type = JBOOL;
        j->p += 5;
    } else if (c == 'n' && j->n - j->p >= 4 && !memcmp(j->s + j->p, "null", 4)) {
        j->t[id].type = JNULL;
        j->p += 4;
    } else {
        j->t[id].type = JNUM;
        start = j->p;
        if (c == '-') j->p++;
        if (j->p >= j->n) return -1;
        if (j->s[j->p] == '0') j->p++;
        else {
            if (j->s[j->p] < '1' || j->s[j->p] > '9') return -1;
            while (j->p < j->n && isdigit((unsigned char) j->s[j->p])) j->p++;
        }
        if (j->p < j->n && j->s[j->p] == '.') {
            j->p++;
            if (j->p >= j->n || !isdigit((unsigned char) j->s[j->p])) return -1;
            while (j->p < j->n && isdigit((unsigned char) j->s[j->p])) j->p++;
        }
        if (j->p < j->n && (j->s[j->p] == 'e' || j->s[j->p] == 'E')) {
            j->p++;
            if (j->p < j->n && (j->s[j->p] == '+' || j->s[j->p] == '-')) j->p++;
            if (j->p >= j->n || !isdigit((unsigned char) j->s[j->p])) return -1;
            while (j->p < j->n && isdigit((unsigned char) j->s[j->p])) j->p++;
        }
        if (start == j->p) return -1;
    }
    j->t[id].end = (int) j->p;
    j->depth--;
    return id;
}

static int valid_utf8(const char *s) {
    const unsigned char *p = (const unsigned char *) s;
    while (*p) {
        unsigned c = *p++, u, min;
        int n, i;
        if (c < 128) continue;
        if (c >= 0xC2 && c <= 0xDF) {
            n = 1;
            u = c & 31;
            min = 0x80;
        } else if (c >= 0xE0 && c <= 0xEF) {
            n = 2;
            u = c & 15;
            min = 0x800;
        } else if (c >= 0xF0 && c <= 0xF4) {
            n = 3;
            u = c & 7;
            min = 0x10000;
        } else return 0;
        for (i = 0; i < n; i++) {
            if ((*p & 0xC0) != 0x80) return 0;
            u = (u << 6) | (*p++ & 63);
        }
        if (u < min || u > 0x10FFFF || (u >= 0xD800 && u <= 0xDFFF)) return 0;
    }
    return 1;
}

static int jtext(JP *j, int id, char *out, size_t cap);

static int tree_valid(JP *j) {
    int i;
    char left[NS], right[NS];
    for (i = 0; i < j->used; i++) {
        if (j->t[i].type == JSTR) {
            size_t n = (size_t)(j->t[i].end - j->t[i].start) + 1;
            char *v = malloc(n);
            int ok = v && jtext(j, i, v, n);
            free(v);
            if (!ok) return 0;
        }
        if (j->t[i].type == JOBJ) {
            int a, b;
            for (a = j->t[i].child; a >= 0;) {
                int av = j->t[a].next;
                if (!jtext(j, a, left, sizeof left)) return 0;
                for (b = av >= 0 ? j->t[av].next : -1; b >= 0;) {
                    int bv = j->t[b].next;
                    if (!jtext(j, b, right, sizeof right) || !strcmp(left, right)) return 0;
                    b = bv >= 0 ? j->t[bv].next : -1;
                }
                a = av >= 0 ? j->t[av].next : -1;
            }
        }
    }
    return 1;
}

static int json(JP *j, const char *s) {
    memset(j, 0, sizeof * j);
    j->s = s;
    j->n = strlen(s);
    if (!valid_utf8(s)) return fail("invalid UTF-8");
    j->t = calloc(NJ, sizeof * j->t);
    if (!j->t) return fail("out of memory");
    if (parse_value(j) != 0) {
        free(j->t);
        j->t = NULL;
        return fail("malformed JSON");
    }
    ws(j);
    if (j->p != j->n) {
        free(j->t);
        j->t = NULL;
        return fail("trailing JSON input");
    }
    if (!tree_valid(j)) {
        free(j->t);
        j->t = NULL;
        return fail("invalid JSON string or duplicate key");
    }
    return 1;
}

static int utf8(char *out, size_t cap, size_t *p, unsigned u) {
    unsigned char b[4];
    size_t n = 0, i;
    if (u < 128) b[n++] = (unsigned char) u;
    else if (u < 2048) {
        b[n++] = (unsigned char)(192 | (u >> 6));
        b[n++] = (unsigned char)(128 | (u & 63));
    } else if (u < 65536) {
        b[n++] = (unsigned char)(224 | (u >> 12));
        b[n++] = (unsigned char)(128 | ((u >> 6) & 63));
        b[n++] = (unsigned char)(128 | (u & 63));
    } else {
        b[n++] = (unsigned char)(240 | (u >> 18));
        b[n++] = (unsigned char)(128 | ((u >> 12) & 63));
        b[n++] = (unsigned char)(128 | ((u >> 6) & 63));
        b[n++] = (unsigned char)(128 | (u & 63));
    }
    if (*p + n >= cap) return 0;
    for (i = 0; i < n; i++) out[(*p)++] = (char) b[i];
    return 1;
}

static int jtext(JP *j, int id, char *out, size_t cap) {
    size_t p = 0, a, b;
    if (id < 0 || !cap) return 0;
    a = (size_t) j->t[id].start;
    b = (size_t) j->t[id].end;
    if (j->t[id].type == JSTR) {
        a++;
        b--;
        while (a < b) {
            unsigned char c = (unsigned char) j->s[a++];
            if (c == '\\') {
                c = (unsigned char) j->s[a++];
                if (c == 'u') {
                    unsigned u = 0;
                    int i;
                    for (i = 0; i < 4; i++) u = u *16 + (unsigned) hexval(j->s[a++]);
                    if (u >= 0xD800 && u <= 0xDBFF) {
                        unsigned v = 0;
                        if (a + 6 > b || j->s[a++] != '\\' || j->s[a++] != 'u') return 0;
                        for (i = 0; i < 4; i++) v = v *16 + (unsigned) hexval(j->s[a++]);
                        if (v < 0xDC00 || v > 0xDFFF) return 0;
                        u = 0x10000 + ((u - 0xD800) << 10) + (v - 0xDC00);
                    } else if (u >= 0xDC00 && u <= 0xDFFF) return 0;
                    if (u == 0 || !utf8(out, cap, &p, u)) return 0;
                    continue;
                }
                if (c == 'b') c = '\b';
                else if (c == 'f') c = '\f';
                else if (c == 'n') c = '\n';
                else if (c == 'r') c = '\r';
                else if (c == 't') c = '\t';
            }
            if (p + 1 >= cap) return 0;
            out[p++] = (char) c;
        }
    } else {
        if (b - a >= cap) return 0;
        memcpy(out, j->s + a, b - a);
        p = b - a;
    }
    out[p] = 0;
    return 1;
}

static int jeq(JP *j, int id, const char *s) {
    char b[256];
    return id >= 0 && jtext(j, id, b, sizeof b) && !strcmp(b, s);
}

static int get(JP *j, int obj, const char *key) {
    int k;
    if (obj < 0 || j->t[obj].type != JOBJ) return -1;
    for (k = j->t[obj].child; k >= 0;) {
        int v = j->t[k].next;
        if (v < 0) return -1;
        if (jeq(j, k, key)) return v;
        k = j->t[v].next;
    }
    return -1;
}

static double jnumber(JP *j, int id, double fallback) {
    char b[96], *e;
    double x;
    if (id < 0 || j->t[id].type != JNUM || !jtext(j, id, b, sizeof b)) return fallback;
    x = strtod(b, &e);
    return *e || !isfinite(x) ? fallback : x;
}

static int jraw(JP *j, int id, char *out, size_t cap) {
    size_t n;
    if (id < 0) return 0;
    n = (size_t)(j->t[id].end - j->t[id].start);
    if (n >= cap) return 0;
    memcpy(out, j->s + j->t[id].start, n);
    out[n] = 0;
    return 1;
}

static char *read_file(const char *path, size_t *n) {
    FILE *f = fopen(path, "rb");
    char *s;
    long z;
    if (!f) {
        snprintf(error_message, sizeof error_message, "cannot open %.180s", path);
        return NULL;
    }
    if (fseek(f, 0, SEEK_END) || (z = ftell(f)) < 0 || (unsigned long) z > MAX_FILE || fseek(f, 0, SEEK_SET)) {
        fclose(f);
        fail("file exceeds 4 MiB limit or cannot seek");
        return NULL;
    }
    s = malloc((size_t) z + 1);
    if (!s) {
        fclose(f);
        fail("out of memory");
        return NULL;
    }
    if (fread(s, 1, (size_t) z, f) != (size_t) z) {
        free(s);
        fclose(f);
        fail("file read failed");
        return NULL;
    }
    fclose(f);
    s[z] = 0;
    if (memchr(s, 0, (size_t) z)) {
        free(s);
        fail("embedded NUL in file");
        return NULL;
    }
    if (n) * n = (size_t) z;
    return s;
}

typedef struct {
    char value[256];
    char *aliases[NVAL];
    int n;
} Enum;

typedef struct {
    char word[64];
    double factor;
} Unit;

typedef struct {
    char name[64], description[256];
    int type, required;
    double min, max;
    int has_min, has_max;
    char def[NS];
    int has_default;
    Enum *values;
    int nv;
    Unit *units;
    int nu;
} Property;

enum {
    PSTR = 1,
    PNUM,
    PINT,
    PBOOL
};

typedef struct {
    char name[96], description[NS];
    Property *p;
    int np, allocated;
} Tool;

typedef struct {
    char word[96];
    int start, end, slot, id, quoted;
} Token;

typedef struct {
    Token t[NW];
    int n, limit;
} Tokens;

typedef struct {
    char text[NS];
    int tool;
    Tokens tokens;
    char *args[NP];
    int present[NP];
    int synthetic, corrected;
} Example;

typedef struct {
    char word[96];
    int df;
    double idf, v[ND];
} Word;

typedef struct {
    Tool tool[NT];
    int nt;
    Example *ex;
    int ne;
    Word *word;
    int nv;
    double signatures[NT + 1][ND];
    int tool_examples[NT + 1];
    unsigned accepted[NT + 1], rejected[NT + 1];
    uint64_t identity;
    char *corrections[NCORRECTIONS];
    int ncorrections;
} Model;

static int tokenize(const char *s, Tokens *out) {
    int i = 0, n = 0, quoted = 0;
    size_t length = strlen(s);
    memset(out, 0, sizeof * out);
    if (!valid_utf8(s)) return fail("invalid UTF-8");
    if (length >= NS) return fail("text exceeds 2047 bytes");
    while (s[i]) {
        int begin = i, k = 0, slot = 0;
        Token *t;
        if (s[i] == '{' && s[i + 1] && strchr(s + i + 1, '}')) {
            slot = 1;
            i++;
            begin = i;
            while (s[i] && s[i] != '}') i++;
        } else if (isalnum((unsigned char) s[i]) || (unsigned char) s[i] >= 128 || ((s[i] == '-' || s[i] == '+')
            && isdigit((unsigned char) s[i + 1]))) {
            i++;
            while (isalnum((unsigned char) s[i]) || (unsigned char) s[i] >= 128 || ((s[i] == '.' || s[i] == '\'')
                && isalnum((unsigned char) s[i + 1]))) i++;
        } else {
            if (s[i] == '"' && (i == 0 || s[i - 1] != '\\')) quoted = !quoted;
            i++;
            continue;
        }
        if (n >= NW) return fail("text exceeds 96 tokens");
        t = &out->t[n++];
        t->start = begin;
        t->end = i;
        t->slot = slot;
        t->id = -1;
        t->quoted = quoted;
        if (i - begin >= 96) return fail("token exceeds 95 bytes");
        while (begin < i) t->word[k++] = (char) tolower((unsigned char) s[begin++]);
        t->word[k] = 0;
        if (slot && s[i] == '}') i++;
    }
    out->n = n;
    out->limit = (int) length;
    return 1;
}

static int vocab(Model *m, const char *s, int add) {
    int i;
    for (i = 0; i < m->nv; i++) if (!strcmp(m->word[i].word, s)) return i;
    if (!add) return -1;
    if (m->nv >= NV) {
        fail("vocabulary exceeds 4096 words");
        return -2;
    }
    i = m->nv++;
    {
        Word *grown = realloc(m->word, (size_t) m->nv * sizeof * grown);
        if (!grown) {
            fail("out of memory");
            m->nv--;
            return -2;
        }
        m->word = grown;
        memset(&m->word[i], 0, sizeof m->word[i]);
    }
    copy(m->word[i].word, sizeof m->word[i].word, s);
    return i;
}

static int tool_id(Model *m, const char *s) {
    int i;
    for (i = 0; i < m->nt; i++) if (!strcmp(m->tool[i].name, s)) return i;
    return -1;
}

static int prop_id(Tool *t, const char *s) {
    int i;
    for (i = 0; i < t->np; i++) if (!strcmp(t->p[i].name, s)) return i;
    return -1;
}

static int validate_scalar(Property *p, const char *raw) {
    JP j;
    int ok = 1;
    double v;
    char value[NS];
    int i;
    if (!json(&j, raw)) return 0;
    if (p->type == PSTR) ok = j.t[0].type == JSTR;
    else if (p->type == PBOOL) ok = j.t[0].type == JBOOL;
    else {
        ok = j.t[0].type == JNUM;
        v = jnumber(&j, 0, NAN);
        if (!isfinite(v) || (p->type == PINT && floor(v) != v) || (p->has_min && v < p->min) || (p->has_max
            && v > p->max)) ok = 0;
    }
    if (ok && p->nv) {
        ok = 0;
        if (jtext(&j, 0, value, sizeof value)) for (i = 0; i < p->nv; i++) if (!strcmp(value, p->values[i].value)) ok = 1;
    }
    free(j.t);
    return ok;
}

static int allowed_keys(JP *j, int obj, const char *allowed) {
    int k;
    char name[128], needle[132];
    if (obj < 0 || j->t[obj].type != JOBJ) return fail("schema must be an object");
    for (k = j->t[obj].child; k >= 0;) {
        int v = j->t[k].next;
        if (!jtext(j, k, name, sizeof name)) return fail("schema key too long");
        snprintf(needle, sizeof needle, "|%s|", name);
        if (!strstr(allowed, needle)) {
            snprintf(error_message, sizeof error_message, "unsupported schema keyword: %.120s", name);
            return 0;
        }
        k = j->t[v].next;
    }
    return 1;
}

static int load_tools(Model *m, const char *path) {
    char *s;
    size_t sz;
    JP j;
    int a, x;
    if (!(s = read_file(path, &sz))) return 0;
    m->identity = hash_bytes(m->identity, s, sz);
    if (!json(&j, s)) {
        free(s);
        return 0;
    }
    a = j.t[0].type == JARR ? 0 : get(&j, 0, "tools");
    if (a < 0 || j.t[a].type != JARR) {
        fail("tools must be a JSON array or an object containing tools");
        goto bad;
    }
    for (x = j.t[a].child; x >= 0; x = j.t[x].next) {
        int o = x, f, par, props, k, req;
        Tool *t;
        if (m->nt >= NT) {
            fail("tool limit: 64");
            goto bad;
        }
        f = get(&j, o, "function");
        if (f >= 0) o = f;
        t = &m->tool[m->nt];
        if (!jtext(&j, get(&j, o, "name"), t->name, sizeof t->name) || !t->name[0]) {
            fail("tool requires a nonempty name under 96 bytes");
            goto bad;
        }
        if (tool_id(m, t->name) >= 0) {
            fail("duplicate tool name");
            goto bad;
        }
        f = get(&j, o, "description");
        if (f >= 0 && !jtext(&j, f, t->description, sizeof t->description)) {
            fail("tool description too long");
            goto bad;
        }
        par = get(&j, o, "parameters");
        if (par < 0) par = get(&j, o, "input_schema");
        if (par >= 0) {
            if (j.t[par].type != JOBJ || !jeq(&j, get(&j, par, "type"), "object")) {
                fail("parameters must be an object schema");
                goto bad;
            }
            if (!allowed_keys(&j, par, "|type|properties|required|additionalProperties|description|title|$schema|")) goto bad;
            if (get(&j, par, "oneOf") >= 0 || get(&j, par, "anyOf") >= 0 || get(&j, par, "allOf") >= 0
                || get(&j, par, "$ref") >= 0) {
                fail("unsupported composite schema");
                goto bad;
            }
            props = get(&j, par, "properties");
            if (props >= 0 && j.t[props].type != JOBJ) {
                fail("properties must be an object");
                goto bad;
            }
            for (k = props < 0 ? -1 : j.t[props].child; k >= 0;) {
                int v = j.t[k].next, typ, e, al, u;
                Property *p;
                if (t->np >= NP) {
                    fail("property limit: 16 per tool");
                    goto bad;
                }
                {
                    Property *grown = realloc(t->p, (size_t)(t->np + 1) * sizeof * grown);
                    if (!grown) {
                        fail("out of memory");
                        goto bad;
                    }
                    t->p = grown;
                    t->allocated = t->np + 1;
                    memset(&t->p[t->np], 0, sizeof * t->p);
                }
                p = &t->p[t->np];
                if (!jtext(&j, k, p->name, sizeof p->name) || prop_id(t, p->name) >= 0) {
                    fail("invalid or duplicate property name");
                    goto bad;
                }
                if (!allowed_keys(&j, v, "|type|enum|default|description|title|minimum|maximum|x-unit|x-aliases|")) goto bad;
                typ = get(&j, v, "type");
                if (jeq(&j, typ, "string")) p->type = PSTR;
                else if (jeq(&j, typ, "number")) p->type = PNUM;
                else if (jeq(&j, typ, "integer")) p->type = PINT;
                else if (jeq(&j, typ, "boolean")) p->type = PBOOL;
                else {
                    fail("only flat string, number, integer, boolean properties are supported");
                    goto bad;
                }
                if (get(&j, v, "oneOf") >= 0 || get(&j, v, "anyOf") >= 0 || get(&j, v, "allOf") >= 0
                    || get(&j, v, "$ref") >= 0 || get(&j, v, "pattern") >= 0 || get(&j, v, "format") >= 0
                    || get(&j, v, "exclusiveMinimum") >= 0 || get(&j, v, "exclusiveMaximum") >= 0 || get(&j,
                    v, "minLength") >= 0 || get(&j, v, "maxLength") >= 0 || get(&j, v, "multipleOf") >= 0) {
                    fail("unsupported property constraint");
                    goto bad;
                }
                e = get(&j, v, "description");
                if (e >= 0 && !jtext(&j, e, p->description, sizeof p->description)) {
                    fail("property description too long");
                    goto bad;
                }
                e = get(&j, v, "minimum");
                if (e >= 0) {
                    p->has_min = 1;
                    p->min = jnumber(&j, e, NAN);
                    if (!isfinite(p->min)) {
                        fail("invalid minimum");
                        goto bad;
                    }
                }
                e = get(&j, v, "maximum");
                if (e >= 0) {
                    p->has_max = 1;
                    p->max = jnumber(&j, e, NAN);
                    if (!isfinite(p->max)) {
                        fail("invalid maximum");
                        goto bad;
                    }
                }
                if (p->has_min && p->has_max && p->min > p->max) {
                    fail("minimum exceeds maximum");
                    goto bad;
                }
                p->values = calloc(NVAL, sizeof * p->values);
                p->units = calloc(NVAL, sizeof * p->units);
                if (!p->values || !p->units) {
                    fail("out of memory");
                    goto bad;
                }
                e = get(&j, v, "enum");
                if (e >= 0) {
                    int ev;
                    if (j.t[e].type != JARR) {
                        fail("enum must be an array");
                        goto bad;
                    }
                    for (ev = j.t[e].child; ev >= 0; ev = j.t[ev].next) {
                        char raw[NS];
                        if (p->nv >= NVAL || !jtext(&j, ev, p->values[p->nv].value, sizeof p->values[0].value)
                            || !jraw(&j, ev, raw, sizeof raw)) {
                            fail("enum limit exceeded");
                            goto bad;
                        }
                        {
                            int saved = p->nv, ok;
                            p->nv = 0;
                            ok = validate_scalar(p, raw);
                            p->nv = saved;
                            if (!ok) {
                                fail("enum value type mismatch");
                                goto bad;
                            }
                        }
                        p->nv++;
                    }
                }
                al = get(&j, v, "x-aliases");
                if (al >= 0) {
                    int ak;
                    if (j.t[al].type != JOBJ) {
                        fail("x-aliases must be an object");
                        goto bad;
                    }
                    for (ak = j.t[al].child; ak >= 0;) {
                        char name[256];
                        int av = j.t[ak].next, vi = -1, ai, z;
                        if (!jtext(&j, ak, name, sizeof name)) {
                            fail("invalid alias key");
                            goto bad;
                        }
                        for (z = 0; z < p->nv; z++) if (!strcmp(name, p->values[z].value)) vi = z;
                        if (vi < 0 && p->type == PBOOL && (!strcmp(name, "true") || !strcmp(name, "false"))
                            && p->nv < NVAL) {
                            vi = p->nv++;
                            copy(p->values[vi].value, sizeof p->values[vi].value, name);
                        }
                        if (vi < 0 || j.t[av].type != JARR) {
                            fail("alias key must name an enum value or boolean");
                            goto bad;
                        }
                        for (ai = j.t[av].child; ai >= 0; ai = j.t[ai].next) {
                            Enum *en = &p->values[vi];
                            if (en->n >= NVAL || (en->aliases[en->n] = calloc(128, 1)) == NULL || !jtext(&j,
                                ai, en->aliases[en->n], 128)) {
                                fail("alias limit exceeded");
                                goto bad;
                            }
                            en->n++;
                        }
                        ak = j.t[av].next;
                    }
                }
                u = get(&j, v, "x-unit");
                if (u >= 0) {
                    int uk;
                    if (j.t[u].type != JOBJ || (p->type != PNUM && p->type != PINT)) {
                        fail("x-unit requires a numeric property and object");
                        goto bad;
                    }
                    for (uk = j.t[u].child; uk >= 0;) {
                        int uv = j.t[uk].next;
                        if (p->nu >= NVAL || !jtext(&j, uk, p->units[p->nu].word, sizeof p->units[0].word)) {
                            fail("unit limit exceeded");
                            goto bad;
                        }
                        p->units[p->nu].factor = jnumber(&j, uv, NAN);
                        if (!isfinite(p->units[p->nu].factor) || p->units[p->nu].factor <= 0) {
                            fail("unit factor must be positive");
                            goto bad;
                        }
                        p->nu++;
                        uk = j.t[uv].next;
                    }
                }
                e = get(&j, v, "default");
                if (e >= 0) {
                    if (!jraw(&j, e, p->def, sizeof p->def) || !validate_scalar(p, p->def)) {
                        fail("invalid property default");
                        goto bad;
                    }
                    p->has_default = 1;
                }
                t->np++;
                k = j.t[v].next;
            }
            req = get(&j, par, "required");
            if (req >= 0) {
                int r;
                if (j.t[req].type != JARR) {
                    fail("required must be an array");
                    goto bad;
                }
                for (r = j.t[req].child; r >= 0; r = j.t[r].next) {
                    char name[64];
                    int pi;
                    if (!jtext(&j, r, name, sizeof name) || (pi = prop_id(t, name)) < 0) {
                        fail("required names unknown property");
                        goto bad;
                    }
                    t->p[pi].required = 1;
                }
            }
        }
        m->nt++;
    }
    free(j.t);
    free(s);
    if (!m->nt) return fail("at least one tool is required");
    return 1;
    bad:
    free(j.t);
    free(s);
    return 0;
}

static int add_example(Model *m, const char *text, int tool, int synthetic) {
    Example *e;
    if (m->ne >= NE) return fail("example limit: 2048");
    {
        Example *grown = realloc(m->ex, (size_t)(m->ne + 1) * sizeof * grown);
        if (!grown) return fail("out of memory");
        m->ex = grown;
        memset(&m->ex[m->ne], 0, sizeof * m->ex);
    }
    e = &m->ex[m->ne];
    if (strlen(text) >= sizeof e->text) return fail("example text too long");
    copy(e->text, sizeof e->text, text);
    e->tool = tool;
    e->synthetic = synthetic;
    if (!tokenize(text, &e->tokens)) return 0;
    m->ne++;
    return 1;
}

static int load_examples(Model *m, const char *path) {
    char *s, *line, *next;
    size_t sz;
    unsigned count = 0;
    if (!(s = read_file(path, &sz))) return 0;
    m->identity = hash_bytes(m->identity, s, sz);
    line = s;
    while (line && *line) {
        JP j;
        int id, tool, ar, k;
        char name[96], text[NS];
        next = strchr(line, '\n');
        if (next) * next++ = 0;
        while (isspace((unsigned char) * line)) line++;
        if (! * line) {
            line = next;
            continue;
        }
        if (!json(&j, line)) {
            free(s);
            return 0;
        }
        id = get(&j, 0, "tool");
        if (id < 0) {
            free(j.t);
            free(s);
            return fail("each example requires tool (name or null)");
        }
        if (j.t[id].type == JNULL) tool = m->nt;
        else if (!jtext(&j, id, name, sizeof name) || (tool = tool_id(m, name)) < 0) {
            free(j.t);
            free(s);
            return fail("example names unknown tool");
        }
        if (get(&j, 0, "text") < 0 || j.t[get(&j, 0, "text")].type != JSTR || !jtext(&j, get(&j, 0, "text"),
            text, sizeof text) || !add_example(m, text, tool, 0)) {
            free(j.t);
            free(s);
            return fail("invalid example text or resource limit");
        }
        ar = get(&j, 0, "arguments");
        if (ar >= 0 && j.t[ar].type != JOBJ) {
            free(j.t);
            free(s);
            return fail("example arguments must be an object");
        }
        for (k = ar < 0 ? -1 : j.t[ar].child; k >= 0;) {
            char key[64], val[NS];
            int v = j.t[k].next, pi;
            if (tool == m->nt || !jtext(&j, k, key, sizeof key) || (pi = prop_id(&m->tool[tool], key)) < 0) {
                free(j.t);
                free(s);
                return fail("example argument names unknown property");
            }
            m->ex[m->ne - 1].args[pi] = calloc(NS, 1);
            if (!m->ex[m->ne - 1].args[pi] || !jraw(&j, v, m->ex[m->ne - 1].args[pi], NS) || !jtext(&j,
                v, val, sizeof val)) {
                free(j.t);
                free(s);
                return fail("example argument too long");
            }
            if (!(j.t[v].type == JSTR && val[0] == '{' && val[strlen(val) - 1] == '}') && !validate_scalar(&m->tool[tool].p[pi],
                m->ex[m->ne - 1].args[pi])) {
                free(j.t);
                free(s);
                return fail("example argument violates schema");
            }
            m->ex[m->ne - 1].present[pi] = 1;
            k = j.t[v].next;
        }
        count++;
        free(j.t);
        line = next;
    }
    free(s);
    if (!count) return fail("examples file is empty");
    return 1;
}

static int filler(const char *s) {
    static const char *w[] = { "a", "an", "the", "please", "could", "would", "can", "you", "i", "me",
        "my", "we", "our", "to", "of", "for", "is", "are", "be", "it", "this", "that", "some", "with",
        "and", "then", "now", "just", "kindly", "want", "need", "like", "would", NULL};
    int i;
    for (i = 0; w[i]; i++) if (!strcmp(w[i], s)) return 1;
    return 0;
}

static double weight(Model *m, const Token *t) {
    if (t->slot) return 0;
    if (t->quoted) return .015;
    if (filler(t->word)) return .12;
    return t->id >= 0 ? m->word[t->id].idf : 1.;
}

static void project(double *v, const char *word, double scale) {
    uint64_t h = hash(word);
    int i;
    for (i = 0; i < 3; i++) {
        int k = (int)(h % ND);
        v[k] += ((h >> 20) & 1) ? scale : -scale;
        h = h * UINT64_C(6364136223846793005) + 1;
    }
}

static void normalize(double *v) {
    double z = 0;
    int d;
    for (d = 0; d < ND; d++) z += v[d] * v[d];
    z = sqrt(z);
    if (z > 1e-12) for (d = 0; d < ND; d++) v[d] /= z;
}

static double dot(const double *a, const double *b) {
    int d;
    double z = 0;
    for (d = 0; d < ND; d++) z += a[d] * b[d];
    return z;
}

static void derive_slots(Model *m, Example *e) {
    int p;
    if (e->tool >= m->nt) return;
    for (p = 0; p < m->tool[e->tool].np; p++) if (e->present[p]) {
        JP j;
        Tokens literal;
        char value[NS];
        int k, z;
        if (!json(&j, e->args[p])) continue;
        if (!jtext(&j, 0, value, sizeof value) || value[0] == '{' || !tokenize(value, &literal) || !literal.n) {
            free(j.t);
            continue;
        }
        free(j.t);
        for (k = 0; k + literal.n <= e->tokens.n; k++) {
            for (z = 0; z < literal.n; z++) if (e->tokens.t[k + z].slot || strcmp(e->tokens.t[k + z].word,
                literal.t[z].word)) break;
            if (z == literal.n) {
                int end = e->tokens.t[k + literal.n - 1].end;
                e->tokens.t[k].slot = 1;
                copy(e->tokens.t[k].word, sizeof e->tokens.t[k].word, m->tool[e->tool].p[p].name);
                e->tokens.t[k].end = end;
                for (z = k + 1; z + literal.n - 1 < e->tokens.n; z++) e->tokens.t[z] = e->tokens.t[z + literal.n - 1];
                e->tokens.n -= literal.n - 1;
                break;
            }
        }
    }
}

static int build_field(Model *m) {
    int i, j, k, d;
    for (i = 0; i < m->ne; i++) derive_slots(m, &m->ex[i]);
    for (i = 0; i < m->nt; i++) {
        char name[NS];
        copy(name, sizeof name, m->tool[i].name);
        for (j = 0; name[j]; j++) if (name[j] == '_') name[j] = ' ';
        if (!add_example(m, name, i, 1)) return 0;
        if (m->tool[i].description[0] && !add_example(m, m->tool[i].description, i, 1)) return 0;
    }
    for (i = 0; i < m->ne; i++) {
        Tokens *t = &m->ex[i].tokens;
        m->tool_examples[m->ex[i].tool]++;
        for (j = 0; j < t->n; j++) if (!t->t[j].slot) {
            int v = vocab(m, t->t[j].word, 1);
            if (v < 0) return 0;
            t->t[j].id = v;
            for (k = 0; k < j; k++) if (t->t[k].id == v) break;
            if (k == j) m->word[v].df++;
        }
    }
    for (i = 0; i < m->nv; i++) {
        m->word[i].idf = 1. + log((m->ne + 1.) / (m->word[i].df + 1.));
        project(m->word[i].v, m->word[i].word, 1.);
    }
    /* Hebbian context: simultaneous corpus tokens contribute signed context
  * projections; no random trainable embedding table is introduced. */
    for (i = 0; i < m->ne; i++) {
        Tokens *t = &m->ex[i].tokens;
        for (j = 0; j < t->n; j++) if (t->t[j].id >= 0) for (k = 0; k < t->n; k++) if (k != j && t->t[k].id >= 0
            && !filler(t->t[k].word)) {
            double proximity = 1. / (1. + fabs((double) j - k));
            project(m->word[t->t[j].id].v, t->t[k].word, .30 * proximity / sqrt(m->word[t->t[j].id].df));
        }
    }
    for (i = 0; i < m->nv; i++) normalize(m->word[i].v);
    for (i = 0; i < m->ne; i++) {
        Example *e = &m->ex[i];
        for (j = 0; j < e->tokens.n; j++) if (e->tokens.t[j].id >= 0) {
            Word *w = &m->word[e->tokens.t[j].id];
            double z = weight(m, &e->tokens.t[j]);
            for (d = 0; d < ND; d++) m->signatures[e->tool][d] += w->v[d] * z;
        }
    }
    for (i = 0; i <= m->nt; i++) normalize(m->signatures[i]);
    return 1;
}

typedef struct {
    double field, neural, keyword, prophecy, evidence;
    int best;
} Candidate;

typedef struct {
    char raw[NS], source[NS];
    int start, end, present;
    double evidence, alternative;
    int candidates;
} Capture;

typedef struct {
    Candidate c[NT + 1];
    Capture arg[NP];
    int winner, status, iterations;
    double confidence, margin;
    Tokens input;
    double trajectory[ITERATIONS][NT + 1];
} Result;

enum {
    CALL = 0,
    NO_CALL,
    AMBIGUOUS,
    MISSING
};

static double morphology(const char *a, const char *b) {
    size_t na = strlen(a), nb = strlen(b), i, j;
    int common = 0;
    if (na < 4 || nb < 4) return 0;
    for (i = 0; i + 2 < na; i++) for (j = 0; j + 2 < nb; j++) if (!memcmp(a + i, b + j, 3)) {
        common++;
        break;
    }
    return .35 * common / (double)(na + nb - 4 - common);
}

static double relation(Model *m, Token *a, Token *b) {
    double z, lex;
    if (a->slot || b->slot) return 0;
    if ((a->quoted != 0) != (b->quoted != 0)) return .01;
    if (!strcmp(a->word, b->word)) return 1;
    lex = morphology(a->word, b->word);
    z = (a->id >= 0 && b->id >= 0) ? clamp(dot(m->word[a->id].v, m->word[b->id].v), 0, 1) : 0;
    return fmax(lex, .32 * z);
}

static double sigmoid(double z) {
    return 1. / (1. + exp(-clamp(z, -40, 40)));
}

/* Negation is a clause-level input feature, not a tool-name rule. Matching
 * negative examples must compete on the same footing as positive examples;
 * otherwise a fully covered positive template can overwhelm an unseen denial.
 * Literal quoted/content spans do not change the action's polarity. */
static int negative_clause(Tokens *tokens) {
    int i;
    for (i = 0; i < tokens->n; i++) {
        const char *word = tokens->t[i].word;
        if (tokens->t[i].quoted || tokens->t[i].slot) continue;
        if (!strcmp(word, "not") && i + 1 < tokens->n && !strcmp(tokens->t[i + 1].word, "only")) continue;
        if (!strcmp(word, "not") || !strcmp(word, "never") || !strcmp(word, "don't") || !strcmp(word, "dont")) return 1;
    }
    return 0;
}

/* Function words are weak topic evidence, but their ordered prefix carries
 * the speaker's role. Compare that prefix with the user's examples separately
 * instead of letting a short imperative erase an unmatched subject or modal.
 * This uses the same corpus vocabulary; it does not classify tools by verbs. */
static int prefix_words(Model *m, Tokens *tokens, int *positions) {
    int i, n = 0;
    for (i = 0; i < tokens->n; i++) {
        Token *t = &tokens->t[i];
        if (t->quoted || t->slot) break;
        if (!filler(t->word) && strcmp(t->word, "am")
            && strcmp(t->word, "was") && strcmp(t->word, "were") && strcmp(t->word, "have")
            && strcmp(t->word, "has") && strcmp(t->word, "had") && strcmp(t->word, "no")
            && strcmp(t->word, "longer") && strcmp(t->word, "he") && strcmp(t->word, "she")
            && strcmp(t->word, "they") && strcmp(t->word, "i'd")) {
            if (vocab(m, t->word, 0) < 0) continue;
            break;
        }
        if (!strcmp(t->word, "a") || !strcmp(t->word, "an") || !strcmp(t->word, "the")
            || !strcmp(t->word, "please") || !strcmp(t->word, "just") || !strcmp(t->word, "kindly")
            || !strcmp(t->word, "for") || !strcmp(t->word, "to") || !strcmp(t->word, "of")
            || !strcmp(t->word, "with")) continue;
        if (!strcmp(t->word, "you")) {
            int k, desire = 0;
            for (k = 0; k < n; k++) if (!strcmp(tokens->t[positions[k]].word, "want")
                || !strcmp(tokens->t[positions[k]].word, "need") || !strcmp(tokens->t[positions[k]].word, "like")) desire = 1;
            if (desire) continue;
        }
        positions[n++] = i;
    }
    return n;
}

static int modal_word(const char *s) {
    return !strcmp(s, "can") || !strcmp(s, "could") || !strcmp(s, "would");
}

static int desire_word(const char *s) {
    return !strcmp(s, "want") || !strcmp(s, "need") || !strcmp(s, "like");
}

static int self_word(const char *s) {
    return !strcmp(s, "i") || !strcmp(s, "i'd");
}

static double prefix_agreement(Model *m, Tokens *q, Tokens *example) {
    int a[NW], b[NW], nq = prefix_words(m, q, a), ne = prefix_words(m, example, b), i, j = 0, matched = 0;
    if (!nq) return 1.;
    for (i = 0; i < nq; i++) {
        int k;
        for (k = j; k < ne; k++) if (!strcmp(q->t[a[i]].word, example->t[b[k]].word)
            || (modal_word(q->t[a[i]].word) && modal_word(example->t[b[k]].word))
            || (desire_word(q->t[a[i]].word) && desire_word(example->t[b[k]].word))
            || (self_word(q->t[a[i]].word) && self_word(example->t[b[k]].word))) {
            matched++;
            j = k + 1;
            break;
        }
    }
    {
        double overlap = matched / fmax(1., nq + ne - matched);
        return .30 + .70 * overlap * overlap;
    }
}

static void example_scores(Model *m, Tokens *q, Example *e, double *field, double *attention, double *order,
    double *keyword) {
    double matched = 0, total = 0, qmatch = 0, qtotal = 0, km = 0, kt = 0, seq = 0, seqtotal = 0, att = 0;
    int i, j;
    for (i = 0; i < e->tokens.n; i++) {
        Token *w = &e->tokens.t[i];
        double wt = weight(m, w), best = 0, literal = 0;
        if (!wt) continue;
        for (j = 0; j < q->n; j++) {
            double r = relation(m, w, &q->t[j]);
            if (r > best) best = r;
            if (!strcmp(w->word, q->t[j].word)) literal = 1;
        }
        matched += wt * best;
        total += wt;
        km += wt * literal;
        kt += wt;
        /* Content attention is sharpened; a weakly associated token cannot stand
   * in for a strongly present relation. An actual nonlinear neuron response. */
        att += wt * best * best;
    }
    for (j = 0; j < q->n; j++) {
        Token *w = &q->t[j];
        double wt = weight(m, w), best = 0;
        if (w->id < 0) wt *= .10;
        for (i = 0; i < e->tokens.n; i++) {
            double r = relation(m, w, &e->tokens.t[i]);
            if (r > best) best = r;
        }
        qmatch += wt * best;
        qtotal += wt;
    }
    for (i = 0; i + 1 < e->tokens.n; i++) {
        Token *a = &e->tokens.t[i], *b = &e->tokens.t[i + 1];
        double w = fmin(weight(m, a), weight(m, b)), best = 0;
        if (w <= .12) continue;
        for (j = 0; j + 1 < q->n; j++) {
            double z = relation(m, a, &q->t[j]) * relation(m, b, &q->t[j + 1]);
            if (z > best) best = z;
        }
        seq += w * best;
        seqtotal += w;
    }
    * field = total ? (.78 * matched / total + .22 * qmatch / fmax(qtotal, 1e-9)) : 0;
    *attention = total ? (.78 * att / total + .22 * qmatch / fmax(qtotal, 1e-9)) : 0;
    *order = seqtotal ? seq / seqtotal : 0;
    *keyword = kt ? km / kt : 0;
    if (e->synthetic) {
        * field *= .80;
        *attention *= .80;
        *keyword *= .80;
    }
    if (negative_clause(q) != negative_clause(&e->tokens)) {
        *field *= .25;
        *attention *= .25;
        *order *= .25;
    }
}

static void score(Model *m, Tokens *q, Result *r, int mode) {
    double drive[NT + 1] = { 0}, mass[NT + 1] = { 0}, embed[ND] = { 0}, state[NT + 1] = { 0};
    double role[NT + 1] = { 0};
    int role_examples[NT + 1] = { 0};
    int i, j, d, it;
    for (i = 0; i <= m->nt; i++) {
        r->c[i].best = -1;
        r->c[i].field = 0;
        r->c[i].keyword = 0;
    }
    for (j = 0; j < q->n; j++) {
        q->t[j].id = vocab(m, q->t[j].word, 0);
        if (q->t[j].id >= 0) {
            double w = weight(m, &q->t[j]);
            for (d = 0; d < ND; d++) embed[d] += m->word[q->t[j].id].v[d] * w;
        }
    }
    normalize(embed);
    if (mode == 2) {
        for (i = 0; i < m->ne; i++) {
            Example *e = &m->ex[i];
            double hit = 0, total = 0;
            for (j = 0; j < e->tokens.n; j++) {
                double w = weight(m, &e->tokens.t[j]);
                int k;
                if (!w) continue;
                total += w;
                for (k = 0; k < q->n; k++) if (!q->t[k].quoted && !strcmp(e->tokens.t[j].word, q->t[k].word)) {
                    hit += w;
                    break;
                }
            }
            if (total) {
                double value = hit / total * (e->synthetic ? .8 : 1.);
                Candidate *c = &r->c[e->tool];
                if (value > c->keyword) {
                    c->keyword = value;
                    c->best = i;
                }
            }
        }
        return;
    }
    for (i = 0; i < m->ne; i++) if (!m->ex[i].synthetic) {
        double agreement = prefix_agreement(m, q, &m->ex[i].tokens);
        role_examples[m->ex[i].tool]++;
        if (agreement > role[m->ex[i].tool]) role[m->ex[i].tool] = agreement;
    }
    for (i = 0; i < m->nt; i++) if (!role_examples[i]) role[i] = 1.;
    /* Rejection examples remain applicable to any speaker/request prefix. */
    role[m->nt] = 1.;
    for (i = 0; i < m->ne; i++) {
        double f, a, p, k, n;
        Candidate *c = &r->c[m->ex[i].tool];
        example_scores(m, q, &m->ex[i], &f, &a, &p, &k);
        f *= role[m->ex[i].tool];
        a *= role[m->ex[i].tool];
        p *= role[m->ex[i].tool];
        n = .90 * a + .10 * p;
        if (f > c->field) {
            c->field = f;
            if (mode == 1) c->best = i;
        }
        if (mode == 1) continue;
        if (k > c->keyword) c->keyword = k;
        if (n > c->evidence) {
            c->evidence = n;
            c->prophecy = p;
            c->best = i;
        }
        /* Boltzmann content attention over the example neurons of each tool. */
        {
            double h = exp(10. * n);
            drive[m->ex[i].tool] += h * n;
            mass[m->ex[i].tool] += h;
        }
    }
    if (mode == 1) return;
    for (i = 0; i <= m->nt; i++) {
        double attended = mass[i] ? drive[i] / mass[i] : 0;
        drive[i] = .88 * r->c[i].evidence + .12 * attended;
        state[i] = sigmoid(8. * (drive[i] - .53));
    }
    for (it = 0; it < ITERATIONS; it++) {
        double next[NT + 1], sum = 0, context[ND];
        for (i = 0; i <= m->nt; i++) sum += state[i];
        /* Tool -> semantic context feedback. Competing active tools bend the next
   * context, so later attractor alignment depends on the evolving population. */
        for (d = 0; d < ND; d++) {
            context[d] = embed[d];
            for (i = 0; i <= m->nt; i++) context[d] += .45 * state[i] * state[i] * m->signatures[i][d] / fmax(sum,
                1e-9);
        }
        normalize(context);
        for (i = 0; i <= m->nt; i++) {
            /* Persistent activation is destiny; schema/corpus semantic direction is
    * the attractor. Lateral inhibition makes competing actions compete. */
            double attraction = fmax(0, dot(context, m->signatures[i]));
            double competitors = (sum - state[i]) / fmax(1, m->nt);
            next[i] = sigmoid(7. * (drive[i] - .53) + .80 * state[i] + .22 * attraction - .45 * competitors);
            r->trajectory[it][i] = next[i];
        }
        for (i = 0; i <= m->nt; i++) state[i] = next[i];
    }
    r->iterations = mode == 0 ? ITERATIONS : 0;
    for (i = 0; i <= m->nt; i++) {
        double reliability = 1.;
        unsigned total = m->accepted[i] + m->rejected[i];
        if (total) reliability = .9 + .1 * (m->accepted[i] + 1.) / (total + 2.);
        r->c[i].neural = state[i] * reliability;
    }
}

static double selected_score(Candidate *c, int mode) {
    return mode == 1 ? c->field : mode == 2 ? c->keyword : c->neural;
}

static void emit_string(FILE *f, const char *s) {
    const unsigned char *p = (const unsigned char *) s;
    fputc('"', f);
    for (; *p; p++) {
        switch (*p) {
            case '"':
            fputs("\\\"", f);
            break;
            case '\\':
            fputs("\\\\", f);
            break;
            case '\n':
            fputs("\\n", f);
            break;
            case '\r':
            fputs("\\r", f);
            break;
            case '\t':
            fputs("\\t", f);
            break;
            default:
            if (*p < 32) fprintf(f, "\\u%04x", *p);
            else fputc(*p, f);
        }
    }
    fputc('"', f);
}

static int quote_raw(const char *s, char *out, size_t cap) {
    size_t k = 0;
    const unsigned char *p = (const unsigned char *) s;
    if (cap < 3) return 0;
    out[k++] = '"';
    for (; *p; p++) {
        char b[8];
        size_t n = 1;
        b[0] = (char) * p;
        if (*p == '"' || *p == '\\') {
            b[0] = '\\';
            b[1] = (char) * p;
            n = 2;
        } else if (*p < 32) {
            snprintf(b, sizeof b, "\\u%04x", *p);
            n = 6;
        }
        if (k + n + 2 > cap) return 0;
        memcpy(out + k, b, n);
        k += n;
    }
    out[k++] = '"';
    out[k] = 0;
    return 1;
}

static int small_number(const char *s) {
    static const char *v[] = { "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
        "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"};
    int i;
    for (i = 0; i < 28; i++) if (!strcmp(s, v[i])) return i < 20 ? i : (i - 18) * 10;
    return -1;
}

static int numeric_atom(Tokens *q, int i, int end, double *x, int *finish) {
    char *tail;
    int z;
    errno = 0;
    *x = strtod(q->t[i].word, &tail);
    *finish = i + 1;
    if (*tail || tail == q->t[i].word || errno) {
        z = small_number(q->t[i].word);
        if (z < 0) {
            if (!strcmp(q->t[i].word, "a") || !strcmp(q->t[i].word, "an")) * x = 1;
            else if (!strcmp(q->t[i].word, "half")) * x = .5;
            else return 0;
        } else *x = z;
        if (z >= 20 && i + 1 < end) {
            int b = small_number(q->t[i + 1].word);
            if (b > 0 && b < 10) {
                * x += b;
                (*finish)++;
            }
        }
        if (*finish < end && !strcmp(q->t[*finish].word, "hundred")) {
            * x *= 100;
            (*finish)++;
        }
    }
    return isfinite(*x);
}

static int parse_number(Property *p, Tokens *q, int start, int end, double *out, int *at, int *until) {
    int i, found = 0;
    double sum = 0;
    /* Prefer explicitly unit-bearing quantities. Unrelated bare numbers do not
  * become duration merely because they occur later in the sentence. */
    if (p->nu) for (i = 0; i < q->n; i++) {
        double x;
        int finish, u;
        if (!numeric_atom(q, i, q->n, &x, &finish)) continue;
        for (u = 0; u < p->nu; u++) if (finish < q->n && !strcmp(q->t[finish].word, p->units[u].word)) {
            double factor = p->units[u].factor;
            finish++;
            if (finish + 2 < q->n && !strcmp(q->t[finish].word, "and") && !strcmp(q->t[finish + 1].word,
                "a") && !strcmp(q->t[finish + 2].word, "half")) {
                x += .5;
                finish += 3;
            }
            if (!found) * at = i;
            sum += x * factor;
            *until = finish;
            found++;
            i = finish - 1;
            break;
        }
    }
    if (found) {
        * out = sum;
        return 1;
    }
    for (i = start; i < end; i++) {
        double x;
        int finish;
        if (!numeric_atom(q, i, end, &x, &finish)) continue;
        if (!strcmp(q->t[i].word, "a") || !strcmp(q->t[i].word, "an")) continue;
        if (found) return 0;
        *at = i;
        *until = finish;
        sum = x;
        found = 1;
        i = finish - 1;
    }
    if (!found) return 0;
    *out = sum;
    return 1;
}

static int phrase_at(Tokens *q, int pos, const char *phrase, int *end) {
    Tokens t;
    int i;
    if (!tokenize(phrase, &t) || !t.n || pos + t.n > q->n) return 0;
    for (i = 0; i < t.n; i++) if (strcmp(q->t[pos + i].word, t.t[i].word)) return 0;
    *end = pos + t.n;
    return 1;
}

static int enum_value(Property *p, Tokens *q, int begin, int end, char *out, size_t cap, int *at, int *until) {
    int v, i, a, got = -1;
    for (v = 0; v < p->nv; v++) {
        for (i = begin; i < end; i++) {
            int en;
            if (phrase_at(q, i, p->values[v].value, &en) && en <= end) {
                if (got >= 0 && got != v) return 0;
                got = v;
                *at = i;
                *until = en;
            }
            for (a = 0; a < p->values[v].n; a++) if (phrase_at(q, i, p->values[v].aliases[a], &en) && en <= end) {
                if (got >= 0 && got != v) return 0;
                got = v;
                *at = i;
                *until = en;
            }
        }
    }
    if (got < 0) return 0;
    if (p->type == PSTR) return quote_raw(p->values[got].value, out, cap);
    copy(out, cap, p->values[got].value);
    return 1;
}

typedef struct {
    int begin[NP], end[NP];
    int bound[NP];
    double score;
    int matched;
    int first, last;
} Alignment;

/* Generic monotonic template alignment. Slots capture spans; literal anchors
 * must actually occur, rather than hallucinating missing argument boundaries. */
typedef struct {
    int begin[NW], end[NW];
    int literal[NW];
    double score;
    int matched, first, last;
} Match;

static void align_rec(Tokens *pat, Tokens *q, int pi, int qi, Match *cur, Match *best, int *budget) {
    int k;
    if (-- * budget < 0) return;
    if (pi == pat->n) {
        if (cur->matched && cur->score > best->score) * best = *cur;
        return;
    }
    if (pat->t[pi].slot) {
        int max = q->n;
        if (pi + 1 == pat->n) {
            cur->begin[pi] = qi;
            cur->end[pi] = q->n;
            align_rec(pat, q, pi + 1, q->n, cur, best, budget);
            return;
        }
        for (k = qi; k <= max; k++) {
            cur->begin[pi] = qi;
            cur->end[pi] = k;
            align_rec(pat, q, pi + 1, k, cur, best, budget);
        }
        return;
    }
    for (k = qi; k < q->n; k++) if ((pat->t[pi].quoted != 0) == (q->t[k].quoted != 0) && !strcmp(pat->t[pi].word, q->t[k].word)) {
        Match next = *cur;
        double wt = filler(pat->t[pi].word) ? .1 : 1.;
        next.score += wt - .035 * (k - qi);
        next.matched++;
        next.literal[pi] = k;
        if (next.first < 0) next.first = k;
        next.last = k + 1;
        align_rec(pat, q, pi + 1, k + 1, &next, best, budget);
    }
    {
        Match skipped = *cur;
        skipped.score -= filler(pat->t[pi].word) ? .05 : .85;
        align_rec(pat, q, pi + 1, qi, &skipped, best, budget);
    }
}

static int align_template(Example *e, Tokens *q, Alignment *a, Tool *tool) {
    Match cur, best;
    int budget = 25000, i, j;
    memset(&cur, 0, sizeof cur);
    memset(&best, 0, sizeof best);
    cur.first = -1;
    best.score = -1e30;
    for (i = 0; i < NW; i++) cur.begin[i] = cur.end[i] = cur.literal[i] = -1;
    align_rec(&e->tokens, q, 0, 0, &cur, &best, &budget);
    if (best.score < .5) return 0;
    memset(a, 0, sizeof * a);
    a->score = best.score;
    a->matched = best.matched;
    a->first = best.first;
    a->last = best.last;
    for (j = 0; j < NP; j++) a->begin[j] = a->end[j] = -1;
    for (i = 0; i < e->tokens.n; i++) if (e->tokens.t[i].slot) {
        int pi = prop_id(tool, e->tokens.t[i].word);
        if (pi >= 0) {
            a->begin[pi] = best.begin[i];
            a->end[pi] = best.end[i];
            a->bound[pi] = i > 0 && !e->tokens.t[i - 1].slot && best.literal[i - 1] >= 0;
        }
    }
    return 1;
}

static void trim_span(const char *input, int *start, int *end) {
    while (*start < *end && isspace((unsigned char) input[*start]))(*start)++;
    while (*end > *start && (isspace((unsigned char) input[*end - 1]) || strchr(".!?", input[*end - 1])))(*end)--;
    if (*end - *start >= 2 && ((input[*start] == '"' && input[*end - 1] == '"') || (input[*start] == '\''
        && input[*end - 1] == '\''))) {
        (*start)++;
        (*end)--;
    }
}

static int frame_word(Model *m, int tool, const char *word) {
    int i, j;
    for (i = 0; i < m->ne; i++) if (m->ex[i].tool == tool && !m->ex[i].synthetic) {
        Tokens *t = &m->ex[i].tokens;
        for (j = 0; j < t->n; j++) if (!t->t[j].slot && !strcmp(t->t[j].word, word)) return 1;
    }
    return 0;
}

static int frame_related(Model *m, int tool, int property, const char *word) {
    int i, j;
    Token query;
    Tokens description;
    if (filler(word) || frame_word(m, tool, word)) return 1;
    memset(&query, 0, sizeof query);
    copy(query.word, sizeof query.word, word);
    query.id = vocab(m, word, 0);
    for (i = 0; i < m->ne; i++) if (m->ex[i].tool == tool && !m->ex[i].synthetic) {
        Tokens *t = &m->ex[i].tokens;
        for (j = 0; j < t->n; j++) if (!t->t[j].slot && relation(m, &query, &t->t[j]) >= .08) return 1;
    }
    if (tokenize(m->tool[tool].p[property].description, &description)) {
        for (j = 0; j < description.n; j++) {
            description.t[j].id = vocab(m, description.t[j].word, 0);
            if (relation(m, &query, &description.t[j]) >= .08) return 1;
        }
    }
    return 0;
}

static void string_span(Model *m, const char *input, Tokens *q, Tool *tool, int property, int *begin, int *end,
    int *start, int *finish) {
    int i, k, en;
    while (*end > *begin && !q->t[*end - 1].quoted && (!strcmp(q->t[*end - 1].word, "please")
        || !strcmp(q->t[*end - 1].word, "kindly")))(*end)--;
    /* Benefactive politeness belongs to the request, unless it was explicitly
     * included in literal content. Keep a title consisting of "For Me" intact. */
    if (*end - *begin > 2 && !q->t[*end - 2].quoted && !q->t[*end - 1].quoted
        && !strcmp(q->t[*end - 2].word, "for")
        && (!strcmp(q->t[*end - 1].word, "me") || !strcmp(q->t[*end - 1].word, "us"))) *end -= 2;
    /* Other categorical properties delimit a free text slot, based on schema. */
    for (i = *begin; i < *end; i++) for (k = 0; k < tool->np; k++) if (k != property) {
        Property *p = &tool->p[k];
        int v;
        for (v = 0; v < p->nv; v++) if (!q->t[i].quoted && phrase_at(q, i, p->values[v].value, &en)) {
            * end = i;
            while (*end > *begin && (filler(q->t[*end - 1].word) || !strcmp(q->t[*end - 1].word, "in")
                || !strcmp(q->t[*end - 1].word, "using")))(*end)--;
        }
    }
    * start = *begin < *end ? q->t[*begin].start : (int) strlen(input);
    *finish = *end == q->n ? q->limit : q->t[*end].start;
    while (*start > 0 && (input[*start - 1] == '"' || input[*start - 1] == '\''))(*start)--;
    /* Quotes and a colon explicitly delimit literal content. A complete quoted
  * span wins over an introduction such as 'the track' or 'saying'. */
    {
        int a = -1, b = -1, introduction = 1, tail = 1;
        for (i = *start; i < *finish; i++) if (input[i] == '"' && (i == 0 || input[i - 1] != '\\')) {
            if (a < 0) a = i;
            else {
                b = i;
                break;
            }
        }
        for (i = *begin; i < *end && q->t[i].start < a; i++) if (!frame_related(m, (int)(tool - m->tool), property,
            q->t[i].word)) introduction = 0;
        for (i = b + 1; i < *finish; i++) if (!isspace((unsigned char) input[i]) && !strchr(".!?,;", input[i])) tail = 0;
        /* Corpus frame words can introduce one complete quoted value. A quote
         * embedded in arbitrary content does not silently erase that content. */
        if (a >= 0 && b > a && introduction && tail) {
            * start = a + 1;
            *finish = b;
            return;
        }
    }
    for (i = *start; i < *finish; i++) if (input[i] == ':' && !(i > 0 && isdigit((unsigned char) input[i - 1])
        && isdigit((unsigned char) input[i + 1]))) {
        * start = i + 1;
        break;
    }
    trim_span(input, start, finish);
    while (*finish > *start && strchr(",;", input[*finish - 1]))(*finish)--;
}

typedef struct {
    int start, end;
    double score;
} SpanCandidate;

/* The absent-value neuron competes with distinct source spans. Tool confidence
 * is deliberately not an argument-presence score: binding anchors, literal
 * delimiters and novel content provide separate evidence for each property. */
static int string_candidates(Model *m, const char *input, Result *r, int p, Capture *capture) {
    Tool *tool = &m->tool[r->winner];
    SpanCandidate candidates[NW];
    int count = 1, i, j, chosen = 0, second = -1;
    candidates[0].start = candidates[0].end = -1;
    candidates[0].score = 1.;
    for (i = 0; i < m->ne; i++) if (m->ex[i].tool == r->winner && !m->ex[i].synthetic) {
        Alignment a;
        int begin, end, start, finish, novel = 0, quoted = 0, content_words = 0;
        double scorev, total = 0;
        if (!align_template(&m->ex[i], &r->input, &a, tool) || a.begin[p] < 0 || a.begin[p] >= a.end[p]) continue;
        begin = a.begin[p]; end = a.end[p];
        string_span(m, input, &r->input, tool, p, &begin, &end, &start, &finish);
        if (finish <= start) continue;
        for (j = 0; j < m->ex[i].tokens.n; j++) if (!m->ex[i].tokens.t[j].slot) {
            total += filler(m->ex[i].tokens.t[j].word) ? .1 : 1.;
        }
        for (j = begin; j < end; j++) if (r->input.t[j].start >= start && r->input.t[j].end <= finish) {
            if (r->input.t[j].quoted) quoted = 1;
            if (!filler(r->input.t[j].word)) content_words++;
            if (!filler(r->input.t[j].word) && !frame_word(m, r->winner, r->input.t[j].word)) novel = 1;
        }
        /* An explicit literal may itself consist entirely of command words. */
        if (quoted) novel = 1;
        /* Strongly matched bindings can introduce literal values made only of
         * function words (a title such as "For Me"). An unmatched binding still
         * cannot turn a trailing request word into an argument. */
        if (a.bound[p] && !content_words) novel = 1;
        scorev = (a.bound[p] ? 1. : .15) + .6 * clamp(a.score / fmax(1., total), 0., 1.) + .4 * novel
            + .05 * a.score;
        if (quoted) scorev += .25;
        if (!novel && end - begin <= 2 && !quoted) scorev -= .8;
        for (j = 1; j < count; j++) if (candidates[j].start == start && candidates[j].end == finish) break;
        if (j == count) {
            if (count >= NW) continue;
            candidates[count].start = start; candidates[count].end = finish;
            candidates[count++].score = scorev;
        } else if (scorev > candidates[j].score) candidates[j].score = scorev;
    }
    /* A schema slot's own corpus preposition can also bind a fronted phrase.
     * The comma is a structural boundary; no place names or tool names enter
     * this rule. Ordinary complete aligned bindings retain higher support. */
    if (r->input.n > 2 && !r->input.t[0].quoted) {
        int binder = 0, cut = -1;
        for (i = 0; i < m->ne && !binder; i++) if (m->ex[i].tool == r->winner && !m->ex[i].synthetic) {
            Tokens *t = &m->ex[i].tokens;
            for (j = 1; j < t->n; j++) if (t->t[j].slot && !strcmp(t->t[j].word, tool->p[p].name)
                && (filler(t->t[j - 1].word) || !strcmp(t->t[j - 1].word, "in"))
                && !strcmp(t->t[j - 1].word, r->input.t[0].word)) binder = 1;
        }
        if (binder) for (i = 1; i + 1 < r->input.n; i++) {
            int k;
            for (k = r->input.t[i].end; k < r->input.t[i + 1].start; k++) if (input[k] == ',') cut = i + 1;
            if (cut >= 0) break;
        }
        if (cut > 1 && count < NW) {
            candidates[count].start = r->input.t[1].start;
            candidates[count].end = r->input.t[cut - 1].end;
            candidates[count++].score = 1.25 + .4 * r->c[r->winner].field;
        }
    }
    for (i = 1; i < count; i++) {
        if (candidates[i].score > candidates[chosen].score) { second = chosen; chosen = i; }
        else if (second < 0 || candidates[i].score > candidates[second].score) second = i;
    }
    capture->evidence = candidates[chosen].score;
    capture->alternative = second >= 0 ? candidates[second].score : 0.;
    capture->candidates = count;
    if (!chosen) return 0;
    capture->start = candidates[chosen].start;
    capture->end = candidates[chosen].end;
    {
        char value[NS];
        int length = capture->end - capture->start;
        if (length <= 0 || length >= NS) return 0;
        memcpy(value, input + capture->start, (size_t) length); value[length] = 0;
        if (!quote_raw(value, capture->raw, sizeof capture->raw)) return 0;
    }
    return 1;
}

static int extract(Model *m, const char *input, Result *r) {
    Tool *tool = &m->tool[r->winner];
    Alignment best;
    int best_e = -1, i, p, complete = 1;
    memset(r->arg, 0, sizeof r->arg);
    memset(&best, 0, sizeof best);
    best.score = -1e30;
    for (i = 0; i < m->ne; i++) if (m->ex[i].tool == r->winner && !m->ex[i].synthetic) {
        Alignment a;
        if (align_template(&m->ex[i], &r->input, &a, tool)) {
            int anchors = 0, j;
            double scorev;
            for (j = 0; j < m->ex[i].tokens.n; j++) if (!m->ex[i].tokens.t[j].slot) anchors++;
            scorev = a.score + .08 * anchors;
            if (scorev > best.score) {
                best = a;
                best.score = scorev;
                best_e = i;
            }
        }
    }
    for (p = 0; p < tool->np; p++) {
        Property *pr = &tool->p[p];
        Capture *c = &r->arg[p];
        int begin = 0, end = r->input.n, at = 0, until = 0;
        double value;
        if (best_e >= 0 && best.begin[p] >= 0) {
            begin = best.begin[p];
            end = best.end[p];
        }
        if (pr->nv) {
            if (enum_value(pr, &r->input, begin, end, c->raw, sizeof c->raw, &at, &until)) c->present = 1;
        } else if (pr->type == PNUM || pr->type == PINT) {
            int ok = parse_number(pr, &r->input, begin, end, &value, &at, &until);
            if (!ok) {
                int n = 0, z;
                for (z = 0; z < tool->np; z++) if (tool->p[z].type == PNUM || tool->p[z].type == PINT) n++;
                if (n == 1) ok = parse_number(pr, &r->input, 0, r->input.n, &value, &at, &until);
            }
            if (ok) {
                snprintf(c->raw, sizeof c->raw, "%.17g", value);
                c->present = 1;
            }
        } else if (pr->type == PBOOL) {
            for (i = begin; i < end; i++) if (!strcmp(r->input.t[i].word, "true") || !strcmp(r->input.t[i].word,
                "false")) {
                copy(c->raw, sizeof c->raw, r->input.t[i].word);
                at = i;
                until = i + 1;
                c->present = 1;
                break;
            }
        } else if (pr->type == PSTR) {
            c->present = string_candidates(m, input, r, p, c);
        }
        if (c->present && (!c->end) && until > at) {
            c->start = r->input.t[at].start;
            c->end = r->input.t[until - 1].end;
        }
        if (c->present) {
            copy(c->source, sizeof c->source, "input");
            if (!validate_scalar(pr, c->raw)) c->present = 0;
        }
        /* Concrete example constants are permitted only when all non-slot words
   * matched and the constant is itself present in the request; defaults are
   * the explicit way to supply an absent value. */
        if (!c->present && best_e >= 0 && m->ex[best_e].present[p]) {
            JP j;
            char val[NS];
            if (json(&j, m->ex[best_e].args[p])) {
                if (jtext(&j, 0, val, sizeof val) && val[0] != '{') {
                    for (i = 0; i < r->input.n; i++) {
                        int en;
                        if (phrase_at(&r->input, i, val, &en)) {
                            copy(c->raw, sizeof c->raw, m->ex[best_e].args[p]);
                            c->start = r->input.t[i].start;
                            c->end = r->input.t[en - 1].end;
                            copy(c->source, sizeof c->source, "example value observed in input");
                            c->present = 1;
                            break;
                        }
                    }
                }
                free(j.t);
            }
        }
        if (!c->present && pr->has_default) {
            copy(c->raw, sizeof c->raw, pr->def);
            copy(c->source, sizeof c->source, "schema default");
            c->present = 1;
        }
        /* A user-confirmed exact observation may carry a value absent from
         * its text. It remains ordinary corpus evidence for tool selection. */
        for (i = 0; i < m->ne; i++) if (m->ex[i].corrected && m->ex[i].tool == r->winner
            && m->ex[i].present[p] && !strcmp(m->ex[i].text, input)) {
            copy(c->raw, sizeof c->raw, m->ex[i].args[p]);
            copy(c->source, sizeof c->source, "correction");
            c->start = c->end = 0;
            c->present = 1;
            c->evidence = 1.; c->alternative = 0.; c->candidates = 2;
        }
        if (c->present && !validate_scalar(pr, c->raw)) c->present = 0;
        if (!c->candidates) {
            c->candidates = c->present ? 2 : 1;
            c->evidence = 1.; c->alternative = 0.;
        }
        if (!c->present && pr->required) complete = 0;
    }
    return complete;
}

static int rank_candidates(Model *m, Result *r, int mode, int *second, double *best, double *runner) {
    int i, winner = -1;
    *second = -1;
    *best = *runner = -1;
    for (i = 0; i <= m->nt; i++) {
        double v = selected_score(&r->c[i], mode);
        if (v > *best) {
            * runner = *best;
            *second = winner;
            *best = v;
            winner = i;
        } else if (v > *runner) {
            * runner = v;
            *second = i;
        }
    }
    return winner;
}

static int explicit_continuation(const char *text, Tokens *q, int i) {
    int k;
    const char *word;
    if (i <= 0 || i >= q->n || q->t[i].quoted) return 0;
    word = q->t[i].word;
    if (strcmp(word, "also") && strcmp(word, "additionally") && strcmp(word, "then") && strcmp(word, "next")) return 0;
    for (k = q->t[i - 1].end; k < q->t[i].start; k++) if (strchr(".;!?", text[k])) return 1;
    return 0;
}

static void scope_content(Model *m, const char *text, Tokens *q, int mode) {
    int i, k;
    for (i = 1; i < q->n; i++) {
        int colon = 0;
        for (k = q->t[i - 1].end; k < q->t[i].start; k++) if (text[k] == ':' && !(k > 0 && isdigit((unsigned char) text[k - 1])
            && isdigit((unsigned char) text[k + 1]))) colon = 1;
        if (colon && !q->t[i].quoted) {
            Result pre;
            int second, w, p, begin = 0;
            double best, runner;
            memset(&pre, 0, sizeof pre);
            pre.input = *q;
            /* Earlier observations do not change the role of the clause that
             * actually introduces this literal argument. */
            for (k = 1; k < i; k++) {
                int z;
                if (q->t[k].quoted) continue;
                for (z = q->t[k - 1].end; z < q->t[k].start; z++) if (strchr(".;!?", text[z])
                    && !(text[z] == '.' && z > 0 && isdigit((unsigned char) text[z - 1])
                    && isdigit((unsigned char) text[z + 1]))) begin = k;
            }
            pre.input.n = i - begin;
            for (k = begin; k < i; k++) pre.input.t[k - begin] = q->t[k];
            score(m, &pre.input, &pre, mode);
            w = rank_candidates(m, &pre, mode, &second, &best, &runner);
            if (w >= 0 && w < m->nt && best > .70 && best - runner > .07) {
                for (p = 0; p < m->tool[w].np; p++) if (m->tool[w].p[p].type == PSTR && !m->tool[w].p[p].nv) {
                    /* A colon introduces content, while an explicit new
                     * instruction after a sentence boundary resumes action
                     * language. Existing quotation marks remain literal. */
                    int stop = q->n;
                    for (k = i + 1; k < q->n; k++) if (explicit_continuation(text, q, k)) {
                        stop = k;
                        break;
                    }
                    for (k = i; k < stop; k++) if (!q->t[k].quoted) q->t[k].quoted = 2;
                    return;
                }
            }
        }
    }
}

/* Sentences and conjunctions define candidate request clauses. Each clause
 * still goes through the same neural field. A positive clause may coexist with
 * a no-call clause; two positive actions remain explicitly ambiguous. */
static int clause_choice(Model *m, const char *text, Result *r, int mode) {
    int cuts[NW + 1], nc = 1, i, j, chosen = -1, positives = 0, different = 0;
    Result saved;
    cuts[0] = 0;
    for (i = 1; i < r->input.n; i++) {
        int split = 0;
        if (r->input.t[i].quoted || (r->input.t[i - 1].quoted && !explicit_continuation(text, &r->input, i))) continue;
        if (!strcmp(r->input.t[i].word, "and") || !strcmp(r->input.t[i].word, "then")) split = 1;
        if (split && !strcmp(r->input.t[i].word, "and") && i + 1 < r->input.n) {
            double number;
            int after;
            /* A numeric continuation is part of one quantity, not a second
             * action. Schema-aware parsing below still validates the value. */
            if (numeric_atom(&r->input, i + 1, r->input.n, &number, &after)) split = 0;
        }
        for (j = r->input.t[i - 1].end; j < r->input.t[i].start; j++) if (strchr(".;:", text[j]) && !(text[j] == '.'
            && j > 0 && isdigit((unsigned char) text[j - 1]) && isdigit((unsigned char) text[j + 1]))) split = 1;
        if (split) cuts[nc++] = i;
    }
    cuts[nc] = r->input.n;
    if (nc < 2) return 0;
    for (i = 0; i < nc; i++) {
        Result sub;
        int begin = cuts[i], end = cuts[i + 1], second, w;
        double best, runner;
        while (begin < end && (!strcmp(r->input.t[begin].word, "and") || !strcmp(r->input.t[begin].word,
            "then") || !strcmp(r->input.t[begin].word, "also") || !strcmp(r->input.t[begin].word, "additionally")
            || !strcmp(r->input.t[begin].word, "next"))) begin++;
        if (begin >= end) continue;
        memset(&sub, 0, sizeof sub);
        sub.input.n = end - begin;
        sub.input.limit = end < r->input.n ? r->input.t[end].start : r->input.limit;
        for (j = begin; j < end; j++) sub.input.t[j - begin] = r->input.t[j];
        score(m, &sub.input, &sub, mode);
        w = rank_candidates(m, &sub, mode, &second, &best, &runner);
        if (w >= 0 && w < m->nt && best > .65 && best - runner > .07 && (mode != 0 || sub.c[w].evidence > .57)) {
            sub.winner = w;
            if (!extract(m, text, &sub)) continue;
            if (chosen >= 0 && chosen != w) different = 1;
            positives++;
            chosen = w;
            saved = sub;
            saved.winner = w;
            saved.confidence = best;
            saved.margin = best - runner;
        }
    }
    if (positives > 1 && (different || m->tool[chosen].np)) {
        r->status = AMBIGUOUS;
        return 2;
    }
    if (positives >= 1) {
        if (chosen == r->winner && r->c[chosen].evidence >= .52) return 0;
        *r = saved;
        r->winner = chosen;
        return 1;
    }
    return 0;
}

static int infer(Model *m, const char *text, Result *r, int mode) {
    int i, second = -1, winner = -1;
    double best = -1, runner = -1;
    memset(r, 0, sizeof * r);
    if (!tokenize(text, &r->input)) return 0;
    scope_content(m, text, &r->input, mode);
    score(m, &r->input, r, mode);
    for (i = 0; i <= m->nt; i++) {
        double s = selected_score(&r->c[i], mode);
        if (s > best) {
            runner = best;
            second = winner;
            best = s;
            winner = i;
        } else if (s > runner) {
            runner = s;
            second = i;
        }
    }
    r->winner = winner;
    r->confidence = clamp(best, 0, 1);
    r->margin = best - runner;
    r->status = CALL;
    {
        int split = clause_choice(m, text, r, mode);
        if (split == 2) return 1;
        if (split == 1) {
            winner = r->winner;
            best = r->confidence;
            second = -1;
            runner = 0;
        }
    }
    if (!r->input.n || winner == m->nt || (mode == 0 && (r->c[winner].field < .50 || r->c[winner].evidence < .52))
        || (mode == 1 && best < .50) || (mode == 2 && best < .55)) {
        r->status = NO_CALL;
        return 1;
    }
    if (second >= 0 && ((mode == 0 && best - runner < .065 && runner > .52 && r->c[winner].evidence - r->c[second].evidence < .08)
        || (mode != 0 && best - runner < .065 && runner > .45))) {
        r->status = AMBIGUOUS;
        return 1;
    }
    if (!extract(m, text, r)) r->status = MISSING;
    return 1;
}

static const char *status_name(int s) {
    return s == CALL ? "call" : s == NO_CALL ? "no_call" : s == AMBIGUOUS ? "ambiguous" : "missing_arguments";
}

/* One serializer serves CLI streams and caller-owned API buffers. Counting
 * continues after capacity is exhausted, so the caller can allocate exactly. */
typedef struct {
    FILE *file;
    char *buffer;
    size_t capacity, used;
} Sink;

static void sink_char(Sink *s, int c) {
    if (s->file) fputc(c, s->file);
    if (s->buffer && s->used + 1 < s->capacity) s->buffer[s->used] = (char)c;
    s->used++;
}

static void sink_puts(Sink *s, const char *text) {
    while (*text) sink_char(s, (unsigned char)*text++);
}

static void sink_printf(Sink *s, const char *format, ...) {
    char text[256];
    va_list args;
    va_start(args, format);
    vsnprintf(text, sizeof text, format, args);
    va_end(args);
    sink_puts(s, text);
}

static void sink_string(Sink *s, const char *text) {
    const unsigned char *p = (const unsigned char *)text;
    sink_char(s, '"');
    for (; *p; p++) {
        if (*p == '"') sink_puts(s, "\\\"");
        else if (*p == '\\') sink_puts(s, "\\\\");
        else if (*p == '\n') sink_puts(s, "\\n");
        else if (*p == '\r') sink_puts(s, "\\r");
        else if (*p == '\t') sink_puts(s, "\\t");
        else if (*p < 32) sink_printf(s, "\\u%04x", *p);
        else sink_char(s, *p);
    }
    sink_char(s, '"');
}

static void serialize(Model *m, const char *text, Result *r, int mode, int reasoning, Sink *sink) {
    int i, j;
    sink_puts(sink, "{\"calls\":[");
    if (r->status == CALL) {
        Tool *t = &m->tool[r->winner];
        sink_puts(sink, "{\"name\":");
        sink_string(sink, t->name);
        sink_puts(sink, ",\"arguments\":{");
        j = 0;
        for (i = 0; i < t->np; i++) if (r->arg[i].present) {
            if (j++) sink_char(sink, ',');
            sink_string(sink, t->p[i].name);
            sink_char(sink, ':');
            sink_puts(sink, r->arg[i].raw);
        }
        sink_puts(sink, "}}");
    }
    sink_puts(sink, "],\"status\":");
    sink_string(sink, status_name(r->status));
    sink_printf(sink, ",\"confidence\":%.6f", r->confidence);
    if (r->status == MISSING) {
        Tool *t = &m->tool[r->winner];
        sink_puts(sink, ",\"tool\":");
        sink_string(sink, t->name);
        sink_puts(sink, ",\"missing\":[");
        j = 0;
        for (i = 0; i < t->np; i++) if (t->p[i].required && !r->arg[i].present) {
            if (j++) sink_char(sink, ',');
            sink_string(sink, t->p[i].name);
        }
        sink_char(sink, ']');
    }
    if (reasoning == 1) {
        sink_puts(sink, ",\"reasoning\":{\"mode\":");
        sink_string(sink, mode == 0 ? "neural" : mode == 1 ? "field" : "keyword");
        sink_printf(sink, ",\"iterations\":%d,\"margin\":%.6f,\"score_kind\":\"activation, not calibrated probability\",\"candidates\":[",
            r->iterations, r->margin);
        for (i = 0; i <= m->nt; i++) {
            if (i) sink_char(sink, ',');
            sink_puts(sink, "{\"tool\":");
            if (i == m->nt) sink_puts(sink, "null");
            else sink_string(sink, m->tool[i].name);
            sink_printf(sink, ",\"score\":%.6f,\"field\":%.6f,\"prophecy\":%.6f", selected_score(&r->c[i], mode),
                r->c[i].field, r->c[i].prophecy);
            if (r->c[i].best >= 0) {
                sink_puts(sink, ",\"example\":");
                sink_string(sink, m->ex[r->c[i].best].text);
            }
            sink_char(sink, '}');
        }
        sink_char(sink, ']');
        sink_puts(sink, ",\"evidence\":[");
        j = 0;
        if (r->winner >= 0 && r->c[r->winner].best >= 0) {
            Tokens *t = &m->ex[r->c[r->winner].best].tokens;
            for (i = 0; i < r->input.n; i++) {
                int k;
                double strength = 0;
                const char *related = NULL;
                for (k = 0; k < t->n; k++) {
                    double z = relation(m, &r->input.t[i], &t->t[k]);
                    if (z > strength) {
                        strength = z;
                        related = t->t[k].word;
                    }
                }
                if (strength > .30 && !filler(r->input.t[i].word)) {
                    if (j++) sink_char(sink, ',');
                    sink_puts(sink, "{\"text\":");
                    sink_string(sink, r->input.t[i].word);
                    sink_puts(sink, ",\"relation\":");
                    sink_string(sink, related);
                    sink_printf(sink, ",\"strength\":%.6f,\"span\":[%d,%d]}", strength, r->input.t[i].start, r->input.t[i].end);
                }
            }
        }
        sink_char(sink, ']');
        sink_puts(sink, ",\"arguments\":[");
        j = 0;
        if (r->winner >= 0 && r->winner < m->nt) for (i = 0; i < m->tool[r->winner].np; i++) if (r->arg[i].present) {
            Capture *c = &r->arg[i];
            if (j++) sink_char(sink, ',');
            sink_puts(sink, "{\"name\":");
            sink_string(sink, m->tool[r->winner].p[i].name);
            sink_puts(sink, ",\"value\":");
            sink_puts(sink, c->raw);
            sink_puts(sink, ",\"source\":");
            sink_string(sink, c->source);
            sink_printf(sink, ",\"span\":[%d,%d],\"evidence\":%.6f,\"alternative\":%.6f,\"candidates\":%d}",
                c->start, c->end, c->evidence, c->alternative, c->candidates);
        }
        sink_char(sink, ']');
        sink_puts(sink, ",\"missing_arguments\":[");
        j = 0;
        if (r->status == MISSING && r->winner >= 0 && r->winner < m->nt) {
            Tool *t = &m->tool[r->winner];
            for (i = 0; i < t->np; i++) if (t->p[i].required && !r->arg[i].present) {
                Capture *c = &r->arg[i];
                if (j++) sink_char(sink, ',');
                sink_puts(sink, "{\"name\":");
                sink_string(sink, t->p[i].name);
                sink_printf(sink, ",\"evidence\":%.6f,\"alternative\":%.6f,\"candidates\":%d}",
                    c->evidence, c->alternative, c->candidates);
            }
        }
        sink_char(sink, ']');
        sink_puts(sink, ",\"trajectory\":[");
        for (i = 0; i < r->iterations; i++) {
            if (i) sink_char(sink, ',');
            sink_printf(sink, "%.6f", r->trajectory[i][r->winner]);
        }
        sink_puts(sink, "]}");
    }

    if (reasoning == 2) {
        sink_puts(sink, ",\"reasoning\":{\"mode\":");
        sink_string(sink, mode == 0 ? "neural" : mode == 1 ? "field" : "keyword");
        sink_puts(sink, ",\"score_kind\":\"activation, not calibrated probability\",\"winner\":");
        if (r->winner < 0 || r->winner == m->nt) sink_puts(sink, "null");
        else sink_string(sink, m->tool[r->winner].name);
        sink_puts(sink, ",\"evidence\":[");
        j = 0;
        if (r->winner >= 0 && r->c[r->winner].best >= 0) {
            Tokens *t = &m->ex[r->c[r->winner].best].tokens;
            for (i = 0; i < r->input.n && j < 8; i++) {
                int k;
                double strength = 0;
                for (k = 0; k < t->n; k++) {
                    double z = relation(m, &r->input.t[i], &t->t[k]);
                    if (z > strength) strength = z;
                }
                if (strength > .30 && !filler(r->input.t[i].word)) {
                    if (j++) sink_char(sink, ',');
                    sink_string(sink, r->input.t[i].word);
                }
            }
        }
        sink_puts(sink, "],\"arguments\":[");
        j = 0;
        if (r->winner >= 0 && r->winner < m->nt) for (i = 0; i < m->tool[r->winner].np; i++) if (r->arg[i].present) {
            Capture *c = &r->arg[i];
            if (j++) sink_char(sink, ',');
            sink_puts(sink, "{\"name\":");
            sink_string(sink, m->tool[r->winner].p[i].name);
            sink_puts(sink, ",\"value\":");
            sink_puts(sink, c->raw);
            sink_puts(sink, ",\"source\":");
            sink_string(sink, c->source);
            sink_printf(sink, ",\"span\":[%d,%d],\"evidence\":%.6f,\"alternative\":%.6f,\"candidates\":%d}",
                c->start, c->end, c->evidence, c->alternative, c->candidates);
        }
        sink_printf(sink, "],\"margin\":%.6f}", r->margin);
    }
    sink_puts(sink, "}\n");
    (void) text;
}

#ifndef WOLFE_NO_MAIN
static void output(Model *m, const char *text, Result *r, int mode, int reasoning) {
    Sink sink = {stdout, NULL, 0, 0};
    serialize(m, text, r, mode, reasoning, &sink);
    fflush(stdout);
}

static void output_error(const char *message) {
    fputs("{\"calls\":[],\"status\":\"error\",\"error\":", stdout);
    emit_string(stdout, message);
    fputs("}\n", stdout);
    fflush(stdout);
}

#endif /* WOLFE_NO_MAIN */

/* Explicit corrections are bounded declarative examples. No inference result
 * is recorded here; only a caller-supplied record can enter this buffer. */
static int correction_record(Model *m, JP *j, int node, int append) {
    int key, ti, text_id, tool_node, args, p, seen[NP] = {0};
    char text[NS], name[96];
    Tokens tokens;
    if (node < 0 || j->t[node].type != JOBJ) return fail("correction must be an object");
    for (key = j->t[node].child; key >= 0; key = j->t[j->t[key].next].next) {
        char field[64];
        if (!jtext(j, key, field, sizeof field) || (strcmp(field, "text") && strcmp(field, "tool") && strcmp(field, "arguments")))
            return fail("unknown correction field");
    }
    text_id = get(j, node, "text");
    tool_node = get(j, node, "tool");
    args = get(j, node, "arguments");
    if (text_id < 0 || j->t[text_id].type != JSTR || !jtext(j, text_id, text, sizeof text)
        || !text[0] || !tokenize(text, &tokens) || !tokens.n) return fail("correction requires nonempty text under 2048 bytes");
    if (tool_node < 0) return fail("correction requires tool (name or null)");
    if (j->t[tool_node].type == JNULL) ti = m->nt;
    else if (j->t[tool_node].type != JSTR || !jtext(j, tool_node, name, sizeof name) || (ti = tool_id(m, name)) < 0)
        return fail("correction names unknown tool");
    if (args < 0 && ti != m->nt) return fail("correction requires complete arguments");
    if (args >= 0 && j->t[args].type != JOBJ) return fail("correction arguments must be an object");
    for (key = args < 0 ? -1 : j->t[args].child; key >= 0; key = j->t[j->t[key].next].next) {
        char prop[64], raw[NS];
        int value = j->t[key].next;
        if (ti == m->nt || !jtext(j, key, prop, sizeof prop) || (p = prop_id(&m->tool[ti], prop)) < 0)
            return fail("correction argument names unknown property");
        if (!jraw(j, value, raw, sizeof raw) || !validate_scalar(&m->tool[ti].p[p], raw))
            return fail("correction argument violates schema");
        seen[p] = 1;
    }
    if (ti != m->nt) for (p = 0; p < m->tool[ti].np; p++) if (m->tool[ti].p[p].required && !seen[p])
        return fail("correction requires all required arguments");
    if (!append) return 1;
    /* A correction supersedes contradictory construction evidence with exactly
     * the same text, through corpus rebuilding rather than a routing cache. */
    for (p = 0; p < m->ne;) {
        if (!strcmp(m->ex[p].text, text)) {
            int a;
            for (a = 0; a < NP; a++) free(m->ex[p].args[a]);
            memmove(&m->ex[p], &m->ex[p + 1], (size_t)(m->ne - p - 1) * sizeof *m->ex);
            m->ne--;
        } else p++;
    }
    if (!add_example(m, text, ti, 0)) return 0;
    m->ex[m->ne - 1].corrected = 1;
    /* A correction is literal user input, not a template declaration. Only
     * derive_slots may subsequently turn observed argument values into slots. */
    for (p = 0; p < m->ex[m->ne - 1].tokens.n; p++) m->ex[m->ne - 1].tokens.t[p].slot = 0;
    for (key = args < 0 ? -1 : j->t[args].child; key >= 0; key = j->t[j->t[key].next].next) {
        char prop[64];
        jtext(j, key, prop, sizeof prop);
        p = prop_id(&m->tool[ti], prop);
        m->ex[m->ne - 1].args[p] = calloc(NS, 1);
        if (!m->ex[m->ne - 1].args[p]) return fail("out of memory");
        jraw(j, j->t[key].next, m->ex[m->ne - 1].args[p], NS);
        m->ex[m->ne - 1].present[p] = 1;
    }
    return 1;
}

static int store_correction(Model *m, const char *record, int replace) {
    JP j;
    int at, i;
    char text[NS];
    char *saved;
    size_t n = strlen(record);
    if (n >= CORRECTION_BYTES) return fail("correction record exceeds 65535 bytes");
    if (!json(&j, record)) return 0;
    if (!correction_record(m, &j, 0, 0)) { free(j.t); return 0; }
    jtext(&j, get(&j, 0, "text"), text, sizeof text);
    free(j.t);
    at = m->ncorrections;
    for (i = 0; i < m->ncorrections; i++) {
        char previous[NS];
        if (!json(&j, m->corrections[i])) return 0;
        jtext(&j, get(&j, 0, "text"), previous, sizeof previous);
        free(j.t);
        if (!strcmp(previous, text)) { at = i; break; }
    }
    if (at < m->ncorrections && !replace) return fail("duplicate correction text in state");
    if (m->ncorrections == NCORRECTIONS && at == m->ncorrections && !replace)
        return fail("state exceeds 32 corrections");
    saved = malloc(n + 1);
    if (!saved) return fail("out of memory");
    memcpy(saved, record, n + 1);
    if (at < m->ncorrections) {
        free(m->corrections[at]);
        m->corrections[at] = saved;
    } else {
        if (at == NCORRECTIONS) {
            free(m->corrections[0]);
            memmove(m->corrections, m->corrections + 1, (NCORRECTIONS - 1) * sizeof *m->corrections);
            at--;
            m->ncorrections--;
        }
        m->corrections[at] = saved;
        m->ncorrections++;
    }
    return 1;
}

static int append_corrections(Model *m) {
    int i;
    for (i = 0; i < m->ncorrections; i++) {
        JP j;
        int ok;
        if (!json(&j, m->corrections[i])) return 0;
        ok = correction_record(m, &j, 0, 1);
        free(j.t);
        if (!ok) return 0;
    }
    return 1;
}

static int load_state(Model *m, const char *path) {
    char *s;
    JP j;
    size_t n;
    char identity[32], expected[32];
    int a, x, version;
    if (!path) return 1;
    {
        FILE *f = fopen(path, "rb");
        if (!f) {
            if (errno == ENOENT) return 1;
            return fail("cannot open state");
        }
        fclose(f);
    }
    if (!(s = read_file(path, &n))) return 0;
    if (!json(&j, s)) {
        free(s);
        return 0;
    }
    if (jnumber(&j, get(&j, 0, "version"), 0) != 1 && jnumber(&j, get(&j, 0, "version"), 0) != 2) {
        free(j.t); free(s); return fail("unsupported state version");
    }
    version = (int)jnumber(&j, get(&j, 0, "version"), 0);
    snprintf(expected, sizeof expected, "%016llx", (unsigned long long) m->identity);
    if (!jtext(&j, get(&j, 0, "identity"), identity, sizeof identity) || strcmp(expected, identity)) {
        free(j.t);
        free(s);
        return fail("state identity does not match tools and examples; delete state to reset");
    }
    a = get(&j, 0, "tools");
    if (a < 0 || j.t[a].type != JOBJ) {
        free(j.t);
        free(s);
        return fail("invalid state tools");
    }
    for (x = j.t[a].child; x >= 0;) {
        char name[96];
        int v = j.t[x].next, ti;
        double accepted, rejected;
        if (!jtext(&j, x, name, sizeof name) || (ti = tool_id(m, name)) < 0) {
            free(j.t);
            free(s);
            return fail("state names unknown tool");
        }
        accepted = jnumber(&j, get(&j, v, "accepted"), NAN);
        rejected = jnumber(&j, get(&j, v, "rejected"), NAN);
        if (!isfinite(accepted) || !isfinite(rejected) || accepted < 0 || rejected < 0 || accepted > 65535
            || rejected > 65535 || floor(accepted) != accepted || floor(rejected) != rejected) {
            free(j.t);
            free(s);
            return fail("invalid bounded state counters");
        }
        m->accepted[ti] = (unsigned) accepted;
        m->rejected[ti] = (unsigned) rejected;
        x = j.t[v].next;
    }
    a = get(&j, 0, "corrections");
    if ((version == 2 && (a < 0 || j.t[a].type != JARR))
        || (version == 1 && a >= 0)) {
        free(j.t); free(s); return fail("invalid state corrections");
    }
    if (a >= 0) for (x = j.t[a].child; x >= 0; x = j.t[x].next) {
        size_t length = (size_t)(j.t[x].end - j.t[x].start);
        char *record;
        int ok;
        if (length >= CORRECTION_BYTES) { free(j.t); free(s); return fail("correction record exceeds 65535 bytes"); }
        record = malloc(length + 1);
        if (!record) { free(j.t); free(s); return fail("out of memory"); }
        memcpy(record, s + j.t[x].start, length);
        record[length] = 0;
        ok = store_correction(m, record, 0);
        free(record);
        if (!ok) { free(j.t); free(s); return 0; }
    }
    free(j.t);
    free(s);
    return 1;
}

static int save_state(Model *m, const char *path) {
    char tmp[4096];
    FILE *f;
    int i;
    if (strlen(path) + 5 >= sizeof tmp) return fail("state path too long");
    snprintf(tmp, sizeof tmp, "%s.tmp", path);
    f = fopen(tmp, "wb");
    if (!f) return fail("cannot create temporary state file");
    fprintf(f, "{\"version\":2,\"identity\":\"%016llx\",\"tools\":{", (unsigned long long) m->identity);
    for (i = 0; i < m->nt; i++) {
        if (i) fputc(',', f);
        emit_string(f, m->tool[i].name);
        fprintf(f, ":{\"accepted\":%u,\"rejected\":%u}", m->accepted[i], m->rejected[i]);
    }
    fputs("},\"corrections\":[", f);
    for (i = 0; i < m->ncorrections; i++) {
        if (i) fputc(',', f);
        fputs(m->corrections[i], f);
    }
    fputs("]}\n", f);
    {
        int bad = ferror(f);
        if (fclose(f)) bad = 1;
        if (bad) {
        remove(tmp);
        return fail("state write failed");
        }
    }
    if (rename(tmp, path)) {
        remove(tmp);
        return fail("atomic state replacement failed");
    }
    return 1;
}

#ifndef WOLFE_NO_MAIN
static int feedback(Model *m, Result *r, const char *kind, const char *path) {
    unsigned *a, *b;
    if (!kind) return 1;
    if (!path) return fail("feedback requires --state");
    if (r->status != CALL) return fail("feedback requires a complete call");
    a = &m->accepted[r->winner];
    b = &m->rejected[r->winner];
    if (*a + *b >= 65535) {
        * a /= 2;
        *b /= 2;
    }
    if (!strcmp(kind, "accepted"))(*a)++;
    else(*b)++;
    return save_state(m, path);
}

static size_t model_bytes(Model *m) {
    size_t n = sizeof * m + (size_t) m->ne * sizeof * m->ex + (size_t) m->nv * sizeof * m->word;
    int i, p, v;
    for (i = 0; i < m->nt; i++) {
        n += (size_t) m->tool[i].np * sizeof (Property);
        for (p = 0; p < m->tool[i].np; p++) {
            Property *pr = &m->tool[i].p[p];
            n += NVAL * (sizeof (Enum) + sizeof (Unit));
            for (v = 0; v < pr->nv; v++) n += (size_t) pr->values[v].n * 128;
        }
    }
    for (i = 0; i < m->ne; i++) for (p = 0; p < NP; p++) if (m->ex[i].args[p]) n += NS;
    for (i = 0; i < m->ncorrections; i++) n += strlen(m->corrections[i]) + 1;
    return n;
}

#endif /* WOLFE_NO_MAIN */

static void destroy(Model *m) {
    int i, p, v, a;
    if (!m) return;
    for (i = 0; i < NT; i++) {
        Tool *t = &m->tool[i];
        for (p = 0; p < t->allocated; p++) {
            Property *pr = &t->p[p];
            if (pr->values) for (v = 0; v < NVAL; v++) for (a = 0; a < NVAL; a++) free(pr->values[v].aliases[a]);
            free(pr->values);
            free(pr->units);
        }
        free(t->p);
    }
    for (i = 0; i < m->ne; i++) for (p = 0; p < NP; p++) free(m->ex[i].args[p]);
    for (i = 0; i < m->ncorrections; i++) free(m->corrections[i]);
    free(m->ex);
    free(m->word);
    free(m);
}

/* Public embedding API. Define WOLFE_NO_MAIN before including this file, or
 * compile with -DWOLFE_NO_MAIN and declare these signatures in your host.
 * Models can be reused and independent models may be interleaved. Calls must
 * be externally serialized: the bounded parser currently shares error scratch.
 * A call performs no file I/O. Load/correct are explicit file operations.
 * Mode and reasoning are orthogonal; explanations do not alter inference. */
typedef struct Wolfe Wolfe;
enum { WOLFE_OK = 0, WOLFE_ERROR = 1, WOLFE_BUFFER_TOO_SMALL = 2 };
enum { WOLFE_NEURAL = 0, WOLFE_FIELD = 1, WOLFE_KEYWORD = 2 };
enum { WOLFE_REASONING_OFF = 0, WOLFE_REASONING_FULL = 1, WOLFE_REASONING_COMPACT = 2 };
Wolfe *wolfe_load(const char *tools, const char *examples, const char *state,
    char *error, size_t error_capacity);
int wolfe_call(Wolfe *wolf, const char *text, int mode, int reasoning,
    char *output, size_t output_capacity, size_t *required_bytes);
int wolfe_correct(Wolfe *wolf, const char *correction_json);
const char *wolfe_error(const Wolfe *wolf);
void wolfe_free(Wolfe *wolf);

struct Wolfe {
    Model *model;
    Result *result;
    char *tools, *examples, *state;
    char error[256];
};

static char *duplicate_string(const char *s) {
    char *d;
    size_t n;
    if (!s) return NULL;
    n = strlen(s) + 1;
    d = malloc(n);
    if (d) memcpy(d, s, n);
    return d;
}

static Model *prepare_model(const char *tools, const char *examples, const char *state, const char *correction) {
    Model *m = calloc(1, sizeof *m);
    if (!m) { fail("out of memory"); return NULL; }
    m->identity = UINT64_C(1469598103934665603);
    if (!load_tools(m, tools) || !load_examples(m, examples) || !load_state(m, state)
        || (correction && !store_correction(m, correction, 1))
        || !append_corrections(m) || !build_field(m)) {
        destroy(m);
        return NULL;
    }
    return m;
}

void wolfe_free(Wolfe *wolf) {
    if (!wolf) return;
    destroy(wolf->model);
    free(wolf->result);
    free(wolf->tools);
    free(wolf->examples);
    free(wolf->state);
    free(wolf);
}

Wolfe *wolfe_load(const char *tools, const char *examples, const char *state,
    char *error, size_t error_capacity) {
    Wolfe *wolf;
    if (error && error_capacity) error[0] = 0;
    if (!tools || !examples) {
        if (error) copy(error, error_capacity, "tools and examples paths are required");
        return NULL;
    }
    wolf = calloc(1, sizeof *wolf);
    if (!wolf) { if (error) copy(error, error_capacity, "out of memory"); return NULL; }
    wolf->tools = duplicate_string(tools);
    wolf->examples = duplicate_string(examples);
    wolf->state = duplicate_string(state);
    wolf->result = calloc(1, sizeof *wolf->result);
    if (!wolf->tools || !wolf->examples || (state && !wolf->state) || !wolf->result) {
        if (error) copy(error, error_capacity, "out of memory");
        wolfe_free(wolf);
        return NULL;
    }
    wolf->model = prepare_model(tools, examples, state, NULL);
    if (!wolf->model) {
        if (error) copy(error, error_capacity, error_message);
        wolfe_free(wolf);
        return NULL;
    }
    return wolf;
}

const char *wolfe_error(const Wolfe *wolf) {
    return wolf ? wolf->error : "invalid Wolfe context";
}

int wolfe_call(Wolfe *wolf, const char *text, int mode, int reasoning,
    char *output, size_t output_capacity, size_t *required_bytes) {
    Sink sink = {NULL, output, output_capacity, 0};
    if (output && output_capacity) output[0] = 0;
    if (required_bytes) *required_bytes = 0;
    if (!wolf) return WOLFE_ERROR;
    wolf->error[0] = 0;
    if (!text || mode < 0 || mode > 2 || reasoning < 0 || reasoning > 2 || (!output && output_capacity)) {
        copy(wolf->error, sizeof wolf->error, "invalid call arguments");
        return WOLFE_ERROR;
    }
    if (!infer(wolf->model, text, wolf->result, mode)) {
        copy(wolf->error, sizeof wolf->error, error_message);
        return WOLFE_ERROR;
    }
    serialize(wolf->model, text, wolf->result, mode, reasoning, &sink);
    if (required_bytes) *required_bytes = sink.used + 1;
    if (sink.used >= output_capacity) {
        if (output && output_capacity) output[0] = 0;
        copy(wolf->error, sizeof wolf->error, "output buffer too small");
        return WOLFE_BUFFER_TOO_SMALL;
    }
    output[sink.used] = 0;
    return WOLFE_OK;
}

int wolfe_correct(Wolfe *wolf, const char *correction_json) {
    Model *candidate;
    if (!wolf) return WOLFE_ERROR;
    wolf->error[0] = 0;
    if (!wolf->state || !correction_json) {
        copy(wolf->error, sizeof wolf->error, "correction requires a state path and JSON record");
        return WOLFE_ERROR;
    }
    candidate = prepare_model(wolf->tools, wolf->examples, wolf->state, correction_json);
    if (!candidate) {
        copy(wolf->error, sizeof wolf->error, error_message);
        return WOLFE_ERROR;
    }
    if (candidate->identity != wolf->model->identity) {
        destroy(candidate);
        copy(wolf->error, sizeof wolf->error, "source identity changed; reload before correcting");
        return WOLFE_ERROR;
    }
    if (!save_state(candidate, wolf->state)) {
        destroy(candidate);
        copy(wolf->error, sizeof wolf->error, error_message);
        return WOLFE_ERROR;
    }
    destroy(wolf->model);
    wolf->model = candidate;
    return WOLFE_OK;
}

#ifndef WOLFE_NO_MAIN
static void usage(void) {
    puts("WOLFE — Weightless Ontological Language Function Engine\nUsage: wolfe [options] [query]\n  --tools PATH       JSON tool declarations (default tools.json)\n  --examples PATH    JSONL examples (default examples.jsonl)\n  --reasoning        expose field evidence and argument provenance\n  --reasoning-compact  short evidence and argument explanation\n  --mode MODE        neural (default), field, or keyword\n  --batch            read {\"text\":\"...\"} JSONL from stdin\n  --state PATH       opt-in counters and up to 32 explicit corrections\n  --correct PATH     save one JSON correction, rebuild, and exit\n  --feedback KIND    accepted or rejected, for this complete call\n  --stats            resource/field statistics on stderr\nNo tools are executed. A request emits at most one validated call.");
}

int main(int argc, char * *argv) {
    const char *tools = "tools.json", *examples = "examples.jsonl", *state = NULL, *fb = NULL, *correction_path = NULL;
    char text[NS] = { 0};
    int batch = 0, reasoning = 0, stats = 0, mode = 0, i, exitcode = 0;
    Model *m;
    Result *r;
    clock_t begun = clock();
    for (i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--help") || !strcmp(argv[i], "-h")) {
            usage();
            return 0;
        } else if (!strcmp(argv[i], "--reasoning") || !strcmp(argv[i], "--explain")) reasoning = 1;
        else if (!strcmp(argv[i], "--reasoning-compact")) reasoning = 2;
        else if (!strcmp(argv[i], "--batch")) batch = 1;
        else if (!strcmp(argv[i], "--stats")) stats = 1;
        else if (!strcmp(argv[i], "--tools") || !strcmp(argv[i], "--examples") || !strcmp(argv[i], "--state")
            || !strcmp(argv[i], "--feedback") || !strcmp(argv[i], "--correct") || !strcmp(argv[i], "--mode")) {
            const char *key = argv[i];
            if (++i >= argc) {
                fprintf(stderr, "missing option value\n");
                return 2;
            }
            if (!strcmp(key, "--tools")) tools = argv[i];
            else if (!strcmp(key, "--examples")) examples = argv[i];
            else if (!strcmp(key, "--state")) state = argv[i];
            else if (!strcmp(key, "--feedback")) fb = argv[i];
            else if (!strcmp(key, "--correct")) correction_path = argv[i];
            else if (!strcmp(argv[i], "neural")) mode = 0;
            else if (!strcmp(argv[i], "field")) mode = 1;
            else if (!strcmp(argv[i], "keyword")) mode = 2;
            else {
                fprintf(stderr, "unknown mode\n");
                return 2;
            }
        } else if (argv[i][0] == '-' && argv[i][1] == '-') {
            fprintf(stderr, "unknown option: %s\n", argv[i]);
            return 2;
        } else {
            size_t n = strlen(text), a = strlen(argv[i]);
            if (n + a + 2 >= sizeof text) {
                fprintf(stderr, "query too long\n");
                return 2;
            }
            if (n) text[n++] = ' ';
            memcpy(text + n, argv[i], a + 1);
        }
    }
    if (fb && strcmp(fb, "accepted") && strcmp(fb, "rejected")) {
        fprintf(stderr, "feedback must be accepted or rejected\n");
        return 2;
    }
    if (fb && !state) {
        fprintf(stderr, "feedback requires --state\n");
        return 2;
    }
    if (batch && text[0]) {
        fprintf(stderr, "--batch cannot take a positional query\n");
        return 2;
    }
    if (batch && fb) {
        fprintf(stderr, "batch feedback must not implicitly mark every request; use individual requests\n");
        return 2;
    }
    if (correction_path) {
        char *record;
        size_t length;
        if (!state || batch || fb || text[0]) {
            fprintf(stderr, "--correct requires --state and cannot combine with a query, batch, or feedback\n");
            return 2;
        }
        record = read_file(correction_path, &length);
        if (!record) { fprintf(stderr, "WOLFE: %s\n", error_message); return 2; }
        m = prepare_model(tools, examples, state, record);
        free(record);
        if (!m) { fprintf(stderr, "WOLFE: %s\n", error_message); return 2; }
        if (!save_state(m, state)) {
            fprintf(stderr, "WOLFE: %s\n", error_message); destroy(m); return 2;
        }
        printf("{\"status\":\"corrected\",\"corrections\":%d}\n", m->ncorrections);
        destroy(m);
        return 0;
    }
    m = prepare_model(tools, examples, state, NULL);
    r = calloc(1, sizeof * r);
    if (!m || !r) {
        fprintf(stderr, "WOLFE: %s\n", m ? "out of memory" : error_message);
        destroy(m);
        free(r);
        return 2;
    }
    if (stats) fprintf(stderr, "{\"tools\":%d,\"examples\":%d,\"vocabulary\":%d,\"field_dimensions\":%d,\"iterations\":%d,\"model_capacity_bytes\":%lu,\"startup_cpu_ms\":%.3f,\"identity\":\"%016llx\",\"pretrained_parameters\":0}\n",
        m->nt, m->ne, m->nv, ND, ITERATIONS, (unsigned long) model_bytes(m), 1000. * (clock() - begun) / CLOCKS_PER_SEC,
        (unsigned long long) m->identity);
    if (batch) {
        char line[16384];
        while (fgets(line, sizeof line, stdin)) {
            JP j;
            size_t n = strlen(line);
            if (n == sizeof line - 1 && line[n - 1] != '\n') {
                int c;
                while ((c = getchar()) != EOF && c != '\n') {
                }
                output_error("batch line exceeds 16382 bytes");
                exitcode = 1;
                continue;
            }
            if (!json(&j, line)) {
                output_error(error_message);
                exitcode = 1;
                continue;
            }
            if (get(&j, 0, "text") < 0 || j.t[get(&j, 0, "text")].type != JSTR || !jtext(&j, get(&j,
                0, "text"), text, sizeof text)) {
                free(j.t);
                output_error("batch item requires text under 2048 bytes");
                exitcode = 1;
                continue;
            }
            free(j.t);
            if (!infer(m, text, r, mode)) {
                output_error(error_message);
                exitcode = 1;
                continue;
            }
            output(m, text, r, mode, reasoning);
        }
        if (ferror(stdin)) {
            fprintf(stderr, "stdin read failed\n");
            exitcode = 2;
        }
    } else {
        if (!text[0]) {
            if (!fgets(text, sizeof text, stdin)) {
                fprintf(stderr, "provide a query or --batch\n");
                destroy(m);
                free(r);
                return 2;
            }
            if (strlen(text) == sizeof text - 1 && text[sizeof text - 2] != '\n') {
                fprintf(stderr, "query too long\n");
                destroy(m);
                free(r);
                return 2;
            }
        }
        if (!infer(m, text, r, mode)) {
            output_error(error_message);
            exitcode = 1;
        } else if (!feedback(m, r, fb, state)) {
            output_error(error_message);
            exitcode = 1;
        } else output(m, text, r, mode, reasoning);
    }
    free(r);
    destroy(m);
    return exitcode;
}

#endif /* WOLFE_NO_MAIN */
