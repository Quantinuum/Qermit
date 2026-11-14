qermit.frame_randomisation
==========================

Frame randomisation samples logically equivalent circuits with different
single-qubit frames and combines their counts into one result per original
experiment. Averaging the variants can change the effective noise channel;
whether this improves an estimate depends on the device's noise and the chosen
randomisation scheme.

Offline example
------------------------------

This local Aer example prepares ``|11>`` and combines four Pauli-frame samples.
It needs no hardware account. The ideal outcome stays the same across the
randomised circuits.

.. jupyter-execute::

    from math import ceil
    from pytket import Circuit
    from pytket.extensions.qiskit import AerBackend
    from qermit import CircuitShots
    from qermit.frame_randomisation import (
        FrameRandomisation, gen_Frame_Randomisation_MitRes,
    )

    circuit = Circuit(2).X(0).CX(0, 1).measure_all()
    shots = 101
    samples = 4
    mitigation = gen_Frame_Randomisation_MitRes(
        AerBackend(),
        samples=samples,
        frame_randomisation=FrameRandomisation.PauliFrameRandomisation,
    )
    result = mitigation.run([CircuitShots(circuit, shots)])[0]
    counts = result.get_counts()
    expected_shots = samples * ceil(shots / samples)
    assert counts[(1, 1)] == expected_shots
    assert sum(counts.values()) == expected_shots
    print({"counts": dict(counts), "executed_shots": expected_shots})

Shot allocation and scheme choice
------------------------------------

Each sampled circuit receives ``ceil(shots / samples)`` shots. The example
therefore executes 104 shots, rather than exactly 101. Choose a shot count
divisible by ``samples`` when an exact total budget is needed. Increasing
``samples`` also increases the number of circuit submissions, even when the
total shot budget remains similar.

The explicit Pauli choice above uses Pauli-frame randomisation. The default is
``UniversalFrameRandomisation``, which rebases the circuit into a single cycle
and additionally assumes comparable noise for ``Rz(x)`` and ``Rz(-x)``. Check that
the chosen scheme's assumptions suit the target device.

The returned ``MitRes`` aggregates counts; expectation-value experiments can
compose it into a ``MitEx`` workflow. The noiseless example checks the logical
action and shot accounting. It does not measure a hardware error reduction.

API reference
------------------------------

.. autofunction:: qermit.frame_randomisation.frame_randomisation.gen_Frame_Randomisation_MitRes

.. autoclass:: qermit.frame_randomisation.frame_randomisation.FrameRandomisation
    :members:
    :special-members:

.. autofunction:: qermit.frame_randomisation.frame_randomisation.frame_randomisation_circuits_task_gen

.. autofunction:: qermit.frame_randomisation.frame_randomisation.frame_randomisation_result_task_gen
