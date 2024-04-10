# Laundromat

## Workflow

### Data Analysis

`git checkout data_analysis`

For each product create a directory `{product}_data_analysis`

Do any miscellaneous data analyses in that folder

### Writing an Algo

```
git checkout main
cd strategy
```

Write up strategy in `{strategy_name}.py`. Comment out `logger.flush`

```
prosperity2bt {strategy_name}.py 0 --print
```

### Submitting an Algo

Copy the `{strategy_name}.py` into `laundromat`. Uncomment `logger.flush`. Submit to IMC Prosperity.

### Analysing an Algo

Follow steps on <https://jmerle.github.io/imc-prosperity-2-visualizer/visualizer>.
