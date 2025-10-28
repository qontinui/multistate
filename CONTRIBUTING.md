# Contributing to MultiState

Thank you for your interest in contributing to MultiState! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, constructive, and collaborative. We're all here to build something useful together.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/jspinak/multistate/issues)
2. If not, create a new issue with:
   - Clear title describing the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS
   - Code sample if applicable

### Suggesting Features

1. Check existing [Issues](https://github.com/jspinak/multistate/issues) and [Discussions](https://github.com/jspinak/multistate/discussions)
2. Create a new discussion or issue describing:
   - The problem you're trying to solve
   - Your proposed solution
   - Example use cases

### Pull Requests

1. **Fork the repository** and create a branch from `main`
2. **Install development dependencies:**
   ```bash
   poetry install --with dev
   ```

3. **Make your changes:**
   - Write clear, documented code
   - Follow existing code style (black, ruff)
   - Add tests for new functionality
   - Update documentation if needed

4. **Run tests and linting:**
   ```bash
   poetry run pytest
   poetry run black .
   poetry run ruff check --fix .
   poetry run mypy src/
   ```

5. **Commit your changes:**
   - Use clear commit messages
   - Reference issues when applicable

6. **Push to your fork** and submit a pull request

7. **Address review feedback** if requested

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/multistate.git
cd multistate

# Install with dev dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run linting
poetry run black .
poetry run ruff check --fix .

# Run type checking
poetry run mypy src/
```

## Code Style

- **Python**: Follow PEP 8, enforced by `black` and `ruff`
- **Type hints**: Required for all public APIs
- **Docstrings**: Google style for all public functions/classes
- **Line length**: 88 characters (black default)

## Testing

- Write tests for all new features
- Maintain or improve code coverage
- Use `pytest` for unit tests
- Use `hypothesis` for property-based tests when applicable

## Documentation

- Update docstrings for any API changes
- Add examples for new features
- Update README.md if needed
- Consider adding to docs-site if it's a major feature

## Project Structure

```
multistate/
├── src/multistate/          # Main source code
│   ├── core/                # Core state management
│   ├── pathfinding/         # Pathfinding algorithms
│   ├── transitions/         # Transition logic
│   └── dynamics/            # Dynamic transitions
├── tests/                   # Test suite
├── examples/                # Example code
├── docs-site/               # Docusaurus documentation
└── benchmarks/              # Performance benchmarks
```

## Areas for Contribution

### Good First Issues
- Bug fixes
- Documentation improvements
- Example projects
- Test coverage improvements

### Advanced Contributions
- Performance optimizations
- New pathfinding algorithms
- Advanced features (dynamic transitions, occlusion)
- Integration with other frameworks

## Questions?

- Open a [Discussion](https://github.com/jspinak/multistate/discussions)
- Ask in an issue
- Check the [documentation](https://jspinak.github.io/multistate/)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🎉
