"""
Create all figures used in the Commentary.

NOTE: In December 2023 the Commentary was revised to correct an error in the
calculation of lifetime wealth. The original version erroneously dropped the future
households outside of the ages 26-60 and therefore underestimated lifetime wealth
for the youngest households. 

Because the Board of Governors updates summary dataset to be in the most recent
dollars, we also adjust for inflation to ensure that all figures are in 2019
dollars. This adjustment is "hard-coded" in "scf_data_clean" page 36 of the
Report found at https://www.federalreserve.gov/publications/files/scf23.pdf
"""

import os
if not os.path.exists('../main/figures'):
    os.makedirs('../main/figures')

import scf_data_clean
import scf_figures
import scf_lifetime_wealth
