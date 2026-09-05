"""Tests of the test oracles: incorrect simulator output must never pass."""
import copy
import math
import unittest

from tests import support


def vector(*values):
    return {
        'format': 'jasp-to-qir-statevector-v1',
        'num_qubits': len(values).bit_length() - 1,
        'basis_order': 'qubit 0 is the leftmost (most-significant) bit',
        'qubits': ['q0'],
        'amplitudes': [[complex(v).real, complex(v).imag] for v in values],
    }


class StatevectorOracleTest(unittest.TestCase):
    def test_global_phase_is_irrelevant(self):
        a = 1 / math.sqrt(2)
        support.compare_statevectors(vector(a, a), vector(a * 1j, a * 1j), 'bell', 'dynamic')

    def test_relative_phase_and_basis_changes_fail(self):
        a = 1 / math.sqrt(2)
        for expected, actual in ((vector(a, a), vector(a, -a)),
                                 (vector(1, 0), vector(0, 1))):
            with self.subTest(actual=actual), self.assertRaises(support.TestFailure):
                support.compare_statevectors(expected, actual, 'bad', 'static')

    def test_malformed_vectors_fail_even_when_both_sides_match(self):
        for field, value in (
            ('amplitudes', []), ('amplitudes', [[0, 0], [0, 0]]),
            ('amplitudes', [[float('nan'), 0], [0, 0]]),
            ('amplitudes', [[float('inf'), 0], [0, 0]]),
            ('amplitudes', [[1], [0, 0]]), ('num_qubits', -1),
            ('basis_order', 'unknown'),
        ):
            bad = copy.deepcopy(vector(1, 0))
            bad[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(support.TestFailure):
                support.compare_statevectors(bad, bad, 'bad', 'static')

    def test_unused_qubits_must_be_zero(self):
        projected = support.remove_zero_suffix_qubits(vector(0, 0, 1, 0), 1, 'case', 'dynamic')
        support.compare_statevectors(vector(0, 1), projected, 'case', 'dynamic')
        with self.assertRaises(support.TestFailure):
            support.remove_zero_suffix_qubits(vector(0, 1, 0, 0), 1, 'case', 'dynamic')


class MeasurementOracleTest(unittest.TestCase):
    def test_packed_and_scalar_outputs_are_little_endian(self):
        self.assertEqual(support.qrisp_result_bits((True, [5]), (1, 3), 'case'), [1, 1, 0, 1])
        self.assertEqual(support.selene_result_bits([('a', 5)], (3,), 'case', 'dynamic'), [1, 0, 1])
        self.assertEqual(support.selene_result_bits([('a', 1), ('b', 0), ('c', 1)],
                                                   (3,), 'case', 'static'), [1, 0, 1])

    def test_buffer_record_and_packed_duplicate_must_agree(self):
        entries = [('a', [1, 0, 1, 0]), ('a', 5)]
        self.assertEqual(support.selene_result_bits(entries, (3,), 'case', 'dynamic'), [1, 0, 1])
        entries[1] = ('a', 4)
        with self.assertRaises(support.TestFailure):
            support.selene_result_bits(entries, (3,), 'case', 'dynamic')

    def test_bad_records_fail(self):
        for entries, widths, mode in (
            ([], (1,), 'static'), ([('a', 1), ('b', 0)], (1,), 'static'),
            ([('a', 2)], (1,), 'static'), ([('a', 8)], (3,), 'dynamic'),
            ([('a', 0.5)], (1,), 'static'), ([('a', '1')], (1,), 'static'),
            ([('a', 1)], (0,), 'static'),
        ):
            with self.subTest(entries=entries, widths=widths), self.assertRaises(support.TestFailure):
                support.selene_result_bits(entries, widths, 'bad', mode)
