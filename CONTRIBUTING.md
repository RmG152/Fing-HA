# Contributing to Fing-HA

Thank you for your interest in contributing to Fing-HA, a Home Assistant integration for Fing! This guide outlines how you can help improve the project.

## How to Contribute

### Reporting Issues
If you encounter bugs, have feature requests, or need help, please use the [GitHub Issues](https://github.com/your-repo/Fing-HA/issues) page. Before creating a new issue:
- Search existing issues to avoid duplicates.
- Use the appropriate issue template:
  - [Bug Report](.github/ISSUE_TEMPLATE/bug_report.yml)
  - [Feature Request](.github/ISSUE_TEMPLATE/feature_request.yml)
  - [Question](.github/ISSUE_TEMPLATE/question.yml)
- Provide detailed information including steps to reproduce, expected vs. actual behavior, and your environment details.

### Submitting Pull Requests
1. Fork the repository and create a feature branch from `main`.
2. Make your changes following the coding standards below.
3. Write or update tests for your changes.
4. Ensure all tests pass and code meets quality checks.
5. Submit a pull request with a clear description of the changes and why they are needed.
6. Address any feedback from reviewers.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/Fing-HA.git
   cd Fing-HA
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements_test.txt
   ```

4. Install the integration in development mode:
   - Copy `custom_components/fing_ha` to your Home Assistant `custom_components` directory.
   - Restart Home Assistant and configure the integration.

## Coding Standards

- Follow [PEP 8](https://pep8.org/) for Python code style.
- Use meaningful variable and function names.
- Add docstrings to all public functions and classes.
- Keep lines under 88 characters (use Black formatter if possible).
- Ensure code is compatible with Python 3.9+.

## Testing

- Run tests using pytest:
  ```bash
  pytest
  ```
- Aim for high test coverage, especially for new features.
- Tests are located in the `tests/` directory.
- Integration tests should validate Home Assistant functionality.

## Project-Specific Guidelines

- **Home Assistant Integration Best Practices**: Follow the [Home Assistant integration development guidelines](https://developers.home-assistant.io/docs/development_guidelines).
- **Configuration**: Use `config_flow.py` for user-friendly configuration.
- **Sensors and Switches**: Implement entities in `sensor.py` and `switch.py` following HA entity standards.
- **API Handling**: Use `api.py` for Fing API interactions with proper error handling.
- **Constants**: Define all constants in `const.py`.
- **Localization**: Update `strings.json` for translatable strings.

## Additional Resources

- [Home Assistant Developer Documentation](https://developers.home-assistant.io/)
- [Fing API Documentation](https://example.com/fing-api-docs) (if available)

## Code of Conduct

Please review and adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) in all interactions.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).