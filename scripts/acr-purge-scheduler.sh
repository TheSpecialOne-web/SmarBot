# https://learn.microsoft.com/en-us/azure/container-registry/container-registry-auto-purge
# 現在行われているコンテナレジストリの不要なイメージの定期削除を設定しているスクリプト
# スケジュール内容を変更するときは、このスクリプトを変更してから実行すること
# 現在のスケジュール内容: 毎日1時に7日前のイメージを削除

PURGE_CMD="acr purge \
  --filter 'neo-smart-chat-api:.*' --filter 'neo-smart-chat-jobs:.*' --filter 'neo-smart-chat-function:.*' \
  --ago 7d --untagged --keep 3"

az acr task create --name dailyPurgeTask \
  --cmd "$PURGE_CMD" \
  --schedule "0 1 * * *" \
  --registry crneoscdev \
  --context /dev/null

# 単発実行用コマンド
# az acr run --cmd "$PURGE_CMD" --registry crneoscdev /dev/null
