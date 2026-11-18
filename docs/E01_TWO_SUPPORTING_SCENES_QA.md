# E01 — physical no-login source test for two support shots

**These are only supporting scenes**, not S01, and they do not replace the existing 12-scene storyboard.

S10 — Two adults drinking coffee at a wooden cafe table. Pexels ID 4828603, cottonbro studio, source page https://www.pexels.com/video/two-persons-sitting-by-the-table-while-drinking-their-coffee-4828603/ . Source labels 2160x4096 / 25fps / 28s. Story scene 55.56..62.16 (6.60s). Risk: casual conversation may not convey compassionate support; assess hands, faces and endorsement.

S05 — Vertical historic stone corridor with arches and benches. Pexels ID 37340388, HÜSEYİN AVCI, source page https://www.pexels.com/video/historic-stone-corridor-with-arches-37340388/ . Source labels 2160x3840 / 60fps / 23s. Story scene 22.58..30.20 (7.62s). HIGH editorial risk of recognisable real religious architecture: cannot state or imply this is historical Judah or a known scene from Habakkuk.

License https://www.pexels.com/license/ allows edited stock footage in YouTube videos subject to limits on identifiable people, endorsement and depiction. Verify each source and local context before acceptance.

The one-shot workflow fetches public Pexels download redirects from videos.pexels.com without user auth or API key, byte-caps to 250 MB each, measures original MP4 SHA256/metadata, makes one 720x1280 8s extract per scene, derives 30fps (never claims it was shot at 30fps), validates full FFmpeg decode, emits hashes and samples at 15/50/85 percent. Original full-source files are deleted from the runner; preview files remain in temporary one-day GitHub artifacts only until reviewed. No source is automatically approved for master. Do not combine this footage with the eight recurring actor shots before explicit visual continuity clearance.

After physical test, inspect every sample and save accepted-or-rejected QA report. For accepted candidate previews, private Drive archive is recommended; never embed personal Drive identifiers in public repo.
