# Radial velocities and the CCF

This page gives the science meaning behind the numbers, so you know which
columns are "the answer" and what the rest are for. No math — just the chain
from photons to a velocity.

## From a spectrum to a velocity

A star's spectrum is full of narrow dark absorption lines from atoms in its
atmosphere. As the star moves toward or away from us, those lines shift slightly
in wavelength (the Doppler effect). The {term}`radial velocity (RV)` is that
shift converted to a speed along our line of sight, in m/s.

This matters because a planet makes its host star wobble in a small orbit.
Measuring the star's RV over time reveals that periodic motion — and so reveals
the planet. NEID and EXPRES are built to measure RV to better than a meter per
second.

## How the pipeline measures the shift

You do not measure the line shift line by line. The standard approach is the
{term}`CCF (cross-correlation function)`: the observed spectrum is
cross-correlated against a template (a "mask") of known stellar lines, producing
a single average line profile. The **center** of that profile gives the Doppler
shift, hence the RV; its depth and width also diagnose the measurement.

You never compute any of this yourself. The {term}`L2` data level stores the
finished CCF results.

## Which columns are the answer

- **The RV itself:** {term}`ccfrvmod` (NEID) / {term}`v / e_v (EXPRES)` (`v` for
  EXPRES). This is the number you plot against time.
- **Its error bar:** {term}`ccfnoise` (NEID) / `e_v` (EXPRES).
- **The precise time:** {term}`ccfjdsum`, often the right x-axis for an RV time
  series.
- **An alternate RV (NEID):** `ccfrvsum`, a co-added-CCF cross-check on
  `ccfrvmod`.
- **EXPRES quality:** {term}`dvrms (EXPRES)` (the photon-noise precision floor)
  and {term}`extsnr (EXPRES)` (extracted signal-to-noise).

For the full column tour, see {doc}`results-columns`.
