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

# 2. ノード数が100のファイルを削除（実際のファイル名パターンに基づく）
echo "2. ノード数が100のファイルを削除中..."
# 実際のファイル名パターン: node_i_BTC_伝搬遅延_1000_100000_first_seen_dynamic_share.csv
# ノード数が100の場合、パターンは node_i_BTC_伝搬遅延_1000_100_first_seen_dynamic_share.csv になるはず
NODE_100_FILES=$(find "$TARGET_DIR" -name "node_*_BTC_*_1000_100_first_seen_dynamic_share*" -type f)
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
        find "$TARGET_DIR" -name "node_*_BTC_*_1000_100_first_seen_dynamic_share*" -type f -delete
        echo "ノード数が100のファイルを削除しました"
    else
        echo "削除をキャンセルしました"
    fi
else
    echo "ノード数が100のファイルは見つかりませんでした"
fi

echo ""
echo "削除処理が完了しました"
