.PHONY: black
black:
	black .

.PHONY: flake8
flake8:
	flake8 .

.PHONY: isort
isort:
	isort .

.PHONY: prettier
prettier:
	npx prettier --write .

.PHONY: lint
lint: isort black prettier flake8


.PHONY: test
test:
	pytest