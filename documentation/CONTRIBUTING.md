
# Contributing to LLM-Lens

Thank you for your interest in contributing to LLM-Lens! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Types of Contributions

We welcome all types of contributions:

- **Bug Reports** - Found a bug? Let us know!
- **Feature Requests** - Have an idea for improvement?
- **Code Contributions** - Submit pull requests
- **Documentation** - Help improve our docs
- **Testing** - Help test new features
- **Community Support** - Help other users

### Getting Started

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/your-username/llm-lens.git
   cd llm-lens
   ```

2. **Set Up Development Environment**
   ```bash
   # Install dependencies
   pip install fastapi uvicorn sqlalchemy httpx jinja2 python-multipart
   
   # Run the application
   python main.py
   ```

3. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

## 🐛 Reporting Bugs

### Before Submitting a Bug Report

- Check the [existing issues](https://github.com/your-username/llm-lens/issues)
- Ensure you're using the latest version
- Test with a minimal reproduction case

### Bug Report Template

```markdown
**Describe the Bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

**Expected Behavior**
A clear description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
- OS: [e.g. Windows 10, Ubuntu 20.04, macOS 12]
- Python Version: [e.g. 3.11.2]
- LLM-Lens Version: [e.g. 1.0.0]
- Local LLM: [e.g. LM Studio, Ollama]

**Additional Context**
Add any other context about the problem here.
```

## 💡 Feature Requests

### Before Submitting a Feature Request

- Check if the feature already exists
- Search existing feature requests
- Consider if the feature fits the project scope

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request.
```

## 💻 Code Contributions

### Development Setup

1. **Install Development Dependencies**
   ```bash
   pip install fastapi uvicorn sqlalchemy httpx jinja2 python-multipart
   pip install black isort flake8 pytest  # Development tools
   ```

2. **Run Tests**
   ```bash
   pytest tests/
   ```

3. **Code Formatting**
   ```bash
   black .
   isort .
   flake8 .
   ```

### Code Style Guidelines

- **Python**: Follow PEP 8
- **JavaScript**: Use ESLint configuration
- **HTML/CSS**: Maintain consistent indentation
- **Comments**: Write clear, helpful comments
- **Variables**: Use descriptive names

### Commit Message Guidelines

Use clear, descriptive commit messages:

```
feat: add streaming support for optimization suggestions
fix: resolve database connection timeout issues
docs: update API documentation for cost tracking
style: improve dashboard button styling
refactor: extract alert logic into separate module
test: add unit tests for performance calculations
```

### Pull Request Process

1. **Create a Pull Request**
   - Use a descriptive title
   - Reference related issues
   - Provide a detailed description

2. **Pull Request Template**
   ```markdown
   ## Description
   Brief description of changes made.

   ## Type of Change
   - [ ] Bug fix (non-breaking change which fixes an issue)
   - [ ] New feature (non-breaking change which adds functionality)
   - [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
   - [ ] Documentation update

   ## Testing
   - [ ] Tests pass locally
   - [ ] New tests added for new functionality
   - [ ] Manual testing completed

   ## Screenshots (if applicable)
   Add screenshots to help explain your changes.

   ## Checklist
   - [ ] Code follows the style guidelines
   - [ ] Self-review of code completed
   - [ ] Code is commented where necessary
   - [ ] Documentation updated
   - [ ] No new warnings introduced
   ```

3. **Review Process**
   - Maintainers will review your PR
   - Address feedback promptly
   - Keep your branch updated

## 🏗️ Development Guidelines

### Project Structure

```
llm-lens/
├── main.py              # FastAPI application
├── database.py          # Database models and connection
├── templates/           # HTML templates
│   ├── index.html      # Dashboard template
│   └── landing.html    # Landing page
├── static/             # Static assets
│   └── style.css       # CSS styles
├── tests/              # Test files
├── docs/               # Documentation
└── README.md           # Main documentation
```

### Adding New Features

1. **Database Changes**
   - Add new models to `database.py`
   - Include migration logic if needed
   - Update initialization code

2. **API Endpoints**
   - Add endpoints to `main.py`
   - Follow RESTful conventions
   - Include proper error handling
   - Add API documentation

3. **Frontend Changes**
   - Update templates in `templates/`
   - Add CSS to `static/style.css`
   - Ensure mobile responsiveness
   - Test across browsers

4. **Documentation**
   - Update README.md
   - Add API documentation
   - Include usage examples

### Testing Guidelines

1. **Unit Tests**
   ```python
   # tests/test_analytics.py
   import pytest
   from main import calculate_performance_score

   def test_performance_score_calculation():
       score = calculate_performance_score(1000, 25.0, False)
       assert 0 <= score <= 1
       assert score > 0.5  # Should be decent performance
   ```

2. **Integration Tests**
   ```python
   # tests/test_api.py
   from fastapi.testclient import TestClient
   from main import app

   client = TestClient(app)

   def test_dashboard_loads():
       response = client.get("/dashboard")
       assert response.status_code == 200
       assert "LLM-Lens Dashboard" in response.text
   ```

3. **Test Database**
   - Use in-memory SQLite for tests
   - Clean up after tests
   - Mock external dependencies

### Performance Considerations

- **Database Queries**: Use efficient queries and indexes
- **API Responses**: Keep response times under 200ms
- **Memory Usage**: Monitor memory usage for large datasets
- **Frontend Performance**: Optimize JavaScript and CSS

### Security Guidelines

- **Input Validation**: Validate all user inputs
- **SQL Injection**: Use parameterized queries
- **XSS Prevention**: Escape HTML content
- **Error Handling**: Don't expose sensitive information

## 📝 Documentation

### Types of Documentation

1. **Code Documentation**
   - Function docstrings
   - Inline comments
   - Type hints

2. **API Documentation**
   - Endpoint descriptions
   - Request/response examples
   - Error codes

3. **User Documentation**
   - Installation guides
   - Usage tutorials
   - Troubleshooting

### Documentation Style

- Use clear, concise language
- Include practical examples
- Keep documentation up-to-date
- Use proper formatting

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=main

# Run specific test
pytest tests/test_analytics.py::test_performance_score
```

### Test Categories

1. **Unit Tests** - Test individual functions
2. **Integration Tests** - Test API endpoints
3. **End-to-End Tests** - Test complete workflows
4. **Performance Tests** - Test under load

### Writing Good Tests

- Test one thing at a time
- Use descriptive test names
- Include edge cases
- Mock external dependencies

## 🔄 Release Process

### Version Numbering

We use Semantic Versioning (semver):
- **Major** (1.0.0): Breaking changes
- **Minor** (1.1.0): New features
- **Patch** (1.1.1): Bug fixes

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version number bumped
- [ ] CHANGELOG.md updated
- [ ] Release notes prepared
- [ ] Tag created

## 🏷️ Issue Labels

We use these labels to categorize issues:

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements to documentation
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `question` - Further information requested
- `wontfix` - This will not be worked on

## 👥 Community Guidelines

### Code of Conduct

We are committed to providing a welcoming and inclusive environment:

- **Be respectful** - Treat everyone with respect
- **Be inclusive** - Welcome people of all backgrounds
- **Be patient** - Help others learn and grow
- **Be constructive** - Provide helpful feedback

### Communication Channels

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - General questions and ideas
- **Pull Requests** - Code contributions and reviews

### Getting Help

If you need help contributing:

1. Check the documentation
2. Search existing issues
3. Create a new issue with the `question` label
4. Join the community discussions

## 🎯 Priority Areas

We're particularly looking for contributions in:

1. **Performance Optimization**
   - Query optimization
   - Frontend performance
   - Memory usage improvements

2. **New Features**
   - Advanced analytics
   - Additional LLM integrations
   - Export formats

3. **User Experience**
   - UI/UX improvements
   - Mobile responsiveness
   - Accessibility features

4. **Documentation**
   - API examples
   - Tutorials
   - Video guides

5. **Testing**
   - Test coverage improvements
   - Performance tests
   - Browser compatibility

## 📞 Contact

- **Project Maintainer**: [Your Name]
- **Email**: [your-email@example.com]
- **GitHub**: [@your-username]

Thank you for contributing to LLM-Lens! Your contributions help make AI observability better for everyone. 🚀
