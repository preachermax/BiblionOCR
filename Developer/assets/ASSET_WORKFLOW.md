# Asset Workflow

The EPS files in [Licensed images](c:/Users/Max/Projects/BiblionOCR/Developer/assets/Licensed%20images) remain the source archive.
That source archive can now also contain the higher-quality JPEG files you want to classify directly.

The working surface for review and tagging is [PNG previews](c:/Users/Max/Projects/BiblionOCR/Developer/assets/PNG%20previews).
If those generated previews are not good enough, place higher-quality replacements in `Developer/assets/Reference previews`; the selector will prefer them while preserving the same manifest rows and A-E assignments.

Use [storyboard_asset_selector.py](c:/Users/Max/Projects/BiblionOCR/Developer/assets/storyboard_asset_selector.py) when you want an interactive PNG-based review tool for assigning storyboard categories.
The selector reads its editable category list from [storyboard_categories.csv](c:/Users/Max/Projects/BiblionOCR/Developer/assets/storyboard_categories.csv).
That file preserves the canonical A-E storyboard asset maps, including display labels, destination folders, and category guidance.

## Intended Flow

1. Add or update source `.eps` files in `Licensed images`.
2. Regenerate PNG previews and the contact sheet.
3. Review the PNG output instead of opening EPS files directly, or work directly from the JPEG source set if those are now the better visuals.
4. Update [asset_tags.csv](c:/Users/Max/Projects/BiblionOCR/Developer/assets/asset_tags.csv) using either the generated PNG previews, the JPEG source files in `Licensed images`, or any higher-quality replacements surfaced by [storyboard_asset_selector.py](c:/Users/Max/Projects/BiblionOCR/Developer/assets/storyboard_asset_selector.py).
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
- `storyboard_categories.csv` is the editable source for storyboard category labels and destination folders.
- The category folders remain a non-destructive sort; the source EPS set stays intact.