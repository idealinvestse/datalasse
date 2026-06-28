---
name: "start-crypto-miner"
description: "Start SRBMiner-Multi on hemmalasse for GPU mining. Detects binary, validates config, launches in background with health checks."
---

# Start Crypto Miner — GPU Mining on hemmalasse

> **Status:** 📝 Proposal — pending review → ready to apply
> **Owner:** Alabama
> **Target host:** hemmalasse (Windows + RTX 5070 12GB)
> **Default algorithm:** `octopus` (Cortex, CTXC) — chosen by Alabama ("C")
> **Wallet handling:** Local config file only — never hardcoded in skill or transmitted via Telegram

## Purpose

Launch SRBMiner-Multi on hemmalasse to mine cryptocurrency on a configurable pool. Designed to be triggered remotely by Moss (via Telegram or `sessions_send`).

**Note on algorithm choice:** Alabama chose algo C = `octopus` (Cortex) over the original `pearlhash` (Pearl). Octopus is better optimized for newer NVIDIA architectures (Blackwell) than PearlHash, which is unverified on RTX 5070.

## ⚠️ Important — read before use

This skill launches a long-running compute process. Be aware of:

1. **Electricity cost** — RTX 5070 at full load draws ~200W. 24/7 mining ≈ $50–100/month in electricity (Swedish kWh price ~0.5–1 SEK/kWh).
2. **GPU wear** — Continuous high load reduces GPU lifespan. NVIDIA consumer warranty does **not** cover mining damage.
3. **Thermal** — Sustained load produces heat; ensure adequate case airflow in summer months.
4. **ROI** — Verify profitability on whattomine.com or similar BEFORE running 24/7. Octopus on RTX 5070 is also new — hashrate unverified.
5. **Pool fees** — Pool takes a small fee; payouts below threshold are forfeited.

## 🔒 Wallet address handling

The wallet address is **never** hardcoded in the skill and **never** transmitted via Telegram. The skill reads it from a local config file that Alabama creates on hemmalasse himself.

```
C:\Users\<USER>\.openclaw\miner-config.json
```

Alabama must:
1. Log in to his mining pool account
2. Copy his payment address from the pool's "My Account" page
3. Paste it into the config file **locally on hemmalasse**

The wallet address that ends up being used will be the one Alabama physically types into the config file. Moss never sees or transmits it.

## Pre-flight checks (run before launching miner)

- [ ] `SRBMiner-MULTI.exe` exists in expected path (default: `C:\mining\SRBMiner-MULTI.exe`)
- [ ] NVIDIA driver is recent (≥555.x recommended for Blackwell)
- [ ] GPU 0 is RTX 5070 and not currently in use (no LM Studio inference running)
- [ ] `miner-config.json` exists with valid wallet address + worker name
- [ ] Pool URL is reachable (`Test-NetConnection <pool-host> -Port <pool-port>`)

## Configuration file (per-user, set locally on hemmalasse)

Location: `C:\Users\$env:USERNAME\.openclaw\miner-config.json`

```json
{
  "walletAddress": "<USER FILLS IN LOCALLY>",
  "workerName": "<USER FILLS IN LOCALLY>",
  "algorithm": "octopus",
  "poolUrl": "cortex.woolypooly.com:3000",
  "poolPassword": "x",
  "srbminerPath": "C:\\mining\\SRBMiner-MULTI.exe",
  "logPath": "C:\\mining\\logs\\miner.log",
  "autoRestart": true,
  "maxTempC": 83,
  "disableCpu": true
}
```

Common pool URLs for octopus (Cortex):
- `cortex.woolypooly.com:3000` (multi-region)
- `cortex.2miners.com:2222` (EU/US/Asia)
- `cortex.herominers.com:1123`

## Usage

```powershell
# Direct call (from hemmalasse PowerShell):
.\bin\invoke-miner.ps1 -Start

# Remote call (from Moss via Telegram):
# Alabama → @datalasse_bot: "starta miner på hemmalasse"
# Moss → hemmalasse: invoke skill with args=["start"]
```

## Implementation outline

1. **Resolve config:** Read `miner-config.json` from user home dir. Fail fast if missing or invalid.
2. **Validate inputs:**
   - Wallet address is non-empty string
   - Worker name is alphanumeric + dash/underscore only (max 32 chars)
   - Algorithm is in supported list: `octopus`, `pearlhash`, `kheavyhash`, `kawpow`, `autolykos2`
   - `srbminerPath` exists and is executable
3. **Pre-flight checks:**
   - Run `nvidia-smi --query-gpu=index,name,utilization.gpu,temperature.gpu --format=csv`
   - If GPU util > 50 %: abort (LM Studio or other workload active)
   - If GPU temp > 75 °C: abort (thermal risk)
4. **Launch miner:**
   ```powershell
   $args = @(
     "--algorithm", $config.algorithm
     "--pool", $config.poolUrl
     "--wallet", "$($config.walletAddress).$($config.workerName)"
     "--password", $config.poolPassword
   )
   if ($config.disableCpu) { $args += "--disable-cpu" }
   $args += @("--log-file", $config.logPath)
   Start-Process -FilePath $config.srbminerPath -ArgumentList $args -WindowStyle Hidden
   ```
5. **Health check (after 30 s):**
   - Confirm process is running (`Get-Process SRBMiner-MULTI`)
   - Read first 50 lines of log; expect "Pool connected" + non-zero hashrate
   - If hashrate = 0 for >2 min: kill process, alert Alabama via Telegram
6. **Watchdog:**
   - If `autoRestart: true`: monitor process every 5 min; restart on crash
   - If GPU temp > `maxTempC`: throttle power limit via `nvidia-smi -pl 70`

## Stopping the miner

```powershell
# Direct call:
.\bin\invoke-miner.ps1 -Stop

# Kills all SRBMiner-MULTI.exe processes:
Get-Process SRBMiner-MULTI -ErrorAction SilentlyContinue | Stop-Process -Force
```

## Telemetry & logs

- Per-run log: `C:\mining\logs\miner-YYYY-MM-DD.log`
- Summary every 6 h: hashrate, temp, accepted/rejected shares, payout estimate
- Alerts: Telegram @datalasse_bot → Alabama if process crashes, temp >85 °C, hashrate drops 50 %+ for >10 min

## Rollback

Removing the skill is safe:
1. Stop miner (`Stop-Process SRBMiner-MULTI`)
2. Delete `C:\mining\` directory (or wherever SRBMiner lives)
3. Delete `C:\Users\$env:USERNAME\.openclaw\miner-config.json`
4. Uninstall via skill-workshop (Moss workspace side)

## Notes

- This skill is **NOT** yet installed on hemmalasse. After approval, it needs to be synced from the workspace to hemmalasse via Tailscale + the workspace-sync procedure (or manually copied).
- Wallet address verification is Alabama's responsibility — log in to the pool's website and confirm before first run.
