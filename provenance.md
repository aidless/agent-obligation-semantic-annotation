# Provenance

Built from the frozen 48-case semantic sample. Public packets contain only prompt, tool sequence, and initial-to-ending persisted-state differences. Full local states, model identity, guard arm, native score, strict score, and minimal score are excluded. All identities and URLs are AgentDojo synthetic fixtures.

The v1 staging directory failed inventory verification because it contained 65 packets: 48 frozen IDs plus 17 stale packets left by an earlier sample build. It was never published. v2 copies exactly the 48 IDs in semantic-sample.json and passes the release verifier.
