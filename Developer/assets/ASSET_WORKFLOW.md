# Asset Workflow

The EPS files in [Licensed images](c:/Users/Max/Projects/BiblionOCR/Developer/assets/Licensed%20images) remain the source archive.

The working surface for review and tagging is [PNG previews](c:/Users/Max/Projects/BiblionOCR/Developer/assets/PNG%20previews).

Use [storyboard_asset_selector.py](c:/Users/Max/Projects/BiblionOCR/Developer/assets/storyboard_asset_selector.py) when you want an interactive PNG-based review tool for assigning storyboard categories.

## Intended Flow

1. Add or update source `.eps` files in `Licensed images`.
2. Regenerate PNG previews and the contact sheet.
3. Review the PNG output instead of opening EPS files directly.
4. Update [asset_tags.csv](c:/Users/Max/Projects/BiblionOCR/Developer/assets/asset_tags.csv) using the PNG previews as the tagging reference, either directly or through [storyboard_asset_selector.py](c:/Users/Max/Projects/BiblionOCR/Developer/assets/storyboard_asset_selector.py).
5. Copy approved EPS assets into the A-E category folders.

## Regeneration Command

```powershell
& 'C:\Program Files\Python311\python.exe' 'c:\Users\Max\Projects\BiblionOCR\Developer\assets\generate_png_previews.py'
```

```powershell
& 'C:\Program Files\Python311\python.exe' 'c:\Users\Max\Projects\BiblionOCR\Developer\assets\storyboard_asset_selector.py'
```

## Notes

- `contact_sheet.png` is generated inside `PNG previews` for fast visual review.
- `asset_tags.csv` now includes both the EPS source file and the PNG preview file for each classified asset.
- The category folders remain a non-destructive sort; the source EPS set stays intact.