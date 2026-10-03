.PHONY: setup doctor system-info build-image smoke summarize check
setup:
	./scripts/setup.sh
doctor:
	./scripts/doctor.sh
system-info:
	./scripts/system-info.sh
build-image:
	python3 scripts/benchmark.py build-image
smoke:
	BENCHMARK_TEST_COUNT=3 ./scripts/run-aider.sh
summarize:
	./scripts/summarize-results.py
check:
	@for script in scripts/*.sh; do bash -n "$$script" || exit; done
	python3 -m unittest discover -s tests -v
