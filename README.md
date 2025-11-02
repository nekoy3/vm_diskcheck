# vm_diskcheck

仮想マシンのディスク使用状況をチェックするPythonスクリプト  
Python script to check disk space usage on multiple virtual machines

## 概要 / Overview

このスクリプトは、SSH経由で複数のVMに接続し、各VMのディスク使用状況を監視します。使用率が指定された閾値を超えると警告を表示します。

This script connects to multiple VMs via SSH and monitors disk usage on each VM. It displays warnings when usage exceeds a specified threshold.

## 機能 / Features

- 複数のVMを同時にチェック / Check multiple VMs simultaneously
- SSH接続によるリモート監視 / Remote monitoring via SSH
- カスタマイズ可能な警告閾値 / Customizable warning threshold
- テキストまたはJSON形式での出力 / Output in text or JSON format
- エラーハンドリングと接続タイムアウト / Error handling and connection timeout
- SSHキー認証サポート / SSH key authentication support

## 必要要件 / Requirements

- Python 3.6+
- SSH access to target VMs
- PyYAML library

## インストール / Installation

1. リポジトリをクローン / Clone the repository:
```bash
git clone https://github.com/nekoy3/vm_diskcheck.git
cd vm_diskcheck
```

2. 依存関係をインストール / Install dependencies:
```bash
pip install -r requirements.txt
```

3. 設定ファイルを作成 / Create configuration file:
```bash
cp vms.yml.example vms.yml
```

4. vms.ymlを編集してVMの情報を設定 / Edit vms.yml with your VM details:
```bash
nano vms.yml
```

## 設定 / Configuration

`vms.yml`ファイルに監視対象のVMを設定します：

Configure your VMs in the `vms.yml` file:

```yaml
vms:
  - name: "Web Server 1"
    host: "192.168.1.10"
    user: "admin"
    port: 22
    ssh_key: "/path/to/ssh/key"
  
  - name: "Database Server"
    host: "192.168.1.20"
    user: "root"
```

### 設定項目 / Configuration Options

- `name`: VM名（表示用） / VM name (for display)
- `host`: ホスト名またはIPアドレス / Hostname or IP address
- `user`: SSHユーザー名 / SSH username (default: root)
- `port`: SSHポート / SSH port (default: 22)
- `ssh_key`: SSH秘密鍵のパス（オプション） / Path to SSH private key (optional)

## 使用方法 / Usage

### 基本的な使い方 / Basic usage:
```bash
python3 vm_diskcheck.py -c vms.yml
```

### カスタム閾値を指定 / Custom threshold (90%):
```bash
python3 vm_diskcheck.py -c vms.yml --threshold 90
```

### JSON形式で出力 / JSON output:
```bash
python3 vm_diskcheck.py -c vms.yml --format json
```

### JSONファイルに保存 / Save to JSON file:
```bash
python3 vm_diskcheck.py -c vms.yml --format json > output.json
```

### ヘルプを表示 / Show help:
```bash
python3 vm_diskcheck.py --help
```

## 出力例 / Output Examples

### テキスト形式 / Text format:
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

### JSON形式 / JSON format:
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
      }
    ]
  }
]
```

## 終了コード / Exit Codes

- `0`: すべてのVMが正常で警告なし / All VMs OK, no warnings
- `1`: 警告あり（ディスク使用率が閾値超過） / Warnings present (disk usage exceeds threshold)
- `2`: エラーあり（VM接続失敗など） / Errors occurred (VM connection failures, etc.)

## SSH設定 / SSH Configuration

スクリプトが動作するには、対象VMへのSSHアクセスが必要です：

The script requires SSH access to target VMs:

1. SSH公開鍵を各VMに配置 / Deploy SSH public key to each VM
2. または、SSHパスワード認証を有効化（非推奨） / Or enable SSH password authentication (not recommended)
3. StrictHostKeyCheckingは自動的に無効化されます / StrictHostKeyChecking is automatically disabled

## トラブルシューティング / Troubleshooting

### 接続タイムアウト / Connection timeout:
- VMがオンラインか確認 / Verify VM is online
- ファイアウォール設定を確認 / Check firewall settings
- SSHポートが正しいか確認 / Verify SSH port is correct

### 認証失敗 / Authentication failure:
- SSH鍵のパスが正しいか確認 / Verify SSH key path is correct
- SSH鍵のパーミッション（600）を確認 / Check SSH key permissions (600)
- ユーザー名が正しいか確認 / Verify username is correct

### YAML設定エラー / YAML configuration error:
- YAMLファイルの構文を確認 / Check YAML file syntax
- インデントが正しいか確認 / Verify indentation is correct

## ライセンス / License

MIT License - 詳細はLICENSEファイルを参照 / See LICENSE file for details

## 貢献 / Contributing

プルリクエストを歓迎します！/ Pull requests are welcome!

## 作者 / Author

Created with AI assistance