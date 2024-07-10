.PHONY: format
format:
	poetry run ruff format

.PHONY: lint
lint:
	poetry run ruff check --fix

.PHONY: docdev
docdev:
	poetry run mkdocs serve --watch src

.PHONY: testonly
testonly:
	poetry run pytest

.PHONY: testcov
testcov:
	poetry run coverage run -m pytest

.PHONY: covreport
covreport: testcov
	coverage report

.PHONY: test
test: testcov
	coverage html
	poetry run python -m webbrowser ./htmlcov/index.html