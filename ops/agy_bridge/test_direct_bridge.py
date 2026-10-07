"""direct_bridge.py end to end on local git repos with a fake agy (0 network, 0 model calls)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "flow"))
import direct_bridge as DB  # noqa: E402
import agytask  # noqa: E402

TEST = "from calc import add\nimport unittest\n\nclass T(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n"


def sh(*a, cwd=None):
    subprocess.run(a, cwd=cwd, check=True, capture_output=True)


class Bridge(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        for n in ("code.git", "box.git"):
            sh("git", "init", "-q", "--bare", "-b", "main", str(self.d / n))
        seed = self.d / "seed"
        sh("git", "clone", "-q", str(self.d / "code.git"), str(seed))
        (seed / "calc.py").write_text("def add(a, b):\n    return 0\n")
        (seed / "tests").mkdir()
        (seed / "tests" / "__init__.py").write_text("")
        sh("git", "add", ".", cwd=seed)
        sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "seed", cwd=seed)
        sh("git", "push", "-q", "origin", "HEAD:refs/heads/vm/BASE", cwd=seed)
        sh("git", "clone", "-q", str(self.d / "code.git"), str(self.d / "repo"))
        b = self.d / "boxseed"
        sh("git", "clone", "-q", str(self.d / "box.git"), str(b))
        (b / "README").write_text("box\n")
        sh("git", "add", ".", cwd=b)
        sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "box", cwd=b)
        sh("git", "push", "-q", "origin", "HEAD:refs/heads/ga-mailbox", cwd=b)
        self.base = b
        self.cfg = {**DB.DEFAULTS, "box": str(self.d / "box"), "origin_url": str(self.d / "box.git"),
                    "repos": {"ga-sdk": str(self.d / "repo")}, "python": sys.executable,
                    "done_file": str(self.d / "done")}
        (self.d / "t").mkdir()
        (self.d / "t" / "test_calc.py").write_text(TEST)

    def mail(self, id_="CMD-T1", files=("calc.py",), model="gemini-3.1-pro-high"):
        text = agytask.build(id_, 1, model, "ga-sdk", "vm/BASE", "Make add return the sum of its two arguments.",
                             list(files), [str(self.d / "t" / "test_calc.py")], [])
        sh("git", "pull", "-q", "--rebase", "origin", "ga-mailbox", cwd=self.base)
        p = self.base / "to" / "AGY-direct" / f"20261007T000000.000000Z-{id_}.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        sh("git", "add", ".", cwd=self.base)
        sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "task", cwd=self.base)
        sh("git", "push", "-q", "origin", "HEAD:ga-mailbox", cwd=self.base)

    def fake(self, edit):
        def agy(argv, cwd, timeout):
            if argv[1:] == ["models"]:
                return subprocess.CompletedProcess(argv, 0, "gemini-3.1-pro-high   Gemini 3.1 Pro (High)\n", "")
            assert "--model" in argv and "--prompt" in argv
            edit(Path(cwd))
            return subprocess.CompletedProcess(argv, 0, "summary: changed calc.py\n", "")
        return agy

    def reply(self):
        out = sorted((Path(self.cfg["box"]) / "to" / "baseline-direct").glob("*.md"))
        return json.loads(out[-1].read_text().split("```agy-result\n", 1)[1].split("\n```", 1)[0])

    def test_done_pushes_the_branch_and_replies(self):
        self.mail()
        n = DB.one_pass(self.cfg, agy=self.fake(lambda wt: (wt / "calc.py").write_text("def add(a, b):\n    return a + b\n")), log=lambda s: None)
        self.assertEqual(n, 1)
        r = self.reply()
        self.assertEqual((r["status"], r["branch"]), ("done", "agv/CMD-T1-r1"), r)
        self.assertIn("passed", r["test"])
        sh("git", "fetch", "-q", "origin", "agv/CMD-T1-r1", cwd=self.d / "repo")
        self.assertEqual(DB.one_pass(self.cfg, agy=self.fake(lambda wt: None), log=lambda s: None), 0)  # once only

    def test_failing_tests_stop_and_push_nothing(self):
        self.mail()
        DB.one_pass(self.cfg, agy=self.fake(lambda wt: None), log=lambda s: None)
        r = self.reply()
        self.assertEqual(r["status"], "stop")
        self.assertIn("tests fail", r["reason"])

    def test_editing_the_test_or_other_files_stops(self):
        self.mail()
        DB.one_pass(self.cfg, agy=self.fake(lambda wt: (wt / "tests" / "test_calc.py").write_text("x = 1\n")), log=lambda s: None)
        self.assertIn("test file", self.reply()["reason"])
        self.mail("CMD-T2")
        DB.one_pass(self.cfg, agy=self.fake(lambda wt: (wt / "other.py").write_text("y = 2\n")), log=lambda s: None)
        self.assertIn("outside the spec", self.reply()["reason"])

    def test_unknown_model_and_bad_mail(self):
        self.mail()
        def agy(argv, cwd, timeout):
            return subprocess.CompletedProcess(argv, 0, "gemini-3.7-flash-low  x\n", "")
        DB.one_pass(self.cfg, agy=agy, log=lambda s: None)
        self.assertIn("not in agy models", self.reply()["reason"])
        sh("git", "pull", "-q", "--rebase", "origin", "ga-mailbox", cwd=self.base)
        p = self.base / "to" / "AGY-direct" / "20261007T000001.000000Z-bad.md"
        p.write_text("hello")
        sh("git", "add", ".", cwd=self.base)
        sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "bad", cwd=self.base)
        sh("git", "push", "-q", "origin", "HEAD:ga-mailbox", cwd=self.base)
        DB.one_pass(self.cfg, agy=agy, log=lambda s: None)
        self.assertEqual(self.reply()["status"], "declined")


if __name__ == "__main__":
    unittest.main()
