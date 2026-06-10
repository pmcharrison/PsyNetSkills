---
score:
---

# Evaluation

## Summary

Generally quite good and followed the right instructions. Particularly impressed that it figured out by trying different sources to retreive free licensed images.

## Strengths

- Nice custom card CSS to display the images encapsulating the Tinder idea
- I asked it to make a quick popup with a text when choices are made. It did the job by hacking around with PsyNet

## Weaknesses

- It ignored my request to make a fancy landing page that is a twist of the actual Tinder application and instead just generated a simple InfoPage. This is likely due to the model not having direct access to image generation. I could've piped an image directly into the git for it to use as landing page.
- Image is not centred and shifted to one side, it didn't try to address this bug

## Criteria

- [x] The experiment runs locally in PsyNet and presents a complete participant flow with instructions, 15 image trials, and a completion page.
- [x] The stimulus set contains five clothes images, five house interior images, and five painting images, with source metadata documented for each image.
- [x] All displayed images are standardized to 500 x 500 px.
- [x] Each trial presents one image in a swipe-style card layout and accepts only left-arrow and right-arrow responses for the like/dislike decision.
- [x] Left-arrow responses are recorded as "Dislike" and produce brief red "Dislike" feedback.
- [x] Right-arrow responses are recorded as "Like" and produce brief green "Like" feedback.
- [x] Trial data include enough metadata to identify the image, category, source, response direction, binary preference response, and response time.
- [x] The implementation avoids custom service credentials and uses only local demo assets and configuration.

## Notes

- Score and feedback should come from a human evaluator, captured
  conversationally when working with Cursor Cloud Agents.
- Evidence collected: `evidence/participant.mp4`, `evidence/performance.json`,
  `evidence/monitor.html`, and `evidence/data.zip`.
- `psynet export local` successfully wrote regular database/basic-data exports.
  The optional source-code download prompt was skipped by terminating the waiting
  process after the data export had completed; source code is already committed
  under `code/`.
