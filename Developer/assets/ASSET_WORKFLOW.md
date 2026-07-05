# Asset Workflow

The source files in [Licensed images](c:/Users/Max/Projects/BiblionOCR/Developer/assets/Licensed%20images) remain the archive set.
At this stage the preferred review assets are the higher-quality JPEG files you added there.

The working surface for review and tagging is [PNG previews](c:/Users/Max/Projects/BiblionOCR/Developer/assets/PNG%20previews).
If those generated previews are not good enough, place higher-quality replacements in `Developer/assets/Reference previews`; the selector will prefer them while preserving the same manifest rows and A-E assignments.

Use [storyboard_asset_selector.py](c:/Users/Max/Projects/BiblionOCR/Developer/assets/storyboard_asset_selector.py) when you want an interactive PNG-based review tool for assigning storyboard categories.
The selector reads its editable category list from [storyboard_categories.csv](c:/Users/Max/Projects/BiblionOCR/Developer/assets/storyboard_categories.csv).
That file preserves the canonical A-E storyboard asset maps, including display labels, destination folders, and category guidance.

## Intended Flow

1. Add or update source image files in `Licensed images`.
2. Regenerate PNG previews and the contact sheet when a normalized preview set is still useful.
3. Review either the generated PNG output or the JPEG source set directly, depending on which visuals are better.
4. Update [asset_tags.csv](c:/Users/Max/Projects/BiblionOCR/Developer/assets/asset_tags.csv) using either the generated PNG previews, the JPEG source files in `Licensed images`, or any higher-quality replacements surfaced by [storyboard_asset_selector.py](c:/Users/Max/Projects/BiblionOCR/Developer/assets/storyboard_asset_selector.py).
5. Copy approved source assets into the A-E category folders.

## Regeneration Command

```powershell
& 'C:\Program Files\Python311\python.exe' 'c:\Users\Max\Projects\BiblionOCR\Developer\assets\generate_png_previews.py'
```

```powershell
& 'C:\Program Files\Python311\python.exe' 'c:\Users\Max\Projects\BiblionOCR\Developer\assets\storyboard_asset_selector.py'
```

## Notes

- `contact_sheet.png` is generated inside `PNG previews` for fast visual review.
- `asset_tags.csv` keeps the source filename in the `eps_file` column for compatibility with the current selector workflow, even when the source asset is now a JPEG.
- `storyboard_categories.csv` is the editable source for storyboard category labels and destination folders.
- The category folders remain a non-destructive sort; the source archive stays intact.