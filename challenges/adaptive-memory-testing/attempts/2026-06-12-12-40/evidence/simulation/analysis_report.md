# Simulation analysis

The simulation ran 10 synthetic participants at each of three true memory
ability levels (`r_i = 0.35`, `1.0`, and `3.0`) for both adaptive and
non-adaptive policies, giving 30 adaptive and 30 non-adaptive participants.

The final participant ability estimate was computed two ways:

- the experiment's NumPy mean-field variational posterior;
- an HMC posterior check using the same Gamma memory-ability model.

Mean absolute HMC ability-estimation error by policy and ability:

| Ability | Policy | Mean selected length | Late mean length | HMC MAE (`r_i`) |
| --- | --- | ---: | ---: | ---: |
| low | adaptive | 7.23 | 5.08 | 0.136 |
| low | random | 11.80 | 11.74 | 0.152 |
| medium | adaptive | 11.36 | 11.24 | 0.430 |
| medium | random | 10.88 | 10.86 | 0.325 |
| high | adaptive | 16.09 | 18.38 | 0.653 |
| high | random | 11.16 | 10.30 | 1.089 |

The adaptive policy reacts in the expected direction: it moves late-trial
lengths down for low-ability participants and up for high-ability participants.
The HMC comparison improves under adaptive sampling for low and high synthetic
abilities; the short 10-trial medium-ability condition is similar but slightly
better under random sampling in this seed.
