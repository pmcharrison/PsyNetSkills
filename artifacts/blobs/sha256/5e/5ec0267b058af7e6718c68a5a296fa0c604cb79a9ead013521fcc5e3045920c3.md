---
title: "Aesthetics Tinder"
type: experiment implementation
difficulty: 5
authors: [harin-git]
---

Implement a PsyNet experiment that measures participants' aesthetic preferences
for real-world images using a swipe-style interface inspired by dating apps such
as Tinder. The experiment should focus on the image-rating component: each
participant views a fixed set of images and indicates whether they like or
dislike each one using the keyboard.

The experiment should:

- Compile a small demo image set with three image categories: clothes, house
  interiors, and paintings.
- Include five images per category, for a total of 15 stimuli.
- Use public or otherwise freely usable web images suitable for demo purposes,
  and document the source for each image.
- Standardize all images to 500 x 500 px before presenting them.
- Present all 15 images as separate trials, in randomized order unless there is
  a clear reason to preserve a fixed order.
- Style the image presentation page to resemble a swipe-based dating app card,
  with one prominent image visible at a time.
- Explain at the beginning of the experiment that the left arrow key means
  "Dislike" and the right arrow key means "Like".
- Require participants to answer each image trial using the left or right arrow
  key.
- When the participant responds, show brief visual feedback: "Like" in green for
  a right-arrow response, or "Dislike" in red for a left-arrow response.
- Save, for each trial, the image identifier, category, image source metadata,
  response direction, like/dislike response, and response time.
- Include a short completion page after all images have been rated.

The task does not require a production-scale stimulus database or a trained
preference-prediction model. The goal is a runnable PsyNet demo that cleanly
collects binary aesthetic preference judgments over a curated 15-image set.
