/* Build from the repository root:
 * cc -O2 -std=c99 -Wall -Wextra -Wpedantic examples/embed.c -lm -o .work/embed
 * .work/embed "play Portishead" "pause music"
 */
#define WOLFE_NO_MAIN
#include "../wolfe.c"

int main(int argc, char **argv) {
    const char *defaults[] = {"play Portishead", "pause music"};
    char error[256];
    size_t capacity = 4096;
    char *output = malloc(capacity);
    Wolfe *wolf;
    int i, exit_code = 0, count = argc > 1 ? argc - 1 : 2;
    if (!output) { fputs("out of memory\n", stderr); return 1; }
    wolf = wolfe_load("tools.json", "examples.jsonl", NULL, error, sizeof error);
    if (!wolf) { fprintf(stderr, "%s\n", error); free(output); return 1; }
    for (i = 0; i < count; i++) {
        const char *text = argc > 1 ? argv[i + 1] : defaults[i];
        size_t required = 0;
        int status = wolfe_call(wolf, text, WOLFE_NEURAL, WOLFE_REASONING_COMPACT,
            output, capacity, &required);
        if (status == WOLFE_BUFFER_TOO_SMALL) {
            char *larger = realloc(output, required);
            if (!larger) { fputs("out of memory\n", stderr); exit_code = 1; break; }
            output = larger;
            capacity = required;
            status = wolfe_call(wolf, text, WOLFE_NEURAL, WOLFE_REASONING_COMPACT,
                output, capacity, &required);
        }
        if (status != WOLFE_OK) {
            fprintf(stderr, "%s\n", wolfe_error(wolf));
            exit_code = 1;
            break;
        }
        /* The host decides what to do with JSON. This example only prints it. */
        fputs(output, stdout);
    }
    wolfe_free(wolf);
    free(output);
    return exit_code;
}
