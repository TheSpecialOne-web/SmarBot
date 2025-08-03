export const APPROACH_VARIABLES = [
  {
    key: "query_system_prompt",
    description:
      "クエリ生成を行うChatGPTのシステムプロンプトを設定。neoAI Chat上に制作物を乗せるPoC以外では基本的にはいじらなくて良い部分。精度が気になる場合は、後述のドキュメントに関するパラメータを調整するか、開発メンバーにご一報いただきたい。",
    disabled: false,
    type: "text",
  },
  {
    key: "response_system_prompt",
    description:
      "回答生成を行うChatGPTのシステムプロンプトを設定する箇所1。デフォルトでは、アシスタントの役割、タスク内容、ドキュメントが何についてか、などを記述している。注意点などを変更したい場合は、response_system_prompt_hiddenを変更してください。",
    disabled: false,
    type: "text",
  },
  {
    key: "response_system_prompt_hidden",
    description:
      "回答生成を行うChatGPTのシステムプロンプトを設定する箇所2。デフォルトでは、生成の際の注意点を記述しており、ユーザーには見せない部分。注意点などはここに記述してください。",
    disabled: false,
    type: "text",
  },
  {
    key: "document_limit",
    description:
      "Azure AI Searchで検索してくる文書数を設定。デフォルトの値は5。類似度検索の結果の1、2位が回答に使われることが多い印象なので、15とか20とかに増やしてもノイズになって、かえって精度が落ちる。精度が出てないなと感じたら、10くらいまでは増やしてみるのも良さそう。",
    disabled: false,
    type: "number",
  },
  {
    key: "text_chunk_size",
    description:
      "テキストデータを区切る文字数を設定。デフォルトは500。1,000とかに増やすのも良さそう。精度に効いてくる部分。小さい方が詳細な回答が得られる一方で、大きい方が概論的な回答を得られる印象。クライアントのドキュメントやユースケースによって最適なチャンクサイズは変わる。",
    disabled: false,
    type: "number",
  },
  {
    key: "chunk_overlap",
    description:
      "各チャンクにまたがる文字数を設定。デフォルトは50。増やしすぎるとチャンク間の記述内容の差異が小さくなるため、0〜10程度で良さそう。大きくしすぎない限りはあまり精度に影響しない印象。",
    disabled: false,
    type: "number",
  },
  {
    key: "table_chunk_size",
    description:
      "表データ（htmlのtable、tr、tdなどのタグ）を区切る文字数を設定。デフォルトは3,000。テーブルがあるところでチャンク切りをするとカラムの情報が落ちて著しく精度が落ちるため、トークン数制限に影響が出ない範囲でできるだけ大きめの値にしている。",
    disabled: false,
    type: "number",
  },
  {
    key: "search_service_endpoint",
    description:
      "Azure AI Searchのエンドポイント。ボットごとにインデックスを作成する場合は、ボットごとにエンドポイントを設定する。",
    disabled: true,
    type: "text",
  },
] as const;
