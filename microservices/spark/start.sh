#!/bin/sh
echo "Starting ngrok."
ngrok http 5000 --log /ngrok.log >/dev/null &
echo "Waiting for tunnel URL..."
while true; do
  URL=$(curl -s localhost:4040/api/tunnels | jq -r .tunnels[0].public_url)
  [ "$URL" == "null" ] && continue
  [ "$URL" ] && break
  sleep 1
done
export roomfinder_spark_bot_url=$URL
python /app/spark_bot.py

