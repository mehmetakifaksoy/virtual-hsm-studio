# File signing walkthrough

This POC creates a detached binary RSA PKCS#1 v1.5/SHA-256 signature. A PDF can be signed as bytes,
but this is not a PDF/PAdES signature embedded in the PDF or a certificate-backed identity signature.

## Prepare

Use SoftHSM2 or a hardware provider supporting SHA256_RSA_PKCS. The local Virtual HSM simulator cannot sign.
Initialize a token with your administration tool. In Key Manager, connect the same DLL and token,
choose Generate Key, select RSA-2048 or another supported RSA size, enter a label and USER PIN, and generate.
The private key is created sensitive and non-extractable; public-key export does not export private material.

## Sign

1. Start HsmSignVerify.exe and Connect HSM.
2. Select an initialized token and Sign with Selected Token.
3. Enter USER PIN and Load RSA Signing Keys. PIN clears immediately after submission.
4. Select the RSA key by label and ID. The client requires one public/private pair with the same nonempty ID.
5. Choose a document up to 16 MiB, then re-enter USER PIN and press Sign File.
6. Save the public key in the prompted PEM dialog. Save Signature writes a binary .sig file.

The worker checks the produced signature against the matching public key before returning it.
No private-key attributes are sent to the GUI. No automatic login retry is made.
If no signing keys appear, having RSA objects alone is insufficient: the private key must have CKA_SIGN enabled.

## Verify without the HSM

Close the signing dialog. Choose Verify File Signature and select:

1. The original document.
2. Its detached .sig file.
3. The matching RSA public key .pem.

VALID proves the signature matches those bytes and that public key. It does not authenticate the claimed
owner of the key or check a certificate chain. Keep a trusted copy/fingerprint of the public key when identity matters.

To test failure, make a copy of the original document and change one character. Verify the changed copy
with the original .sig and .pem: it must report INVALID. A wrong public key or modified signature must also fail.
Identical public keys saved under different file names are interchangeable.

## Current boundaries

No private/secret-key export, wrapped-key backup, RSA-PSS, ECDSA, certificates, timestamping or PDF signature UI.
SoftHSM2 integration has been tested. Hardware support, including Procenne, requires a separate device pilot.
