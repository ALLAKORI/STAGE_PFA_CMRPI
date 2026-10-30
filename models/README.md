# Local model artifacts

The trained classifier and scaler are generated locally and are intentionally
not committed to the public repository. This avoids publishing bulky derived
artifacts and keeps the repository reproducible from the public data sources.

After preparing the local dataset, run:

```powershell
python train_model.py
```

The script writes the generated artifacts to this directory. The application
handles missing artifacts explicitly and reports that model analysis is
unavailable until local preparation is complete.
