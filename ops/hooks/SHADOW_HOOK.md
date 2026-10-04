# 새 세션의 K17 예산 훅 — shadow (사용자 허락: BD-318)

새로 여는 작업 세션은 **첫 단계**로 아래를 한다. shadow = 기록만, 아무것도 막지 않는다(baseline 이 200k 문맥 사건으로 확인: 출력 없음, `stage: checkpoint` 기록).
Claude Code 는 세션 중에 바뀐 설정의 hooks 를 바로 적용하고, `.claude/settings.local.json` 은 커밋에서 빠진다(문서: settings — When edits take effect / Keep personal settings out of a repository).

```sh
python3 -m venv .ga/hookvenv
.ga/hookvenv/bin/pip -q install "rlo-sdk[sensor] @ git+https://github.com/cogito5170/rlo-SDK@063b861df32e783f5cacde5db079187965a82f5c"
mkdir -p .ga && .ga/hookvenv/bin/python -m rlo.hooks install-hook \
  --settings .claude/settings.local.json \
  --model "$(.ga/hookvenv/bin/python -c 'import rlo,os;print(os.path.join(os.path.dirname(rlo.__file__),"data","cc_tools_model.json"))')" \
  --mode shadow --record "$PWD/.ga/rlo-hook.jsonl" \
  --budget-soft 120000 --budget-hard 150000 --budget-state STATE.md --budget-mode shadow --runtime claude_code
```

`.claude/settings.local.json` · `.ga/` 는 커밋하지 않는다. 보고 직전에 예산 기록만 요약해 커밋한다(도구 입력 · 이유 문장은 넣지 않음):

```sh
.ga/hookvenv/bin/python -c "import json;r=[json.loads(l) for l in open('.ga/rlo-hook.jsonl') if '\"stage\"' in l];s=[x for x in r if 'stage' in x];c=[x['ctx'] for x in s if x.get('stage')=='checkpoint' and isinstance(x.get('ctx'),int)];print(json.dumps({'warn':sum(x['stage']=='warn' for x in s),'checkpoint':len(c),'max_ctx':max([x['ctx'] for x in s if isinstance(x.get('ctx'),int)] or [0]),'first_checkpoint_ctx':(c[0] if c else None)}))" > reports/<CMD>.budget.json
```
