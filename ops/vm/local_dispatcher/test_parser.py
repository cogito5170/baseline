import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent))
import dispatcher

def test_vm8():
    with open(str(Path(__file__).parent / "test_vm8_stdout.txt")) as f:
        stdout = f.read()
    
    has_report = False
    blocks = dispatcher.extract_ga_blocks(stdout, "OWNER")
    for b in blocks:
        if b["data"].get("schema") == "report/2":
            has_report = True
            
    assert not has_report, "VM-8 stdout should not have a valid report/2"
    
def test_vm7():
    with open(str(Path(__file__).parent / "test_vm7_stdout.txt")) as f:
        stdout = f.read()
        
    has_report = False
    blocks = dispatcher.extract_ga_blocks(stdout, "OWNER")
    for b in blocks:
        if b["data"].get("schema") == "report/2":
            has_report = True
            
    assert has_report, "VM-7 stdout should have a valid report/2"
    
    reply = dispatcher.prepare_reply("CMD-VM7", 1, stdout, ["D1", "D2", "D3", "D4", "D5"], "gemini-3.1-pro-high", 315711, 2379, 290161, 1, 150.1, stdout)
    
    blocks = dispatcher.extract_ga_blocks(reply, "OWNER")
    report_blocks = [b for b in blocks if b["data"].get("schema") == "report/2"]
    
    assert len(report_blocks) == 1, f"Expected exactly 1 report/2 block, got {len(report_blocks)}"
    assert "agy printed no valid report/2" not in reply, "Should not fallback"

if __name__ == "__main__":
    test_vm8()
    test_vm7()
    print("Parser tests passed!")
