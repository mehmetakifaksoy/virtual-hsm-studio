# Contributing to Virtual HSM Studio

Thank you for your interest in Virtual HSM Studio.

## Development Setup

Clone the repository:

    git clone https://github.com/mehmetakifaksoy/virtual-hsm-studio.git
    cd virtual-hsm-studio

Create a virtual environment:

    python -m venv .venv

On Windows Git Bash:

    source .venv/Scripts/activate

On Linux/macOS:

    source .venv/bin/activate

Install development dependencies:

    pip install -r requirements-dev.txt

Run the tests:

    pytest -q

Compile-check the project:

    python -m compileall src tests

## Architecture

Virtual HSM Studio follows a layered architecture:

- Domain
- Application
- Infrastructure
- Presentation

The GUI must not directly depend on vendor-specific PKCS#11 implementations.

Provider-specific functionality belongs in the infrastructure layer.

## Branch Naming

Use descriptive branch names such as:

- feature/session-management
- feature/key-generation
- fix/pkcs11-slot-discovery
- docs/architecture-update

## Pull Requests

Pull requests should:

- Have a clear purpose
- Keep changes focused
- Include tests for new behavior where practical
- Pass existing tests
- Preserve provider abstraction
- Avoid committing credentials or cryptographic secrets

## Security

Never commit:

- Production private keys
- HSM credentials
- User or SO PINs
- API tokens
- Certificates containing private keys
- Vendor credentials
- Environment secrets

See SECURITY.md for additional security guidance.
