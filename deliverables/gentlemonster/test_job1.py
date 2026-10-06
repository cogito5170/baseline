# Acceptance test for CMD-GM1 (written by baseline; the executor may not edit it).
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import check  # noqa: E402

check("job1",
      req_words=["미적 감각", "미학", "문화", "패션", "AI 디바이스", "프로토타입", "생성형 AI", "멀티모달", "아카이빙"],
      app_words=["AI Experience"],
      port_heads=["무엇이며", "가능성과 한계", "행동이나 경험", "패션 또는 브랜드"],
      port_words=["한계"],
      gap_words=["학력", "전공"])
