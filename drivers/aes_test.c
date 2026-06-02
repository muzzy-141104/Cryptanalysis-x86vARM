#include <openssl/evp.h>
#include <stdio.h>

int main() {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();

    if (!ctx) {
        printf("Failed to initialize OpenSSL\n");
        return 1;
    }

    printf("OpenSSL AES initialized successfully\n");

    EVP_CIPHER_CTX_free(ctx);

    return 0;
}
