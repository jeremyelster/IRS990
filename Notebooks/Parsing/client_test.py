import pandas as pd
import numpy as np
import os
import sys
sys.path.append("../../")
import irsparser as irs

# Runtime
client = irs.Client(
    local_data_dir="../../data", ein_filename="eins",
    index_years=[2018], save_xml=False,
    parser="propublica")
client.parse_xmls(add_organization_info=True)
df = client.getFinalDF()
print(df.columns)
print(df.head())
