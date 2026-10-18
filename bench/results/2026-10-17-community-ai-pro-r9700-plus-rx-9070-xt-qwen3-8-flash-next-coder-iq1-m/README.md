# Community benchmark on AMD Radeon AI PRO R9700 + AMD Radeon RX 9070 XT

Measured on 2026-10-17 with `tools/strata_bench.py` (suite 1, 3 runs per test, medians with ranges). Speeds are the engine's own timings; first-token times are measured by the client over HTTP. Speed only: no correctness check was run.

## Hardware and software

- GPU and VRAM: AMD Radeon AI PRO R9700 + AMD Radeon RX 9070 XT, 48 GiB VRAM
- CPU: AMD Ryzen 7 7800X3D 8-Core Processor (8 cores, 16 threads); installed RAM: 63.2 GiB; storage: not measured
- OS: Windows 11 (10.0.26200); GPU driver: 32.0.32015.2008; CUDA: not read
- Strata: project 0.1.44.1, commit 9832cad5; engine 0.1.44.1
- Background workloads and power limits: not recorded

## Model and configuration

- Model and quantization: qwen3.8-flash-next-coder-iq1_m
- Context: 131072 tokens; parallel slots: 1
- Settings: the install's own configuration, unchanged (hip backend); thinking off for the suite; temperature 0

```text
strata.exe --pack coder-iq1_m --native Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00001-of-00002.gguf --ple-gguf Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00002-of-00002.gguf --expert-profile expert-profile-coder.bin --expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mtp rt --max-context 131072 --kv int8 --kv-resident 32768 --vision
```

Environment of the config: `STRATA_HIPBLASLT_TUNING=gfx1201-hipblaslt-100500.txt`, `HIP_VISIBLE_DEVICES=0,2`, `STRATA_PCIE_AUTO_SPLIT=1`, `STRATA_ARENA_PIN_GIB=8`

## Method

Run by `python tools/strata_bench.py` against the HTTP API of a Strata server (started by the benchmark from the install configuration); model loading is not timed. One warm-up chat and a 1K prompt are discarded first. Every prompt starts with a unique tag, so the conversation cache cannot help the fresh-prompt tests.

- short chat: the three questions of `tools/ab_engine.py`, up to 100 new tokens, 3 runs
- 4K / 16K prompts: generated word lists sized by a calibration request, 24 new tokens, 3 fresh prompts each
- agent session: system prompt and four tools, then 5 turns that each add about 1500 words of a project file and continue from the model's own earlier answers (the way agent clients resend a conversation), 64 new tokens per turn, 3 sessions; the cache numbers come from the answer's usage (`cached_tokens`) and timings (`prompt_n`)
- concurrency (when run): N requests sent at the same moment, total tokens over the wall time of the burst, latency over all requests

## Results

| Configuration | Actual prompt tokens | Reused tokens | Generated tokens | Runs | Prompt tok/s median and range | Decode tok/s median and range | TTFT seconds median and range |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| short chat | 46 (43-51) | 0 | 100 (100-100) | 9 | not measured | 55.4 (49.8-89.9) | 0.29 (0.26-0.33) |
| 4K prompt, fresh | 4019 (4019-4019) | 0 (0-0) | 24 cap | 3 | 1371.8 (1359.1-1374.4) | not measured | 2.98 (2.95-3.00) |
| 16K prompt, fresh | 16058 (16058-16058) | 0 (0-0) | 24 cap | 3 | 1952.9 (1945.1-1970.6) | not measured | 8.28 (8.19-8.30) |
| agent session, follow-up turns | 14540 (14521-14542) at the last turn | see below | up to 64 | 3 | see below | 62.2 (45.8-74.0) | 2.49 (1.68-2.84) |

Ranges are the lowest and highest of the runs; `Runs` counts requests that returned a token.

### Agent session (conversation cache)

Cache hit over the follow-up turns: 68.5 % (68.5-68.7); earlier-turn tokens read again per session: 74 (4-75) (earlier turns that the cache did not hold; the 13729 (13729-13730) new tokens of the files are read once); first turn (nothing cached) first token: 1.00 s (0.97-1.07).

| Turn (run 1) | Prompt tokens | Reused | Read | Prompt tok/s | First token (s) | Decode tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 609 | 0 | 609 | 592.8 | 1.075 | 62.7 |
| 1 | 3758 | 635 | 3123 | 1250.8 | 2.546 | 62.2 |
| 2 | 5291 | 3821 | 1470 | 892.3 | 1.681 | 54.6 |
| 3 | 8689 | 5309 | 3380 | 1214.8 | 2.839 | 45.8 |
| 4 | 11577 | 8715 | 2862 | 1157.8 | 2.52 | 65.2 |
| 5 | 14540 | 11641 | 2899 | 1201.3 | 2.48 | 58.2 |

Per-request data: `results.json`. Engine log lines from the start: `engine-log-excerpt.txt` (when this run started the server).

## Correctness and limitations

Not measured: this is a speed suite. The conversation uses the model's own replies, so token counts differ a little between runs. Machine details come from the server, `nvidia-smi`/`rocm-smi` and the OS; background load and power limits are not recorded. Total time of the suite: 109 s.
