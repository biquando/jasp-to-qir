#!/usr/bin/env python3
"""Parallel unittest CLI with isolated worker caches and a semantic report."""
import io
import logging
import os
import sys
import unittest
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import get_context
from pathlib import Path

logging.getLogger("matplotlib.font_manager").addFilter(
    lambda record: record.getMessage()
    != "Matplotlib is building the font cache; this may take a moment."
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests import support


def start_worker(temp: str) -> None:
    support.TEMP_ROOT = Path(temp)
    support.start_session()


RESULT_FIELDS = ("failures", "errors", "skipped", "expectedFailures", "unexpectedSuccesses")


def run_test(test, verbosity, failfast, buffer):
    support.REPORT.clear()
    stream = unittest.runner._WritelnDecorator(io.StringIO())
    result = unittest.TextTestResult(stream, True, verbosity)
    result.failfast, result.buffer = failfast, buffer
    unittest.TestSuite([test]).run(result)
    outcomes = {field: getattr(result, field) for field in RESULT_FIELDS}
    return result.testsRun, outcomes, result.shouldStop, stream.getvalue(), support.REPORT


def test_cases(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from test_cases(test)
        else:
            yield test


class ParallelSuite(unittest.TestSuite):
    def run(self, result, debug=False):
        verbosity = 2 if result.showAll else 1 if result.dots else 0
        with ProcessPoolExecutor(mp_context=get_context("spawn"), initializer=start_worker,
                                 initargs=(str(support.temp_dir()),)) as pool:
            futures = [pool.submit(run_test, test, verbosity, result.failfast, result.buffer)
                       for test in test_cases(self)]
            for future in as_completed(futures):
                count, outcomes, stopped, output, report = future.result()
                result.stream.write(output)
                result.stream.flush()
                result.testsRun += count
                for field, entries in outcomes.items():
                    getattr(result, field).extend(entries)
                support.REPORT.extend(report)
                if stopped:
                    result.stop()
                    for pending in futures:
                        pending.cancel()
                    break
        return result


class ParallelRunner(unittest.TextTestRunner):
    def run(self, test):
        return super().run(ParallelSuite(test))


def main() -> int:
    os.chdir(ROOT)
    support.start_session()
    success = False
    try:
        args = sys.argv[1:] or ['discover', '-s', 'tests', '-t', '.']
        result = unittest.main(module=None, argv=[sys.argv[0], *args],
                               verbosity=2, exit=False, testRunner=ParallelRunner).result
        success = result.wasSuccessful() and result.testsRun > 0
    finally:
        support.finish_session(success)
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
