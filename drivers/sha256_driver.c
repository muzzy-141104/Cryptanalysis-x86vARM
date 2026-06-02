#include <openssl/evp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

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

    unsigned char *input = (unsigned char *)malloc(data_size);
    unsigned char digest[EVP_MAX_MD_SIZE];
    unsigned int digest_len = 0;

    if (!input)
    {
        printf("Memory allocation failed\n");
        return 1;
    }

    memset(input, 'A', data_size);

    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    if (!ctx)
    {
        printf("Failed to create digest context\n");
        free(input);
        return 1;
    }

    struct timespec start;
    struct timespec end;

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < iterations; i++)
    {
        if (EVP_DigestInit_ex(ctx, EVP_sha256(), NULL) != 1 ||
            EVP_DigestUpdate(ctx, input, data_size) != 1 ||
            EVP_DigestFinal_ex(ctx, digest, &digest_len) != 1)
        {
            printf("SHA256 operation failed\n");
            EVP_MD_CTX_free(ctx);
            free(input);
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

    printf("Algorithm: SHA256\n");
    printf("Data Size: %zu\n", data_size);
    printf("Iterations: %d\n", iterations);
    printf("Execution Time: %lld ns\n", elapsed_ns);
    printf("Throughput: %.2f MB/s\n", throughput);

    EVP_MD_CTX_free(ctx);
    free(input);

    return 0;
}
