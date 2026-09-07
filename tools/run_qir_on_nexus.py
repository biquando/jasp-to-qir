import argparse
import datetime
from pathlib import Path

import qnexus as qnx
from qir_qis import qir_ll_to_bc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("-p", "--project", type=str, default="jasp-to-qir")
    parser.add_argument("-q", "--qubits", type=int, required=True)
    parser.add_argument("-s", "--shots", type=int, required=True)
    args = parser.parse_args()

    # Set up nexus
    qnx.login()
    project = qnx.projects.get_or_create(name=args.project)
    qnx.context.set_active_project(project)

    # Upload qir program
    with open(args.input, 'r') as f:
        qir_text = f.read()
    qir = qir_ll_to_bc(qir_text)
    qir_upload = qnx.qir.upload(qir=qir, name=str(args.input), project=project)

    # Set up backend
    config = qnx.models.HeliosConfig(
        system_name="Helios-1E-lite",
        emulator_config=qnx.models.HeliosEmulatorConfig(n_qubits=args.qubits),
    )

    # Start job
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    job_name = f"jasp-to-qir_Helios-1E-lite_{str(args.input)}_{timestamp}"
    job = qnx.start_execute_job(
        programs=[qir_upload],
        n_shots=[args.shots],
        backend_config=config,
        name=job_name
    )

    # Get results
    qnx.jobs.wait_for(job)
    result = qnx.jobs.results(job)[0].download_result()
    print(result.results)

if __name__ == "__main__":
    main()
