# Simulation analysis

The simulation ran 10 synthetic participants at each of three true ability
levels (`theta = 0.9`, `0.0`, and `-0.9`) for both adaptive and non-adaptive
policies, giving 30 adaptive and 30 non-adaptive participants.

The final ability estimate for each participant was computed two ways:

- the experiment's NumPy mean-field variational posterior;
- an HMC posterior check using the same response likelihood.

Mean absolute HMC ability-estimation error by policy and ability:

| Ability | Policy | Mean selected length | Late mean length | HMC MAE |
| --- | --- | ---: | ---: | ---: |
| low | adaptive | 9.77 | 4.74 | 0.213 |
| low | random | 11.80 | 11.74 | 0.391 |
| medium | adaptive | 12.86 | 9.80 | 0.297 |
| medium | random | 10.88 | 10.86 | 0.467 |
| high | adaptive | 16.35 | 15.56 | 0.488 |
| high | random | 11.16 | 10.30 | 0.264 |

The adaptive policy reacts in the expected direction: it moves late-trial
lengths down for low-ability participants and up for high-ability participants.
The HMC comparison improves under adaptive sampling for low and medium synthetic
abilities, while this short 10-trial run estimates high ability more accurately
under random sampling because the adaptive policy rapidly concentrates at the
upper length bound.
