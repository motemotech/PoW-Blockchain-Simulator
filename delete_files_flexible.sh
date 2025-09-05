#!/bin/bash

# 削除対象ディレクトリ
TARGET_DIR="data/20250903_125025"

# ディレクトリが存在するかチェック
if [ ! -d "$TARGET_DIR" ]; then
    echo "エラー: ディレクトリ '$TARGET_DIR' が見つかりません"
    exit 1
fi

echo "削除対象ディレクトリ: $TARGET_DIR"
echo ""

# 1. copyという文字列が含まれるファイルを削除
echo "1. copyという文字列が含まれるファイルを削除中..."
COPY_FILES=$(find "$TARGET_DIR" -name "*copy*" -type f)
if [ -n "$COPY_FILES" ]; then
    echo "削除対象ファイル数: $(echo "$COPY_FILES" | wc -l)"
    echo "削除対象ファイル（最初の10件）:"
    echo "$COPY_FILES" | head -10
    if [ $(echo "$COPY_FILES" | wc -l) -gt 10 ]; then
        echo "... 他 $(($(echo "$COPY_FILES" | wc -l) - 10)) ファイル"
    fi
    echo ""
    echo "これらのファイルを削除しますか？ (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        find "$TARGET_DIR" -name "*copy*" -type f -delete
        echo "copyという文字列が含まれるファイルを削除しました"
    else
        echo "削除をキャンセルしました"
    fi
else
    echo "copyという文字列が含まれるファイルは見つかりませんでした"
fi

echo ""

# 2. ノード数が100のファイルを削除
echo "2. ノード数が100のファイルを削除中..."
# 複数のパターンを試す（実際のファイル名に応じて調整）
NODE_100_FILES=""
PATTERNS=(
    "node_*_BTC_*_1000_100_first_seen_dynamic_share*"
    "node_*_BTC_*_*_100_*"
    "node_*_BTC_*_100_*"
)

for pattern in "${PATTERNS[@]}"; do
    files=$(find "$TARGET_DIR" -name "$pattern" -type f)
    if [ -n "$files" ]; then
        NODE_100_FILES="$files"
        echo "パターン '$pattern' でファイルが見つかりました"
        break
    fi
done

if [ -n "$NODE_100_FILES" ]; then
    echo "削除対象ファイル数: $(echo "$NODE_100_FILES" | wc -l)"
    echo "削除対象ファイル（最初の10件）:"
    echo "$NODE_100_FILES" | head -10
    if [ $(echo "$NODE_100_FILES" | wc -l) -gt 10 ]; then
        echo "... 他 $(($(echo "$NODE_100_FILES" | wc -l) - 10)) ファイル"
    fi
    echo ""
    echo "これらのファイルを削除しますか？ (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "$NODE_100_FILES" | xargs rm -f
        echo "ノード数が100のファイルを削除しました"
    else
        echo "削除をキャンセルしました"
    fi
else
    echo "ノード数が100のファイルは見つかりませんでした"
    echo "利用可能なファイル名パターンを確認しますか？ (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "ディレクトリ内のファイル名パターン:"
        find "$TARGET_DIR" -name "node_*" -type f | head -20 | sed 's/.*\///' | sort | uniq -c
    fi
fi

echo ""
echo "削除処理が完了しました"
