# Goo-net Pit 自動車OBD診断プラットフォーム

AWS/Bedrock ベースの日本車専用OBD診断システム

## 🚗 概要

SmarBotをベースに、日本の自動車市場向けのOBD診断プラットフォームを構築しました。AWS/Bedrockを活用し、Goo-net Pitのデータ形式に対応した専門的な診断システムです。

## 🔧 主要機能

### 1. OBDコード分析
- 日本車特有のOBDコード（U3003-1C、C1AE687等）の解析
- ホンダ、トヨタ、日産等の主要メーカー対応
- リアルタイム診断と修理提案

### 2. 診断データ検索
- セマンティック検索（BM25 + ベクトル検索）
- 車種・メーカー別フィルタリング
- 関連記事の自動推奨

### 3. AI診断チャット
- 専門知識を持つAIアシスタント
- 日本語での技術説明
- 修理手順の詳細ガイド

### 4. CSVデータ取り込み
- Goo-net Pit形式のCSV自動処理
- OBDコード自動抽出
- 車両情報のパース

## 🏗️ アーキテクチャ

### AWS サービス
```
Azure OpenAI → AWS Bedrock (Claude/Titan)
Azure Cognitive Search → AWS OpenSearch
Azure Blob Storage → AWS S3
Azure Functions → AWS Lambda
Azure Monitor → AWS CloudWatch
```

### データモデル
- **DiagnosticArticle**: 診断記事
- **OBDCode**: 故障診断コード
- **Vehicle**: 車両情報
- **ServiceGarage**: サービス工場
- **DiagnosticSession**: 診断セッション

## 🚀 セットアップ

### 1. 環境変数設定
```bash
# AWS設定
AWS_BEDROCK_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_OPENSEARCH_ENDPOINT=your_endpoint
```

### 2. サービス起動
```bash
# OpenSearchとS3を含む開発環境
docker compose up -d

# または個別サービス
docker compose up opensearch s3-local
```

### 3. インデックス作成
```bash
curl -X POST http://localhost:8888/api/automotive/health
```

## 📊 データ形式

### CSV入力例
```csv
article_id,create_time,category_id,text,summary,article_length,sentence_scores
1051429,2025-03-08T04:47:49.956554,10,"ホンダ・Ｎ－ＢＯＸカスタム（2017）の故障診断...U3003-1C　12Vバッテリ 電圧値異常...","ホンダ・N-BOXカスタムのパワーステアリング診断",106,"[[1.4133414 1.5787659]]"
```

### 対応OBDコード
- **Uコード**: ネットワーク/通信エラー（U3003-1C等）
- **Pコード**: パワートレイン系（P0171等）
- **Cコード**: シャシー系（C1AE687等）
- **Bコード**: ボディ系（B1342等）

## 🔍 API エンドポイント

### OBDコード分析
```http
POST /api/automotive/analyze-obd-code
Content-Type: application/json

{
  "obd_code": "U3003-1C",
  "vehicle_make": "Honda",
  "vehicle_model": "N-BOX",
  "vehicle_year": 2017
}
```

### 診断検索
```http
POST /api/automotive/search-diagnostics
Content-Type: application/json

{
  "query": "パワーステアリング 異常",
  "vehicle_make": "Honda",
  "limit": 10
}
```

### AIチャット
```http
POST /api/automotive/chat
Content-Type: application/json

{
  "message": "N-BOXのパワーステアリング警告灯が点灯しました"
}
```

### CSV取り込み
```http
POST /api/automotive/ingest-csv
Content-Type: multipart/form-data

file: sample_automotive_data.csv
```

## 🎯 専門機能

### 1. 日本語技術用語対応
- カタカナ・ひらがな・漢字の混在テキスト処理
- 自動車専門用語の正規化
- メーカー固有の表現理解

### 2. OBDコード自動抽出
```python
# テキストからOBDコードを自動検出
patterns = [
    r'[PCBU]\d{4}[-]?\w*',  # 標準OBDコード
    r'[UPC]\d{4}[-]?\d*[A-Z]*',  # 日本独自形式
]
```

### 3. 車両情報パース
```python
# 日本語テキストから車両情報を抽出
make_patterns = {
    VehicleMake.HONDA: [r'ホンダ', r'Honda', r'Ｎ－ＢＯＸ'],
    VehicleMake.TOYOTA: [r'トヨタ', r'Toyota', r'プリウス'],
    VehicleMake.NISSAN: [r'ニッサン', r'Nissan', r'セレナ'],
}
```

## 📱 フロントエンド

### React コンポーネント
- **AutomotiveDiagnostic**: メイン診断インターフェース
- 日本語UI完全対応
- リアルタイムOBD検索
- セマンティック診断結果表示

### 主要画面
1. **OBDコード分析画面**: コード入力と解析結果
2. **診断検索画面**: キーワード検索と結果一覧
3. **AIチャット画面**: 対話式診断サポート
4. **データ管理画面**: CSV取り込みとインデックス管理

## 🔧 開発・カスタマイズ

### モデル追加
```python
# 新しい車両メーカー追加
class VehicleMake(Enum):
    HONDA = "Honda"
    TOYOTA = "Toyota"
    # 新規追加
    LEXUS = "Lexus"
```

### プロンプト調整
```python
# 診断特化プロンプト
AUTOMOTIVE_DIAGNOSTIC_PROMPT = """
あなたは日本の自動車OBD診断の専門家です。
特定のメーカー・車種に精通し、実践的なアドバイスを提供してください。
"""
```

## 📈 パフォーマンス

### 検索性能
- **ハイブリッド検索**: BM25 + kNN ベクトル検索
- **多言語対応**: Kuromoji 日本語アナライザー
- **リアルタイム**: <200ms レスポンス

### スケーラビリティ
- **OpenSearch**: 水平スケーリング対応
- **Bedrock**: サーバーレススケーリング
- **S3**: 無制限ストレージ

## 🔒 セキュリティ

### AWS セキュリティ
- IAM ロールベースアクセス制御
- VPC 内部ネットワーク
- 暗号化ストレージ（S3/OpenSearch）

### データ保護
- 診断データの匿名化
- GDPR 準拠データ処理
- セキュアAPI通信（HTTPS）

## 📚 参考資料

### OBD規格
- ISO 15031 (OBD-II)
- SAE J1979 (診断プロトコル)
- 日本独自拡張仕様

### AWS サービス
- [Bedrock ドキュメント](https://docs.aws.amazon.com/bedrock/)
- [OpenSearch ガイド](https://docs.aws.amazon.com/opensearch-service/)
- [S3 開発者ガイド](https://docs.aws.amazon.com/s3/)

## 🤝 コントリビューション

1. Issue 作成
2. Feature ブランチ作成
3. Pull Request 送信
4. レビュー・マージ

## 📄 ライセンス

MIT License - 詳細は LICENSE ファイルを参照

---

**開発チーム**: AWS/Bedrock 移行プロジェクト  
**更新日**: 2025年3月8日  
**バージョン**: 1.0.0 (初期リリース)