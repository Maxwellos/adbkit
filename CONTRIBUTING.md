# Contributing to PyADBKit

We welcome contributions to PyADBKit! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```
   git clone https://github.com/your-username/pyadbkit.git
   cd pyadbkit
   ```
3. Create a virtual environment and install the development dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   pip install -r requirements-dev.txt
   ```

## Making Changes

1. Create a new branch for your changes:
   ```
   git checkout -b your-feature-branch
   ```
2. Make your changes and ensure that the tests pass:
   ```
   python -m unittest discover tests
   ```
3. Write new tests for your changes if applicable.
4. Update the documentation if necessary.
5. Commit your changes:
   ```
   git commit -am "Add a brief description of your changes"
   ```

## Submitting a Pull Request

1. Push your changes to your fork on GitHub:
   ```
   git push origin your-feature-branch
   ```
2. Go to the PyADBKit repository on GitHub and create a new pull request.
3. Describe your changes in the pull request description.
4. Wait for a maintainer to review your pull request. They may ask for changes or clarifications.

## Code Style

- Follow PEP 8 guidelines for Python code style.
- Use type hints where appropriate.
- Write clear, concise comments and docstrings.

## Reporting Issues

If you find a bug or have a suggestion for improvement:

1. Check if the issue already exists in the GitHub issue tracker.
2. If not, create a new issue, providing as much detail as possible, including:
   - Steps to reproduce the issue
   - Expected behavior
   - Actual behavior
   - PyADBKit version
   - Python version
   - Operating system

## Questions

If you have any questions about contributing, feel free to ask in the GitHub issues.

Thank you for contributing to PyADBKit!
