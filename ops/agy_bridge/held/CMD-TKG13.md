TKG13 (held until TKG12 integrated; red-checked on Token 4720d5f 10-06 20:07 KST)
goal: quota create() must reject bool for limit_microusd and for thresholds (bool is an int subclass).
files: backend/app/domains/quota/service.py (:121-122)
test file: backend/app/domains/quota/tests/test_tkg13_budget_bool.py
```python
import unittest
from app.domains.quota.service import MemoryStore, QuotaError, QuotaService


class T(unittest.TestCase):
    def test_bool_limit_and_threshold_rejected(self):
        svc = QuotaService(MemoryStore(), summary=lambda *a: {})
        with self.assertRaises(QuotaError):
            svc.create("w", None, "workspace", "month", "list", True)
        with self.assertRaises(QuotaError):
            svc.create("w", None, "workspace", "month", "list", 1000, thresholds=[True])
```
red: AssertionError: QuotaError not raised (limit_microusd=True accepted as 1)
command: python3 -m unittest discover -s backend/app/domains/quota -t backend -p 'test_tkg*_*.py'
