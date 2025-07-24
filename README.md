# EQEAI OpenHands: EQEAI 表現品質評価AI

このリポジトリは、EQEAI_Specification.mdに基づいて、表現品質評価AIを実装したStreamlitアプリケーションです。

## セットアップ

1. 依存関係のインストール:

   ```
   pip install -r Requirements.txt
   ```

2. `.env`ファイルの作成:

   プロジェクトルートに`.env`ファイルを配置し、`.env.example`を参考にAzure OpenAIの認証情報を設定してください。

3. アプリケーションの実行:

   ```
   streamlit run app.py --server.port 52242 --server.address 0.0.0.0 --server.enableCORS false
   ```

4. Web UIへのアクセス:

   http://localhost:52242 にブラウザでアクセスしてください。

## ファイル構成

- `app.py`: Streamlitアプリケーション本体
- `Requirements.txt`: 必要なPythonモジュール
- `EQEAI_Specification.md`: 仕様書
- `README.md`: このファイル
- `.env.example`: 環境変数テンプレート
- `.gitignore`: Git無視ファイル設定

## 環境変数 (`.env`)

以下の変数を設定してください:

```
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_VERSION=your_api_version_here
AZURE_OPENAI_DEPLOYMENT_NAME=o4-mini
```

## ライセンス

MIT