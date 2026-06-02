#include <openssl/evp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static unsigned char key[32] = {0};
static unsigned char nonce[16] = {0};

int main(int argc, char *argv[])
{
    if (argc != 3)
    {
        printf("Usage: %s <data_size_bytes> <iterations>\n", argv[0]);
        return 1;
    }

    size_t data_size = strtoull(argv[1], NULL, 10);
    int iterations = atoi(argv[2]);

    if (data_size == 0 || iterations <= 0)
    {
        printf("Invalid arguments: data_size_bytes > 0 and iterations > 0 are required\n");
        return 1;
    }

    unsigned char *plaintext = (unsigned char *)malloc(data_size);
    unsigned char *ciphertext = (unsigned char *)malloc(data_size + 16);

    if (!plaintext || !ciphertext)
    {
        printf("Memory allocation failed\n");
        free(plaintext);
        free(ciphertext);
        return 1;
    }

    memset(plaintext, 'A', data_size);

    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx)
    {
        printf("Failed to create cipher context\n");
        free(plaintext);
        free(ciphertext);
        return 1;
    }

    struct timespec start;
    struct timespec end;

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < iterations; i++)
    {
        int len = 0;

        if (EVP_EncryptInit_ex(ctx, EVP_chacha20(), NULL, key, nonce) != 1 ||
            EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, data_size) != 1)
        {
            printf("ChaCha20 operation failed\n");
            EVP_CIPHER_CTX_free(ctx);
            free(plaintext);
            free(ciphertext);
            return 1;
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    long long elapsed_ns =
        (end.tv_sec - start.tv_sec) * 1000000000LL +
        (end.tv_nsec - start.tv_nsec);

    double total_mb =
        ((double)data_size * iterations) /
        (1024.0 * 1024.0);

    double seconds = elapsed_ns / 1000000000.0;
    double throughput = total_mb / seconds;

    printf("Algorithm: ChaCha20\n");
    printf("Data Size: %zu\n", data_size);
    printf("Iterations: %d\n", iterations);
    printf("Execution Time: %lld ns\n", elapsed_ns);
    printf("Throughput: %.2f MB/s\n", throughput);

    EVP_CIPHER_CTX_free(ctx);
    free(plaintext);
    free(ciphertext);

    return 0;
}
