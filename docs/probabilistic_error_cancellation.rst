qermit.probabilistic_error_cancellation
=======================================

Learning-based probabilistic error cancellation (PEC) uses Clifford training
circuits to learn a signed linear combination of circuit variants. Applying
the learned quasi-probability weights to noisy measurements estimates the
ideal observable. These weights can be negative: they are not probabilities
for ordinary sampling, and the corrected result is not a histogram of counts.

Offline workflow
------------------------------------

The example below runs both the device and ideal training circuits on local,
noiseless Aer backends. It needs no hardware account. X, CZ and T prepare
``|10>`` up to phase, giving Z on qubit 0 equal to -1 and ZZ equal to -1. The
returned terms include the observable coefficients, so they are -2 and -0.5.

.. jupyter-execute::

    import numpy as np
    from pytket import Circuit, Qubit
    from pytket.extensions.qiskit import AerBackend
    from pytket.pauli import Pauli, QubitPauliString
    from pytket.utils import QubitPauliOperator
    from qermit import AnsatzCircuit, ObservableExperiment, ObservableTracker, SymbolsDict
    from qermit.probabilistic_error_cancellation import gen_PEC_learning_based_MitEx

    z0 = QubitPauliString(Qubit(0), Pauli.Z)
    zz = QubitPauliString([Qubit(0), Qubit(1)], [Pauli.Z, Pauli.Z])
    experiment = ObservableExperiment(
        AnsatzCircuit(Circuit(2).X(0).CZ(0, 1).T(1), 256, SymbolsDict()),
        ObservableTracker(QubitPauliOperator({z0: 2.0, zz: 0.5})),
    )
    workflow = gen_PEC_learning_based_MitEx(
        device_backend=AerBackend(), simulator_backend=AerBackend(),
        num_cliff=20, optimisation_level=0, seed=7,
    )
    result = workflow.run([experiment])[0]
    assert np.isclose(float(result[z0]), -2.0, atol=1e-8)
    assert np.isclose(float(result[zz]), -0.5, atol=1e-8)
    print(result)

Training, cost and interpretation
------------------------------------

``device_backend`` executes noisy circuit variants; ``simulator_backend``
provides ideal training values. Using two noiseless backends here checks the
workflow and coefficient handling, not a reduction of device noise. The device
backend's gate set must include CX or CZ. Initial compilation, gate labelling
and frame rebasing are handled by the returned workflow.

``num_cliff`` controls the number of Clifford training circuits generated for
each primary circuit. It trades additional training measurements and ideal
simulation against the information available for fitting quasi-probabilities.
The ``seed`` controls NumPy's random training-circuit generation; it does not
guarantee repeatable shot samples on an arbitrary backend.

The shot count in ``AnsatzCircuit`` is used for generated measurement circuits,
not as a total budget across training and target variants. Account for both
training and evaluation submissions when planning a hardware run. The number
of variants also grows with the circuit's frame structure.

Signed weights can amplify measurement variance. A large sum of absolute
weights can require many more shots for a fixed precision, and finite training
data or a poorly conditioned fit can add bias. Learned corrections also depend
on the device noise remaining applicable between training and target runs.
Validate transfer on held-out circuits and compare uncertainty with an
unmitigated estimate. A corrected expectation outside an observable's physical
range is possible; it is not evidence that the physical state has that value.

API reference
------------------------------------

.. currentmodule:: qermit.probabilistic_error_cancellation.probabilistic_error_cancellation

.. autofunction:: qermit.probabilistic_error_cancellation.pec_learning_based.gen_PEC_learning_based_MitEx

.. autofunction:: qermit.probabilistic_error_cancellation.pec_learning_based.gen_rebase_to_frames_and_computing

.. autofunction:: qermit.probabilistic_error_cancellation.pec_learning_based.gen_run_with_quasi_prob

.. autofunction:: qermit.probabilistic_error_cancellation.pec_learning_based.collate_results_task_gen

.. autofunction:: qermit.probabilistic_error_cancellation.pec_learning_based.learn_quasi_probs_task_gen

.. autofunction:: qermit.probabilistic_error_cancellation.pec_learning_based.gen_get_clifford_training_set

.. autofunction:: qermit.probabilistic_error_cancellation.pec_learning_based.gen_label_gates

.. autofunction:: qermit.probabilistic_error_cancellation.pec_learning_based.gen_wrap_frame_gates

.. autofunction:: qermit.probabilistic_error_cancellation.pec_learning_based.gen_get_noisy_circuits
