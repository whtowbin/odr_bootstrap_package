# Plan

## Current status
- Added calibration-application helpers to estimate unknown x/y values and propagate confidence bounds.
- Added tests for the new API and updated README/tutorial/examples to show unknown-sample workflows.
- Added a Great Tables example for ion intensity to concentration ppm conversion.

## Next steps
- Keep the Great Tables example behind an optional `examples` extra so the standard install remains lightweight.
- Rebuild docs/examples when releasing and validate the generated HTML tables.
- Run the release-prep workflow before any publish or tag push.
