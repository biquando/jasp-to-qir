"""Prototype Qrisp backend for bound circuits with terminal measurements."""

from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from qrisp import QuantumCircuit, QuantumVariable, measure
from qrisp.interface import Backend
from qrisp.interface.job import Job, JobResult, JobStatus
from qrisp.jasp import make_jaspr

from tools.jasp_to_qir import convert
from tools.run_qir import run


def circuit_mlir(circuit):
    """Replay a Qrisp circuit into Jasp, preserving classical measurement wiring."""
    circuit = circuit.transpile()
    qubits = {q: i for i, q in enumerate(circuit.qubits)}
    clbits = {c: i for i, c in enumerate(circuit.clbits)}
    measured = False
    for instruction in circuit.data:
        op = instruction.op
        if op.name in {"qb_alloc", "qb_dealloc", "barrier"}:
            continue
        if op.name == "measure":
            measured = True
        elif op.num_clbits or measured:
            raise ValueError("QIRBackend supports only terminal measurements, without classical control")

    if not measured:
        raise ValueError("QIRBackend requires a circuit with measurements")

    def replay():
        q = QuantumVariable(len(qubits))
        results = [False] * len(clbits)
        for instruction in circuit.data:
            op = instruction.op
            if op.name in {"qb_alloc", "qb_dealloc", "barrier"}:
                continue
            operands = [q[qubits[bit]] for bit in instruction.qubits]
            if op.name == "measure":
                results[clbits[instruction.clbits[0]]] = measure(operands[0])
            else:
                q.qs.append(op, operands, param_tracers=[float(p) for p in op.params])
        return tuple(results)

    return str(make_jaspr(replay)().to_mlir(lower_stablehlo=True))


class _CompletedJob(Job):
    def __init__(self, backend, counts):
        super().__init__(backend)
        self._result = JobResult(counts)
        self._last_known_status = JobStatus.DONE

    def result(self, timeout=None):
        return self._result

    def status(self):
        return self._last_known_status

    def cancel(self):
        return False


class QIRBackend(Backend):
    """Compile each submitted circuit to QIR and sample it locally with Selene.

    Parameters are bound before compilation. This prototype supports static
    circuits with terminal measurements; it does not support adaptive circuits
    or analytic probabilities. ``shots=None`` uses 1000 shots by default.
    """

    @classmethod
    def _default_options(cls):
        return {"shots": 1000}

    def run_async(self, circuits, shots=None):
        """Execute synchronously and return a completed Qrisp job."""
        shots = self.options["shots"] if shots is None else shots
        self._validate_shots(shots)
        if isinstance(circuits, QuantumCircuit):
            circuits = [circuits]
        counts = []
        for circuit in circuits:
            with TemporaryDirectory(prefix="qrisp-qir-") as directory:
                mlir = Path(directory) / "circuit.mlir"
                qir = mlir.with_suffix(".ll")
                mlir.write_text(circuit_mlir(circuit))
                convert(mlir, qir, output_formats="integer")
                results = run(qir.read_text(), qubits=len(circuit.qubits), shots=shots)
            # Backend bitstrings put the highest classical bit first.
            counts.append(dict(Counter(
                "".join(str(value) for _, value in reversed(shot)) for shot in results
            )))
        return _CompletedJob(self, counts)
