#include <openssl/evp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static unsigned char key[32] = {0};
static unsigned char iv[16] = {0};

int main(int argc, char *argv[])
{
    if (argc != 3)
    {
        printf("Usage: %s <data_size_bytes> <iterations>\n", argv[0]);
        return 1;
    }

    size_t data_size = strtoull(argv[1], NULL, 10);
    int iterations = atoi(argv[2]);

    unsigned char *plaintext = malloc(data_size);
    unsigned char *ciphertext = malloc(data_size + 32);

    if (!plaintext || !ciphertext)
    {
        printf("Memory allocation failed\n");
        return 1;
    }

    memset(plaintext, 'A', data_size);

    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();

    struct timespec start, end;

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < iterations; i++)
    {
        int len;
        int ciphertext_len = 0;

        EVP_EncryptInit_ex(
            ctx,
            EVP_aes_256_cbc(),
            NULL,
            key,
            iv
        );

        EVP_EncryptUpdate(
            ctx,
            ciphertext,
            &len,
            plaintext,
            data_size
        );

        ciphertext_len += len;

        EVP_EncryptFinal_ex(
            ctx,
            ciphertext + ciphertext_len,
            &len
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    long long elapsed_ns =
        (end.tv_sec - start.tv_sec) * 1000000000LL +
        (end.tv_nsec - start.tv_nsec);

    double total_mb =
        ((double)data_size * iterations) /
        (1024.0 * 1024.0);

    double seconds =
        elapsed_ns / 1000000000.0;

    double throughput =
        total_mb / seconds;

    printf("\n=== AES-256-CBC Benchmark ===\n");
    printf("Data Size      : %zu bytes\n", data_size);
    printf("Iterations     : %d\n", iterations);
    printf("Total Data     : %.2f MB\n", total_mb);
    printf("Execution Time : %lld ns\n", elapsed_ns);
    printf("Throughput     : %.2f MB/s\n", throughput);

    EVP_CIPHER_CTX_free(ctx);
    free(plaintext);
    free(ciphertext);

    return 0;
}
