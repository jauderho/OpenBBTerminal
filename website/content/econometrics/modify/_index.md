```
usage: load [-f FILE [FILE ...]] [-h]
```

Modify a dataset by adding, removing or renaming columns. This also has the possibility to combine DataFrames together.

`--add` can be used to create new columns for your dataset. It can use any operator and allows for creating specific 
dummy variables or ratios. For example: `modify -a debt_ratio-dataset debt-dataset div assets-dataset2` will create a 
new column with the name 'debt_ratio' which is the 'debt' column divided by the 'assets' column.

`--delete` allows you to remove any column from your dataset. For example `modify -d debt-thesis assets-thesis`

`--combine` makes it possible to add a column to a different dataset. For example: `modify -c stock_prices close-tsla close-aapl close-googl`

`--rename` changes the name of a column of a dataset. For example: `modify -r fundamentals debt_copy debt`
```
optional arguments:
  -a ADD ADD ADD ADD, --add ADD ADD ADD ADD
                        Add columns to your dataframe with the option to use formulas. Use format: <column>-<dataset> <column-dataset> <sign> <criteria or column-dataset>. Two examples: high_revenue-thesis revenue-thesis > 1000 or
                        debt_ratio-dataset debt-dataset div assets-dataset2 (default: None)
  -d DELETE [DELETE ...], --delete DELETE [DELETE ...]
                        The columns you want to delete from a dataset. Use format: <column-dataset>. (default: None)
  -c COMBINE [COMBINE ...], --combine COMBINE [COMBINE ...]
                        The columns you want to add to a dataset, the first argument is the dataset that you wish to place these columns in. Use format: <dataset> <column-dataset2> <column-<dataset3> (default: None)
  -r RENAME RENAME RENAME, --rename RENAME RENAME RENAME
                        The columns you want to rename from a dataset. Use format: dataset OLD_COLUMN NEW_COLUMN (default: None)
  -h, --help            show this help message (default: False)
```

Example:
```
2022 Feb 24, 05:01 (✨) /econometrics/ $ show thesis
                                                                                            thesis                                                                                            
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃                                                                   ┃ current_assets ┃ assets   ┃ debt     ┃ depr_amor ┃ income ┃ current_liabilities ┃ revenue ┃ equity  ┃ interest_expense ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ ('AAR Corp', Timestamp('2016-01-01 00:00:00'))                    │ 970.70         │ 1522.00  │ 160.00   │ 18.50     │ 9.90   │ 359.70              │ 412.10  │ 858.30  │ 1.70             │
├───────────────────────────────────────────────────────────────────┼────────────────┼──────────┼──────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┤
│ ('AAR Corp', Timestamp('2016-04-01 00:00:00'))                    │ 873.10         │ 1442.10  │ 136.10   │ 17.80     │ 11.80  │ 329.00              │ 468.60  │ 865.80  │ 1.20             │
├───────────────────────────────────────────────────────────────────┼────────────────┼──────────┼──────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┤
│ ('AAR Corp', Timestamp('2017-07-01 00:00:00'))                    │ 904.70         │ 1531.70  │ 189.00   │ 10.20     │ 11.00  │ 312.10              │ 397.90  │ 924.70  │ 1.70             │
├───────────────────────────────────────────────────────────────────┼────────────────┼──────────┼──────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┤
│ ('AAR Corp', Timestamp('2017-10-01 00:00:00'))                    │ 892.20         │ 1544.30  │ 215.80   │ 10.60     │ 13.30  │ 336.50              │ 420.60  │ 906.50  │ 1.90             │
├───────────────────────────────────────────────────────────────────┼────────────────┼──────────┼──────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┤
│ ('AAR Corp', Timestamp('2018-01-01 00:00:00'))                    │ 933.60         │ 1512.20  │ 194.30   │ 10.60     │ 31.30  │ 326.60              │ 456.30  │ 915.20  │ 2.20             │
├───────────────────────────────────────────────────────────────────┼────────────────┼──────────┼──────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┤
│ ('AAR Corp', Timestamp('2018-04-01 00:00:00'))                    │ 942.70         │ 1524.70  │ 177.20   │ 9.10      │ 18.10  │ 333.30              │ 473.50  │ 936.30  │ 2.20             │
├───────────────────────────────────────────────────────────────────┼────────────────┼──────────┼──────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┤
│ ('AAR Corp', Timestamp('2018-07-01 00:00:00'))                    │ 982.40         │ 1537.80  │ 209.10   │ 10.10     │ 18.90  │ 315.10              │ 466.30  │ 929.10  │ 2.10             │
├───────────────────────────────────────────────────────────────────┼────────────────┼──────────┼──────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┤
│ ('AAR Corp', Timestamp('2018-10-01 00:00:00'))                    │ 1040.70        │ 1604.20  │ 218.90   │ 10.40     │ 11.20  │ 344.20              │ 493.30  │ 935.60  │ 2.50             │
├───────────────────────────────────────────────────────────────────┼────────────────┼──────────┼──────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┤
│ ('AAR Corp', Timestamp('2019-01-01 00:00:00'))                    │ 993.40         │ 1546.50  │ 177.20   │ 10.80     │ 27.40  │ 359.60              │ 529.50  │ 899.40  │ 2.60             │
├───────────────────────────────────────────────────────────────────┼────────────────┼──────────┼──────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┤
│ ('American Airlines Group Inc', Timestamp('2016-01-01 00:00:00')) │ 10802.00       │ 49909.00 │ 19134.00 │ 423.00    │ 700.00 │ 15277.00            │ 9435.00 │ 4710.00 │ 250.00           │
└───────────────────────────────────────────────────────────────────┴────────────────┴──────────┴──────────┴───────────┴────────┴─────────────────────┴─────────┴─────────┴──────────────────┘
```
```
2022 Feb 24, 05:08 (✨) /econometrics/ $ modify -a debt_ratio-thesis debt-thesis div assets-thesis

2022 Feb 24, 05:08 (✨) /econometrics/ $ modify -d debt-thesis assets-thesis

2022 Feb 24, 05:10 (✨) /econometrics/ $ modify -c thesis debt-thesis2

2022 Feb 24, 05:11 (✨) /econometrics/ $ modify -r thesis revenue GAINS
```
```
2022 Feb 24, 05:11 (✨) /econometrics/ $ show thesis
                                                                                               thesis                                                                                               
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃                                                                   ┃ current_assets ┃ depr_amor ┃ income ┃ current_liabilities ┃ GAINS   ┃ equity  ┃ interest_expense ┃ debt_ratio ┃ debt_thesis2 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ ('AAR Corp', Timestamp('2016-01-01 00:00:00'))                    │ 970.70         │ 18.50     │ 9.90   │ 359.70              │ 412.10  │ 858.30  │ 1.70             │ 0.11       │ 160.00       │
├───────────────────────────────────────────────────────────────────┼────────────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┼────────────┼──────────────┤
│ ('AAR Corp', Timestamp('2016-04-01 00:00:00'))                    │ 873.10         │ 17.80     │ 11.80  │ 329.00              │ 468.60  │ 865.80  │ 1.20             │ 0.09       │ 136.10       │
├───────────────────────────────────────────────────────────────────┼────────────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┼────────────┼──────────────┤
│ ('AAR Corp', Timestamp('2017-07-01 00:00:00'))                    │ 904.70         │ 10.20     │ 11.00  │ 312.10              │ 397.90  │ 924.70  │ 1.70             │ 0.12       │ 189.00       │
├───────────────────────────────────────────────────────────────────┼────────────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┼────────────┼──────────────┤
│ ('AAR Corp', Timestamp('2017-10-01 00:00:00'))                    │ 892.20         │ 10.60     │ 13.30  │ 336.50              │ 420.60  │ 906.50  │ 1.90             │ 0.14       │ 215.80       │
├───────────────────────────────────────────────────────────────────┼────────────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┼────────────┼──────────────┤
│ ('AAR Corp', Timestamp('2018-01-01 00:00:00'))                    │ 933.60         │ 10.60     │ 31.30  │ 326.60              │ 456.30  │ 915.20  │ 2.20             │ 0.13       │ 194.30       │
├───────────────────────────────────────────────────────────────────┼────────────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┼────────────┼──────────────┤
│ ('AAR Corp', Timestamp('2018-04-01 00:00:00'))                    │ 942.70         │ 9.10      │ 18.10  │ 333.30              │ 473.50  │ 936.30  │ 2.20             │ 0.12       │ 177.20       │
├───────────────────────────────────────────────────────────────────┼────────────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┼────────────┼──────────────┤
│ ('AAR Corp', Timestamp('2018-07-01 00:00:00'))                    │ 982.40         │ 10.10     │ 18.90  │ 315.10              │ 466.30  │ 929.10  │ 2.10             │ 0.14       │ 209.10       │
├───────────────────────────────────────────────────────────────────┼────────────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┼────────────┼──────────────┤
│ ('AAR Corp', Timestamp('2018-10-01 00:00:00'))                    │ 1040.70        │ 10.40     │ 11.20  │ 344.20              │ 493.30  │ 935.60  │ 2.50             │ 0.14       │ 218.90       │
├───────────────────────────────────────────────────────────────────┼────────────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┼────────────┼──────────────┤
│ ('AAR Corp', Timestamp('2019-01-01 00:00:00'))                    │ 993.40         │ 10.80     │ 27.40  │ 359.60              │ 529.50  │ 899.40  │ 2.60             │ 0.11       │ 177.20       │
├───────────────────────────────────────────────────────────────────┼────────────────┼───────────┼────────┼─────────────────────┼─────────┼─────────┼──────────────────┼────────────┼──────────────┤
│ ('American Airlines Group Inc', Timestamp('2016-01-01 00:00:00')) │ 10802.00       │ 423.00    │ 700.00 │ 15277.00            │ 9435.00 │ 4710.00 │ 250.00           │ 0.38       │ 19134.00     │
└───────────────────────────────────────────────────────────────────┴────────────────┴───────────┴────────┴─────────────────────┴─────────┴─────────┴──────────────────┴────────────┴──────────────┘
```