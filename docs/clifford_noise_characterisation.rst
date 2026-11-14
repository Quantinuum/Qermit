qermit.clifford_noise_characterisation
======================================

Clifford noise characterisation uses related circuits whose ideal behaviour is
easier to calculate to estimate a correction for the original experiment.
Qermit provides two workflows:

* Clifford data regression (CDR) generates near-Clifford training circuits,
  evaluates them on a device and a simulator, and fits a correction model.
* Depolarisation-factor suppression for nearest-Clifford (DFSC) builds Clifford
  characterisation circuits for the measured Pauli strings, then rescales the
  experiment using the resulting characterisation expectations.

Offline DFSC example
------------------------------------

This example runs locally with Aer and needs no hardware credentials. The
prepared state is ``|11>``, so Z on qubit 0 has expectation -1 and ZZ has
expectation +1. The result contains the observable coefficients as well: the
two returned terms should be -2 and 0.5, with total expectation -1.5.

.. jupyter-execute::

    import numpy as np
    from pytket import Circuit, Qubit
    from pytket.extensions.qiskit import AerBackend
    from pytket.pauli import Pauli, QubitPauliString
    from pytket.utils import QubitPauliOperator
    from qermit import AnsatzCircuit, ObservableExperiment, ObservableTracker, SymbolsDict
    from qermit.clifford_noise_characterisation import gen_DFSC_MitEx

    z0 = QubitPauliString(Qubit(0), Pauli.Z)
    zz = QubitPauliString([Qubit(0), Qubit(1)], [Pauli.Z, Pauli.Z])
    experiment = ObservableExperiment(
        AnsatzCircuit(Circuit(2).X(0).CX(0, 1), 256, SymbolsDict()),
        ObservableTracker(QubitPauliOperator({z0: 2.0, zz: 0.5})),
    )
    workflow = gen_DFSC_MitEx(AerBackend(), DFSC_threshold=0.01)
    result = workflow.run([experiment])[0]
    assert np.isclose(float(result[z0]), -2.0, atol=1e-8)
    assert np.isclose(float(result[zz]), 0.5, atol=1e-8)
    print(result)

Choosing and budgeting a workflow
------------------------------------

DFSC is useful when a multiplicative characterisation factor is an appropriate
model for the measured observable. The workflow generates extra measurements
for characterisation; the experiment's shot count is not a total budget shared
across all those circuits. More observables and measurement circuits increase
the cost. The ``experiment_mitex`` and ``characterisation_mitex`` keyword
arguments allow separate execution workflows for the two sets of experiments.

The ``DFSC_threshold`` parameter sets the minimum characterisation value used
as a divisor: values at or below it leave the original term unchanged. Small
positive divisors amplify statistical uncertainty;
inspect characterisation quality rather than selecting a very small threshold
just to obtain a correction. A threshold does not establish that the physical
noise is depolarising or that a correction improves an estimate.

For non-Clifford experiments, expose non-Clifford gate parameters through the
``SymbolsDict`` so the workflow can generate its nearest-Clifford variants.
The basis-state example has only Clifford gates and needs no such bindings.

For CDR, :func:`gen_CDR_MitEx` takes separate ``device_backend`` and
``simulator_backend`` arguments. Set ``n_non_cliffords`` to the number of gates
left non-Clifford in each training circuit, ``n_pairs`` to the number exchanged
in a sampling step, and ``total_state_circuits`` to the training-set size.
Keeping more non-Clifford gates can improve similarity to the target while
making ideal simulation harder. Increasing the training set also increases
device measurements and simulation cost. Training values must span enough of
the observable's range for a stable fit: a collection of nearly identical
values cannot reliably determine a correction model.

Both methods rely on characterisation transferring to the target circuit.
The noiseless example checks the public API, coefficient handling and logical
expectations. Assess a noisy device with held-out circuits, repeated sampling
and comparison to an unmitigated estimate before drawing accuracy conclusions.

API reference
------------------------------------

.. autofunction:: qermit.clifford_noise_characterisation.ccl.gen_CDR_MitEx

.. autoclass:: qermit.clifford_noise_characterisation.ccl.LikelihoodFunction
    :members:
    :special-members:

.. autofunction:: qermit.clifford_noise_characterisation.dfsc.gen_DFSC_MitEx

.. autofunction:: qermit.clifford_noise_characterisation.ccl.ccl_state_task_gen

.. autofunction:: qermit.clifford_noise_characterisation.ccl.ccl_result_batching_task_gen

.. autofunction:: qermit.clifford_noise_characterisation.ccl.ccl_likelihood_filtering_task_gen

.. autofunction:: qermit.clifford_noise_characterisation.dfsc.DFSC_circuit_task_gen

.. autofunction:: qermit.clifford_noise_characterisation.dfsc.DFSC_collater_task_gen

.. autofunction:: qermit.clifford_noise_characterisation.dfsc.DFSC_characterisation_task_gen

.. autofunction:: qermit.clifford_noise_characterisation.dfsc.DFSC_correction_task_gen


