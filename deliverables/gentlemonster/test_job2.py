# Acceptance test for CMD-GM2 (written by baseline; the executor may not edit it).
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import check  # noqa: E402

check("job2",
      req_words=["로봇공학", "C++", "Python", "제어", "Isaac Sim", "Isaac Lab", "석사", "1년"],
      app_words=["Future Artifact", "Python"],
      port_heads=["프로젝트", "제어"],
      port_words=["관측", "상태", "결정", "Python"],
      gap_words=["전공", "학위", "C++", "Isaac"])
