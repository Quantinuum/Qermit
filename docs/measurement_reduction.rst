qermit.measurement_reduction
============================

Measurement reduction groups Pauli terms that can be measured with the same
circuit. The resulting ``MitEx`` returns the same per-term expectation
contributions as an ordinary ``MitEx``, using fewer measurement settings when
the observable permits grouping.

Offline example
------------------------------

``Z0``, ``Z1`` and ``Z0 Z1`` share a computational-basis measurement. On the
state ``|10>``, the observable ``2 Z0 + 3 Z1 + 4 Z0 Z1`` has expectation -3.
This example uses the local Aer simulator and requires no hardware account.

.. jupyter-execute::

    import numpy as np
    from pytket import Circuit, Qubit
    from pytket.extensions.qiskit import AerBackend
    from pytket.partition import PauliPartitionStrat
    from pytket.pauli import Pauli, QubitPauliString
    from pytket.utils import QubitPauliOperator
    from qermit import (
        AnsatzCircuit, ObservableExperiment, ObservableTracker, SymbolsDict,
    )
    from qermit.taskgraph.measurement_reduction import gen_MeasurementReduction_MitEx

    terms = [
        QubitPauliString(Qubit(0), Pauli.Z),
        QubitPauliString(Qubit(1), Pauli.Z),
        QubitPauliString([Qubit(0), Qubit(1)], [Pauli.Z, Pauli.Z]),
    ]
    observable = QubitPauliOperator(dict(zip(terms, [2.0, 3.0, 4.0])))
    experiment = ObservableExperiment(
        AnsatzCircuit(Circuit(2).X(0), 1000, SymbolsDict()),
        ObservableTracker(observable),
    )
    mitigation = gen_MeasurementReduction_MitEx(
        AerBackend(), strategy=PauliPartitionStrat.NonConflictingSets,
    )
    result = mitigation.run([experiment])[0]
    contributions = [complex(result[term]).real for term in terms]
    assert np.allclose(contributions, [-2.0, 3.0, -4.0])
    print({"weighted_terms": contributions, "total": sum(contributions)})

The returned coefficients already contain the original observable weights:
they are -2, 3 and -4, rather than the unweighted Pauli expectations -1, 1 and -1.
Summing them gives the expectation of the whole observable.

Grouping and shot cost
------------------------------

``NonConflictingSets`` groups terms with compatible single-qubit measurement
bases. ``CommutingSets`` permits more general commuting groups, which can need
entangling basis-change gates. A reduction in measurement settings can therefore
trade off against extra circuit depth and hardware noise.

The shot count belongs to each measurement circuit, rather than to the entire
observable. In this example the three terms share one setting, so one group uses
1000 shots instead of three separate settings with 1000 shots each. Counts reused
across terms produce correlated estimates; compare schemes at a common total
shot budget when assessing uncertainty.

Measurement reduction controls how an observable is measured. It does not by
itself correct a device's noise, and it cannot group every set of Pauli terms
into a single setting.

API reference
------------------------------

.. currentmodule:: qermit.taskgraph.measurement_reduction

.. autofunction:: qermit.taskgraph.measurement_reduction.measurement_reduction_task_gen

.. autofunction:: qermit.taskgraph.measurement_reduction.gen_MeasurementReduction_MitEx

