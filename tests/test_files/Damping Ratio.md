#Damping-Ratio 
# Definition: 
$$\xi = a/\omega_{n}$$
- $\xi$ is the damping ratio
- $a$ is the rate of exponential decay
	- For second order systems: $e^{-at}$ 
- $\omega_{n}$ is the natural frequency of oscillation 
- Measures the relative rate at which oscillation magnitudes are **reduced**, normalized by the natural frequency of the system
- $\zeta < 1$ ->  underdamped
	- Oscillatory response decays exponentially 
	- Lots of periods to eliminate the motion following a disturbance
- $\zeta=0$ 
	- Indefinitely oscillating response
- $\lim_{\zeta \rightarrow 1} \zeta$
	- Oscillations dissipate in relatively few periods of oscillatory motion
- $\zeta=1$ 
	- Critically damped system, with no motion

## Percent Overshoot Method

$$\zeta = \frac{-\ln(\%OS/100)}{\sqrt{\pi^2 + \ln^2(\%OS/100)}}$$
- ==Response with too few peaks or too small to accurately extract from the time response==
- $\%OS$: Percent overshoot to a step input
	- Applying it to a system with additional poles and/or zeros is a good-way of determining “effective” damping ratio
	- **==Large amount of overshoot but small residual oscillations==**
		- Could be caused by presence of uncanceled zeros in the mid-frequency range (e.g. 1-10 rad/sec)
		- Perceived as lightly damped mode by pilot, especially in turbulence 
> Doesn’t exist for impulse resulting in a steady state value of zero 
## Logarithmic Decrement
$$\zeta = \frac{\delta}{\sqrt{4\pi^2 + \delta^2}}$$
- Where $\delta$ (the natural logarithm of the ratio of successive peaks with period $T$ overreacted in measurement $y(t)$ :
	- $\delta = \ln\left[\frac{y(t)}{y(t+T)}\right]$
- Significant residual oscillations exists
- Used peak times and magnitude to determine natural frequency and decay frequency of the response, from which $\zeta$ is calculated
- Usually calculated from an impulse inputs and rate output (e.g., pitch rate)
	- But step input should work
- At least 3 oscillations required
> From Wikipedia: The method of logarithmic decrement **becomes less and less precise as the damping ratio increases past about 0.5**; it does not apply at all for a damping ratio greater than 1.0 because the system is [overdamped](https://en.m.wikipedia.org/wiki/Overdamped)

