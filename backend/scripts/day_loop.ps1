# Day marathon extended until 2026-09-12 20:00 local time
$ErrorActionPreference = 'Continue'
$stopAt = Get-Date '2026-09-12 20:00:00'
$intervalSec = 1500

while ($true) {
  $now = Get-Date
  if ($now -ge $stopAt) {
    Write-Output 'AGENT_LOOP_TICK_daytime-lexscan {"prompt":"STOP daytime loop. Past 20:00 on 2026-09-12. Summarize all daytime work, finalize DAY_FINAL report, commit remaining docs if needed, do not start major new features."}'
    break
  }

  Start-Sleep -Seconds $intervalSec

  $now = Get-Date
  if ($now -ge $stopAt) {
    Write-Output 'AGENT_LOOP_TICK_daytime-lexscan {"prompt":"STOP daytime loop. Past 20:00 on 2026-09-12. Summarize all daytime work, finalize DAY_FINAL report, commit remaining docs if needed, do not start major new features."}'
    break
  }

  $minsLeft = [math]::Round(($stopAt - $now).TotalMinutes)
  $payload = "AGENT_LOOP_TICK_daytime-lexscan {`"prompt`":`"Daytime tick EXTENDED to 20:00. Minutes left: $minsLeft. Priority: lawyer/accountant pain-point features, professional UI, Lex sharpness, document+commit. Run QA after improvements. Do not stop early.`"}"
  Write-Output $payload
}
