#!/usr/bin/env python 
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Modelon AB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Tests the casadi_collocation module."""

import os
import nose

import numpy as N
import pylab as P

from jmodelica.tests import testattr
from jmodelica.tests import get_files_path
from jmodelica.io import ResultDymolaTextual
from jmodelica.examples import *

try:
    from jmodelica.optimization.casadi_collocation import *
    from jmodelica.casadi_interface import compile_casadi, CasadiModel
except NameError, ImportError:
    pass
    #logging.warning('Could not load Casadi collocation. Check jmodelica.check_packages()')

try:
    try:
        from IPython.Debugger import Tracer; dh = Tracer()
    except ImportError:
        try:
            from IPython.core.debugger import Tracer; dh = Tracer()
        except:
            logging.warning('Could not find IPython debugger module')
except AttributeError:
    # Circumvents trouble when running the tests through MSYS
    pass

path_to_mos = os.path.join(get_files_path(), 'Modelica')

def assert_results(res, cost_ref, u_norm_ref,
                   cost_rtol=1e-3, u_norm_rtol=1e-4):
    """Helper function for asserting optimization results."""
    cost = float(res.solver.solver.output(casadi.NLP_COST))
    u = res["u"]
    u_norm = N.linalg.norm(u) / N.sqrt(len(u))
    N.testing.assert_allclose(cost, cost_ref, cost_rtol)
    N.testing.assert_allclose(u_norm, u_norm_ref, u_norm_rtol)

class TestRadau:
    
    """
    Tests jmodelica.optimization.casadi_collocation.RadauCollocator.
    """
    
    @classmethod
    def setUpClass(cls):
        """Compile the test models."""
        file_path = os.path.join(get_files_path(), 'Modelica', 'VDP.mop')
        class_path = "VDP_pack.VDP_Opt2"
        compile_casadi(class_path, file_path)
        
    def setUp(self):
        """Load the test models."""
        JMU_VDP = 'VDP_pack_VDP_Opt2.jmu'
        self.model_VDP = CasadiModel(JMU_VDP)
    
    @testattr(casadi = True)
    def test_VDP(self):
        """Test optimizing the VDP using default options."""
        opts = self.model_VDP.optimize_options(algorithm="CasadiRadau")
        res = self.model_VDP.optimize(algorithm="CasadiRadau", options=opts)
        assert_results(res, 2.3469089e1, 2.872384555575e-1)
        
    @testattr(casadi = True)
    def test_init_traj(self):
        """Test optimizing the VDP based on an existing optimization reult."""
        opts = self.model_VDP.optimize_options(algorithm="CasadiRadau")
        opts['n_e'] = 30
        opts['n_cp'] = 3
        res = self.model_VDP.optimize(algorithm="CasadiRadau", options=opts)
        
        opts['n_e'] = 100
        opts['init_traj'] = ResultDymolaTextual("VDP_pack_VDP_Opt2_result.txt")
        res = self.model_VDP.optimize(algorithm="CasadiRadau", options=opts)

class TestRadau2:
    
    """
    Tests jmodelica.optimization.casadi_collocation.Radau2Collocator.
    
    The models used for testing are based on the VDP oscillator and CSTR.
    """
    
    @classmethod
    def setUpClass(cls):
        """Compile the test models."""
        file_path = os.path.join(get_files_path(), 'Modelica', 'VDP.mop')
        class_path = "VDP_pack.VDP_Opt_Bounds_Lagrange"
        compile_casadi(class_path, file_path)
        
        file_path = os.path.join(get_files_path(), 'Modelica', 'VDP.mop')
        class_path = "VDP_pack.VDP_Opt_Bounds_Mayer"
        compile_casadi(class_path, file_path)
        
        file_path = os.path.join(get_files_path(), 'Modelica', 'VDP.mop')
        class_path = "VDP_pack.VDP_Opt_Constraints_Mayer"
        compile_casadi(class_path, file_path)
        
        file_path = os.path.join(get_files_path(), 'Modelica', 'CSTR.mop')
        class_path = "CSTR.CSTR_Opt_Bounds_Lagrange"
        compile_casadi(class_path, file_path)
        
        file_path = os.path.join(get_files_path(), 'Modelica', 'CSTR.mop')
        class_path = "CSTR.CSTR_Opt_Bounds_Mayer"
        compile_casadi(class_path, file_path)
    
    def setUp(self):
        """Load the test models."""
        JMU_VDP_bounds_Lagrange = 'VDP_pack_VDP_Opt_Bounds_Lagrange.jmu'
        self.model_VDP_bounds_Lagrange = CasadiModel(JMU_VDP_bounds_Lagrange)
        
        JMU_VDP_bounds_Mayer = 'VDP_pack_VDP_Opt_Bounds_Mayer.jmu'
        self.model_VDP_bounds_Mayer = CasadiModel(JMU_VDP_bounds_Mayer)
        
        JMU_VDP_constraints_Mayer = 'VDP_pack_VDP_Opt_Constraints_Mayer.jmu'
        self.model_VDP_constraints_Mayer = CasadiModel(
                JMU_VDP_constraints_Mayer)
        
        JMU_CSTR_Lagrange = "CSTR_CSTR_Opt_Bounds_Lagrange.jmu"
        self.model_CSTR_Lagrange = CasadiModel(JMU_CSTR_Lagrange)
        self.model_CSTR_scaled_Lagrange = CasadiModel(JMU_CSTR_Lagrange,
                                                      enable_scaling=True)
        
        JMU_CSTR_Mayer = "CSTR_CSTR_Opt_Bounds_Mayer.jmu"
        self.model_CSTR_Mayer = CasadiModel(JMU_CSTR_Mayer)
        
        self.algorithm = "CasadiRadau2"
    
    @testattr(casadi = True)
    def test_init_traj(self):
        """Test optimizing based on an existing optimization reult."""
        model = self.model_VDP_bounds_Mayer
        
        opts = model.optimize_options(self.algorithm)
        opts['n_e'] = 40
        opts['n_cp'] = 2
        res = model.optimize(self.algorithm, opts)
        assert_results(res, 2.8626448086446e0, 2.86716530287e-1)
        
        opts['n_e'] = 75
        opts['n_cp'] = 4
        opts['init_traj'] = ResultDymolaTextual("VDP_pack_VDP_Opt2_result.txt")
        res = model.optimize(self.algorithm, opts)
        assert_results(res, 2.8731453441917e0, 2.79651683022e-1)
        
    @testattr(casadi = True)
    def test_CSTR_Mayer_and_Lagrange(self):
        """Test the CSTR with both Mayer and Lagrange costs."""
        Mayer_model = self.model_CSTR_Mayer
        Lagrange_model = self.model_CSTR_Lagrange
        
        # References values
        cost_ref = 1.8576873858261e3
        u_norm_ref = 3.0556730059e2
        
        # Mayer
        opts = Mayer_model.optimize_options(self.algorithm)
        res = Mayer_model.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref)
        
        # Lagrange
        res = Lagrange_model.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref)
        
    @testattr(casadi = True)
    def test_path_constraints(self):
        """Test a simple path constraint with and without exact Hessian."""
        model = self.model_VDP_constraints_Mayer
        
        # References values
        cost_ref = 5.273481330869811e0
        u_norm_ref = 3.2936323844551e-1
        
        # Without exact Hessian
        opts = model.optimize_options(self.algorithm)
        opts['exact_Hessian'] = False
        res = model.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref)
        
        # With exact Hessian
        opts['exact_Hessian'] = True
        res = model.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref)
    
    @testattr(casadi = True)
    def test_element_lengths(self):
        """Test non-uniformly distributed elements."""
        model = self.model_VDP_bounds_Mayer
        opts = model.optimize_options(self.algorithm)
        opts['n_e'] = 23
        opts['hs'] = (4 * [0.01] + 2 * [0.05] + 10 * [0.02] + 5 * [0.02] + 
                     2 * [0.28])
        res = model.optimize(self.algorithm, opts)
        assert_results(res, 2.8725837143130e0, 3.23454473152e-1)
    
    @testattr(casadi = True)
    def test_free_element_lengths(self):
        """Test optimized element lengths with both result modes."""
        model = self.model_VDP_bounds_Mayer
        
        # References values
        cost_ref = 3.927658955199e0
        u_norm_ref = 3.800349369066e-1
        
        # Free element lengths data
        c = 0.5
        Q = N.eye(3)
        bounds = (0.5, 2.0)
        free_ele_data = FreeElementLengthData(c, Q, bounds)
        
        # Set options shared by both result modes
        opts = model.optimize_options(self.algorithm)
        opts['n_e'] = 20
        opts['hs'] = "free"
        opts['free_element_lengths_data'] = free_ele_data
        
        # Collocation points
        opts['result_mode'] = "collocation_points"
        res = model.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref)
        indices = range(1, 4) + range(opts['n_e'] - 3, opts['n_e'])
        values = N.array([0.5, 0.5, 0.5, 2.0, 2.0, 2.0]).reshape([-1, 1])
        N.testing.assert_allclose(res.h_opt[indices], values, 5e-3)
        
        # Element interpolation
        opts['result_mode'] = "element_interpolation"
        res = model.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref, u_norm_rtol=3e-2)
        
    @testattr(casadi = True)
    def test_scaling(self):
        """
        Test optimizing the CSTR with scaling.

        This test also tests writing both the unscaled and scaled result as
        well as eliminating derivative variables.
        """
        unscaled_model = self.model_CSTR_Lagrange
        scaled_model = self.model_CSTR_scaled_Lagrange
        
        # References values
        cost_ref = 1.8576873858261e3
        u_norm_ref = 3.0556730059e2
        
        # Unscaled model, with derivatives
        opts = unscaled_model.optimize_options(self.algorithm)
        opts['write_scaled_result'] = False
        opts['eliminate_der_var'] = False
        res = unscaled_model.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref)

        # Scaled model & unscaled result, eliminated derivatives
        opts['write_scaled_result'] = False
        opts['eliminate_der_var'] = True
        res = scaled_model.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref)
        c_unscaled = res['cstr.c']

        # Scaled model & scaled result, eliminated derivatives
        opts['write_scaled_result'] = True
        opts['eliminate_der_var'] = True
        res = scaled_model.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref)
        c_scaled = res['cstr.c']
        N.testing.assert_allclose(c_unscaled, 1000. * c_scaled,
                                  rtol=0, atol=1e-5)
    
    @testattr(casadi = True)
    def test_result_mode(self):
        """
        Test the two different result modes.
        
        The difference between the trajectories of the two result modes should
        be very small if n_e * n_cp is sufficiently large. Eliminating
        derivative variables is also tested for element interpolation.
        """
        model = self.model_VDP_bounds_Lagrange
        
        # References values
        cost_ref = 2.8731453597567e0
        u_norm_ref = 2.794322054089e-1
        
        # Collocation points
        opts = model.optimize_options(self.algorithm)
        opts['n_e'] = 100
        opts['n_cp'] = 5
        opts['result_mode'] = "collocation_points"
        res = model.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref)
        
        # Element interpolation
        opts['result_mode'] = "element_interpolation"
        opts['eliminate_der_var'] = True
        opts['n_eval_points'] = 15
        res = model.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref, u_norm_rtol=5e-3)
    
    @testattr(casadi = True)
    def test_blocking_factors(self):
        """Test blocking factors."""
        model = self.model_VDP_bounds_Lagrange
        
        opts = model.optimize_options(self.algorithm)
        opts['n_e'] = 40
        opts['n_cp'] = 3
        opts['blocking_factors'] = opts['n_e'] * [1]
        res = model.optimize(self.algorithm, opts)
        assert_results(res, 2.9414928549335e0, 2.830653018537e-1,
                       cost_rtol=1.5e-1, u_norm_rtol=5e-2)
        
        opts['n_e'] = 20
        opts['n_cp'] = 4
        opts['blocking_factors'] = [1, 2, 1, 1, 2, 13]
        res = model.optimize(self.algorithm, opts)
        assert_results(res, 8.3561931655395, 4.57767608709e-1,
                       cost_rtol=1.5e-1, u_norm_rtol=5e-2)
    
    @testattr(casadi = True)
    def test_eliminate_der_var(self):
        """
        Test that results are consistent regardless of eliminate_der_var.
        """
        model_Mayer = self.model_VDP_bounds_Mayer
        model_Lagrange = self.model_VDP_bounds_Lagrange
        
        # References values
        cost_ref = 2.8730955269669685e0
        u_norm_ref = 2.80098775976e-1
        
        # Keep derivative variables
        opts = model_Lagrange.optimize_options(self.algorithm)
        opts["eliminate_der_var"] = False
        res = model_Lagrange.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref)
        
        # Mayer, eliminate derivative variables
        # Currently does not work due to lack of support for Mayer
        #~ opts["eliminate_der_var"] = True
        #~ opts['init_traj'] = ResultDymolaTextual("VDP_pack_VDP_Opt2_result.txt")
        #~ res = model_Mayer.optimize(self.algorithm, opts)
        #~ assert_results(res, cost_ref, u_norm_ref)
        
        # Lagrange, eliminate derivative variables
        opts["eliminate_der_var"] = True
        opts['init_traj'] = ResultDymolaTextual("VDP_pack_VDP_Opt2_result.txt")
        res = model_Lagrange.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref)
    
    @testattr(casadi = True)
    def test_eliminate_cont_var(self):
        """
        Test that results are consistent regardless of eliminate_cont_var.
        """
        model = self.model_VDP_bounds_Mayer
        
        # References values
        cost_ref = 2.8730955269669685e0
        u_norm_ref = 2.80098775976e-1
        
        # Keep continuity variables
        opts = model.optimize_options(self.algorithm)
        opts["eliminate_cont_var"] = False
        res = model.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref)
        
        # Eliminate continuity variables
        opts["eliminate_cont_var"] = True
        opts['init_traj'] = ResultDymolaTextual("VDP_pack_VDP_Opt2_result.txt")
        res = model.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref)
    
    @testattr(casadi = True)
    def test_n_cp(self):
        """
        Test varying n_e and n_cp.
        """
        model = self.model_VDP_bounds_Mayer
        opts = model.optimize_options(self.algorithm)
        
        # n_cp = 1
        opts['n_e'] = 100
        opts['n_cp'] = 1
        res = model.optimize(self.algorithm, opts)
        assert_results(res, 2.471555915589e0, 2.578857243e-1)
        
        # n_cp = 3
        opts['n_e'] = 50
        opts['n_cp'] = 3
        res = model.optimize(self.algorithm, opts)
        assert_results(res, 2.8730955269669e0, 2.800987759761e-1)
        
        # n_cp = 8
        opts['n_e'] = 20
        opts['n_cp'] = 8
        opts['init_traj'] = ResultDymolaTextual("VDP_pack_VDP_Opt2_result.txt")
        res = model.optimize(self.algorithm, opts)
        assert_results(res, 2.8731453593189755e0, 2.823304724e-1)
        
    @testattr(casadi = True)
    def test_graphs_and_exact_Hessian(self):
        """
        Test that results are consistent regardless of graph and exact_Hessian.
        
        The test also checks the elimination of derivative and continuity
        variables.
        """
        model = self.model_VDP_bounds_Lagrange
        
        # References values
        cost_ref = 2.87290424868901e0
        u_norm_ref = 2.800987759761e-1
        
        # Solve problem to get initialization trajectory
        opts = model.optimize_options(self.algorithm)
        res = model.optimize(self.algorithm, opts)
        assert_results(res, cost_ref, u_norm_ref)
        opts['init_traj'] = ResultDymolaTextual("VDP_pack_VDP_Opt2_result.txt")
        
        # SX with exact Hessian and eliminated variables
        opts['graph'] = "SX"
        opts['exact_Hessian'] = True
        opts['eliminate_der_var'] = True
        opts['eliminate_cont_var'] = True
        res = model.optimize(self.algorithm, opts)
        sol_with = res.times['sol']
        assert_results(res, cost_ref, u_norm_ref)
        
        # SX without exact Hessian and eliminated variables
        opts['exact_Hessian'] = False
        opts['eliminate_der_var'] = False
        opts['eliminate_cont_var'] = False
        res = model.optimize(self.algorithm, opts)
        sol_without = res.times['sol']
        nose.tools.assert_true(sol_with < 0.5 * sol_without)
        assert_results(res, cost_ref, u_norm_ref)
        
        # expanded_MX with exact Hessian and eliminated variables
        opts['graph'] = "expanded_MX"
        opts['exact_Hessian'] = True
        opts['eliminate_der_var'] = True
        opts['eliminate_cont_var'] = True
        res = model.optimize(self.algorithm, opts)
        sol_with = res.times['sol']
        assert_results(res, cost_ref, u_norm_ref)
        
        # expanded_MX without exact Hessian and eliminated variables
        opts['exact_Hessian'] = False
        opts['eliminate_der_var'] = False
        opts['eliminate_cont_var'] = False
        res = model.optimize(self.algorithm, opts)
        sol_without = res.times['sol']
        nose.tools.assert_true(sol_with < 0.5 * sol_without)
        assert_results(res, cost_ref, u_norm_ref)
        
        # MX with exact Hessian and eliminated variables
        opts['graph'] = "MX"
        opts['exact_Hessian'] = True
        opts['eliminate_der_var'] = True
        opts['eliminate_cont_var'] = True
        res = model.optimize(self.algorithm, opts)
        sol_with = res.times['sol']
        assert_results(res, cost_ref, u_norm_ref)
        
        # MX without exact Hessian and eliminated variables
        opts['exact_Hessian'] = False
        opts['eliminate_der_var'] = False
        opts['eliminate_cont_var'] = False
        res = model.optimize(self.algorithm, opts)
        sol_without = res.times['sol']
        nose.tools.assert_true(sol_with < 0.9 * sol_without)
        assert_results(res, cost_ref, u_norm_ref)
        
    @testattr(casadi = True)
    def test_CasADi_option(self):
        """
        Test the CasADi option numeric_jacobian.
        """
        model = self.model_VDP_bounds_Mayer
        
        # References values
        cost_ref = 2.87290424868901e0
        u_norm_ref = 2.800987759761e-1
        
        # numeric_jacobian = True
        opts = model.optimize_options(self.algorithm)
        opts['CasADi_options_G']['numeric_jacobian'] = True
        res = model.optimize(self.algorithm, opts)
        sol_with = res.times['sol']
        assert_results(res, cost_ref, u_norm_ref)
        
        # numeric_jacobian = False
        opts['CasADi_options_G']['numeric_jacobian'] = False
        res = model.optimize(self.algorithm, opts)
        sol_without = res.times['sol']
        nose.tools.assert_true(sol_without < 0.95 * sol_with)
        assert_results(res, cost_ref, u_norm_ref)

class TestPseudoSpectral:
    
    """
    Tests jmodelica.optimization.casadi_collocation.PseudoSpectral.
    """
    
    @classmethod
    def setUpClass(cls):
        """Compile the test models."""
        file_path = os.path.join(get_files_path(), 'Modelica', 'VDP.mop')
        class_path = "VDP_pack.VDP_Opt2"
        compile_casadi(class_path, file_path)
        
        file_path = os.path.join(get_files_path(), 'Modelica', 'TwoState.mop')
        class_path = "TwoState"
        compile_casadi(class_path, file_path)
    
    def setUp(self):
        """Load the test models."""
        JMU_VDP = 'VDP_pack_VDP_Opt2.jmu'
        self.model_VDP = CasadiModel(JMU_VDP)
        
        JMU_two_state = 'TwoState.jmu'
        self.model_two_state = CasadiModel(JMU_two_state)
    
    @testattr(casadi = True)
    def test_two_state(self):
        """Tests the different discretization on the TwoState example."""
        opts = self.model_two_state.optimize_options("CasadiPseudoSpectral")
        opts['n_e'] = 1
        opts['n_cp'] = 30
                
        #Test LG points
        opts['discr'] = "LG"
        res = self.model_two_state.optimize(algorithm="CasadiPseudoSpectral",
                                            options=opts)
        y1 = res["y1"]
        y2 = res["y2"]
        u = res["u"]
        time = res["time"]
        nose.tools.assert_almost_equal(y1[-1], 0.5000000000, places=5)
        nose.tools.assert_almost_equal(y2[-1], 1.124170946790, places=5)
        nose.tools.assert_almost_equal(u[-1], 0.498341205247, places=5)
        
        #Test LGR points
        opts['discr'] = "LGR"
        res = self.model_two_state.optimize(algorithm="CasadiPseudoSpectral",
                                            options=opts)
        y1 = res["y1"]
        y2 = res["y2"]
        u = res["u"]
        time = res["time"]
        nose.tools.assert_almost_equal(y1[-1], 0.5000000000, places=5)
        nose.tools.assert_almost_equal(y2[-1], 1.124170946790, places=5)
        nose.tools.assert_almost_equal(u[-1], 0.498341205247, places=5)
        
        #Test LGL points
        opts['discr'] = "LGL"
        res = self.model_two_state.optimize(algorithm="CasadiPseudoSpectral",
                                            options=opts)
        y1 = res["y1"]
        y2 = res["y2"]
        u = res["u"]
        time = res["time"]
        nose.tools.assert_almost_equal(y1[-1], 0.5000000000, places=5)
        nose.tools.assert_almost_equal(y2[-1], 1.124170946790, places=5)
        nose.tools.assert_almost_equal(u[-1], 0.498341205247, places=5)
    
    @testattr(casadi = True)
    def test_two_state_init_traj(self):
        """
        Tests that the option init_traj is functional.
        
        NOTE: SHOULD ALSO TEST THAT THE NUMBER OF ITERATIONS SHOULD BE SMALLER.
        """
        opts = self.model_two_state.optimize_options("CasadiPseudoSpectral")
        opts['n_e'] = 1
        opts['n_cp'] = 30
        opts['discr'] = "LG"
        res = self.model_two_state.optimize(algorithm="CasadiPseudoSpectral",
                                            options=opts)

        #Test LG points
        opts['discr'] = "LG"
        opts['init_traj'] = ResultDymolaTextual("TwoState_result.txt")
        res = self.model_two_state.optimize(algorithm="CasadiPseudoSpectral",
                                            options=opts)
        y1 = res["y1"]
        y2 = res["y2"]
        u = res["u"]
        time = res["time"]
        nose.tools.assert_almost_equal(y1[-1], 0.5000000000, places=5)
        nose.tools.assert_almost_equal(y2[-1], 1.124170946790, places=5)
        nose.tools.assert_almost_equal(u[-1], 0.498341205247, places=5)
        
        #Test LGL points
        opts['discr'] = "LGL"
        opts['init_traj'] = ResultDymolaTextual("TwoState_result.txt")
        res = self.model_two_state.optimize(algorithm="CasadiPseudoSpectral",
                                            options=opts)
        y1 = res["y1"]
        y2 = res["y2"]
        u = res["u"]
        time = res["time"]
        nose.tools.assert_almost_equal(y1[-1], 0.5000000000, places=5)
        nose.tools.assert_almost_equal(y2[-1], 1.124170946790, places=5)
        nose.tools.assert_almost_equal(u[-1], 0.498341205247, places=5)
        
        #Test LGR points
        opts['discr'] = "LGR"
        opts['init_traj'] = ResultDymolaTextual("TwoState_result.txt")
        res = self.model_two_state.optimize(algorithm="CasadiPseudoSpectral",
                                            options=opts)
        y1 = res["y1"]
        y2 = res["y2"]
        u = res["u"]
        time = res["time"]
        nose.tools.assert_almost_equal(y1[-1], 0.5000000000, places=5)
        nose.tools.assert_almost_equal(y2[-1], 1.124170946790, places=5)
        nose.tools.assert_almost_equal(u[-1], 0.498341205247, places=5)
    
    @testattr(casadi = True)
    def test_doubleintegrator(self):
        """Tests the different discretization on the DoubleIntegrator example."""
        
        """
        UNCOMMENT WHEN FREE TIME HAVE BEEN FIXED!!!
        
        jn = compile_casadi("DoubleIntegrator", os.path.join(path_to_mos,"DoubleIntegrator.mop"))
        VDP = CasadiModel(jn)
        
        opts = VDP.optimize_options("CasadiPseudoSpectral")
        opts['n_e'] = 8
        opts['n_cp'] = 5
                
        #Test LG points
        opts['discr'] = "LG"
        res = VDP.optimize(algorithm="CasadiPseudoSpectral", options=opts)
        y1 = res["x1"]
        y2 = res["x2"]
        u = res["u"]
        time = res["time"]
        nose.tools.assert_almost_equal(y1[-1], 0.00000000, places=5)
        nose.tools.assert_almost_equal(y2[-1], 0.00000000, places=5)
        nose.tools.assert_almost_equal(u[-1], 1.000000000, places=5)
        
        #Test LGR points
        opts['discr'] = "LGR"
        res = VDP.optimize(algorithm="CasadiPseudoSpectral", options=opts)
        y1 = res["x1"]
        y2 = res["x2"]
        u = res["u"]
        time = res["time"]
        nose.tools.assert_almost_equal(y1[-1], 0.00000000, places=5)
        nose.tools.assert_almost_equal(y2[-1], 0.00000000, places=5)
        nose.tools.assert_almost_equal(u[-1], 1.000000000, places=5)
        #Test LGL points
        opts['discr'] = "LGL"
        res = VDP.optimize(algorithm="CasadiPseudoSpectral", options=opts)
        y1 = res["x1"]
        y2 = res["x2"]
        u = res["u"]
        time = res["time"]
        nose.tools.assert_almost_equal(y1[-1], 0.00000000, places=5)
        nose.tools.assert_almost_equal(y2[-1], 0.00000000, places=5)
        nose.tools.assert_almost_equal(u[-1], 1.000000000, places=5)
        
        """
        
    @testattr(casadi = True)
    def test_VDP(self):
        """Tests the different discretization options on a modified VDP."""
        opts = self.model_VDP.optimize_options("CasadiPseudoSpectral")
        opts['n_e'] = 1
        opts['n_cp'] = 60
        
        #Test LG points
        opts['discr'] = "LG"
        res = self.model_VDP.optimize(algorithm="CasadiPseudoSpectral",
                                      options=opts)
        cost = res["cost"]
        nose.tools.assert_almost_equal(cost[-1], 2.3463724e1, places=1)
        
        #Test LGR points
        opts['discr'] = "LGR"
        res = self.model_VDP.optimize(algorithm="CasadiPseudoSpectral",
                                      options=opts)
        cost = res["cost"]
        nose.tools.assert_almost_equal(cost[-1], 2.3463724e1, places=1)
        
        #Test LGL points
        opts['discr'] = "LGL"
        res = self.model_VDP.optimize(algorithm="CasadiPseudoSpectral",
                                      options=opts)
        cost = res["cost"]
        nose.tools.assert_almost_equal(cost[-1], 2.3463724e1, places=1)
        """
        opts['n_e'] = 20
        opts['n_cp'] = 6
        
        #Test LG points
        opts['discr'] = "LG"
        res = VDP.optimize(algorithm="CasadiPseudoSpectral", options=opts)
        cost = res["cost"]
        nose.tools.assert_almost_equal(cost[-1], 2.3463724e1, places=1)
        
        #Test LGR points
        opts['discr'] = "LGR"
        res = VDP.optimize(algorithm="CasadiPseudoSpectral", options=opts)
        cost = res["cost"]
        nose.tools.assert_almost_equal(cost[-1], 2.3463724e1, places=1)
        
        #Test LGL points
        opts['discr'] = "LGL"
        res = VDP.optimize(algorithm="CasadiPseudoSpectral", options=opts)
        cost = res["cost"]
        nose.tools.assert_almost_equal(cost[-1], 2.3463724e1, places=1)
        """
