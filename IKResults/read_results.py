#Read motion file

import pandas as pd
df = pd.read_csv('ik_tiny_file.mot', sep='\t',skiprows=6) 