from pathlib import Path
from tempfile import TemporaryDirectory
from demos.magnetization_lcu.magnetization import shots
from tools.jasp_to_qir import convert
from tools.estimate_cost import estimate_cost

source = Path("demos/magnetization_lcu")
with TemporaryDirectory() as directory:
    for model, counts in shots.items():
        total = 0
        for i, count in enumerate(counts):
            name = f"{model}_{i:02d}"
            output = Path(directory) / f"{name}.ll"
            convert(source / f"{name}.mlir", output,
                    output_formats="integer", require_mcmr=True)
            cost = estimate_cost(output.read_text(), qubits=13, shots=count)
            total += cost
            print(f"{name}: {count} shots, {cost:.2f} HQC")
        print(f"{model} total: {total:.2f} HQC")
