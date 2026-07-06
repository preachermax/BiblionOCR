# Third-Party Licensing Notes

The root [LICENSE](LICENSE) applies to original BiblionOCR work unless a file or directory states different terms.

This repository also contains third-party material under separate licenses. Those upstream licenses remain in force for the relevant files.

Known examples surfaced during the public-repo audit:

- [ViewController/Developer/Qt5CharacterMap.py](ViewController/Developer/Qt5CharacterMap.py#L1) is a PyQt example distributed under BSD terms embedded in the file header.
- [ViewController/0-MainUI/web/standard_fonts/LICENSE_LIBERATION](ViewController/0-MainUI/web/standard_fonts/LICENSE_LIBERATION) documents SIL Open Font License terms for Liberation font assets.
- [ViewController/Developer/build/pdf.worker.js.map](ViewController/Developer/build/pdf.worker.js.map) contains bundled Mozilla PDF.js source map content under Apache-2.0 notices.

Excluded from the intended public-tracked repo surface:

- `ViewController/0-MainUI/pyTesseractTrainer-1.03.py` is GPL-licensed upstream tooling and should stay local or be redistributed separately with its GPL terms.
- `ViewController/0-MainUI/glyphtracer-master/` is vendored GPL upstream tooling and should stay local or be redistributed separately with its GPL terms.
- `ViewController/0-MainUI/potrace-main/` is vendored GPL upstream tooling and should stay local or be redistributed separately with its GPL terms.

Public release guidance:

- Keep upstream license files with the third-party code they cover.
- Do not assume the root license relicenses third-party directories.
- Keep GPL vendored tools out of the public-tracked surface unless you explicitly want to publish them under their original GPL terms.
- Remove or relocate separately licensed assets if you do not want to publish them.
- The stock-media workflow under [Developer/assets](Developer/assets) should be treated separately from software licensing because media redistribution terms are not the same as code licensing.