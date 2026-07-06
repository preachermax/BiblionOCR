# Storyboard Asset Selector

Use [storyboard_asset_selector.py](c:/Users/Max/Projects/BiblionOCR/Developer/assets/storyboard_asset_selector.py) to review the generated PNG previews and assign them to storyboard categories.

The category list is defined in [storyboard_categories.csv](c:/Users/Max/Projects/BiblionOCR/Developer/assets/storyboard_categories.csv), so you can preserve the canonical A-E storyboard asset maps while still editing destination folders and category guidance without editing Python.
If the EPS-derived previews are not usable, place better replacement images in a `Reference previews` folder under `Developer/assets`; the selector will prefer those files over the generated PNGs.
If your working set is now JPEG-based, the selector will also discover supported source images directly from [Licensed images](c:/Users/Max/Projects/BiblionOCR/Developer/assets/Licensed%20images) and let you assign them even before they exist in the manifest.

## Launch

```powershell
& 'C:\Program Files\Python311\python.exe' 'c:\Users\Max\Projects\BiblionOCR\Developer\assets\storyboard_asset_selector.py'
```

## What It Does

- loads the review surface from [PNG previews](c:/Users/Max/Projects/BiblionOCR/Developer/assets/PNG%20previews)
- prefers external replacement previews from `Reference previews` when matching files are available
- falls back to supported source images in [Licensed images](c:/Users/Max/Projects/BiblionOCR/Developer/assets/Licensed%20images) when the manifest or generated preview set does not yet include them
- reads and writes category assignments, tags, and notes in [asset_tags.csv](c:/Users/Max/Projects/BiblionOCR/Developer/assets/asset_tags.csv)
- loads storyboard category definitions from [storyboard_categories.csv](c:/Users/Max/Projects/BiblionOCR/Developer/assets/storyboard_categories.csv)
- shows the configured A-E storyboard category guidance in the UI while you assign assets
- lets you filter by assigned category or unassigned assets
- can sync the non-destructive EPS category folders from the saved manifest

## Replacement Preview Matching

- drop replacement `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, or `.webp` files into `Developer/assets/Reference previews`
- the selector first looks for a file matching `png_preview_file`
- if none exists, it then looks for a file matching the EPS stem, such as `shutterstock_2806729833.jpg`
- if no replacement exists, it will try the generated preview and then the source asset in `Licensed images`

## Shortcuts

- `Left` / `Right`: previous or next asset
- `1`-`9`: assign the first nine configured categories
- category code keys: assign directly by the configured category code
- `Ctrl+S`: save the manifest