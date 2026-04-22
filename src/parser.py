from asammdf import MDF
import pandas as pd 

file_path = "data/sample.MF4"

mdf = MDF(file_path)

df = mdf.to_dataframe()

print(df.head(5))