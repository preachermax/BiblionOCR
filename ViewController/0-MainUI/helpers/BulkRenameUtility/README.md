# Bulk File & Folder Rename Tool - User Guide

Welcome to the Bulk File & Folder Rename Tool. This utility allows you to rename multiple files and directories quickly using simple text replacement or powerful Regular Expressions (Regex).

---

## 🚀 Getting Started

1. **Select Target Directory**: Click the **Browse** button to choose the folder containing the files you want to rename.
2. **Configure Options**:
   * **Include Subfolders (Recursive)**: Check this box to rename files inside all subfolders. This operates bottom-up, ensuring files are processed safely before their parent folders.
   * **Use Regular Expressions (Regex)**: Check this box to enable pattern-based renaming.
3. **Enter Search & Replace Rules**:
   * **Search for**: Specify the exact text or pattern to look for.
   * **Replace with**: Specify what should replace the matched text. Leave empty to delete the matched text.
4. **Preview**: Click **Preview Changes** to see a side-by-side mapping (`Old Path -> New Name`) without modifying your files.
5. **Apply**: Click **Apply Rename** to permanently update your file names on disk.

---

## 🔬 Using Regular Expressions (Regex)

When the **Regex** checkbox is enabled, you can use Python's standard `re` syntax for advanced patterns.

### Common Match Patterns
* `\d+` - Matches one or more digits (e.g., matching numbers like `123`).
* `\.txt$` - Matches only files ending with the `.txt` extension.
* `^img_` - Matches names that start exactly with `img_`.
* `\s+` - Matches any whitespace characters (spaces, tabs).

### Capture Groups & Rearranging
You can capture parts of the original file name using parentheses `()` and reuse them in your replacement using `\1`, `\2`, etc.

* **Example 1: Swapping Parts**
  * **Search**: `(\d+)-(.*)`
  * **Replace**: `\2-\1`
  * **Result**: `01-Document.txt` becomes `Document-01.txt`
* **Example 2: Adding a Prefix to Numbers**
  * **Search**: `(v\d+)`
  * **Replace**: `Final_\1`
  * **Result**: `report_v2.pdf` becomes `report_Final_v2.pdf`

---

## ⚠️ Important Safety Tips

* **Always Preview First**: Before executing a bulk operation, always run a preview to verify your rules operate exactly as intended.
* **Case Sensitivity**: Simple search and replace is case-sensitive. For regex, you can use `(?i)` at the start of your search pattern to make it case-insensitive (e.g., `(?i)draft`).
* **Name Collisions**: If your rename rules cause multiple files to share the exact same new name in the same directory, file system errors may prevent some modifications.
