# CHANGELOG

<!-- version list -->

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
