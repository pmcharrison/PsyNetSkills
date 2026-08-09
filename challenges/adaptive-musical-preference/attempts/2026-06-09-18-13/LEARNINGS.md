# Learnings

## On-demand asset URLs can be cached before IDs exist

Manual browser testing caught a media-loading failure that bot tests missed: `AudioPrompt` requested `/on-demand-asset?id=None` even though the trial lifecycle had registered an on-demand asset. The local fix uses a small `SessionBoundOnDemandAsset` wrapper that adds the asset to the DB session and flushes before URL generation, then asserts numeric IDs in the bot regression test.

*Actions:*
- **PsyNetSkills:** Mention browser media fetch validation in experiment evidence guidance, especially for on-demand audio assets. Confidence: medium. Status: considering.
- **PsyNet:** Consider making `OnDemandAsset.get_url()` robust against stale pre-ID URL generation for trial-owned assets. Confidence: medium. Status: considering.

## Audio evidence needs browser launch under the recording sink

The first successful screen recording had an AAC stream but was effectively silent because Chrome was already running outside the PulseAudio null sink. Relaunching Chrome with `PULSE_SERVER` pointed at the recording sink produced non-silent participant audio.

*Actions:*
- **PsyNetSkills:** Add an explicit "launch a fresh browser under the PulseAudio sink" check to participant-video instructions. Confidence: high. Status: considering.
