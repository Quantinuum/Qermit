qermit.spectral_filtering
===============================

Spectral filtering estimates an expectation landscape over the symbolic angles
of a circuit, transforms it with a discrete Fourier transform, filters its
coefficients, and transforms back. The returned ``MitEx`` evaluates the filtered
landscape at the parameter values supplied in each ``ObservableExperiment``.

This can remove small components associated with sampling noise, but a filter
can also remove physical signal. It does not guarantee a more accurate estimate
for every circuit or noise model.

Offline example
---------------

The following example uses the local Aer simulator and needs no hardware
account. For ``H Rz(theta) H`` acting on zero, the ideal Z expectation is
``cos(pi * theta)`` because pytket angles are measured in half turns.

.. jupyter-execute::

    import numpy as np
    from sympy import Symbol
    from pytket import Circuit, Qubit
    from pytket.extensions.qiskit import AerBackend
    from pytket.pauli import Pauli, QubitPauliString
    from pytket.utils import QubitPauliOperator
    from qermit import (
        AnsatzCircuit, ObservableExperiment, ObservableTracker, SymbolsDict,
    )
    from qermit.spectral_filtering.spectral_filtering import (
        gen_spectral_filtering_MitEx,
    )
    from qermit.spectral_filtering.signal_filter import SmallCoefficientSignalFilter

    theta = Symbol("theta")
    circuit = Circuit(1).H(0).Rz(theta, 0).H(0)
    z_string = QubitPauliString(Qubit(0), Pauli.Z)
    observable = QubitPauliOperator({z_string: 1.0})
    symbols = SymbolsDict().symbols_from_dict({theta: 0.25})
    experiment = ObservableExperiment(
        AnsatzCircuit(circuit, 8192, symbols),
        ObservableTracker(observable),
    )

    mitigation = gen_spectral_filtering_MitEx(
        backend=AerBackend(),
        n_vals=8,
        signal_filter=SmallCoefficientSignalFilter(tol=0.5),
    )
    filtered = mitigation.run([experiment])
    estimate = complex(filtered[0][z_string]).real
    ideal = np.cos(np.pi * 0.25)
    print({"filtered": estimate, "ideal": ideal})
    assert np.isclose(estimate, ideal, atol=0.1)

The ideal value is approximately 0.7071. The filtered estimate fluctuates with
the sampled counts. This noiseless example illustrates the workflow and the
output structure; assessing mitigation requires comparing against an unfiltered
estimate under a representative noise model.

Choosing the grid and filter
------------------------------

``n_vals`` sets the number of equally spaced values in ``[0, 2)`` for each symbol,
in half-turn units. With ``d`` symbols, the grid contains ``n_vals ** d`` parameter
points. Each point can require several measurement circuits for its observable,
so both the circuit count and shot cost can grow quickly.

The grid must resolve the physical frequencies of the chosen parameterisation;
increasing it cannot recover information already lost to aliasing. Ensure that
the supplied parameter values lie within the sampled grid for interpolation.
The example uses 0.25, which is itself a grid point.

``SmallCoefficientSignalFilter`` thresholds absolute magnitudes of the
unnormalised FFT coefficients. Its tolerance therefore depends on the grid size
and signal scale, rather than being a bound on the final expectation error. The
eight-point cosine has two ideal coefficients of magnitude four; ``tol=0.5``
keeps them, whereas the default tolerance of five would remove them. Inspect the
signal and vary the tolerance before applying it to a new problem.

API reference
-------------

.. currentmodule:: qermit.spectral_filtering.spectral_filtering

.. autofunction:: qermit.spectral_filtering.spectral_filtering.gen_spectral_filtering_MitEx

.. autofunction:: qermit.spectral_filtering.spectral_filtering.gen_result_extraction_task

.. autofunction:: qermit.spectral_filtering.spectral_filtering.gen_mitigation_task

.. autofunction:: qermit.spectral_filtering.spectral_filtering.gen_fft_task

.. autofunction:: qermit.spectral_filtering.spectral_filtering.gen_ndarray_to_dict_task

.. autofunction:: qermit.spectral_filtering.spectral_filtering.gen_inv_fft_task

.. autofunction:: qermit.spectral_filtering.spectral_filtering.gen_flatten_task

.. autofunction:: qermit.spectral_filtering.spectral_filtering.gen_reshape_task

.. autofunction:: qermit.spectral_filtering.spectral_filtering.gen_obs_exp_grid_gen_task

.. autofunction:: qermit.spectral_filtering.spectral_filtering.gen_symbol_val_gen_task

.. autofunction:: qermit.spectral_filtering.spectral_filtering.gen_wire_copy_task

.. autofunction:: qermit.spectral_filtering.spectral_filtering.gen_param_grid_gen_task

.. autoclass:: qermit.spectral_filtering.signal_filter.SmallCoefficientSignalFilter
    :members:

.. autoclass:: qermit.spectral_filtering.signal_filter.SignalFilter
    :members:
