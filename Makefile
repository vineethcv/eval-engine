openai:
\tpython3 runner.py --mode openai --model gpt-4o-mini --temperature 0.0
\tpython3 regression_compare.py baselines/baseline_results_openai_gpt-4o-mini.json results/latest_results.json 0.3

mock:
\tpython3 runner.py
\tpython3 regression_compare.py baselines/baseline_results_mock.json results/latest_results.json 0.3