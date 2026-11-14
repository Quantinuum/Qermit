"""Verify each spectral grid point prepares its own physical state."""

from itertools import product

import numpy as np
import pytest
from pytket import Circuit, OpType, Qubit
from pytket.pauli import Pauli, QubitPauliString
from pytket.utils import QubitPauliOperator
from sympy import symbols

from qermit import AnsatzCircuit, ObservableExperiment, ObservableTracker, SymbolsDict
from qermit.spectral_filtering.spectral_filtering import gen_obs_exp_grid_gen_task
from qermit.taskgraph.mitex import filter_observable_tracker_task_gen


@pytest.mark.parametrize("n_qubits", [1, 2])
@pytest.mark.parametrize("prepopulated", [False, True])
def test_prepared_grid_expectations(n_qubits: int, prepopulated: bool) -> None:
    angles = symbols(f"theta:{n_qubits}")
    circuit = Circuit(n_qubits)
    for qubit, angle in enumerate(angles):
        circuit.H(qubit).Rz(angle, qubit).H(qubit)
    observable = QubitPauliString(
        [Qubit(i) for i in range(n_qubits)], [Pauli.Z] * n_qubits
    )
    tracker = ObservableTracker(QubitPauliOperator({observable: 1.0}))
    parameters = SymbolsDict().symbols_from_dict(dict.fromkeys(angles, 0.25))
    experiment = ObservableExperiment(AnsatzCircuit(circuit, 100, parameters), tracker)
    if prepopulated:
        filter_observable_tracker_task_gen()([[experiment]])
    original_measurements = [
        measurement.get_parametric_circuit().to_dict()
        for measurement in tracker.measurement_circuits
    ]
    values = [0.0, 0.5, 1.0]
    meshes = np.meshgrid(*([values] * n_qubits), indexing="ij")
    grid = gen_obs_exp_grid_gen_task()([[experiment], [meshes]])[0][0]
    prepared, _ = filter_observable_tracker_task_gen()([list(grid.flat)])

    diagonal = np.array(
        [(-1) ** int(index).bit_count() for index in range(2**n_qubits)]
    )
    for index, point in enumerate(product(values, repeat=n_qubits)):
        measured = prepared[index][0].Circuit
        # Evaluate the actual prepared circuit before measurement, independently
        # of the experiment's parameter dictionary or observable tracker.
        quantum = Circuit(n_qubits)
        for command in measured.get_commands():
            if command.op.type != OpType.Measure:
                quantum.add_gate(command.op, command.args)
        state = quantum.get_statevector()
        actual = np.vdot(state, diagonal * state).real
        expected = np.prod(np.cos(np.pi * np.array(point)))
        assert np.isclose(actual, expected, atol=1e-12), (point, actual, expected)

    # Preparing grid circuits must leave the caller's tracker and values intact.
    assert [
        measurement.get_parametric_circuit().to_dict()
        for measurement in tracker.measurement_circuits
    ] == original_measurements
    assert list(parameters._symbolic_map.values()) == [0.25] * n_qubits
