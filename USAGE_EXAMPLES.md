# 使用例 / Usage Examples

## セットアップ / Setup

```bash
# リポジトリをクローン / Clone repository
git clone https://github.com/nekoy3/vm_diskcheck.git
cd vm_diskcheck

# セットアップスクリプトを実行 / Run setup script
bash setup.sh

# または手動でセットアップ / Or setup manually
pip3 install -r requirements.txt
cp vms.yml.example vms.yml
nano vms.yml
```

## 基本的な使い方 / Basic Usage

### デフォルト設定で実行 / Run with default settings
```bash
python3 vm_diskcheck.py -c vms.yml
```

出力例 / Output example:
```
================================================================================
VM Disk Space Check Results
================================================================================

VM: Web Server 1 (192.168.1.10)
--------------------------------------------------------------------------------
  ✓ OK /
    Device: /dev/sda1
    Size: 100G, Used: 45G, Available: 50G
    Usage: 47%

  ⚠️  WARNING /var
    Device: /dev/sda2
    Size: 50G, Used: 42G, Available: 5G
    Usage: 89%

VM: Database Server (192.168.1.20)
--------------------------------------------------------------------------------
  ✓ OK /
    Device: /dev/sda1
    Size: 200G, Used: 80G, Available: 110G
    Usage: 42%
```

## カスタム閾値 / Custom Threshold

### 閾値を90%に設定 / Set threshold to 90%
```bash
python3 vm_diskcheck.py -c vms.yml --threshold 90
```

これにより、90%以上のディスク使用率の場合のみ警告が表示されます。  
This will only show warnings when disk usage is 90% or higher.

## JSON出力 / JSON Output

### JSON形式で出力 / Output in JSON format
```bash
python3 vm_diskcheck.py -c vms.yml --format json
```

出力例 / Output example:
```json
[
  {
    "name": "Web Server 1",
    "host": "192.168.1.10",
    "status": "success",
    "disks": [
      {
        "device": "/dev/sda1",
        "size": "100G",
        "used": "45G",
        "available": "50G",
        "usage_percent": 47,
        "mount": "/",
        "warning": false
      },
      {
        "device": "/dev/sda2",
        "size": "50G",
        "used": "42G",
        "available": "5G",
        "usage_percent": 89,
        "mount": "/var",
        "warning": true
      }
    ]
  },
  {
    "name": "Database Server",
    "host": "192.168.1.20",
    "status": "success",
    "disks": [
      {
        "device": "/dev/sda1",
        "size": "200G",
        "used": "80G",
        "available": "110G",
        "usage_percent": 42,
        "mount": "/",
        "warning": false
      }
    ]
  }
]
```

### JSONをファイルに保存 / Save JSON to file
```bash
python3 vm_diskcheck.py -c vms.yml --format json > /tmp/disk_status.json
```

## 自動化 / Automation

### Cronジョブで定期実行 / Schedule with cron
```bash
# 毎日午前2時に実行し、結果をログに保存
# Run daily at 2 AM and save results to log
0 2 * * * /usr/bin/python3 /path/to/vm_diskcheck.py -c /path/to/vms.yml >> /var/log/vm_diskcheck.log 2>&1
```

### 閾値超過時にメール通知 / Email notification on threshold exceeded
```bash
#!/bin/bash
# check_and_notify.sh

OUTPUT=$(/usr/bin/python3 /path/to/vm_diskcheck.py -c /path/to/vms.yml)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 1 ] || [ $EXIT_CODE -eq 2 ]; then
    echo "$OUTPUT" | mail -s "VM Disk Space Alert" admin@example.com
fi
```

### Slackに通知 / Slack notification
```bash
#!/bin/bash
# slack_notify.sh

WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
OUTPUT=$(/usr/bin/python3 /path/to/vm_diskcheck.py -c /path/to/vms.yml --format json)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 1 ] || [ $EXIT_CODE -eq 2 ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"VM Disk Space Alert\n\`\`\`$OUTPUT\`\`\`\"}" \
        "$WEBHOOK_URL"
fi
```

## 監視ツールとの統合 / Integration with Monitoring Tools

### Nagios/Icinga統合 / Nagios/Icinga integration
```bash
#!/bin/bash
# nagios_check_vm_disks.sh

/usr/bin/python3 /path/to/vm_diskcheck.py -c /path/to/vms.yml > /dev/null 2>&1
EXIT_CODE=$?

case $EXIT_CODE in
    0)
        echo "OK - All VMs disk usage normal"
        exit 0
        ;;
    1)
        echo "WARNING - Some VMs have high disk usage"
        exit 1
        ;;
    2)
        echo "CRITICAL - Connection errors or critical disk usage"
        exit 2
        ;;
esac
```

### Prometheusへのエクスポート / Export to Prometheus
```bash
# JSON出力をPrometheusのテキスト形式に変換
# Convert JSON output to Prometheus text format
python3 vm_diskcheck.py -c vms.yml --format json | jq -r '.[] | 
  select(.status=="success") | 
  .disks[] | 
  "vm_disk_usage_percent{vm=\"\(.name)\",mount=\"\(.mount)\"} \(.usage_percent)"'
```

## トラブルシューティング例 / Troubleshooting Examples

### デバッグモードで実行 / Run in debug mode
```bash
# SSH接続の詳細を表示
# Show SSH connection details
python3 vm_diskcheck.py -c vms.yml 2>&1 | tee debug.log
```

### 特定のVMのみテスト / Test specific VM only
```bash
# テスト用の設定ファイルを作成
# Create test configuration file
cat > test_vm.yml << EOF
vms:
  - name: "Test VM"
    host: "192.168.1.10"
    user: "admin"
EOF

python3 vm_diskcheck.py -c test_vm.yml
```

### SSH接続テスト / Test SSH connection
```bash
# スクリプトを使わずに直接SSH接続をテスト
# Test SSH connection directly without script
ssh -o StrictHostKeyChecking=no admin@192.168.1.10 "df -h"
```

## ベストプラクティス / Best Practices

1. **閾値の設定 / Threshold Settings**
   - 通常のシステム: 80-85%
   - データベースサーバー: 70-75%
   - ログサーバー: 85-90%

2. **チェック頻度 / Check Frequency**
   - 本番環境: 15-30分ごと
   - 開発環境: 1-2時間ごと
   - ログ保存: 日次

3. **セキュリティ / Security**
   - SSH鍵認証を使用
   - 専用の監視ユーザーを作成
   - 読み取り専用権限で実行

4. **アラート / Alerts**
   - 警告: 閾値超過時
   - エラー: 接続失敗時
   - 情報: 日次サマリー
