# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2018.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Test the Unroll3qOrMore pass"""
import numpy as np

from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit.circuit.library import CCXGate, RCCXGate
from qiskit.transpiler.passes import Unroll3qOrMore
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.quantum_info.operators import Operator
from qiskit.quantum_info.random import random_unitary
from qiskit.test import QiskitTestCase
from qiskit.extensions import UnitaryGate
from qiskit.transpiler import Target


class TestUnroll3qOrMore(QiskitTestCase):
    """Tests the Unroll3qOrMore pass, for unrolling all
    gates until reaching only 1q or 2q gates."""

    def test_ccx(self):
        """Test decompose CCX."""
        qr1 = QuantumRegister(2, "qr1")
        qr2 = QuantumRegister(1, "qr2")
        circuit = QuantumCircuit(qr1, qr2)
        circuit.ccx(qr1[0], qr1[1], qr2[0])
        dag = circuit_to_dag(circuit)
        pass_ = Unroll3qOrMore()
        after_dag = pass_.run(dag)
        op_nodes = after_dag.op_nodes()
        self.assertEqual(len(op_nodes), 15)
        for node in op_nodes:
            self.assertIn(node.name, ["h", "t", "tdg", "cx"])

    def test_cswap(self):
        """Test decompose CSwap (recursively)."""
        qr1 = QuantumRegister(2, "qr1")
        qr2 = QuantumRegister(1, "qr2")
        circuit = QuantumCircuit(qr1, qr2)
        circuit.cswap(qr1[0], qr1[1], qr2[0])
        dag = circuit_to_dag(circuit)
        pass_ = Unroll3qOrMore()
        after_dag = pass_.run(dag)
        op_nodes = after_dag.op_nodes()
        self.assertEqual(len(op_nodes), 17)
        for node in op_nodes:
            self.assertIn(node.name, ["h", "t", "tdg", "cx"])

    def test_decompose_conditional(self):
        """Test decompose a 3-qubit gate with a conditional."""
        qr = QuantumRegister(3, "qr")
        cr = ClassicalRegister(1, "cr")
        circuit = QuantumCircuit(qr, cr)
        circuit.ccx(qr[0], qr[1], qr[2]).c_if(cr, 0)
        dag = circuit_to_dag(circuit)
        pass_ = Unroll3qOrMore()
        after_dag = pass_.run(dag)
        op_nodes = after_dag.op_nodes()
        self.assertEqual(len(op_nodes), 15)
        for node in op_nodes:
            self.assertIn(node.name, ["h", "t", "tdg", "cx"])
            self.assertEqual(node.op.condition, (cr, 0))

    def test_decompose_unitary(self):
        """Test unrolling of unitary gate over 4qubits."""
        qr = QuantumRegister(4, "qr")
        circuit = QuantumCircuit(qr)
        unitary = random_unitary(16, seed=42)
        circuit.unitary(unitary, [0, 1, 2, 3])
        dag = circuit_to_dag(circuit)
        pass_ = Unroll3qOrMore()
        after_dag = pass_.run(dag)
        after_circ = dag_to_circuit(after_dag)
        self.assertTrue(Operator(circuit).equiv(Operator(after_circ)))

    def test_identity(self):
        """Test unrolling of identity gate over 3qubits."""
        qr = QuantumRegister(3, "qr")
        circuit = QuantumCircuit(qr)
        gate = UnitaryGate(np.eye(2**3))
        circuit.append(gate, range(3))
        dag = circuit_to_dag(circuit)
        pass_ = Unroll3qOrMore()
        after_dag = pass_.run(dag)
        after_circ = dag_to_circuit(after_dag)
        self.assertTrue(Operator(circuit).equiv(Operator(after_circ)))

    def test_target(self):
        """Test target is respected by the unroll 3q or more pass."""
        target = Target(num_qubits=3)
        target.add_instruction(CCXGate())
        qc = QuantumCircuit(3)
        qc.ccx(0, 1, 2)
        qc.append(RCCXGate(), [0, 1, 2])
        unroll_pass = Unroll3qOrMore(target=target)
        res = unroll_pass(qc)
        self.assertIn("ccx", res.count_ops())
        self.assertNotIn("rccx", res.count_ops())

    def test_basis_gates(self):
        """Test basis_gates are respected by the unroll 3q or more pass."""
        basis_gates = ["rccx"]
        qc = QuantumCircuit(3)
        qc.ccx(0, 1, 2)
        qc.append(RCCXGate(), [0, 1, 2])
        unroll_pass = Unroll3qOrMore(basis_gates=basis_gates)
        res = unroll_pass(qc)
        self.assertNotIn("ccx", res.count_ops())
        self.assertIn("rccx", res.count_ops())

    def test_target_over_basis_gates(self):
        """Test target is respected over basis_gates  by the unroll 3q or more pass."""
        target = Target(num_qubits=3)
        basis_gates = ["rccx"]
        target.add_instruction(CCXGate())
        qc = QuantumCircuit(3)
        qc.ccx(0, 1, 2)
        qc.append(RCCXGate(), [0, 1, 2])
        unroll_pass = Unroll3qOrMore(target=target, basis_gates=basis_gates)
        res = unroll_pass(qc)
        self.assertIn("ccx", res.count_ops())
        self.assertNotIn("rccx", res.count_ops())
