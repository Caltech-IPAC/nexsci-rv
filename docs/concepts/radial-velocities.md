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
the planet. The spectrographs whose archives this package serves are built to
measure RV to better than a meter per second.

## How the pipeline measures the shift

You do not measure the line shift line by line. The standard approach is the
{term}`CCF (cross-correlation function)`: the observed spectrum is
cross-correlated against a template (a "mask") of known stellar lines, producing
a single average line profile. The **center** of that profile gives the Doppler
shift, hence the RV; its depth and width also diagnose the measurement.

You never compute any of this yourself. The {term}`L2` data level stores the
finished CCF results.

## Which columns are the answer

Every archive's L2 table answers the same handful of questions, though the
column names differ between archives:

- **The RV itself** — the number you plot against time.
- **Its error bar** — needed to weight points in a fit.
- **The precise time** — a Julian Date, often the right x-axis for an RV time
  series.
- **Quality indicators** — the photon-noise precision floor ({term}`dvrms`) and
  the extracted signal-to-noise ({term}`extsnr`).

| Question | NEID | EXPRES |
| --- | --- | --- |
| Radial velocity | {term}`ccfrvmod` | `v` |
| RV uncertainty | {term}`ccfnoise` | `e_v` |
| Time of the RV | {term}`ccfjdsum` | {term}`ccfjdsum` |

Each archive's page lists its full set of RV columns. For the column tour, see
{doc}`results-columns`.
