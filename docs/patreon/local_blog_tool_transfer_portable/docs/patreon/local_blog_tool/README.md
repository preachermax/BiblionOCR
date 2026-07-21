# Patreon Blog Tool

This local-only workspace manages a rolling seven-post Patreon queue and renders Markdown drafts.

## Workflow

1. Keep `blog_queue.json` at seven entries.
2. Mark each post with both an intended audience and its current visibility.
3. Render one or all drafts into the `generated/` folder before posting.
4. Use the `post` action to prepare a manual-safe publish in your normal browser.
5. Use `complete-post` only after the Patreon post is actually live, so the queue rolls at the right moment.
6. Use the launcher preview and copy actions to move ready-to-paste content into Patreon after login.

## Audience Fields

- `audience_intent`: The kind of post you normally want to publish. Allowed values are `public` and `members_only`.
- `visibility`: The exposure you want right now. Allowed values are `public` and `members_only`.

This lets you draft a members-only style post that is temporarily published as public.

## Commands

```powershell
python docs/patreon/local_blog_tool/patreon_blog_tool.py list
python docs/patreon/local_blog_tool/patreon_blog_tool.py render
python docs/patreon/local_blog_tool/patreon_blog_tool.py set-visibility website-prototype-members-preview public
python docs/patreon/local_blog_tool/patreon_blog_tool.py seed-week --start-date 2026-07-07 --force
python docs/patreon/local_blog_tool/patreon_blog_tool.py doctor
python docs/patreon/local_blog_tool/patreon_blog_tool.py gui
python docs/patreon/local_blog_tool/patreon_blog_tool.py post --dry-run
python docs/patreon/local_blog_tool/patreon_blog_tool.py post
python docs/patreon/local_blog_tool/patreon_blog_tool.py complete-post website-prototype-members-preview
python docs/patreon/local_blog_tool/patreon_blog_tool.py post --automated
```

## Posting

Patreon does not currently expose public API write endpoints for creating posts, and Google-style sign-in flows may reject automated browser contexts. Because of that, the default `post` workflow now prepares a manual-safe publish in your normal browser.

The automation is configured through `patreon_post_config.json`, so if Patreon changes its composer labels or button text you can adjust the local config instead of editing Python code.

Each queue item can carry a `pre_post_body`. That field is treated as the primary ready-to-paste composer text. If it is empty, the tool falls back to generating body copy from the excerpt, sections, links, and call to action.

### Local setup

```powershell
pip install playwright
python -m playwright install chromium
```

### What `post` does by default

1. Renders the selected draft.
2. Writes the ready-to-paste composer packet.
3. Copies the packet to the clipboard when possible.
4. Opens Patreon’s composer in your normal browser.
5. Leaves the actual login and paste step to you.

After you publish manually, run `complete-post` to archive the post and roll the queue.

### Automated fallback

If you still want to try the old Playwright path, use `post --automated`. This is now opt-in because some sign-in providers treat automated browsers as insecure.

Use `post --dry-run` first whenever you want to verify the selected slug, visibility, and queue-roll result without touching Patreon.

Use `doctor` before a live post if you want a quick confirmation that the local config loaded and Playwright is available.

## Login Then Paste Workflow

If Patreon requires login or 2FA first, open the launcher and use this sequence:

1. Select the queued post.
2. Review the ready-to-paste composer body in the preview pane.
3. Click `Post` to copy the packet and open Patreon in your normal browser.
4. Log in and paste the prepared content manually.
5. Click `Complete Post` in the launcher after the post is live.

The `render` command now also writes a companion `-composer.txt` file for each post inside `generated/`.

## Output

Rendered drafts are written to `generated/` using the pattern `YYYY-MM-DD-slug.md`.