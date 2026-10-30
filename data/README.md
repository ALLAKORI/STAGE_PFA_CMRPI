# Local data preparation

Large datasets and collected URLHaus exports are intentionally not committed
to this public repository. They can contain malicious URLs and are only needed
for local reproduction of the training and detection workflow.

## Public sources

- PhiUSIIL Phishing URL Dataset: the public dataset used by the training
  script. Download it from the official UCI Machine Learning Repository and
  place the CSV under `data/raw/`.
- URLHaus recent URL feed: download the CSV from
  `https://urlhaus.abuse.ch/downloads/csv_recent/` with `Download_urls.py`.

No internal company or CMRPI dataset is part of this repository.

## Local layout

```text
data/
  raw/                  # downloaded public training dataset
  processed/            # generated feature table
  collected/urlhaus/    # generated URLHaus index and history
```

These generated files are ignored by Git. Do not commit them, and do not open
malicious URLs in a browser.
