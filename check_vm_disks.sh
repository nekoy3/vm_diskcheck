#!/bin/bash

#==============================================================================
# 設定項目
#==============================================================================
# DiscordのWebhook URL
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/00000000/xxxxxxxxxxxx"

# アラートを発動させるディスク使用率のしきい値 (%)
ALERT_THRESHOLD=95

# VMホスト名リストの取得コマンド
# これは一例で、権威DNSにmynk_hosts.txtという自己ゾーン転送によって得られたホスト名をテキストファイルにリストとしてまとめて取得できるようにしてある mynk.homeはローカルなドメイン名
HOST_LIST_CMD="curl -s --fail http://ns.mynk.home/mynk_hosts.txt | awk '{print \$1}' | sort -u"

#==============================================================================
# 1. 必要なコマンドの存在チェック
#==============================================================================
if ! command -v jq &> /dev/null; then
    echo "エラー: 'jq' が必要です。インストールしてください。" >&2
    exit 1
fi

#==============================================================================
# 2. メイン処理
#==============================================================================
all_results=""
urgent_hosts=""
has_urgent_host=false

while read -r host; do
    #9100が確かnode_exporterを入れたノードのメトリクス表示するやつ
    metrics=$(curl -s --connect-timeout 2 "http://${host}:9100/metrics")

    if [ $? -eq 0 ]; then
        result_line=$(echo "$metrics" | \
            grep -E 'node_filesystem_(size|avail)_bytes' | \
            awk -v host="$host" '
            BEGIN { FS="} " }
            /node_filesystem_size_bytes/ { gsub(/.*mountpoint="/, "", $1); gsub(/".*/, "", $1); size[$1] = $2 }
            /node_filesystem_avail_bytes/ { gsub(/.*mountpoint="/, "", $1); gsub(/".*/, "", $1); avail[$1] = $2 }
            END {
                mount = "/"
                if (size[mount] > 0 && avail[mount] != "") {
                    used = size[mount] - avail[mount]
                    pct = (used / size[mount]) * 100
                    used_gb = used / (1024*1024*1024)
                    size_gb = size[mount] / (1024*1024*1024)
                    # ★修正点: 全ての列のフォーマットを統一
                    printf "%-25s | %12s | %12s | %8s", host, sprintf("%.2f GB", used_gb), sprintf("%.2f GB", size_gb), sprintf("%.1f%%", pct)
                }
            }')
        
        if [ -n "$result_line" ]; then
            # ★修正点: 改行を確実に追加する
            all_results="${all_results}${result_line}\n"
            percentage=$(echo "$result_line" | awk -F'|' '{print $4}' | tr -d ' %')
            
            if (( $(echo "$percentage >= $ALERT_THRESHOLD" | bc -l) )); then
                has_urgent_host=true
                alert_line=$(echo "$result_line" | awk -F'|' '{printf "%-25s | 使用率: %.1f%%", $1, $4}')
                urgent_hosts="${urgent_hosts}${alert_line}\n"
            fi
        fi
    else
        error_msg=$(ping -c 1 -W 1 "$host" &> /dev/null && echo "Error: no exporter" || echo "Error: timeout")
        # ★修正点: エラー行もデータ行とフォーマットを完全に一致させる
        error_line=$(printf '%-25s | %12s | %12s | %s' "$host" "" "" "$error_msg")
        all_results="${all_results}${error_line}\n"
    fi
done < <(eval $HOST_LIST_CMD)

#==============================================================================
# 3. Discord通知
#==============================================================================
if [ -n "$all_results" ]; then
    report_file=$(mktemp)
    trap 'rm -f "$report_file"' EXIT

    # ★修正点: ヘッダーもデータ行とフォーマットを完全に一致させる
    header=$(printf "%-25s | %-12s | %-12s | %-8s\n" "Host" "Used" "Total" "Usage %")
    separator="--------------------------|--------------|--------------|---------"
    
    echo -e "${header}\n${separator}" > "$report_file"
    # `printf "%b"` を使って変数内の `\n` を確実に解釈させる
    printf "%b" "$all_results" | sed '/^$/d' | sort -t'|' -k4 -hr >> "$report_file"

    total_count=$(printf "%b" "$all_results" | sed '/^$/d' | wc -l | tr -d ' ')
    error_count=$(printf "%b" "$all_results" | grep -c "Error:")
    urgent_count=$(echo -e "$urgent_hosts" | sed '/^$/d' | wc -l | tr -d ' ')

    summary_embed=$(jq -n \
      --arg total "$total_count" \
      --arg errors "$error_count" \
      --arg urgent "$urgent_count" \
      '{
        "embeds": [{
          "title": "ディスク使用率 定期レポート",
          "color": 3447003,
          "fields": [
            {"name": "チェック対象ホスト", "value": ($total + "台"), "inline": true},
            {"name": "エラー", "value": ($errors + "台"), "inline": true},
            {"name": "高負荷アラート ('$ALERT_THRESHOLD'%超)", "value": ($urgent + "台"), "inline": true}
          ],
          "footer": {"text": "詳細は添付の report.txt をご確認ください。"}
        }]
      }')

    curl -s -H "Accept: application/json" \
         -F "payload_json=${summary_embed}" \
         -F "file1=@${report_file};filename=report.txt" \
         "$DISCORD_WEBHOOK_URL" > /dev/null 2>&1
fi

if [ "$has_urgent_host" = true ]; then
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)
    
    json_embed=$(jq -n \
      --arg description "$(echo -e "$urgent_hosts")" \
      --arg ts "$timestamp" \
      '{
        "content": "@everyone ディスク使用率が'${ALERT_THRESHOLD}'%を超えたサーバーがあります！",
        "embeds": [{
            "title": "🚨 緊急ディスク容量アラート",
            "description": ("```\n" + $description + "```"),
            "color": 15158332,
            "timestamp": $ts
        }]
      }')

    curl -s -H "Content-Type: application/json" -X POST -d "$json_embed" "$DISCORD_WEBHOOK_URL" > /dev/null 2>&1
fi
