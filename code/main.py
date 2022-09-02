"""
The scripts creates all of the figures used in the Commentary.

scf_data_clean downloads the data from the Board of Governors website, defines
the relevant variables (income and networth quintiles etc).
scf_lifetime_wealth performs the lifetime wealth calculations.
scf_figures produces all of the figures. 
"""

import os
if not os.path.exists('../main/figures'):
    os.makedirs('../main/figures')

import scf_data_clean
import scf_figures
import scf_lifetime_wealth
