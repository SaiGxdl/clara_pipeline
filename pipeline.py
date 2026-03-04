import json
import logging
from pathlib import Path
import glob

# Import the new modular components
from transcript_parser import TranscriptParser
from extractor import Extractor
from agent_generator import AgentGenerator
from versioning import Versioning

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

class ClaraPipeline:
    def __init__(self, dataset_dir, outputs_dir):
        self.dataset_dir = Path(dataset_dir)
        self.outputs_dir = Path(outputs_dir)
        
        # Initialize modules
        self.parser = TranscriptParser()
        self.extractor = Extractor()
        self.agent_gen = AgentGenerator()
        self.version_diff = Versioning()

    def process_all(self):
        """
        Scans the inputs/demo and inputs/onboarding directories for JSON transcripts.
        Processes them end-to-end to generate v1 and v2 outputs idempotently.
        """
        demo_dir = self.dataset_dir / "inputs" / "demo"
        onboarding_dir = self.dataset_dir / "inputs" / "onboarding"
        
        # Create output base if doesn't exist
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        
        if not demo_dir.exists():
            logging.error(f"Demo directory not found: {demo_dir}")
            return
            
        demo_files = glob.glob(str(demo_dir / "*.json"))
        logging.info(f"Found {len(demo_files)} demo JSOn transcripts. Batch processing...")
        
        for demo_file in demo_files:
            file_name = Path(demo_file).stem
            account_id = file_name.replace("_demo", "")
            
            logging.info(f"Processing Account: {account_id}")
            
            # 1. Parse Fireflies Demo JSON
            try:
                demo_text = self.parser.parse_fireflies_json(demo_file)
            except Exception as e:
                logging.error(f"Failed to parse demo transcript {demo_file}: {e}")
                continue
                
            # Pipeline A: Demo -> Preliminary Agent (v1)
            v1_memo = self.extractor.extract_demo_memo(demo_text, account_id)
            v1_agent_spec = self.agent_gen.generate_spec(v1_memo, version="v1")
            
            # Automatically create output folders
            account_output_dir = self.outputs_dir / "accounts" / account_id
            v1_dir = account_output_dir / "v1"
            v2_dir = account_output_dir / "v2"
            v1_dir.mkdir(parents=True, exist_ok=True)
            v2_dir.mkdir(parents=True, exist_ok=True)
            
            # Idempotent Writes (V1)
            with open(v1_dir / "account_memo.json", "w", encoding="utf-8") as f:
                json.dump(v1_memo, f, indent=4)
            with open(v1_dir / "agent_spec.json", "w", encoding="utf-8") as f:
                json.dump(v1_agent_spec, f, indent=4)
                
            logging.info(f"Generated v1 specs for {account_id}")
                
            # Pipeline B: Onboarding -> Agent Modification (v2)
            onboarding_file = onboarding_dir / f"{account_id}_onboarding.json"
            if onboarding_file.exists():
                logging.info(f"Found onboarding transcript for {account_id}. Generating v2...")
                
                # 1. Parse Fireflies Onboarding JSON
                try:
                    onboarding_text = self.parser.parse_fireflies_json(str(onboarding_file))
                except Exception as e:
                    logging.error(f"Failed to parse onboarding transcript {onboarding_file}: {e}")
                    continue
                    
                # 2. Extract updates dynamically against V1
                v2_memo = self.extractor.extract_onboarding_updates(onboarding_text, v1_memo)
                
                # 3. Regenerate Spec V2
                v2_agent_spec = self.agent_gen.generate_spec(v2_memo, version="v2")
                
                # 4. Generate Changelog Diff
                changelog_text = self.version_diff.compute_diff(v1_memo, v2_memo, account_id)
                
                # Idempotent Writes (V2)
                with open(v2_dir / "account_memo.json", "w", encoding="utf-8") as f:
                    json.dump(v2_memo, f, indent=4)
                with open(v2_dir / "agent_spec.json", "w", encoding="utf-8") as f:
                    json.dump(v2_agent_spec, f, indent=4)
                    
                with open(account_output_dir / "changes.md", "w", encoding="utf-8") as f:
                    f.write(changelog_text)
                    
                logging.info(f"Successfully generated v2 patches and changes.md for {account_id}")
            else:
                 logging.warning(f"No onboarding JSON found for {account_id}. Skipped v2.")
                    
        logging.info("Pipeline execution successfully completed.")

if __name__ == '__main__':
    # Execute batch pipeline logic targeting the dataset subfolders
    pipeline = ClaraPipeline('dataset', 'outputs')
    pipeline.process_all()
