## Stage 07 — O(1) action-bar D-pad focus resolution

`FocusableActionBarState._handleBindingFocusChange` previously called `_focusBindings.indexOf(binding)` each time a remote key changed focus. The candidate stores a binding-to-position map and rebuilds it only when the action list is created or re-bound. Identity restoration, disabled-action checks, and the existing key-event state changes remain unchanged.

This is a small reduction in work per focus notification rather than a promise of dramatic visible speedups. Manual Fire TV remote key-repeat, Back/Select, action removal/reorder, and focus restoration tests remain required after compilation. Source checks ensure no linear binding lookup remains and existing focus restoration is present.
