import numpy, math
import engine, io_system, cell

class NST_ens(object):

   @classmethod
   def from_pdbfile(cls, filedesc, thermo, pot_func, temp = 1.0, dt = 0.1, **kwargs):
      cls.dt = dt
      cls.syst = engine.System.from_pdbfile(filedesc, temp)
      cls.pot_func = pot_func(cls.syst, **kwargs)
      cls.thermo = thermo(temp, dt/2.0)
      return cls()

   @classmethod
   def from_ensemble(cls, ens):
      cls.dt = ens.dt
      cls.syst = engine.System.from_system(ens.syst)
      cls.pot_func = ens.pot_func
      cls.thermo = ens.thermo
      return cls()

   def exp_p(self):
      dist_mat = self.syst.cell.p*self.dt/self.syst.cell.w
      eig = cell.compute_eigp(dist_mat)
      i_eig = cell.compute_ih(eig)
   
      exp_mat = numpy.zeros((3,3), float)
      neg_exp_mat = numpy.zeros((3,3), float)
      for i in range(3):
         exp_mat[i,i] = math.exp(self.syst.cell.p[i,i]*self.dt/self.syst.cell.w)
         neg_exp_mat[i,i] = math.exp(-self.syst.cell.p[i,i]*self.dt/self.syst.cell.w)
      
      exp_mat = numpy.dot(eig, exp_mat)
      exp_mat = numpy.dot(exp_mat, i_eig)
      
      neg_exp_mat = numpy.dot(eig, neg_exp_mat)
      neg_exp_mat = numpy.dot(neg_exp_mat, i_eig)

      return exp_mat, neg_exp_mat

   def thermo_step(self):
      for i in range(self.syst.natoms):
         self.thermo.step(self.syst.atoms[i])
     # self.thermo.step(syst.cell)

   def pos_step(self):
      """Takes the atom positions, velocities and forces and integrates the 
         equations of motion forward by a step dt"""

      #equivalent to R-step in paper

      exp_mat, neg_exp_mat = self.exp_p()
      sinh_mat = 0.5*(exp_mat - neg_exp_mat)
      ip_mat = cell.compute_ih(self.syst.cell.p/self.syst.cell.w)

      for i in range(self.syst.natoms):
         self.syst.atoms[i].q = numpy.dot(exp_mat, self.syst.atoms[i].q) + numpy.dot(ip_mat, numpy.dot(sinh_mat, self.syst.atoms[i].p/self.syst.atoms[i].mass))
         self.syst.atoms[i].p = numpy.dot(neg_exp_mat, self.syst.atoms[i].p)
      
      self.syst.cell.h = numpy.dot(exp_mat, self.syst.cell.h)

   def vel_step(self):
      #equivalent to P-step in paper
      pass

   def apply_pbc(self):
      """Takes the system and applies periodic boundary conditions to fold the
         particle positions back into the unit cell"""

      for i in range(self.syst.natoms):
         self.syst.atoms[i].q = self.syst.cell.apply_pbc(self.syst.atoms[i])

   def syst_update(self):
      self.pot_func.syst_update()
      self.syst.cell_pot = self.syst.cell.pot()
      self.syst.cell_kinetic = self.syst.cell.kinetic()
      self.syst.tot_E = self.syst.pot + self.syst.kinetic + self.syst.cell_pot + self.syst.cell_kinetic

   def simulation(self, maxcount = 5):
      self.syst_update()
      for i in range(maxcount):
         self.thermo_step()
         self.vel_step()
         self.pos_step()
         self.syst_update()
         self.vel_step()
         self.syst_update()
         self.thermo_step()
         self.syst_update()
      #   print self.syst
      for i in range(self.syst.natoms):
         self.apply_pbc()
      print self.syst
      io_system.print_pdb(self.syst.atoms, self.syst.cell)
