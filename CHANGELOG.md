# CHANGELOG

<!-- version list -->

## v1.5.1 (2025-07-31)

### Bug Fixes

- Make release job depend on lint and test
  ([`562b762`](https://github.com/ai-enhanced-engineer/assistant-service/commit/562b762ea56b40d485e048a57f85805bf01b7ef7))


## v1.5.0 (2025-07-31)

### Bug Fixes

- Enable direct push releases in CI workflow
  ([`b03e465`](https://github.com/ai-enhanced-engineer/assistant-service/commit/b03e465f84de58dc7290a98be4f98b8e7fe46e07))

- Use RELEASE_TOKEN for GitHub Actions push permissions
  ([`036cc37`](https://github.com/ai-enhanced-engineer/assistant-service/commit/036cc378eba155f2aff6e3fac4ea7cbb44f040fa))

### Chores

- Final cleanup for public release
  ([#67](https://github.com/ai-enhanced-engineer/assistant-service/pull/67),
  [`fed4a75`](https://github.com/ai-enhanced-engineer/assistant-service/commit/fed4a757a1c9c271304dd5e49c80626be6ab8d6c))

### Documentation

- Address PR review recommendations for documentation consistency
  ([#67](https://github.com/ai-enhanced-engineer/assistant-service/pull/67),
  [`fed4a75`](https://github.com/ai-enhanced-engineer/assistant-service/commit/fed4a757a1c9c271304dd5e49c80626be6ab8d6c))

- Comprehensive README overhaul for clarity and usability
  ([#67](https://github.com/ai-enhanced-engineer/assistant-service/pull/67),
  [`fed4a75`](https://github.com/ai-enhanced-engineer/assistant-service/commit/fed4a757a1c9c271304dd5e49c80626be6ab8d6c))

- Improve technical documentation consistency and usability
  ([#67](https://github.com/ai-enhanced-engineer/assistant-service/pull/67),
  [`fed4a75`](https://github.com/ai-enhanced-engineer/assistant-service/commit/fed4a757a1c9c271304dd5e49c80626be6ab8d6c))

- Polish README for public release and improved clarity
  ([#67](https://github.com/ai-enhanced-engineer/assistant-service/pull/67),
  [`fed4a75`](https://github.com/ai-enhanced-engineer/assistant-service/commit/fed4a757a1c9c271304dd5e49c80626be6ab8d6c))

### Features

- Documentation Overhaul and Cleanup for Public Release
  ([#67](https://github.com/ai-enhanced-engineer/assistant-service/pull/67),
  [`fed4a75`](https://github.com/ai-enhanced-engineer/assistant-service/commit/fed4a757a1c9c271304dd5e49c80626be6ab8d6c))


## v1.3.0 (2025-07-29)

### Chores

- Add Claude Code GitHub Workflow ([#63](https://github.com/lkronecker13/assistant-service/pull/63),
  [`becd7c4`](https://github.com/lkronecker13/assistant-service/commit/becd7c4da0bf027d947405da85804d23cb3d725a))

- Implement Domain-Driven Design with Factory Pattern and Dependency Injection
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

### Documentation

- Add comprehensive PR description for domain-driven design refactor
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Add technical documentation for processors module
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Implement meaningful, non-redundant docstring guidelines
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

### Features

- Implement high priority recommendations from domain-driven design review
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

### Refactoring

- Consolidate configuration classes into entities/config.py
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Consolidate correlation ID functionality into structured_logging
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Consolidate interfaces with implementations to reduce over-abstraction
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Implement domain-driven design with factory pattern and dependency injection
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Improve configuration management with Pydantic Settings
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Improve processor architecture and add comprehensive tests
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Inject tool executor via dependency injection in OpenAIOrchestrator
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Integrate ToolExecutor into RunProcessor as internal component
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Move error_handlers from infrastructure to server directory
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Remove OpenAIClientFactory and simplify client initialization
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Rename models folder to entities
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Rename processor files to more descriptive names
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Rename processors/ to services/ for domain-driven design alignment
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Reorganize assistant_service with improved directory structure
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Reorganize assistant_service/main.py with layer-based architecture
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Reorganize tests to mirror production structure with shared fixtures
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))

- Simplify architecture by removing APIEndpoints abstraction
  ([#64](https://github.com/lkronecker13/assistant-service/pull/64),
  [`acb66f9`](https://github.com/lkronecker13/assistant-service/commit/acb66f986ec87516febd54f3cd196822d12232fc))


## v1.2.0 (2025-07-28)

### Bug Fixes

- Update repository tests to match LocalRepository implementation
  ([#62](https://github.com/lkronecker13/assistant-service/pull/62),
  [`a65bd91`](https://github.com/lkronecker13/assistant-service/commit/a65bd91dfc2dee36487438f6681c1749e677eabd))

- Update tests to work with WebSocket persistence changes
  ([#62](https://github.com/lkronecker13/assistant-service/pull/62),
  [`a65bd91`](https://github.com/lkronecker13/assistant-service/commit/a65bd91dfc2dee36487438f6681c1749e677eabd))

- WebSocket connection now supports continuous conversations
  ([#62](https://github.com/lkronecker13/assistant-service/pull/62),
  [`a65bd91`](https://github.com/lkronecker13/assistant-service/commit/a65bd91dfc2dee36487438f6681c1749e677eabd))

- WebSocket persistence and clean up obsolete module references
  ([#62](https://github.com/lkronecker13/assistant-service/pull/62),
  [`a65bd91`](https://github.com/lkronecker13/assistant-service/commit/a65bd91dfc2dee36487438f6681c1749e677eabd))

### Chores

- Clean up references to removed modules and update build configuration
  ([#62](https://github.com/lkronecker13/assistant-service/pull/62),
  [`a65bd91`](https://github.com/lkronecker13/assistant-service/commit/a65bd91dfc2dee36487438f6681c1749e677eabd))

- Move assistant_engine tests to root tests directory
  ([#62](https://github.com/lkronecker13/assistant-service/pull/62),
  [`a65bd91`](https://github.com/lkronecker13/assistant-service/commit/a65bd91dfc2dee36487438f6681c1749e677eabd))

### Features

- Implement API isolation scripts and reorganize Makefile with enhanced development workflow
  ([#62](https://github.com/lkronecker13/assistant-service/pull/62),
  [`a65bd91`](https://github.com/lkronecker13/assistant-service/commit/a65bd91dfc2dee36487438f6681c1749e677eabd))

### Refactoring

- Remove botbrew_commons and reorganize shared code
  ([#61](https://github.com/lkronecker13/assistant-service/pull/61),
  [`5a80bf1`](https://github.com/lkronecker13/assistant-service/commit/5a80bf18225e61e795c0bbc9a6f03f64aec9e422))

- Rename assistant_engine to assistant_service
  ([#62](https://github.com/lkronecker13/assistant-service/pull/62),
  [`a65bd91`](https://github.com/lkronecker13/assistant-service/commit/a65bd91dfc2dee36487438f6681c1749e677eabd))

- Streamline conversation scripts and improve naming consistency
  ([#62](https://github.com/lkronecker13/assistant-service/pull/62),
  [`a65bd91`](https://github.com/lkronecker13/assistant-service/commit/a65bd91dfc2dee36487438f6681c1749e677eabd))


## v1.1.2 (2025-07-28)

### Bug Fixes

- Add lifespan and DI tests ([#46](https://github.com/lkronecker13/assistant-service/pull/46),
  [`c54cbf6`](https://github.com/lkronecker13/assistant-service/commit/c54cbf60bd8ae2afd11d9237ab7ac119f1b46f37))

- Defer API instantiation to prevent GCP auth errors during imports
  ([#46](https://github.com/lkronecker13/assistant-service/pull/46),
  [`c54cbf6`](https://github.com/lkronecker13/assistant-service/commit/c54cbf60bd8ae2afd11d9237ab7ac119f1b46f37))

- Import ordering and ensure singleton initialization is deferred
  ([#46](https://github.com/lkronecker13/assistant-service/pull/46),
  [`c54cbf6`](https://github.com/lkronecker13/assistant-service/commit/c54cbf60bd8ae2afd11d9237ab7ac119f1b46f37))

### Testing

- Cover client injection and lifespan
  ([#46](https://github.com/lkronecker13/assistant-service/pull/46),
  [`c54cbf6`](https://github.com/lkronecker13/assistant-service/commit/c54cbf60bd8ae2afd11d9237ab7ac119f1b46f37))


## v1.1.1 (2025-07-28)

### Bug Fixes

- Migrate to structured logging and fix all type errors
  ([#58](https://github.com/lkronecker13/assistant-service/pull/58),
  [`8727499`](https://github.com/lkronecker13/assistant-service/commit/8727499c82c73369512bb9c599d8d40f775ed15c))


## v1.1.0 (2025-07-24)

### Bug Fixes

- Implement consistent logging levels with structured context
  ([#57](https://github.com/lkronecker13/assistant-service/pull/57),
  [`201093b`](https://github.com/lkronecker13/assistant-service/commit/201093b551a23ad539e402909aa12ba77b9d8ea9))

### Features

- Comprehensive WebSocket error handling and enhanced structured logging
  ([#57](https://github.com/lkronecker13/assistant-service/pull/57),
  [`201093b`](https://github.com/lkronecker13/assistant-service/commit/201093b551a23ad539e402909aa12ba77b9d8ea9))


## v1.0.6 (2025-07-16)

### Bug Fixes

- Add comprehensive correlation IDs and enhanced error context
  ([#56](https://github.com/lkronecker13/assistant-service/pull/56),
  [`8a2d7c9`](https://github.com/lkronecker13/assistant-service/commit/8a2d7c9410d54301305da9da2bdaf6568f6403d5))

- Remove nonexistent unit test marker from Makefile
  ([#56](https://github.com/lkronecker13/assistant-service/pull/56),
  [`8a2d7c9`](https://github.com/lkronecker13/assistant-service/commit/8a2d7c9410d54301305da9da2bdaf6568f6403d5))


## v1.0.5 (2025-07-02)

### Bug Fixes

- Implement comprehensive tool output error recovery
  ([#55](https://github.com/lkronecker13/assistant-service/pull/55),
  [`c637347`](https://github.com/lkronecker13/assistant-service/commit/c63734738b6edb8525143c17ee42343d8554e60d))


## v1.0.4 (2025-07-02)

### Bug Fixes

- Add pre-commit validation infrastructure
  ([#54](https://github.com/lkronecker13/assistant-service/pull/54),
  [`22709b0`](https://github.com/lkronecker13/assistant-service/commit/22709b08930913a7b2cf0af09b5c184d13d5a247))

- Improve project structure and documentation
  ([#54](https://github.com/lkronecker13/assistant-service/pull/54),
  [`22709b0`](https://github.com/lkronecker13/assistant-service/commit/22709b08930913a7b2cf0af09b5c184d13d5a247))

- Project structure improvements and pre-commit infrastructure
  ([#54](https://github.com/lkronecker13/assistant-service/pull/54),
  [`22709b0`](https://github.com/lkronecker13/assistant-service/commit/22709b08930913a7b2cf0af09b5c184d13d5a247))

### Documentation

- Add critical rule to never create PRs without user permission
  ([#54](https://github.com/lkronecker13/assistant-service/pull/54),
  [`22709b0`](https://github.com/lkronecker13/assistant-service/commit/22709b08930913a7b2cf0af09b5c184d13d5a247))

### Refactoring

- Modernize Makefile with enhanced structure and targets
  ([#54](https://github.com/lkronecker13/assistant-service/pull/54),
  [`22709b0`](https://github.com/lkronecker13/assistant-service/commit/22709b08930913a7b2cf0af09b5c184d13d5a247))


## v1.0.3 (2025-07-02)

### Bug Fixes

- Enhance tool call validation with comprehensive error handling
  ([#53](https://github.com/lkronecker13/assistant-service/pull/53),
  [`937cf78`](https://github.com/lkronecker13/assistant-service/commit/937cf789d05f77b43f2e12b5d4a76bb4d72b2c73))

- Remove unused variable in test to pass linting
  ([#53](https://github.com/lkronecker13/assistant-service/pull/53),
  [`937cf78`](https://github.com/lkronecker13/assistant-service/commit/937cf789d05f77b43f2e12b5d4a76bb4d72b2c73))

### Code Style

- Apply code formatting improvements
  ([#53](https://github.com/lkronecker13/assistant-service/pull/53),
  [`937cf78`](https://github.com/lkronecker13/assistant-service/commit/937cf789d05f77b43f2e12b5d4a76bb4d72b2c73))

### Documentation

- Add mandatory pre-PR validation workflow
  ([#53](https://github.com/lkronecker13/assistant-service/pull/53),
  [`937cf78`](https://github.com/lkronecker13/assistant-service/commit/937cf789d05f77b43f2e12b5d4a76bb4d72b2c73))


## v1.0.2 (2025-07-02)

### Bug Fixes

- Handle OpenAI client failures ([#48](https://github.com/lkronecker13/assistant-service/pull/48),
  [`42ec1c6`](https://github.com/lkronecker13/assistant-service/commit/42ec1c6fae9ef472dc1efc45de688318d9f80a1c))

### Continuous Integration

- Grant checkout read access ([#39](https://github.com/lkronecker13/assistant-service/pull/39),
  [`d776a75`](https://github.com/lkronecker13/assistant-service/commit/d776a75a5d705f5d8c28ed4943428be50108c808))

### Refactoring

- Manage openai client per instance
  ([#42](https://github.com/lkronecker13/assistant-service/pull/42),
  [`504ea3f`](https://github.com/lkronecker13/assistant-service/commit/504ea3f036c5592534ed7a4e3c5d8094ba95dc00))

- Remove globals from main ([#40](https://github.com/lkronecker13/assistant-service/pull/40),
  [`f73f711`](https://github.com/lkronecker13/assistant-service/commit/f73f7111a496c30aedf12397ee34a6de6ceedc39))

- Share run event iteration ([#50](https://github.com/lkronecker13/assistant-service/pull/50),
  [`6b61006`](https://github.com/lkronecker13/assistant-service/commit/6b61006ee1ea631ce78cc69fa6102b7040a0cb9b))


## v1.0.1 (2025-06-06)

### Bug Fixes

- Switch to FastAPI runtime ([#33](https://github.com/lkronecker13/assistant-service/pull/33),
  [`3a161ae`](https://github.com/lkronecker13/assistant-service/commit/3a161ae933e9a12b6314ef34d6656ea9504c1bf4))

- Use port 8000 ([#33](https://github.com/lkronecker13/assistant-service/pull/33),
  [`3a161ae`](https://github.com/lkronecker13/assistant-service/commit/3a161ae933e9a12b6314ef34d6656ea9504c1bf4))


## v1.0.0 (2025-06-06)

- Initial Release
