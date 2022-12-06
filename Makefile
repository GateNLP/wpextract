.PHONY: black
black:
	black .

.PHONY: flake8
flake8:
	flake8 .

.PHONY: isort
isort:
	isort .

.PHONY: lint
lint: isort black flake8

.PHONY: test
test:
	pytest