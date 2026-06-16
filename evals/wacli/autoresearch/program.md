# Wacli Autoresearch Loop

Goal: improve Wacli skills for low-reasoning agents without bloating `SKILL.md`.

Loop:

1. Run each prompt in `tasks/` with `gpt-5.4-mini` and low reasoning.
2. Save the final agent report as `runs/<date>/<task>.txt`.
3. Score reports with:

```bash
python3 score_wacli_eval.py --task read-self --result-file runs/<date>/read-self.txt
python3 score_wacli_eval.py --task sync-plan --result-file runs/<date>/sync-plan.txt
```

4. Patch only repeated or material failures.
5. Keep a patch only when score improves or equal score uses fewer lines/tokens.
6. Run wrapper tests, docs lint, and `py_compile` before reporting.

Do not edit the scorer to make a bad run pass. Improve the skills or wrappers.
