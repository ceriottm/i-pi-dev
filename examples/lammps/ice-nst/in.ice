units		electron
atom_style	full

pair_style	lj/cut/coul/long 17.01
#pair_style      lj/cut/tip4p/long 1 2 1 1 0.278072379 17.
#bond_style      harmonic
bond_style      class2 
angle_style     harmonic
kspace_style	ewald 0.0001

read_data	data.ice
pair_coeff  * * 0 0
pair_coeff  1  1  0.000295147 5.96946

neighbor	2.0 bin

timestep	0.00025

#velocity all create 298.0 2345187

#thermo_style	multi
#thermo		1

#fix		1 all nvt temp 298.0 298.0 30.0 tchain 1
#fix 1 all nve
fix 1 all driver lammps_ice 32345 unix

#dump		1 all xyz 25 dump.xyz

run		100000000

