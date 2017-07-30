.PHONY: all
all: quick doc tox


.PHONY: quick
quick:
	python3 -m pytest

.PHONY: doc
doc:
	${MAKE} -C doc html

.PHONY: tox
tox:
	tox
