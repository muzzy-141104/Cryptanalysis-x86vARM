#include "pin.H"
#include <fstream>

UINT64 instruction_count = 0;
UINT64 memory_reads = 0;
UINT64 memory_writes = 0;
UINT64 aesenc_count = 0;
UINT64 aesdec_count = 0;
UINT64 aesenclast_count = 0;
UINT64 aesdeclast_count = 0;
UINT64 sha256rnds2_count = 0;
UINT64 sha256msg1_count = 0;
UINT64 sha256msg2_count = 0;

KNOB<std::string> KnobOutputFile(
    KNOB_MODE_WRITEONCE,
    "pintool",
    "o",
    "results/x86/profile.csv",
    "output csv file"
);

VOID CountInstruction()
{
    instruction_count++;
}

VOID CountMemoryRead()
{
    memory_reads++;
}

VOID CountMemoryWrite()
{
    memory_writes++;
}

VOID CountAesEnc()
{
    aesenc_count++;
}

VOID CountAesDec()
{
    aesdec_count++;
}

VOID CountAesEncLast()
{
    aesenclast_count++;
}

VOID CountAesDecLast()
{
    aesdeclast_count++;
}

VOID CountSha256Rnds2()
{
    sha256rnds2_count++;
}

VOID CountSha256Msg1()
{
    sha256msg1_count++;
}

VOID CountSha256Msg2()
{
    sha256msg2_count++;
}

VOID Instruction(INS ins, VOID *v)
{
    xed_iclass_enum_t opcode = (xed_iclass_enum_t)INS_Opcode(ins);

    INS_InsertCall(
        ins,
        IPOINT_BEFORE,
        (AFUNPTR)CountInstruction,
        IARG_END
    );

    if (INS_IsMemoryRead(ins))
    {
        INS_InsertCall(
            ins,
            IPOINT_BEFORE,
            (AFUNPTR)CountMemoryRead,
            IARG_END
        );
    }

    if (INS_HasMemoryRead2(ins))
    {
        INS_InsertCall(
            ins,
            IPOINT_BEFORE,
            (AFUNPTR)CountMemoryRead,
            IARG_END
        );
    }

    if (INS_IsMemoryWrite(ins))
    {
        INS_InsertCall(
            ins,
            IPOINT_BEFORE,
            (AFUNPTR)CountMemoryWrite,
            IARG_END
        );
    }

    switch (opcode)
    {
    case XED_ICLASS_AESENC:
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)CountAesEnc, IARG_END);
        break;
    case XED_ICLASS_AESDEC:
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)CountAesDec, IARG_END);
        break;
    case XED_ICLASS_AESENCLAST:
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)CountAesEncLast, IARG_END);
        break;
    case XED_ICLASS_AESDECLAST:
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)CountAesDecLast, IARG_END);
        break;
    case XED_ICLASS_SHA256RNDS2:
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)CountSha256Rnds2, IARG_END);
        break;
    case XED_ICLASS_SHA256MSG1:
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)CountSha256Msg1, IARG_END);
        break;
    case XED_ICLASS_SHA256MSG2:
        INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)CountSha256Msg2, IARG_END);
        break;
    default:
        break;
    }
}

VOID Fini(INT32 code, VOID *v)
{
    std::ofstream out(KnobOutputFile.Value().c_str());

    out << "metric,value" << std::endl;
    out << "instruction_count," << instruction_count << std::endl;
    out << "memory_reads," << memory_reads << std::endl;
    out << "memory_writes," << memory_writes << std::endl;
    out << "aesenc_count," << aesenc_count << std::endl;
    out << "aesdec_count," << aesdec_count << std::endl;
    out << "aesenclast_count," << aesenclast_count << std::endl;
    out << "aesdeclast_count," << aesdeclast_count << std::endl;
    out << "sha256rnds2_count," << sha256rnds2_count << std::endl;
    out << "sha256msg1_count," << sha256msg1_count << std::endl;
    out << "sha256msg2_count," << sha256msg2_count << std::endl;

    out.close();
}

int main(int argc, char *argv[])
{
    if (PIN_Init(argc, argv))
        return 1;

    INS_AddInstrumentFunction(
        Instruction,
        0
    );

    PIN_AddFiniFunction(
        Fini,
        0
    );

    PIN_StartProgram();

    return 0;
}
