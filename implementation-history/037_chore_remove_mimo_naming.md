# Sprint 17 — Migrate from Memo-Centric Architecture to a Provider-Agnostic AI Platform

## ROLE

You are a Principal Software Architect, AI Infrastructure Engineer, DDD Expert, FastAPI Expert, LangChain Expert, and Refactoring Specialist.

Your task is to eliminate every remaining Memo-specific implementation from the codebase and migrate the architecture to a provider-agnostic design.

Originally, the project was implemented using Memo as its only AI engine.

Later, multiple providers were introduced.

However, the architecture still contains many Memo-specific names, abstractions and implementations.

This sprint converts the entire project into a true Provider-based architecture.

Business behavior must remain unchanged.

--------------------------------------------------
OBJECTIVES
--------------------------------------------------

Remove Memo-specific concepts from the codebase.

Replace them with generic Provider abstractions.

The architecture should support adding future providers without further refactoring.

--------------------------------------------------
CODEBASE REVIEW
--------------------------------------------------

Scan the entire repository.

Locate every occurrence of:

Memo

memo

MEMO

memo_provider

memo_client

memo_service

memo_api

memo_response

memo_request

memo_model

memo_completion

memo_generation

or any Memo-specific terminology.

Review each occurrence individually.

Do NOT perform a blind search-and-replace.

Determine whether it represents:

- Domain terminology
- Infrastructure implementation
- Provider implementation
- API naming
- Tests
- Documentation
- Configuration

Refactor appropriately.

--------------------------------------------------
ARCHITECTURE
--------------------------------------------------

Introduce generic provider abstractions.

Examples:

AIProvider

ProviderClient

ProviderRequest

ProviderResponse

ProviderCapabilities

ProviderRegistry

ProviderFactory

ProviderSettings

ProviderConfiguration

ProviderSelectionStrategy

Workflow code should depend only on these abstractions.

--------------------------------------------------
DEPENDENCY DIRECTION
--------------------------------------------------

Business logic

↓

Application

↓

Provider Interface

↓

Memo Provider

OpenAI Provider

Gemini Provider

Claude Provider

DeepSeek Provider

...

The application layer must never depend directly on Memo.

--------------------------------------------------
PROVIDER IMPLEMENTATIONS
--------------------------------------------------

Move Memo-specific logic into its own provider implementation.

For example:

providers/

    memo/

    openai/

    gemini/

    deepseek/

    anthropic/

Each provider owns:

Client

Configuration

Authentication

Capabilities

Provider-specific adapters

--------------------------------------------------
NAMING

Replace Memo-centric naming with provider-neutral terminology.

Examples:

MemoClient

↓

ProviderClient

MemoService

↓

ProviderService

MemoConfig

↓

ProviderConfig

MemoGeneration

↓

GenerationRequest

MemoResponse

↓

ProviderResponse

Only keep "Memo" where it identifies the concrete provider implementation.

--------------------------------------------------
FOLDER STRUCTURE

Review folders.

Move Memo-specific infrastructure into:

providers/memo/

Shared abstractions should live outside provider implementations.

--------------------------------------------------
API

Review DTOs.

Rename provider-specific DTOs to generic equivalents.

Avoid exposing Memo terminology through APIs.

--------------------------------------------------
LANGCHAIN

Workflows should request:

Provider

never

Memo

Provider selection must happen through dependency injection or a provider registry.

--------------------------------------------------
CONFIGURATION

Rename configuration keys where appropriate.

Examples:

MEMO_API_KEY

↓

PROVIDER_API_KEY

or provider-specific configuration scoped under provider implementations.

Review environment variables carefully.

Maintain backward compatibility when practical.

--------------------------------------------------
BACKWARD COMPATIBILITY

Where appropriate:

Support deprecated Memo names temporarily.

Emit deprecation warnings.

Avoid breaking existing deployments unnecessarily.

--------------------------------------------------
TESTS

Review all tests.

Rename:

Fixtures

Mocks

Fake Providers

Helper functions

Snapshot names

Update integration tests.

Ensure all tests continue to pass.

--------------------------------------------------
DOCUMENTATION

Update:

Architecture documentation

Provider documentation

Configuration documentation

API documentation

Developer guides

Migration guides

Replace Memo-centric terminology with Provider terminology.

--------------------------------------------------
MIGRATION NOTES

Create a migration document describing:

Previous naming

New naming

Backward compatibility

Deprecated APIs

Future removal plan

--------------------------------------------------
CODE QUALITY

Search for:

Unused Memo helpers

Dead code

Duplicate provider implementations

Old abstractions

Remove obsolete infrastructure.

--------------------------------------------------
VALIDATION

After refactoring:

The application should not know which provider is being used.

Changing providers should require configuration changes only.

No business logic should contain Memo-specific terminology.

--------------------------------------------------
ACCEPTANCE CRITERIA

✔ Memo-specific architecture is eliminated.

✔ Business logic depends only on provider abstractions.

✔ Memo exists only as one provider implementation.

✔ Folder structure reflects provider isolation.

✔ APIs expose provider-neutral terminology.

✔ Configuration supports multiple providers.

✔ Existing behavior is preserved.

✔ Backward compatibility is maintained where appropriate.

✔ Documentation and tests are updated.

✔ The architecture is ready for adding future providers with minimal effort.
