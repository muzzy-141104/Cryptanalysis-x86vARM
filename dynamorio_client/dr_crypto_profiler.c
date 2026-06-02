#include "dr_api.h"
#include "drmgr.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint64_t instruction_count;
static uint64_t memory_reads;
static uint64_t memory_writes;

static void *counter_lock;
static const char *output_path = "results/arm/profile.csv";

/*
 * Clean-call target used by BB-level aggregation.
 * We update global counters once per basic block execution, not once per
 * instruction, to reduce overhead and avoid instrumentation-amplified counts.
 */
static void count_metrics(int instructions, int reads, int writes)
{
    dr_mutex_lock(counter_lock);
    instruction_count += (uint64_t)instructions;
    memory_reads += (uint64_t)reads;
    memory_writes += (uint64_t)writes;
    dr_mutex_unlock(counter_lock);
}

static dr_emit_flags_t event_app_instruction(void *drcontext, void *tag, instrlist_t *bb,
                                             instr_t *instr, bool for_trace,
                                             bool translating, void *user_data)
{
    instr_t *cur;
    int instructions = 0;
    int reads = 0;
    int writes = 0;

    (void)tag;
    (void)instr;
    (void)for_trace;
    (void)translating;
    (void)user_data;

    /*
     * drmgr invokes this callback for each app instruction in the block.
     * To perform BB aggregation exactly once, only act on the first app instr.
     */
    if (instr != instrlist_first_app(bb))
        return DR_EMIT_DEFAULT;

    /*
     * Instruction counting logic:
     *   count each application instruction in the current basic block once.
     * Memory counting logic:
     *   count 1 read if instr_reads_memory() is true,
     *   count 1 write if instr_writes_memory() is true.
     * This is close to Pin INS_IsMemoryRead/INS_IsMemoryWrite semantics.
     */
    for (cur = instrlist_first_app(bb); cur != NULL; cur = instr_get_next_app(cur)) {
        instructions++;
        if (instr_reads_memory(cur))
            reads++;
        if (instr_writes_memory(cur))
            writes++;
    }

    /* Insert one clean call per BB execution with pre-aggregated counts. */
    if (instructions > 0) {
        dr_insert_clean_call(drcontext, bb, instrlist_first_app(bb), (void *)count_metrics, false, 3,
                             OPND_CREATE_INT32(instructions),
                             OPND_CREATE_INT32(reads),
                             OPND_CREATE_INT32(writes));
    }

    return DR_EMIT_DEFAULT;
}

static void event_exit(void)
{
    FILE *out;

    out = fopen(output_path, "w");
    if (out == NULL) {
        dr_fprintf(STDERR, "dr_crypto_profiler: failed to open output file: %s\n", output_path);
    } else {
        fprintf(out, "metric,value\n");
        fprintf(out, "instruction_count,%llu\n", (unsigned long long)instruction_count);
        fprintf(out, "memory_reads,%llu\n", (unsigned long long)memory_reads);
        fprintf(out, "memory_writes,%llu\n", (unsigned long long)memory_writes);
        fclose(out);
    }

    drmgr_exit();
    dr_mutex_destroy(counter_lock);
}

DR_EXPORT void dr_client_main(client_id_t id, int argc, const char *argv[])
{
    (void)id;

    dr_set_client_name("DynamoRIO Crypto Profiler", "https://dynamorio.org/");

    if (argc >= 2 && argv[1] != NULL && strlen(argv[1]) > 0) {
        output_path = argv[1];
    }

    if (!drmgr_init()) {
        dr_fprintf(STDERR, "dr_crypto_profiler: drmgr_init failed\n");
        dr_abort();
        return;
    }

    counter_lock = dr_mutex_create();
    if (counter_lock == NULL) {
        dr_fprintf(STDERR, "dr_crypto_profiler: mutex creation failed\n");
        drmgr_exit();
        dr_abort();
        return;
    }

    dr_register_exit_event(event_exit);
    if (!drmgr_register_bb_instrumentation_event(NULL, event_app_instruction, NULL)) {
        dr_fprintf(STDERR, "dr_crypto_profiler: bb instrumentation registration failed\n");
        dr_mutex_destroy(counter_lock);
        drmgr_exit();
        dr_abort();
        return;
    }
}
