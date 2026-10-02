# The localmotion promo, made by localmotion

This folder holds the source of the promo video in the main README, exactly as **Qwen 3.8 27B** wrote it, unattended, from [the brief](../briefs/localmotion-promo.txt): 9 scenes, 45 s, 16:9, about 57 minutes on one RTX 3090. `BRIEF.md` and `PLAN.md` are the model's own working notes. The only human addition is the soundtrack, aligned so that its drop lands on "The finished video lands on your phone".

To render it yourself:
1. copy `src/LocalMotion` into your Remotion project's `src/`, and `public/localmotion-promo` into its `public/`;
2. register `<LocalMotion />` in `src/Root.tsx`;
3. put an audio track at `public/localmotion-promo/soundtrack.mp3` (the original isn't included: it's not covered by this repo's license), or remove the `<Soundtrack />` line;
4. run `npx remotion render LocalMotion out/LocalMotion.mp4`.
