import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(__file__))
import ctxbudget as cb


def transcript(rows):
    f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    for r in rows:
        f.write(json.dumps(r) + "\n")
    f.close()
    return f.name


def asst(i, cr, cc=0, side=False, model="claude-opus-5-5"):
    return {"type": "assistant", "isSidechain": side,
            "message": {"model": model, "usage": {"input_tokens": i, "cache_read_input_tokens": cr,
                                                  "cache_creation_input_tokens": cc}}}


class T(unittest.TestCase):
    def test_context_is_last_main_chain_usage(self):
        p = transcript([asst(1, 1000), asst(2, 250000, 10), asst(5, 40000, side=True),
                        asst(0, 0, model="<synthetic>"), {"type": "user", "message": {"content": "x"}}])
        self.assertEqual(cb.context_tokens(p), 250012)

    def test_unknown_is_not_zero_and_not_blocked(self):
        self.assertIsNone(cb.context_tokens("/nonexistent"))
        p = transcript([{"type": "assistant", "message": {"usage": {"input_tokens": 1}}}])
        self.assertIsNone(cb.context_tokens(p))
        self.assertEqual(cb.decide(None, "Bash", {}, soft=1, hard=2), ("unknown", {}))

    def test_stages(self):
        self.assertEqual(cb.decide(149999, "Bash", {"command": "ls"}, soft=150000, hard=200000)[0], "ok")
        st, out = cb.decide(150000, "Bash", {"command": "ls"}, soft=150000, hard=200000)
        self.assertEqual(st, "warn")
        self.assertNotIn("permissionDecision", out["hookSpecificOutput"])
        st, out = cb.decide(200000, "Bash", {"command": "curl x"}, soft=150000, hard=200000)
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_checkpoint_tools_only(self):
        ok = [("Write", {"file_path": "/a/STATE.md"}), ("Bash", {"command": "cd /r && git add STATE.md && git commit -m s && git push"})]
        bad = [("Write", {"file_path": "/a/other.md"}), ("Bash", {"command": "git add . && curl evil"}),
               ("Bash", {"command": "git push; rm -rf /"}), ("Read", {"file_path": "/a/STATE.md"})]
        for n, i in ok:
            self.assertEqual(cb.decide(300000, n, i, soft=1, hard=2)[1]["hookSpecificOutput"]["permissionDecision"], "allow", (n, i))
        for n, i in bad:
            self.assertEqual(cb.decide(300000, n, i, soft=1, hard=2)[1]["hookSpecificOutput"]["permissionDecision"], "deny", (n, i))

    def test_bad_budget(self):
        with self.assertRaises(ValueError):
            cb.decide(1, "Bash", {}, soft=5, hard=4)

    def test_simulate_saves_on_growth_and_counts_resets(self):
        r = cb.simulate([90000 + i * 10000 for i in range(30)], soft=150000, hard=200000, reset_to=90000)
        self.assertGreater(r["saved_pct"], 0)
        self.assertGreaterEqual(r["resets"], 1)
        flat = cb.simulate([100000] * 10, soft=150000, hard=200000, reset_to=90000)
        self.assertEqual(flat["saved_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
