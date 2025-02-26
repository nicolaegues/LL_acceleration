"""
Basic Python Lebwohl-Lasher code.  Based on the paper 
P.A. Lebwohl and G. Lasher, Phys. Rev. A, 6, 426-429 (1972).
This version in 2D.

Run at the command line by typing:

python LebwohlLasher_numpy.py <ITERATIONS> <SIZE> <TEMPERATURE> <PLOTFLAG> 

where:
  ITERATIONS = number of Monte Carlo steps, where 1MCS is when each cell
      has attempted a change once on average (i.e. SIZE*SIZE attempts)
  SIZE = side length of square lattice
  TEMPERATURE = reduced temperature in range 0.0 - 2.0.
  PLOTFLAG = 0 for no plot, 1 for energy plot and 2 for angle plot.
  
The initial configuration is set at random. The boundaries
are periodic throughout the simulation.  During the
time-stepping, an array containing two domains is used; these
domains alternate between old data and new data.

SH 16-Oct-23
"""



import sys
import time
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd


#=======================================================================
def initdat(nmax):
    """
    Arguments:
      nmax (int) = size of lattice to create (nmax,nmax).
    Description:
      Function to create and initialise the main data array that holds
      the lattice.  Will return a square lattice (size nmax x nmax)
	  initialised with random orientations in the range [0,2pi].
	Returns:
	  arr (float(nmax,nmax)) = array to hold lattice.
    """
    arr = np.random.random_sample((nmax,nmax))*2.0*np.pi
    return arr
#=======================================================================
def plotdat(arr,pflag,nmax):
    """
    Arguments:
	  arr (float(nmax,nmax)) = array that contains lattice data;
	  pflag (int) = parameter to control plotting;
      nmax (int) = side length of square lattice.
    Description:
      Function to make a pretty plot of the data array.  Makes use of the
      quiver plot style in matplotlib.  Use pflag to control style:
        pflag = 0 for no plot (for scripted operation);
        pflag = 1 for energy plot;
        pflag = 2 for angles plot;
        pflag = 3 for black plot.
	  The angles plot uses a cyclic color map representing the range from
	  0 to pi.  The energy plot is normalised to the energy range of the
	  current frame.
	Returns:
      NULL
    """
    if pflag==0:
        return
    u = np.cos(arr)
    v = np.sin(arr)
    x = np.arange(nmax)
    y = np.arange(nmax)
    if pflag==1: # colour the arrows according to energy
        mpl.rc('image', cmap='rainbow')
        cols = one_energy_vec(arr)
        norm = plt.Normalize(cols.min(), cols.max())
    elif pflag==2: # colour the arrows according to angle
        mpl.rc('image', cmap='hsv')
        cols = arr%np.pi
        norm = plt.Normalize(vmin=0, vmax=np.pi)
    else:
        mpl.rc('image', cmap='gist_gray')
        cols = np.zeros_like(arr)
        norm = plt.Normalize(vmin=0, vmax=1)

    quiveropts = dict(headlength=0,pivot='middle',headwidth=1,scale=1.1*nmax)
    fig, ax = plt.subplots()
    q = ax.quiver(x, y, u, v, cols,norm=norm, **quiveropts)
    ax.set_aspect('equal')
    plt.show()  
#=======================================================================

def plotdep(energy, order, nsteps, temp): 
    """
    Function to plot the evolution of energy and order parameter over Monte Carlo steps.

    Argumentss:
        energy (np.ndarray): Array containing energy values at each Monte Carlo step.
        order (np.ndarray): Array containing order parameter values at each Monte Carlo step.
        nsteps (int): Number of Monte Carlo steps.
        temp (float): Reduced temperature (T*), used for labeling the plots.

    Returns:
        None
    """
    
    x = np.arange(nsteps + 1)

    fig, axes = plt.subplots((2), figsize = (7, 9))
    axes[0].plot(x, energy, color = "black")
    axes[0].set_ylabel("Reduced Energy U/ε")
    axes[1].plot(x, order, color = "black")
    axes[1].set_ylabel("Order Parameter, S")

    for ax in axes: 
        ax.set_title(f"Reduced Temperature, T* = {temp}")
        ax.set_xlabel("MCS")
    
    current_datetime = datetime.datetime.now().strftime("%a-%d-%b-%Y-at-%I-%M-%S%p")
    plt.savefig(f"vs_MCS_plot_{current_datetime}")
    plt.show()
    
#=======================================================================

def savedat(arr,nsteps,Ts,runtime,ratio,energy,order,nmax):
    """
    Arguments:
	  arr (float(nmax,nmax)) = array that contains lattice data;
	  nsteps (int) = number of Monte Carlo steps (MCS) performed;
	  Ts (float) = reduced temperature (range 0 to 2);
	  ratio (float(nsteps)) = array of acceptance ratios per MCS;
	  energy (float(nsteps)) = array of reduced energies per MCS;
	  order (float(nsteps)) = array of order parameters per MCS;
      nmax (int) = side length of square lattice to simulated.
    Description:
      Function to save the energy, order and acceptance ratio
      per Monte Carlo step to text file.  Also saves run data in the
      header.  Filenames are generated automatically based on
      date and time at beginning of execution.
	Returns:
	  NULL
    """
    # Create filename based on current date and time.
    current_datetime = datetime.datetime.now().strftime("%a-%d-%b-%Y-at-%I-%M-%S%p")
    filename = "LL-Output-{:s}.txt".format(current_datetime)
    FileOut = open(filename,"w")
    # Write a header with run parameters
    print("#=====================================================",file=FileOut)
    print("# File created:        {:s}".format(current_datetime),file=FileOut)
    print("# Size of lattice:     {:d}x{:d}".format(nmax,nmax),file=FileOut)
    print("# Number of MC steps:  {:d}".format(nsteps),file=FileOut)
    print("# Reduced temperature: {:5.3f}".format(Ts),file=FileOut)
    print("# Run time (s):        {:8.6f}".format(runtime),file=FileOut)
    print("#=====================================================",file=FileOut)
    print("# MC step:  Ratio:     Energy:   Order:",file=FileOut)
    print("#=====================================================",file=FileOut)
    # Write the columns of data
    for i in range(nsteps+1):
        print("   {:05d}    {:6.4f} {:12.4f}  {:6.4f} ".format(i,ratio[i],energy[i],order[i]),file=FileOut)
    FileOut.close()
#=======================================================================

def test_equal(curr_energy): 
    """
    Compares the computed energy values with a reference dataset.

    Arguments:
        curr_energy (np.ndarray): Array containing the newly computed energy values.

    Returns:
        None (prints a message saying whether the energy values match the original dataset).
    """

    og_energy = np.loadtxt("OG_output.txt", usecols=(2,))

    curr_energy = np.round(curr_energy.astype(float), 4)

    are_equal = np.array_equal(og_energy, curr_energy)

    if are_equal: 
        print("The new energy values are the same as the original energy values - all good!")
    else: 
        print("The energy values differ from the original - something may have gone wrong. ")

#=======================================================================


def one_energy_vec(arr): 
    """
    Arguments:
      arr (float(nmax,nmax)) = array that contains lattice data;
      Description:
        Function that computes the energy of a single cell of the
        lattice taking into account periodic boundaries.  Working with
        reduced energy (U/epsilon), equivalent to setting epsilon=1 in
        equation (1) in the project notes.
    Returns:
      en (float) = reduced energy of cell.
    """
    
    ang_ixp = arr - np.roll(arr, shift=-1, axis=0)
    ang_ixm = arr - np.roll(arr, shift=1, axis=0)
    ang_iyp = arr - np.roll(arr, shift=-1, axis=1)
    ang_iym = arr - np.roll(arr, shift=1, axis=1)
#
# Add together the 4 neighbour contributions
# to the energy
#

    en = 0.5*(1.0 - 3.0*np.cos(ang_ixp)**2) 
    en += 0.5*(1.0 - 3.0*np.cos(ang_ixm)**2) 
    en += 0.5*(1.0 - 3.0*np.cos(ang_iyp)**2) 
    en += 0.5*(1.0 - 3.0*np.cos(ang_iym)**2)

    return en
#=======================================================================
def all_energy(arr):
    """
    Arguments:
	  arr (float(nmax,nmax)) = array that contains lattice data;
      
    Description:
      Function to compute the energy of the entire lattice. Output
      is in reduced units (U/epsilon).
	Returns:
	  enall (float) = reduced energy of lattice.
    """
    
    enall = np.sum(one_energy_vec(arr))
    return enall
#=======================================================================
def get_order(arr,nmax):
    """
    Arguments:
	  arr (float(nmax,nmax)) = array that contains lattice data;
      nmax (int) = side length of square lattice.
    Description:
      Function to calculate the order parameter of a lattice
      using the Q tensor approach, as in equation (3) of the
      project notes.  Function returns S_lattice = max(eigenvalues(Q_ab)).
	Returns:
	  max(eigenvalues(Qab)) (float) = order parameter for lattice.
    """
    delta = np.eye(3,3)
    #
    # Generate a 3D unit vector for each cell (i,j) and
    # put it in a (3,i,j) array.
    #
    lab = np.vstack((np.cos(arr),np.sin(arr),np.zeros_like(arr))).reshape(3,nmax,nmax)

    Qab = np.einsum('aij,bij->ab', lab, lab)* 3 - nmax**2 *delta
    #follows general pattern of: np.einsum('input_indices->output_indices', tensor1, tensor2)
    #summing over i, j: which is why i and j appear in input but not output

    Qab = Qab/(2*nmax*nmax)
    eigenvalues,eigenvectors = np.linalg.eig(Qab)

    return eigenvalues.max()
#=======================================================================
def mc_vec_diagonals(arr, aran, boltz_random, Ts, mask):
      """
    Performs Monte Carlo updates on a subset of lattice sites (checkerboard diagonals).

    Arguments:
        arr (np.ndarray): 2D array representing the lattice with angle values.
        aran (np.ndarray): 2D array of proposed random angle changes.
        boltz_random (np.ndarray): 2D array of random values for Metropolis criterion.
        Ts (float): Reduced temperature (T*), controlling acceptance probability.
        mask (np.ndarray): Boolean mask indicating which lattice sites to update.

    Returns:
        int: The number of accepted updates.
        """

      en0 = one_energy_vec(arr)[mask]

      arr[mask] += aran[mask]

      en1 = one_energy_vec(arr)[mask]

      boltz = np.exp( -(en1 - en0) / Ts )
      accept_mask = (en1 <= en0) | (boltz >= boltz_random[mask])

      final_cells = arr[mask]
      final_cells[ ~accept_mask] -= aran[mask][ ~accept_mask]

      arr[mask] = final_cells

      accept = np.sum(accept_mask)

      return accept

def MC_step(arr,Ts,nmax):
    """
    Arguments:
	  arr (float(nmax,nmax)) = array that contains lattice data;
	  Ts (float) = reduced temperature (range 0 to 2);
      nmax (int) = side length of square lattice.
    Description:
      Function to perform one MC step, which consists of an average
      of 1 attempted change per lattice site.  Working with reduced
      temperature Ts = kT/epsilon.  Function returns the acceptance
      ratio for information.  This is the fraction of attempted changes
      that are successful.  Generally aim to keep this around 0.5 for
      efficient simulation.
	Returns:
	  accept/(nmax**2) (float) = acceptance ratio for current MCS.
    """
    #
    # Pre-compute some random numbers.  This is faster than
    # using lots of individual calls.  "scale" sets the width
    # of the distribution for the angle changes - increases
    # with temperature.
    scale=0.1+Ts
    accept = 0

    grid_indices = np.indices((nmax, nmax))
    aran = np.random.normal(scale=scale, size=(nmax,nmax))
    boltz_random = np.random.uniform(0.0,1.0, size = (nmax, nmax))
    

    #mask for first ("white") set of diagonals of a checkerboard
    diag_mask_1 = grid_indices.sum(axis = 0) % 2 == 0

    #mask for second ("black") set of diagonals of checkerboard
    diag_mask_2 = ~diag_mask_1


    accept += mc_vec_diagonals(arr, aran, boltz_random, Ts, diag_mask_1)
    accept += mc_vec_diagonals(arr, aran, boltz_random, Ts, diag_mask_2)

    return accept/(nmax*nmax)


#=======================================================================
def main(program, nsteps, nmax, temp, pflag):
  
          
    """
    Arguments:
    program (string) = the name of the program;
    nsteps (int) = number of Monte Carlo steps (MCS) to perform;
      nmax (int) = side length of square lattice to simulate;
    temp (float) = reduced temperature (range 0 to 2);
    pflag (int) = a flag to control plotting.
    Description:
      This is the main function running the Lebwohl-Lasher simulation.
    Returns:
      NULL
    """
  
    np.random.seed(seed=42)
   
    # Create and initialise lattice
    lattice = initdat(nmax)
    # Plot initial frame of lattice
    plotdat(lattice,pflag,nmax)
    # Create arrays to store energy, acceptance ratio and order parameter
    energy = np.zeros(nsteps+1)
    ratio = np.zeros(nsteps+1)
    order = np.zeros(nsteps+1)
    # Set initial values in arrays
    energy[0] = all_energy(lattice)
    ratio[0] = 0.5 # ideal value
    order[0] = get_order(lattice,nmax)

    # Begin doing and timing some MC steps.
    initial = time.time()
    for it in range(1,nsteps+1):
        ratio[it] = MC_step(lattice,temp,nmax)
        energy[it] = all_energy(lattice)
        order[it] = get_order(lattice,nmax)

    final = time.time()
    runtime = final-initial


    # Create and initialise lattice
    lattice = initdat(nmax)
    # Plot initial frame of lattice
    plotdat(lattice,pflag,nmax)
    # Create arrays to store energy, acceptance ratio and order parameter
    energy = np.zeros(nsteps+1)
    ratio = np.zeros(nsteps+1)
    order = np.zeros(nsteps+1)
    # Set initial values in arrays
    energy[0] = all_energy(lattice)
    ratio[0] = 0.5 # ideal value
    order[0] = get_order(lattice,nmax)

    # Begin doing and timing some MC steps.
    initial = time.time()
    for it in range(1,nsteps+1):
        ratio[it] = MC_step(lattice,temp,nmax)
        energy[it] = all_energy(lattice)
        order[it] = get_order(lattice,nmax)

    final = time.time()
    runtime = final-initial
    #print(nmax)

  

    print("{}: Size: {:d}, Steps: {:d}, T*: {:5.3f}: Order: {:5.3f}, Mean ratio : {:5.3f}, Time: {:8.6f} s".format(program, nmax,nsteps, temp,order[nsteps-1], np.mean(ratio), runtime))
    # Plot final frame of lattice and generate output file
    #savedat(lattice,nsteps,temp,runtime,ratio,energy,order,nmax)
    #plotdat(lattice,pflag,nmax)
    #plotdep(energy, order, nsteps, temp)
    #test_equal(energy)
#=======================================================================
# Main part of program, getting command line arguments and calling
# main simulation function.


if __name__ == '__main__':
    if int(len(sys.argv)) == 5:
        PROGNAME = sys.argv[0]
        ITERATIONS = int(sys.argv[1])
        SIZE = int(sys.argv[2])
        TEMPERATURE = float(sys.argv[3])
        PLOTFLAG = int(sys.argv[4])
        main(PROGNAME, ITERATIONS, SIZE, TEMPERATURE, PLOTFLAG)
    else:
        print("Usage: python {} <ITERATIONS> <SIZE> <TEMPERATURE> <PLOTFLAG>".format(sys.argv[0]))
# #=======================================================================
#main("prog", 1000, 20, 0.65, 0, 1)
