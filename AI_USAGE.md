# AI assistance and human decisions

This project was carried out by the user with Codex/LLM assistance.

## Where AI was used

- Planning, interpreting upstream (HF) implementation.
- Writing data preparation, environment/inference wrappers, validation code, normalization and metric implementations, tests, analysis and documentation.
- Reviewing compound candidate forms and selected development contexts. Accepted/rejected decisions explicitly name LLM review; no human approval of each rule is claimed.
- Curating the 117 conversational/function-word boost exclusions after inspecting development weights. No published stopword list supplied those exclusions. The list remains subjective and a sensitivity check is deferred.
- Interpreting results, drafting limitations and proposing the student-exercise assessment.

## User decisions and actions

The user supplied the leaderboard figures, selected the model lineup, the sample/agenda and normalization experiments, supplied corpus downloads, configured the GPU VM and system requirements following driver updates. The user directed report revisions, including the four-score presentation, and deferred sensitivity analysis and full reproduction. User discussion/review does not constitute independent verification of all generated code or conclusions.

## What supplied the evidence

The reported scores come from actual saved model inference and programmatic normalization/alignment, not LLM-assigned transcript quality ratings. Metadata checks use AMI annotations and manifest/frame consistency. Uncertainty values come from the saved-prediction resampling analysis. Dependency versions, checksums, commands and outputs are recorded. Tests exercise specified behavior; LLM-authored tests do not independently validate the scientific relevance of a metric.

No LLM-based ASR, semantic judge, generated reference transcript, speaker-ID inference or relevance-judgment generation was used in the reported scoring. No human listening audit, independent compound/exclusion review, or actual retrieval relevance evaluation was performed. These limits matter when interpreting a search-oriented metric.
