## Stage 09 — pin candidate workflow to selected experimental commit

The previous manual-only candidate workflow checked out `ha-shuffle-v2` even when manually dispatched from an experimental optimization branch. That branch lacks the stacked overlay scripts. This PR replaces the checkout with the exact `${{ github.sha }}` selected by workflow dispatch, verifies `git rev-parse HEAD` matches that SHA and checks expected overlay files before checking out the pinned upstream release.

This is a prerequisite correctness fix, not a claim of runtime performance. An independent Python source audit checks the workflow still enforces selected-commit provenance and remains manual-only. The workflow does not publish or update the existing production APK. No candidate build has been dispatched.
