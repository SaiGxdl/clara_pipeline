# Clara AI Automation Pipeline (Modular)

This automation pipeline ingests raw conversation transcripts from Demo and Onboarding calls and converts them into structured, version-controlled Retell AI Voice Agent configurations.

## Handling Fireflies JSON vs Google Drive Recordings

**Data Sources Explanation:**
1. **Fireflies JSON (Primary Input)**: The pipeline expects to consume `fireflies_transcript.json` files as its primary data vector. Because Fireflies has already transcribed the call and separated out speaker tracking, it allows us to bypass expensive audio/video AI transcription services, satisfying the assignment's strict **zero-cost constraint**.
2. **Google Drive Recordings (Fallback)**: Raw `.mp4`/`.m4a` files in Google Drive should be treated merely as cold backups. They are not processed by this pipeline directly to avoid unneeded complexity and cost, but they are preserved for human audit or retraining if the transcript is corrupt.

## Modular Architecture
- `transcript_parser.py`: Robust unmarshaling structure to load heavily nested or unique Fireflies JSON blobs and stringify the sentences.
- `extractor.py`: Zero-cost parsing logic mocking an open-source LLM extraction. Processes the text to build the `Account Memo JSON` per client.
- `agent_generator.py`: Configuration template engine mapping the extracted properties into a strict prompt configuration defining Business Hour vs After Hour flows.
- `versioning.py`: Generates absolute differentials between `v1` and `v2` dictionaries to automatically generate `changes.md` logs.
- `pipeline.py`: Pure orchestration. Loads `/dataset/inputs/...`, triggers the workflow nodes, and commits idempotent file saves.

## How to Run
All execution is natively configured through Python standard libraries ensuring it is absolutely **zero-cost**.

1. **Install dependencies** (all standard library, but included for convention):
   ```bash
   pip install -r requirements.txt
   ```
2. **Setup your Inputs**:
   - Place your Demo Fireflies JSON transcripts in `dataset/inputs/demo/`
   - Place your Onboarding JSON transcripts in `dataset/inputs/onboarding/`
3. **Execute**:
   ```bash
   python pipeline.py
   ```
4. **Outputs**:
   - The resulting agents are deployed cleanly inside `outputs/accounts/<account_id>/`

## n8n Workflow Outline
If you prefer visual node-based execution within n8n (self-hosted docker image):
1. **Trigger Node**: Webhook catching a post from Fireflies API on-meeting-ended (or simply an S3/Google Drive polling trigger grabbing the JSON).
2. **Read File Node**: Load JSON text dynamically.
3. **Execute Command (Code Node)**: Execute isolated modular python scripts mapping: `transcript_parser.py` -> `extractor.py` via basic stdout streams or standard python runtime nodes inside n8n.
4. **Router Node**: Assess Demo vs Onboarding. 
   - If Demo: Write generated v1 strings to `AWS S3` / `GitHub Repo`.
   - If Onboarding: Pull state, trigger `extractor.extract_onboarding_updates()`, and compute diffs via `versioning.py`.
5. **HTTP Request Node**: Make a `POST` request to the Retell API endpoint (`/create-agent`) using the generated `agent_spec.json` payload directly. 
