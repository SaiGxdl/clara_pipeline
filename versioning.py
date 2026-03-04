class Versioning:
    def compute_diff(self, v1_memo, v2_memo, account_id):
        """
        Computes differences between v1 and v2 memos and generates
        a `changes.md` file listing the updates.
        """
        changes = []
        for key in v2_memo:
            v1_val = v1_memo.get(key)
            v2_val = v2_memo.get(key)
            
            if v1_val != v2_val:
                # Basic formatting for arrays vs strings
                if key == "business_hours":
                    changes.append(f"- Business hours updated from `{v1_val.get('start')} - {v1_val.get('end')}` to `{v2_val.get('start')} - {v2_val.get('end')}`")
                elif key == "emergency_definition":
                    changes.append("- Emergency definition clarified.")
                elif key == "call_transfer_rules":
                    changes.append(f"- Transfer protocol updated: {v2_val}")
                else:
                    changes.append(f"- **{key.replace('_', ' ').capitalize()}** updated.")
        
        changelog_content = f"# Changelog for {account_id}\n\n"
        if changes:
             changelog_content += "\n".join(changes)
        else:
             changelog_content += "No changes detected."
             
        return changelog_content
