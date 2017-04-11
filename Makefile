.PHONY: all
all: quick doc tox


.PHONY: quick
quick:
	py.test

.PHONY: doc
doc:
	${MAKE} -C doc html

.PHONY: tox
tox:
	tox
