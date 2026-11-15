.PHONY: setup demo check demo-check
setup:
	python scripts/manage.py setup
demo:
	python scripts/manage.py demo
check:
	python scripts/manage.py check
demo-check:
	python scripts/manage.py demo-check
