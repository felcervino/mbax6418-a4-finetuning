# G1 spot-check sheet (from data/split_data.zip, IDs are filtered_index)

- train: n=900, unique=900, min=1010, max=19975, classes={'NEUTRAL': 300, 'POSITIVE': 300, 'NEGATIVE': 300}, first 8 ids in file order=[2114, 5555, 6660, 11005, 4447, 16700, 8849, 2359]
- val: n=300, unique=300, min=20000, max=25135, classes={'POSITIVE': 100, 'NEUTRAL': 100, 'NEGATIVE': 100}, first 8 ids in file order=[20000, 20001, 20002, 20003, 20004, 20005, 20006, 20007]
- test: n=300, unique=300, min=30000, max=35859, classes={'POSITIVE': 100, 'NEUTRAL': 100, 'NEGATIVE': 100}, first 8 ids in file order=[30000, 30001, 30002, 30003, 30004, 30007, 30009, 30010]
- overlap train and val: 0
- overlap train and test: 0
- overlap val and test: 0

To check yourself: open data/split_data.zip, count lines in each jsonl, count reference_label values, and compare sets of filtered_index.
