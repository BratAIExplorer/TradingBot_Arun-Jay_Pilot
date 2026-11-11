#!/usr/bin/env bash
# Drift check: do the Voyager files running on the VPS match the committed branch?
# Run from the repo root on the laptop:  bash deploy/verify_sync.sh
# Read-only. Ignores line endings (VPS copies may be CRLF). Exit 1 if anything differs.
# Deploys are by hand (scp + restart); /opt/voyager is NOT pulled from GitHub on purpose.
VPS="${VPS:-root@76.13.179.32}"
FILES="brokers/dip_engine.py brokers/ibkr_broker.py research/spike_logger.py research/spike_scorer.py
deploy/gateway_watch.py deploy/daily_summary.py deploy/setup_alert.py
tests/test_spike.py tests/test_daily_summary.py tests/test_gateway_watch.py tests/test_dip_engine.py"
bad=0
for f in $FILES; do
  l=$(git show "HEAD:$f" | tr -d '\r' | sha256sum | cut -c1-12)
  r=$(ssh -o BatchMode=yes "$VPS" "tr -d '\r' < /opt/voyager/$f | sha256sum" 2>/dev/null | cut -c1-12)
  if [ "$l" = "$r" ]; then echo "ok        $f"; else echo "DIFFERENT $f"; bad=1; fi
done
exit $bad
