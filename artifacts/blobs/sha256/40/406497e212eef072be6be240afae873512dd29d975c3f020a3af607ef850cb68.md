# Criteria

- The experiment runs locally in PsyNet and presents a complete participant flow
  with instructions, 15 image trials, and a completion page.
- The stimulus set contains five clothes images, five house interior images, and
  five painting images, with source metadata documented for each image.
- All displayed images are standardized to 500 x 500 px.
- Each trial presents one image in a swipe-style card layout and accepts only
  left-arrow and right-arrow responses for the like/dislike decision.
- Left-arrow responses are recorded as "Dislike" and produce brief red
  "Dislike" feedback.
- Right-arrow responses are recorded as "Like" and produce brief green "Like"
  feedback.
- Trial data include enough metadata to identify the image, category, source,
  response direction, binary preference response, and response time.
- The implementation avoids custom service credentials and uses only local demo
  assets and configuration.
