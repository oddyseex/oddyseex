# Plinko hero (archived)

The animated Plinko board that sat beside the old hero text: nine red solo cups, pucks falling through a triangular peg board with real collision physics, cups lighting up when a puck lands.

| File | What it is |
| --- | --- |
| `build_profile_with_plinko.py` | The full profile generator as it was with Plinko in the hero (`simulate()` and `plinko()` hold the physics and drawing). |
| `hero-plinko.svg`, `hero-plinko-mobile.svg` | The finished desktop and phone hero graphics from that version, with the "Build $#!%, break $#!%, build $#!% again" text. |

To bring it back, copy `build_profile_with_plinko.py` over `generator/build_profile.py` and run it. It imports `design.py` from the `generator/` folder, so it has to live there to run.
