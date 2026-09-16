/* This host includes the entire one-file organism, suppressing only its CLI. */
#define WOLFE_NO_MAIN
#include "../wolfe.c"

#define CHECK(expr) do { if (!(expr)) { fprintf(stderr, "line %d: %s\n", __LINE__, #expr); return 1; } } while (0)

int main(int argc, char **argv) {
    Wolfe *a, *b;
    char error[256], first[65536], second[65536], state[4096], short_buffer[8];
    size_t need = 0, need2 = 0;
    CHECK(argc == 3);
    snprintf(state, sizeof state, "%s/memory.json", argv[2]);
    a = wolfe_load("tools.json", "examples.jsonl", state, error, sizeof error);
    CHECK(a != NULL && !error[0]);
    CHECK(wolfe_call(a, "play Rammstein", WOLFE_NEURAL, WOLFE_REASONING_OFF,
        first, sizeof first, &need) == WOLFE_OK);
    CHECK(strstr(first, "play_music") && strstr(first, "Rammstein"));
    if (!strcmp(argv[1], "reuse")) {
        int i;
        for (i = 0; i < 20; i++) {
            CHECK(wolfe_call(a, "pause music", WOLFE_NEURAL, WOLFE_REASONING_COMPACT,
                second, sizeof second, NULL) == WOLFE_OK);
            CHECK(strstr(second, "pause_music") && strstr(second, "reasoning"));
            CHECK(wolfe_call(a, "play Rammstein", WOLFE_NEURAL, WOLFE_REASONING_OFF,
                second, sizeof second, &need2) == WOLFE_OK);
            CHECK(!strcmp(first, second) && need == need2);
        }
    } else if (!strcmp(argv[1], "two-models")) {
        b = wolfe_load("examples/custom_tools.json", "examples/custom_examples.jsonl", NULL, error, sizeof error);
        CHECK(b != NULL);
        CHECK(wolfe_call(b, "move the package to Haifa", WOLFE_NEURAL, WOLFE_REASONING_OFF,
            second, sizeof second, NULL) == WOLFE_OK);
        CHECK(strstr(second, "move_package") && strstr(second, "Haifa"));
        CHECK(wolfe_call(a, "play Rammstein", WOLFE_NEURAL, WOLFE_REASONING_OFF,
            second, sizeof second, NULL) == WOLFE_OK);
        CHECK(!strcmp(first, second));
        wolfe_free(b);
    } else if (!strcmp(argv[1], "capacity")) {
        char *exact;
        CHECK(wolfe_call(a, "play Rammstein", WOLFE_NEURAL, WOLFE_REASONING_OFF,
            short_buffer, sizeof short_buffer, &need2) == WOLFE_BUFFER_TOO_SMALL);
        CHECK(!short_buffer[0] && need2 == strlen(first) + 1 && need == need2);
        CHECK(wolfe_call(a, "play Rammstein", WOLFE_NEURAL, WOLFE_REASONING_OFF,
            NULL, 0, &need2) == WOLFE_BUFFER_TOO_SMALL && need2 == need);
        exact = malloc(need);
        CHECK(exact != NULL);
        CHECK(wolfe_call(a, "play Rammstein", WOLFE_NEURAL, WOLFE_REASONING_OFF,
            exact, need, &need2) == WOLFE_OK);
        CHECK(!strcmp(exact, first) && !wolfe_error(a)[0]);
        CHECK(wolfe_call(a, "play Rammstein", WOLFE_NEURAL, WOLFE_REASONING_OFF,
            exact, need - 1, NULL) == WOLFE_BUFFER_TOO_SMALL && !exact[0]);
        free(exact);
    } else if (!strcmp(argv[1], "invalid")) {
        CHECK(wolfe_call(a, "\xff", 0, 0, second, sizeof second, &need2) == WOLFE_ERROR);
        CHECK(!second[0] && !need2 && wolfe_error(a)[0]);
        CHECK(wolfe_call(a, NULL, 0, 0, second, sizeof second, NULL) == WOLFE_ERROR);
        CHECK(wolfe_call(a, "play Rammstein", 3, 0, second, sizeof second, NULL) == WOLFE_ERROR);
        CHECK(wolfe_call(a, "play Rammstein", 0, 3, second, sizeof second, NULL) == WOLFE_ERROR);
        CHECK(wolfe_call(a, "play Rammstein", 0, 0, second, sizeof second, NULL) == WOLFE_OK);
        CHECK(!strcmp(first, second) && !wolfe_error(a)[0]);
    } else if (!strcmp(argv[1], "correction")) {
        CHECK(wolfe_correct(a, "{\"text\":\"play Rammstein\",\"tool\":\"pause_music\",\"arguments\":{}}") == WOLFE_OK);
        CHECK(wolfe_call(a, "play Rammstein", 0, 0, second, sizeof second, NULL) == WOLFE_OK);
        CHECK(strstr(second, "pause_music"));
        strcpy(first, second);
        CHECK(wolfe_correct(a, "{\"text\":\"play Rammstein\",\"tool\":\"unknown\",\"arguments\":{}}") == WOLFE_ERROR);
        CHECK(wolfe_call(a, "play Rammstein", 0, 0, second, sizeof second, NULL) == WOLFE_OK);
        CHECK(!strcmp(first, second));
    } else if (!strcmp(argv[1], "write-failure")) {
        char blocked[4096];
        snprintf(blocked, sizeof blocked, "%s/missing/memory.json", argv[2]);
        b = wolfe_load("tools.json", "examples.jsonl", blocked, error, sizeof error);
        CHECK(b != NULL);
        CHECK(wolfe_correct(b, "{\"text\":\"play Rammstein\",\"tool\":\"pause_music\",\"arguments\":{}}") == WOLFE_ERROR);
        CHECK(wolfe_call(b, "play Rammstein", 0, 0, second, sizeof second, NULL) == WOLFE_OK);
        CHECK(!strcmp(first, second));
        wolfe_free(b);
    } else if (!strcmp(argv[1], "literal-braces")) {
        int i, found = 0;
        CHECK(wolfe_correct(a, "{\"text\":\"store this note: {text}\",\"tool\":\"create_note\",\"arguments\":{\"text\":\"{text}\"}}") == WOLFE_OK);
        CHECK(wolfe_correct(a, "{\"text\":\"save JSON {\\\"key\\\":1}\",\"tool\":\"create_note\",\"arguments\":{\"text\":\"{\\\"key\\\":1}\"}}") == WOLFE_OK);
        for (i = 0; i < a->model->ne; i++) if (a->model->ex[i].corrected) {
            int k;
            found++;
            for (k = 0; k < a->model->ex[i].tokens.n; k++) CHECK(!a->model->ex[i].tokens.t[k].slot);
        }
        CHECK(found == 2);
    } else if (!strcmp(argv[1], "stale-source")) {
        char original_examples[4096];
        FILE *in = fopen("examples.jsonl", "rb"), *out;
        int ch;
        CHECK(in != NULL);
        snprintf(original_examples, sizeof original_examples, "%s/examples.jsonl", argv[2]);
        out = fopen(original_examples, "wb");
        CHECK(out != NULL);
        while ((ch = fgetc(in)) != EOF) CHECK(fputc(ch, out) != EOF);
        CHECK(!ferror(in));
        CHECK(!fclose(in) && !fclose(out));
        b = wolfe_load("tools.json", original_examples, state, error, sizeof error);
        CHECK(b != NULL);
        out = fopen(original_examples, "ab");
        CHECK(out != NULL && fputc('\n', out) != EOF && !fclose(out));
        CHECK(wolfe_correct(b, "{\"text\":\"play Rammstein\",\"tool\":\"pause_music\",\"arguments\":{}}") == WOLFE_ERROR);
        CHECK(strstr(wolfe_error(b), "identity"));
        CHECK(wolfe_call(b, "play Rammstein", 0, 0, second, sizeof second, NULL) == WOLFE_OK);
        CHECK(!strcmp(first, second));
        wolfe_free(b);
    } else { CHECK(0); }
    wolfe_free(a);
    wolfe_free(NULL);
    return 0;
}
