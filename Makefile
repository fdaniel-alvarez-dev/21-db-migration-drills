.PHONY: demo test clean

demo: test
	@echo "Demo complete."

test:
	TEST_MODE=demo python3 tests/run_tests.py

clean:
	rm -rf artifacts
