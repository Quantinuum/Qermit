qermit.zero_noise_extrapolation
===============================

Zero-noise extrapolation estimates an observable at zero noise by running
logically equivalent circuits at several amplified noise levels and fitting
the results. Digital folding inserts a circuit and its inverse: it increases
execution depth without changing the ideal unitary.

Offline workflow
------------------------------------

This local, noiseless Aer example needs no hardware account. It prepares
``|11>``, for which the weighted Z term is -2 and the weighted ZZ term is 0.5.
The assertions check the complete experiment-to-fit path against these
independent computational-basis expectations.

.. jupyter-execute::

    import numpy as np
    from pytket import Circuit, Qubit
    from pytket.extensions.qiskit import AerBackend
    from pytket.pauli import Pauli, QubitPauliString
    from pytket.utils import QubitPauliOperator
    from qermit import AnsatzCircuit, ObservableExperiment, ObservableTracker, SymbolsDict
    from qermit.zero_noise_extrapolation import Fit, Folding, gen_ZNE_MitEx

    z0 = QubitPauliString(Qubit(0), Pauli.Z)
    zz = QubitPauliString([Qubit(0), Qubit(1)], [Pauli.Z, Pauli.Z])
    operator = QubitPauliOperator({z0: 2.0, zz: 0.5})
    experiment = ObservableExperiment(
        AnsatzCircuit(Circuit(2).X(0).CX(0, 1), 256, SymbolsDict()),
        ObservableTracker(operator),
    )
    workflow = gen_ZNE_MitEx(
        AerBackend(), noise_scaling_list=[1, 3, 5],
        folding_type=Folding.circuit, fit_type=Fit.linear,
        optimisation_level=0, seed=7,
    )
    result = workflow.run([experiment])[0]
    assert np.isclose(float(result[z0]), -2.0, atol=1e-8)
    assert np.isclose(float(result[zz]), 0.5, atol=1e-8)
    print(result)

Choosing scales and a fit
------------------------------------

* Include scale 1 to anchor the fit to the original circuit. Odd integer scales
  make full circuit folding exact. Fractional scales can require approximate
  folding, depending on the selected method and circuit structure.
* The example uses a linear fit with three distinct scales. More scales can
  reveal a poor fit, but each scale requires another set of measurements.
  Higher-degree fits need enough distinct points and can amplify shot noise;
  inspect the scaled expectations and fit stability first.
* Keep compilation from cancelling the inserted inverse gates. Initial
  compilation and folding are separate stages; the example explicitly selects
  optimisation level 0. Check a device-specific compilation pipeline before
  interpreting a requested scale as a physical noise multiplier.

Each scale receives the experiment's requested shot count for its observable
measurements: the budget is not divided among scales. Multiple Pauli terms can
require additional measurement circuits. Folding also increases depth, so both
shot cost and device execution cost matter.

The noiseless example validates wiring and extrapolation, rather than a noise
reduction. On a device, the fitted value can lie outside the physical range
because of statistical fluctuations or a poor noise model. ZNE relies on noise
varying consistently with folding and a suitable fit over the chosen range.
Compare uncertainty and bias with the unmitigated estimate before deciding
whether an extrapolation improves accuracy.

API reference
------------------------------------

.. currentmodule:: qermit.zero_noise_extrapolation.zne

.. autofunction:: qermit.zero_noise_extrapolation.zne.gen_ZNE_MitEx

.. autofunction:: qermit.zero_noise_extrapolation.zne.gen_noise_scaled_mitex

.. autoclass:: qermit.zero_noise_extrapolation.zne.Folding
    :members:

.. autoclass:: qermit.zero_noise_extrapolation.zne.Fit
    :members:

.. autofunction:: qermit.zero_noise_extrapolation.zne.digital_folding_task_gen

.. autofunction:: qermit.zero_noise_extrapolation.zne.merge_experiments_task_gen

.. autofunction:: qermit.zero_noise_extrapolation.zne.extrapolation_task_gen

.. autofunction:: qermit.zero_noise_extrapolation.zne.gen_initial_compilation_task

.. autofunction:: qermit.zero_noise_extrapolation.zne.gen_qubit_relabel_task

.. autofunction:: qermit.zero_noise_extrapolation.zne.gen_duplication_task
