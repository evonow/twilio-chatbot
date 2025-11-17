"""
MBOX to EML Converter
Converts MBOX files to individual EML files
"""

import os
import mailbox
import argparse

def convert_mbox_to_eml(mbox_path, output_dir):
    """
    Convert MBOX file to individual EML files
    
    Args:
        mbox_path: Path to MBOX file
        output_dir: Directory to save EML files
    """
    if not os.path.exists(mbox_path):
        print(f"Error: {mbox_path} not found")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        mbox = mailbox.mbox(mbox_path)
        count = 0
        
        print(f"Processing {len(mbox)} messages from {mbox_path}...")
        
        for i, msg in enumerate(mbox):
            try:
                # Generate filename
                subject = msg.get('Subject', 'No Subject')
                date = msg.get('Date', '')
                
                # Clean subject for filename
                safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
                filename = f"{i:05d}_{safe_subject}.eml"
                filepath = os.path.join(output_dir, filename)
                
                # Save as EML
                with open(filepath, 'wb') as f:
                    f.write(msg.as_bytes())
                
                count += 1
                
                if (i + 1) % 100 == 0:
                    print(f"Converted {i + 1}/{len(mbox)} messages...")
            
            except Exception as e:
                print(f"Error converting message {i}: {e}")
                continue
        
        print(f"\nConversion complete! Saved {count} EML files to {output_dir}")
    
    except Exception as e:
        print(f"Error reading MBOX file: {e}")

def main():
    parser = argparse.ArgumentParser(description='Convert MBOX file to individual EML files')
    parser.add_argument('mbox_file', help='Path to MBOX file')
    parser.add_argument('output_dir', help='Output directory for EML files')
    
    args = parser.parse_args()
    
    convert_mbox_to_eml(args.mbox_file, args.output_dir)

if __name__ == '__main__':
    main()

