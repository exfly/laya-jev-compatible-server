# TODO

https://github.com/hxh-robb/pokemon-roms/blob/master/ROM/Pokemon%20-%20Red%20Version%20(USA%2C%20Europe).gb

```bash
cd jev-plays-pokemon-red/
JEV_BASE_URL=http://127.0.0.1:8001 TYPESAFE_API_KEY=test \
    uv run jpp play \
      --rom "../tmp/Pokemon - Red Version (USA, Europe).gb" \
      --state "../tmp/red-bedroom.state" \
      --overlay \
      --max-decisions 10000000000 \
      --out ../tmp/jpp-run.jsonl
```
