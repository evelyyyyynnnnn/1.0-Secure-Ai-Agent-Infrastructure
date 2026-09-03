# Real data for this project

This project has no fetcher of its own. It is scored against the corpus held by
the sibling project `chaintrust-bench`, so the real-data step happens there:

```bash
cd ../chaintrust-bench
python -m data.fetch          # pulls the SmartBugs curated dataset
cd -
python -m src.demo --real     # scores the agent on contracts neither project wrote
```

`--real` refuses if that corpus is absent. It does not fall back to the authored
corpus, because a comparison run on cases this project's own author wrote is a
different claim than one run on someone else's.
