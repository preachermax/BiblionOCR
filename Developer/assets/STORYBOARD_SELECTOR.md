# Storyboard Asset Selector

Use [storyboard_asset_selector.py](c:/Users/Max/Projects/BiblionOCR/Developer/assets/storyboard_asset_selector.py) to review the generated PNG previews and assign them to storyboard categories.

The category list is defined in [storyboard_categories.csv](c:/Users/Max/Projects/BiblionOCR/Developer/assets/storyboard_categories.csv), so you can change storyboard buckets without editing Python.

## Launch

```powershell
& 'C:\Program Files\Python311\python.exe' 'c:\Users\Max\Projects\BiblionOCR\Developer\assets\storyboard_asset_selector.py'
```

## What It Does

- loads the review surface from [PNG previews](c:/Users/Max/Projects/BiblionOCR/Developer/assets/PNG%20previews)
- reads and writes category assignments, tags, and notes in [asset_tags.csv](c:/Users/Max/Projects/BiblionOCR/Developer/assets/asset_tags.csv)
- loads storyboard category definitions from [storyboard_categories.csv](c:/Users/Max/Projects/BiblionOCR/Developer/assets/storyboard_categories.csv)
- lets you filter by assigned category or unassigned assets
- can sync the non-destructive EPS category folders from the saved manifest

## Shortcuts

- `Left` / `Right`: previous or next asset
- `1`-`9`: assign the first nine configured categories
- category code keys: assign directly by the configured category code
- `Ctrl+S`: save the manifest