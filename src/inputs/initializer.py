"""Deals with creating the initiliazer class.

Classes:
   InputInitializer: Initializes the classes that initialize the simulation
      data.
   InputInitFile: Initializes the classes that initialize the simulation data
      from a file.
"""
import numpy as np
from utils.inputvalue import *
from copy import copy, deepcopy
from inputs.beads import InputBeads
from inputs.cell import InputCell
from utils.io import io_xml
import utils.mathtools as mt
import engine.initializer as ei
from utils.messages import verbosity, warning

__all__ = ['InputInitializer', 'InputInitFile', 'InputInitPositions', 'InputInitMomenta', 'InputInitVelocities', 'InputInitMasses', 'InputInitLabels', 'InputInitCell']

class InputInitBase(InputValue):
   """Base class to handle input.

   Attributes:

   """

   attribs = deepcopy(InputValue.attribs)
   attribs["mode"] =     (InputAttribute,{ "dtype" : str, "default": "other", "help": "The input file format. 'xyz' and 'pdb' stand for xyz and pdb input files respectively. 'chk' and 'checkpoint' are both aliases for input from a restart file.", "options": None } )

   default_label = "INITBASE"
   default_help = "This is the base class for initialization. Initializers for different aspects of the simulation can be inherit for it for the base methods."

   _initclass    = ei.InitBase
   _storageclass = float

   def __init__(self, help=None, default=None, dtype=None, options=None, dimension=None):
      """Initializes InputInitFile.

      Just calls the parent initialize function with appropriate arguments.
      """

      super(InputInitBase,self).__init__(dtype=str, dimension=dimension, default=default, options=options, help=help)

   def store(self, ibase):
      """Takes a InitBase instance and stores a minimal representation of it.

      Args:
         ibase: An input base object.
      """

      if ibase.mode == "manual":
         if hasattr(value, __len__):
            value = io_xml.write_list(ibase.value)
         else:  # if it's a single value then just write the value
            value = io_xml.write_type(self._storageclass, ibase.value)
      else:  # just store the value as a string
         value = ibase.value

      super(InputInitBase,self).store(value, units=ibase.units)

      for k in self.attribs:  # store additional attributes from the input class
         self.__dict__[k].store(ibase.__dict__[k])

   def getval(self):
      value = super(InputInitBase,self).fetch()
      if self.mode.fetch() == "manual":
         if '[' in value and ']' in value: # value appears to be a list
            if self._storageclass is float:
               value = io_xml.read_array(np.float, value)
            else:
               value = io_xml.read_list(value)
         else:
            value = io_xml.read_type(self._storageclass, value)
      else:
         value = str(value)  # typically this will be a no-op
      return value

   def fetch(self, initclass=None):
      """Creates an input base object.

      Returns:
         An input base object.
      """

      rdict = {}
      for k in self.attribs:
         rdict[k] = self.__dict__[k].fetch()

      if initclass is None: # allows for some flexibility in return class
         initclass = self._initclass

      return initclass(value=self.getval(), **rdict)


class InputInitFile(InputInitBase):
   attribs = deepcopy(InputInitBase.attribs)
   attribs["mode"][1]["default"] = "chk"
   attribs["mode"][1]["options"] = ["xyz", "pdb", "chk"]

   default_label = "INITFILE"
   default_help = "This is the class to initialize from file."


class InputInitIndexed(InputInitBase):

   attribs = deepcopy(InputInitBase.attribs)
   attribs["index"] =     (InputAttribute,{ "dtype" : int, "default": -1, "help": "The index of the atom of which we are to set the coordinate." } )
   attribs["bead"]  =     (InputAttribute,{ "dtype" : int, "default": -1, "help": "The index of the bead of which we are to set the coordinate." } )

   default_label = "INITINDEXED"
   default_help = "This is a helper class to initialize with an index."


class InputInitPositions(InputInitIndexed):

   attribs = deepcopy(InputInitIndexed.attribs)
   attribs["mode"][1]["default"] = "chk"
   attribs["mode"][1]["options"] = ["manual", "xyz", "pdb", "chk"]

   default_label = "INITPOSITIONS"
   default_help = "This is the class to initialize positions."
   _initclass = ei.InitIndexed


class InputInitMomenta(InputInitPositions):

   attribs = deepcopy(InputInitPositions.attribs)
   attribs["mode"][1]["options"].append( "thermal" )

   default_label = "INITMOMENTA"
   default_help = "This is the class to initialize momenta."

   def fetch(self):
      if self.mode.fetch() == "thermal":
         return self._initclass(value=float(InputValue.fetch(self)),  mode=self.mode.fetch(), units=self.units.fetch(), index=self.index.fetch(), bead=self.bead.fetch())
      else:
         return super(InputInitMomenta,self).fetch()


class InputInitVelocities(InputInitMomenta):

   attribs = deepcopy(InputInitMomenta.attribs)
   #attribs["mode"][1]["options"].append( "thermal" )

   default_label = "INITVELOCITIES"
   default_help = "This is the class to initialize velocities."


class InputInitMasses(InputInitPositions):

   attribs = deepcopy(InputInitPositions.attribs)
   #attribs["mode"][1]["options"]= ['manual', 'xyz', 'pdb', 'chk']

   default_label = "INITMASSES"
   default_help = "This is the class to initialize atomic masses."


class InputInitLabels(InputInitPositions):

   attribs = deepcopy(InputInitPositions.attribs)

   default_label = "INITLABELS"
   default_help = "This is the class to initialize atomic labels."

   _storageclass = str


class InputInitCell(InputInitBase):

   attribs = deepcopy(InputInitBase.attribs)
   attribs["mode"] = (InputAttribute, { "dtype"  : str,
                                        "default": "manual",
                                        "options": ["manual", "pdb", "chk", "abc", "abcABC"],
                                        "help"   : "This decides whether the system box is created from a cell parameter matrix, or from the side lengths and angles between them. If 'mode' is 'manual', then 'cell' takes a 9-elements vector containing the cell matrix (row-major). If 'mode' is 'abcABC', then 'cell' takes an array of 6 floats, the first three being the length of the sides of the system parallelopiped, and the last three being the angles (in degrees) between those sides. Angle A corresponds to the angle between sides b and c, and so on for B and C. If mode is 'abc', then this is the same as ffor 'abcABC', but the cell is assumed to be orthorhombic. 'pdb' and 'chk' read the cell from a PDB or a checkpoint file, respectively."} )

   default_label = "INITCELL"
   default_help = "This is the class to initialize cell."

   def fetch(self):

      mode = self.mode.fetch()

      ibase = super(InputInitCell,self).fetch()
      if mode == "abc" or mode == "abcABC":

         h = io_xml.read_array(np.float, ibase.value)

         if mode == "abc":
            if h.size != 3:
               raise ValueError("If you are initializing cell from cell side lengths you must pass the 'cell' tag an array of 3 floats.")
            else:
               h = mt.abc2h(h[0], h[1], h[2], np.pi/2, np.pi/2, np.pi/2)
         elif mode == "abcABC":
            if h.size != 6:
               raise ValueError("If you are initializing cell from cell side lengths and angles you must pass the 'cell' tag an array of 6 floats.")
            else:
               h = mt.abc2h(h[0], h[1], h[2], h[3]*np.pi/180.0, h[4]*np.pi/180.0, h[5]*np.pi/180.0)

         h.shape = (9,)
         ibase.value = h
         mode = "manual"

      if mode == "manual":
         h = ibase.value
         if h.size != 9:
               raise ValueError("Cell objects must contain a 3x3 matrix describing the cell vectors.")

         if not (h[3] == 0.0 and h[6] == 0.0 and h[7] == 0.0):
            warning("Cell vector matrix must be upper triangular, all elements below the diagonal being set to zero.", verbosity.low)
            h[3] = h[6] = h[7] = 0
         ibase.value = h

      return self._initclass(value=ibase.value, mode=mode, units=self.units.fetch())


class InputInitializer(Input):
   """Input class to handle initialization.

   Attributes:
      nbeads: The number of beads to be used in the simulation.
      extra: A list of all the initialize objects read in dynamically from
         the xml input file.
   """

   attribs = { "nbeads"    : (InputAttribute, {"dtype"     : int,
                                        "help"      : "The number of beads. Will override any provision from inside the initializer. A ring polymer contraction scheme is used to scale down the number of beads if required. If instead the number of beads is scaled up, higher normal modes will be initialized to zero."})
            }

   dynamic = {
           "positions"  : (InputInitPositions,  { "help" : "Initializes atomic positions"}),
           "velocities" : (InputInitVelocities, { "help" : "Initializes atomic velocities" }),
           "momenta"    : (InputInitMomenta,    { "help" : "Initializes atomic momenta" }),
           "masses"     : (InputInitMasses,     { "help" : "Initializes atomic masses" }),
           "labels"     : (InputInitLabels,     { "help" : "Initializes atomic labels" }),
           "cell"       : (InputInitCell,       { "help" : "Initializes the configuration of the cell" }),
           "file"       : (InputInitFile,       { "help" : "Initializes everything possible for the given mode" }),

            }

   default_help = "Specifies the number of beads, and how the system should be initialized."
   default_label = "INITIALIZER"

   def write(self,  name="", indent=""):
      """Overloads Input write() function so that we never write out
      InputInitializer to restart files.

      Returns:
         An empty string.
      """

      return ""

   def store(self, ii):
      """Takes a Initializer instance and stores a minimal representation of it.

      Args:
         iif: An initializer object.
      """

      self.extra = []

      for (k, el) in ii.queue:
         if k == "positions" :
            ip = InputInitPositions()
            ip.store(el)
         elif k == "velocities" :
            ip = InputInitVelocities()
            ip.store(el)
         elif k == "momenta" :
            ip = InputInitMomenta()
            ip.store(el)
         elif k == "masses" :
            ip = InputInitMasses()
            ip.store(el)
         elif k == "labels" :
            ip = InputInitLabels()
            ip.store(el)
         elif k == "cell" :
            ip = InputInitCell()
            ip.store(el)
         self.extra.append((k, ip))

      self.nbeads.store(ii.nbeads)

   def fetch(self):
      """Creates an initializer object.

      Returns:
         An initializer object.
      """

      super(InputInitializer,self).fetch()

      initlist = []
      for (k,v) in self.extra:
         if k == "file":
            mode = v.mode.fetch()
            if mode == "xyz" or mode == "manual" or mode == "pdb" or mode == "chk":
               initlist.append( ( "positions", v.fetch(initclass=ei.InitIndexed) ) )
            if mode == "xyz" or mode == "pdb" or mode == "chk":
               rm = v.fetch(initclass=ei.InitIndexed)
               rm.units = ""
               initlist.append( ( "masses",   rm ) )
               initlist.append( ( "labels",   v.fetch(initclass=ei.InitIndexed) ) )
            if mode == "pdb" or mode == "chk":
               initlist.append( ( "cell", v.fetch(initclass=ei.InitIndexed) ) )
            if mode == "chk":
               rm = v.fetch(initclass=ei.InitIndexed)
               rm.units = ""
               initlist.append( ( "momenta", rm ) )
         else:
            initlist.append( (k, v.fetch()) )

      return ei.Initializer(self.nbeads.fetch(), initlist )
