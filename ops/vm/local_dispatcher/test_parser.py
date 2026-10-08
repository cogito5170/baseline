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

import unittest.mock as mock

def test_vm8_repair_success():
    with open(str(Path(__file__).parent / "test_vm8_stdout.txt")) as f:
        vm8_out = f.read()
    
    directive = {
        "id": "CMD-VM8",
        "rev": 1,
        "done_when": [{"id": "D1", "text": "something"}]
    }
    
    # We want to mock subprocess.Popen for run_agy and subprocess.run for others
    popen_mock = mock.MagicMock()
    # first call is normal agy (returns vm8_out without report)
    # second call is repair agy (returns a valid report/2)
    process1 = mock.MagicMock()
    process1.communicate.return_value = (vm8_out, "")
    process1.returncode = 0
    
    process2 = mock.MagicMock()
    valid_report = '''{
  "response": "```ga\n{\n  \"schema\": \"report/2\",\n  \"from\": \"VM_LOCAL\",\n  \"handled\": [{\"id\": \"CMD-VM8\", \"rev_seen\": 1, \"status\": \"done\"}],\n  \"items\": [{\"id\": \"D1\", \"state\": \"met\", \"evidence\": \"ev\"}]\n}\n```",
  "status": "SUCCESS"
}'''
    process2.communicate.return_value = (valid_report, "")
    process2.returncode = 0
    
    popen_mock.side_effect = [process1, process2]
    
    run_mock = mock.MagicMock()
    run_mock.return_value.returncode = 0
    run_mock.return_value.stdout = ""
    
    with mock.patch('dispatcher.subprocess.Popen', popen_mock), \
         mock.patch('dispatcher.subprocess.run', run_mock), \
         mock.patch('dispatcher.gh_issue_comment') as comment_mock, \
         mock.patch('dispatcher.gh_issue_edit'), \
         mock.patch('dispatcher.DRY_RUN', False):
         
         dispatcher.worker_task(123, directive, "CMD-VM8_1")
         
         # The second call to Popen should be the repair run
         assert popen_mock.call_count == 2
         repair_cmd = popen_mock.call_args_list[1][0][0]
         assert "--model" in repair_cmd
         assert "gemini-3.8-flash-low" in repair_cmd
         assert "--conversation" not in repair_cmd
         
         comment_body = comment_mock.call_args[0][1]
         assert "```ga" in comment_body
         assert "report/2" in comment_body
         assert "declined" not in comment_body

def test_vm8_repair_fail():
    with open(str(Path(__file__).parent / "test_vm8_stdout.txt")) as f:
        vm8_out = f.read()
    
    directive = {
        "id": "CMD-VM8",
        "rev": 1,
        "done_when": [{"id": "D1", "text": "something"}]
    }
    
    popen_mock = mock.MagicMock()
    process1 = mock.MagicMock()
    process1.communicate.return_value = (vm8_out, "")
    process1.returncode = 0
    
    process2 = mock.MagicMock()
    junk_report = '''{"response": "junk", "status": "SUCCESS"}'''
    process2.communicate.return_value = (junk_report, "")
    process2.returncode = 0
    
    popen_mock.side_effect = [process1, process2]
    
    run_mock = mock.MagicMock()
    run_mock.return_value.returncode = 0
    run_mock.return_value.stdout = ""
    
    with mock.patch('dispatcher.subprocess.Popen', popen_mock), \
         mock.patch('dispatcher.subprocess.run', run_mock), \
         mock.patch('dispatcher.gh_issue_comment') as comment_mock, \
         mock.patch('dispatcher.gh_issue_edit'), \
         mock.patch('dispatcher.DRY_RUN', False):
         
         dispatcher.worker_task(123, directive, "CMD-VM8_1")
         
         comment_body = comment_mock.call_args[0][1]
         assert "declined" in comment_body
         assert "agy printed no valid report/2" in comment_body
         assert vm8_out[-100:] in comment_body or "re-asking" not in comment_body

def test_read_only_prompt():
    directive = {
        "id": "CMD-VM9",
        "rev": 2,
        "scope": "read only test",
        "done_when": [{"id": "D1", "text": "something"}]
    }
    
    popen_mock = mock.MagicMock()
    process1 = mock.MagicMock()
    process1.communicate.return_value = ('''{"response": "```ga\n{\"schema\": \"report/2\"}\n```", "status": "SUCCESS"}''', "")
    process1.returncode = 0
    popen_mock.return_value = process1
    
    run_mock = mock.MagicMock()
    run_mock.return_value.returncode = 0
    run_mock.return_value.stdout = ""
    
    with mock.patch('dispatcher.subprocess.Popen', popen_mock), \
         mock.patch('dispatcher.subprocess.run', run_mock), \
         mock.patch('dispatcher.gh_issue_comment'), \
         mock.patch('dispatcher.gh_issue_edit'):
         
         dispatcher.worker_task(123, directive, "CMD-VM9_2")
         
         # Check the prompt argument
         cmd = popen_mock.call_args[0][0]
         prompt_idx = cmd.index("-p") + 1
         prompt_text = cmd[prompt_idx]
         
         assert "report/2" in prompt_text
         assert "D1" in prompt_text
         assert "met" in prompt_text

    test_vm8_repair_success()
    test_vm8_repair_fail()
    test_read_only_prompt()
