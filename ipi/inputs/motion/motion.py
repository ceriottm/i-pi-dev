"""Deals with creating the ensembles class.

Copyright (C) 2013, Joshua More and Michele Ceriotti

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http.//www.gnu.org/licenses/>.


Classes:
   InputEnsemble: Deals with creating the Ensemble object from a file, and
      writing the checkpoints.
"""

import numpy as np
import ipi.engine.initializer
from ipi.engine.motion import Motion, Dynamics, Replay, GeopMover, NEBMover
from ipi.utils.inputvalue import *
from ipi.inputs.thermostats import *
from ipi.inputs.initializer import *
from .geop import InputGeop
from .neb import InputNEB
from .dynamics import InputDynamics
from ipi.inputs.phonons import InputDynMatrix
from ipi.engine.phonons import  DynMatrixMover
from ipi.utils.units import *

__all__ = ['InputMotion']

class InputMotion(Input):
   """Motion calculation input class.

   A class to encompass the different "motion" (non-MD) calculations.

   Attributes:
      mode: An optional string giving the kind of motion calculation to be performed.

   Fields:
      fixcom: An optional boolean which decides whether the centre of mass
         motion will be constrained or not. Defaults to False.
      fixatoms: A list of the indices of atoms that should not be moved.

   """

   attribs={"mode"  : (InputAttribute, {"dtype"   : str,
                                    "help"    : "How atoms should be moved at each step in the simulatio. 'replay' means that a simulation is restarted from a previous simulation.",
                                    "options" : ['calcphonons', 'minimize', 'replay', 'neb', 'dynamics',  'dummy']}) }
   fields={"fixcom": (InputValue, {"dtype"           : bool,
                                   "default"         : True,
                                   "help"            : "This describes whether the centre of mass of the particles is fixed."}),
           "fixatoms" : (InputArray, {"dtype"        : int,
                                    "default"      : np.zeros(0,int),
                                    "help"         : "Indices of the atmoms that should be held fixed."}),
           "optimizer" : ( InputGeop, { "default" : {},
                                     "help":  "Option for geometry optimization" } ),
           "neb_optimizer" : ( InputGeop, { "default" : {},
                                     "help":  "Option for geometry optimization" } ),
           "dynamics" : ( InputDynamics, { "default" : {},
                                     "help":  "Option for (path integral) molecular dynamics" } ),
           "file": (InputInitFile, {"default" : input_default(factory=ipi.engine.initializer.InitBase,kwargs={"mode":"xyz"}),
                           "help"            : "This describes the location to read a trajectory file from."}),
           "calculator" : ( InputDynMatrix, { "default" : {}, 
                                     "help":  "Option for calculating force constant matrix" } )
         }

   dynamic = {  }

   default_help = "Holds all the information that is calculation specific, such as geometry optimization parameters, etc."
   default_label = "MOTION"

   def store(self, sc):
      """Takes a motion calculation instance and stores a minimal representation of it.

      Args:
         sc: A motion calculation class.
      """

      super(InputMotion, self).store(sc)
      tsc = -1
      if type(sc) is Motion:
          self.mode.store("dummy")
      elif type(sc) is Replay:
         self.mode.store("replay")
         tsc = 0
      elif type(sc) is GeopMover:
         self.mode.store("minimize")
         self.optimizer.store(sc)
         tsc = 1
      elif type(sc) is NEBMover:
         self.mode.store("neb")
         self.neb_optimizer.store(sc)
         tsc = 1
      elif type(sc) is Dynamics:
         self.mode.store("dynamics")
         self.dynamics.store(sc)
         tsc = 1   
      elif type(sc) is DynMatrixMover:
         self.mode.store("calcphonons")
         self.calculator.store(sc)
         tsc = 1   
      else: 
         raise ValueError("Cannot store Mover calculator of type "+str(type(sc)))
      
      if tsc == 0:
         self.file.store(sc.intraj)
      elif tsc > 0:
         self.fixcom.store(sc.fixcom)
         self.fixatoms.store(sc.fixatoms)

   def fetch(self):
      """Creates a motion calculator object.

      Returns:
         An ensemble object of the appropriate mode and with the appropriate
         objects given the attributes of the InputEnsemble object.
      """

      super(InputMotion, self).fetch()

      if self.mode.fetch() == "replay":
         sc = Replay(fixcom=self.fixcom.fetch(), fixatoms=self.fixatoms.fetch(), intraj=self.file.fetch())
      elif self.mode.fetch() == "minimize":
         sc = GeopMover(fixcom=self.fixcom.fetch(), fixatoms=self.fixatoms.fetch(), **self.optimizer.fetch())
      elif self.mode.fetch() == "neb":
         sc = NEBMover(fixcom=self.fixcom.fetch(), fixatoms=self.fixatoms.fetch(), **self.neb_optimizer.fetch())
      elif self.mode.fetch() == "dynamics":
         sc = Dynamics(fixcom=self.fixcom.fetch(), fixatoms=self.fixatoms.fetch(), **self.dynamics.fetch())
      elif self.mode.fetch() == "calcphonons":
         sc = DynMatrixMover(fixcom=self.fixcom.fetch(), fixatoms=self.fixatoms.fetch(), **self.calculator.fetch() )
      else:
         sc = Motion()
         #raise ValueError("'" + self.mode.fetch() + "' is not a supported motion calculation mode.")

      return sc
