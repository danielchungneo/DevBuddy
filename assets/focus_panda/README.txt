Custom Focus animation (optional)
=================================

Option 0 — Sprite sheet (one PNG, 5×5 grid, 25 frames)
  - Put ``sprite-max-px-25.png`` in the project ``assets/`` folder (repo root).
  - Or copy it into this folder as ``sprite.png`` or ``sprite_sheet.png``.
  - Frames are read left→right, top→bottom. Each cell is resized to the focus panel.

Option A — Animated GIF (easiest)
  - Save as: focus.gif  OR  panda.gif  OR  anim.gif  OR  animation.gif
  - One file, multiple frames. The app resizes to the focus panel size.

Option B — Image sequence
  - Add 2+ PNG or WebP files (1 image = static, no motion).
  - Use zero-padded names so order is obvious, e.g. frame_001.png … frame_012.png
  - Same aspect ratio per frame works best; transparent backgrounds look good on dark UI.

Restart the app after adding or changing files.
