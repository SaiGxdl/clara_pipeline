import json
import os

class TranscriptParser:
    def parse_fireflies_json(self, file_path):
        """
        Parses a Fireflies transcript JSON file.
        Returns a single concatenated text string of the conversation.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Transcript not found: {file_path}")
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {str(e)}")

        # Fireflies transcripts usually have a 'sentences' or 'transcript' array
        # This fallback logic tries to extract the text no matter the specific schema shape.
        full_text = ""
        
        # Mock Handling: If evaluating the raw provided strings as JSON fails or if it's uniquely formatted
        if isinstance(data, dict):
            if "sentences" in data:
                for sentence in data["sentences"]:
                    speaker = sentence.get("speaker_name", "Speaker")
                    text = sentence.get("text", "")
                    full_text += f"{speaker}: {text}\n"
            elif "transcript" in data:
                for item in data["transcript"]:
                    full_text += f"{item.get('speaker', 'Speaker')}: {item.get('text', '')}\n"
            else:
                # Fallback purely dumping text values if schema is unknown
                full_text = json.dumps(data)
        elif isinstance(data, list):
            for item in data:
                 if isinstance(item, dict) and "text" in item:
                      full_text += item["text"] + " "
        else:
            full_text = str(data)
            
        return full_text
