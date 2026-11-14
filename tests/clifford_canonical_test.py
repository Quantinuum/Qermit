"""Independent matrices for the Hadamard-free Clifford construction."""

import itertools

import numpy as np
import pytest

from qermit.probabilistic_error_cancellation.cliff_circuit_gen import (
    clifford_canonical_F,
    random_clifford_circ,
)


@pytest.mark.parametrize("pauli", range(4))
def test_pauli_layer(pauli: int) -> None:
    expected = [
        np.eye(2),
        np.array([[0, 1], [1, 0]]),
        np.array([[0, -1j], [1j, 0]]),
        np.diag([1, -1]),
    ][pauli]
    circuit = clifford_canonical_F([pauli], np.zeros((1, 1)), np.eye(1))
    np.testing.assert_allclose(circuit.get_unitary(), expected, atol=1e-12)


@pytest.mark.parametrize("n_qubits", [2, 3])
def test_lower_triangular_linear_map(n_qubits: int) -> None:
    """The CX layer sends each basis vector x to Delta x over GF(2)."""
    entries = [(j, i) for j in range(n_qubits) for i in range(j)]
    for values in itertools.product([0, 1], repeat=len(entries)):
        delta = np.eye(n_qubits, dtype=int)
        for (j, i), value in zip(entries, values):
            delta[j, i] = value
        expected = np.zeros((2**n_qubits, 2**n_qubits))
        for basis in range(2**n_qubits):
            bits = np.array([(basis >> i) & 1 for i in reversed(range(n_qubits))])
            mapped = delta @ bits % 2
            output = sum(int(bit) << i for i, bit in enumerate(reversed(mapped)))
            expected[output, basis] = 1
        circuit = clifford_canonical_F([0] * n_qubits, np.zeros_like(delta), delta)
        np.testing.assert_allclose(circuit.get_unitary(), expected, atol=1e-12)


def test_symmetric_phase_matrix() -> None:
    """Gamma contributes i**(x.T Gamma x), independently of the CX layer."""
    for first, second, coupling in itertools.product([0, 1], repeat=3):
        gamma = np.array([[first, coupling], [coupling, second]])
        expected = []
        for basis in range(4):
            bits = np.array([basis >> 1, basis & 1])
            expected.append(1j ** int(bits @ gamma @ bits))
        circuit = clifford_canonical_F([0, 0], gamma, np.eye(2))
        np.testing.assert_allclose(circuit.get_unitary(), np.diag(expected), atol=1e-12)


def test_seeded_sampler_reaches_all_one_qubit_cliffords() -> None:
    """A fixed collection of seeds must cover the entire 24-element group."""
    saved_state = np.random.get_state()
    try:
        signatures = set()
        paulis = [
            np.array([[0, 1], [1, 0]]),
            np.array([[0, -1j], [1j, 0]]),
            np.diag([1, -1]),
        ]
        for seed in range(512):
            unitary = random_clifford_circ(1, seed=seed).get_unitary()
            signature = tuple(
                int(
                    round(np.trace(axis @ unitary @ source @ unitary.conj().T).real / 2)
                )
                for source in paulis
                for axis in paulis
            )
            signatures.add(signature)
        assert len(signatures) == 24
    finally:
        np.random.set_state(saved_state)
