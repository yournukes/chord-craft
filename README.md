# chord-craft

FastAPI + Vue 3 による単一ページのコード進行メモアプリです。キーとスケールを選んでコードを並べ、名前付きで保存・再読み込みできます。Docker コンテナで公開サーバーとして起動できます。

## 必要要件

- Python 3.11 以降
- Docker 環境（コンテナ実行に使用）

## ローカル環境でのセットアップ（venv）

1. リポジトリ直下で仮想環境を作成し、依存関係をインストールします。
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
2. アプリを起動します。
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   または開発中に簡易起動したい場合は、以下で同じくローカルネットワークからアクセス可能な状態で立ち上げられます（`PORT` 環境変数でポート変更可）。
   ```bash
   python main.py
   ```
3. ブラウザで [http://localhost:8000](http://localhost:8000) を開きます。

### Windows の簡易起動

コマンドプロンプトで以下を実行すると、仮想環境の作成・依存関係インストール・サーバー起動をまとめて行います。
```
start.bat
```

## Docker での起動

1. イメージをビルドします。
   ```bash
   docker build -t chord-craft .
   ```
2. コンテナを起動します（データ永続化のためにローカルディレクトリをマウントする例）。
   ```bash
   docker run -d --name chord-craft -p 8000:8000 -v $(pwd)/data:/app/data chord-craft
   ```
3. ブラウザで [http://localhost:8000](http://localhost:8000) を開きます。

## 使い方

1. 画面左上でキーとスケールタイプを選びます。ルート音はすべて♭表記で並び、スケールに含まれる音が緑色でハイライトされます。ダイアトニックコードは C, Dm, Edim といった表記で一覧化され、対応するディグリーネーム（Ⅱdim, Ⅴ, Ⅴm など）が確認できます。
2. ルート音ボタンまたはプルダウンでルートを選び、コードタイプを選択して「コード追加」を押すと進行に追加されます。カード内の矢印で並び替え、編集ボタンで再設定、削除ボタンで除去できます。
3. 進行名を入力し「保存」を押すとサーバーに保存されます。保存済み一覧から読み込むとスケール設定と並びが復元され、不要な進行は削除できます。
4. 新規作成したい場合は「新規」で状態をリセットします。

## 技術構成

- フロントエンド: Vue 3 + Tailwind CSS（CDN）、SPA 構成
- バックエンド: FastAPI（`/api/progressions` で進行を CRUD）
- データ永続化: `data/data.json`（コンテナ外にボリュームマウント推奨）
- コンテナ: `python:3.11-slim` ベース、`uvicorn` でポート 8000 を公開

## 補足

- すべての文章・コミットは日本語で記述します（`agents.md` 参照）。
- ネットワーク不要のシンプル構成で、追加のビルドステップは不要です。
