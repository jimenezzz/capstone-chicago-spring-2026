# Data quality metrics (NADAC ↔ OpenFDA ↔ Orange Book ↔ Purple Book)

Track match rates after building the crosswalk and merging with Orange Book and Purple Book.

---

## 2026-02-05

| Metric | Value |
|--------|--------|
| NADAC rows with ndc11 (unique) | 27,260 |
| % NADAC ndc11 matched to OpenFDA xwalk | 85.10% |
| % matched that have application_number_norm | 98.58% |
| % application_number_norm matched to Orange Book (of matched) | 93.54% |
| % application_number_norm matched to Purple Book (of matched) | 0.56% |

*Generated from `data.ipynb` (metrics report cell).*

### Why is the Purple Book match rate (0.56%) so low?

**Scale of the datasets**
- **NADAC:** ~27k–34k unique NDCs (many rows per NDC across dates/updates).
- **Purple Book:** 2,190 rows but only **832 unique BLAs** — biologics only; small-molecule drugs are in the Orange Book.
- **OpenFDA (products):** only ~3.2% are BLA; the rest are NDA/ANDA/other.

**What the metric means**
- “% application_number_norm matched to Purple Book **(of matched)**” = of the NADAC NDCs that have OpenFDA data, what share have an application number that appears in Purple Book. The denominator is “NADAC NDCs that matched to the OpenFDA xwalk,” not “all NADAC” or “all Purple Book.”

**Why the share is small**
1. **Purple Book is biologics-only (BLA).** The Orange Book covers the vast majority of drugs (NDA/ANDA). So only a small fraction of all NDCs can ever match Purple Book.
2. **Among NADAC NDCs that matched to OpenFDA, most are small molecules.** Only a small fraction of those matched NDCs have a BLA application number; the rest are NDA/ANDA.
3. **Not every BLA in OpenFDA is in Purple Book** (and vice versa), so only some of those BLA NDCs actually match.

So **0.56%** means: of the NADAC NDCs that have OpenFDA application numbers, about one in 200 is a biologic that also appears in the Purple Book. That is expected given that Purple Book is biologics-only and NADAC/OpenFDA are dominated by small-molecule drugs. The BLA normalization fix is working; the low percentage reflects the data, not a bug.

---

To add a new run: copy the table above, add a new `## YYYY-MM-DD` section, and paste the new results.
