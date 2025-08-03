import random
import unicodedata

from tqdm import tqdm  # type: ignore

from .parameters_tuning import (
    set_bm25_weights,
    set_scoring_profile,
    set_semantic_config,
)
from .search_documents_for_ursa import search_documents_for_ursa
from .utils import convert_to_windows_path


def fullwidth_to_halfwidth(text: str) -> str:
    """
    全角文字を半角文字に変換する
    Args:
        text: 変換対象の文字列
    Returns:
        変換後の文字列
    """
    result = []
    for char in text:
        code = ord(char)
        if 0xFF01 <= code <= 0xFF5E:
            code -= 0xFEE0
        elif code == 0x3000:
            code = 0x0020
        result.append(chr(code))
    return "".join(result)


def calculate_mrr(ranks: list) -> float:
    """
    MRR (Mean Reciprocal Rank) を計算する関数。無効なランク（-1や0）は無視する。
    """
    valid_ranks = [r + 1 for r in ranks if r >= 0]  # -1や0の値は無視
    if not valid_ranks:
        return 0.0  # 有効なランキングがない場合は MRR を 0 にする
    reciprocal_ranks = [1.0 / r for r in valid_ranks]
    return sum(reciprocal_ranks) / len(valid_ranks)


def get_rank(
    questions: list,
    answers: list,
    vector_search_params: dict | None = None,
    vector_search: bool = False,
) -> list:
    """
    与えられた質問と回答を用いて、検索結果のランキングを取得する。
    Args:
        questions (list): 質問のリスト
        answers (list): 回答のリスト
        vector_search_params (dict): ベクトル検索のパラメータ
        vector_search (bool): ベクトル検索を行うかどうか
    Returns:
        検索結果のランキング
    """
    rank = []
    for question, answer in zip(questions, answers):
        windows_path = convert_to_windows_path(answer)
        windows_path = unicodedata.normalize("NFC", windows_path)
        windows_path = fullwidth_to_halfwidth(windows_path)
        search_result = search_documents_for_ursa(
            question,
            1000,
            vector_search_params,
            vector_search,
        )
        found = False
        for i, result in enumerate(search_result):
            if unicodedata.normalize("NFC", result["full_path"]) == windows_path:
                rank.append(i)
                found = True
                break
        if not found:
            rank.append(-1)
    print(f"Rank: {rank}")
    return rank


def optimize_parameters_experiment(
    questions: list,
    answers: list,
    params: dict | None = None,
    bm25_experiment: bool = False,
    semantic_experiment: bool = False,
    title_field_experiment: bool = False,
    content_field_experiment: bool = True,
    keywords_field_experiment: bool = False,
    scoring_profile_experiment: bool = False,
    file_name_weight_experiment: bool = True,
    construction_name_weight_experiment: bool = True,
    interpolation_path_weight_experiment: bool = True,
    content_weight_experiment: bool = True,
    vector_search_experiment: bool = False,
) -> tuple:
    """
    パラメータの最適化を実施するための実験を行う関数。

    この関数は、複数のパラメータに対してランダムまたは指定された範囲内で実験を行い、
    与えられた質問と回答に基づいて最適なランキング結果を見つけるために使用されます。

    Args:
        questions (list): 実験で使用する質問のリスト。
        answers (list): 実験で使用する正しい回答のリスト。
        params (dict, optional): 実験で使用する初期パラメータの辞書。デフォルトは None。
        bm25_experiment (bool, optional): BM25 パラメータを実験に含めるかどうか。デフォルトは False。
        semantic_experiment (bool, optional): セマンティック検索のパラメータを実験に含めるかどうか。デフォルトは False。
        title_field_experiment (bool, optional): タイトルフィールドに関連する実験を行うかどうか。デフォルトは False。
        content_field_experiment (bool, optional): コンテンツフィールドに関連する実験を行うかどうか。デフォルトは True。
        keywords_field_experiment (bool, optional): キーワードフィールドに関連する実験を行うかどうか。デフォルトは False。
        scoring_profile_experiment (bool, optional): スコアリングプロファイルに関連する実験を行うかどうか。デフォルトは False。
        file_name_weight_experiment (bool, optional): ファイル名の重み付けの実験を行うかどうか。デフォルトは True。
        construction_name_weight_experiment (bool, optional): 工事名の重み付けの実験を行うかどうか。デフォルトは True。
        interpolation_path_weight_experiment (bool, optional): 補間パスの重み付けの実験を行うかどうか。デフォルトは True。
        content_weight_experiment (bool, optional): コンテンツの重み付けの実験を行うかどうか。デフォルトは True。
        vector_search_experiment (bool, optional): ベクター検索の実験を行うかどうか。デフォルトは False。

    Returns:
        dict: 最適化されたパラメータの辞書とそのパラメータによるランク結果。
    """

    experiment_params = params if params else {}

    if bm25_experiment:
        k1 = round(random.gauss(1.2, 1.2 * 0.1), 2)
        b = round(random.gauss(0.75, 0.75 * 0.1), 2)
        experiment_params["bm25"] = {"k1": k1, "b": b}
        set_bm25_weights(experiment_params)
    else:
        bm25_params = params.get("bm25", None) if params else None
        k1 = bm25_params.get("k1", 1.2) if params else 1.2
        b = bm25_params.get("b", 0.75) if params else 0.75
        experiment_params["bm25"] = {"k1": k1, "b": b}

    if semantic_experiment:
        semantic_config_params = params.get("semantic_config", None) if params else None
        fields = ["file_name", "content", "construction_name", "interpolation_path", "full_path"]
        random.shuffle(fields)
        if title_field_experiment:
            title_field = random.sample(fields, 1)
        else:
            title_field = (
                semantic_config_params.get("title_field", "file_name") if semantic_config_params else "file_name"
            )

        if content_field_experiment:
            content_field = random.sample(fields, k=random.randint(0, len(fields)))
        else:
            content_field = (
                semantic_config_params.get("content_field", ["file_name", "full_path", "content"])
                if semantic_config_params
                else ["file_name", "full_path", "content"]
            )

        if keywords_field_experiment:
            keywords_field = random.sample(fields, k=random.randint(0, len(fields)))
        else:
            keywords_field = semantic_config_params.get("keywords_field", []) if semantic_config_params else []

        experiment_params["semantic_config"] = {
            "title_field": title_field,
            "content_field": content_field,
            "keywords_field": keywords_field,
        }
        set_semantic_config(experiment_params)

    else:
        semantic_config_params = params.get("semantic_config", None) if params else None
        title_field = (
            semantic_config_params.get("title_field", "title_field") if semantic_config_params else "title_field"
        )
        content_field = (
            semantic_config_params.get("content_field", ["file_name", "full_path", "content"])
            if semantic_config_params
            else ["file_name", "full_path", "content"]
        )
        keywords_field = semantic_config_params.get("keywords_field", []) if semantic_config_params else []
        experiment_params["semantic_config"] = {
            "title_field": title_field,
            "content_field": content_field,
            "keywords_field": keywords_field,
        }

    if scoring_profile_experiment:
        scoring_params = params.get("scoring_profile", None) if params else None
        if file_name_weight_experiment:
            file_name_weight = round(random.uniform(0.1, 10), 1)
        else:
            file_name_weight = scoring_params.get("file_name_weight", 2) if scoring_params else 2
        if construction_name_weight_experiment:
            construction_name_weight = round(random.uniform(0.1, 10), 1)
        else:
            construction_name_weight = scoring_params.get("construction_name_weight", 0.5) if scoring_params else 0.5
        if interpolation_path_weight_experiment:
            interpolation_path_weight = round(random.uniform(0.1, 10), 1)
        else:
            interpolation_path_weight = scoring_params.get("interpolation_path_weight", 0.5) if scoring_params else 0.5

        experiment_params["scoring_profile"] = {
            "file_name_weight": file_name_weight,
            "construction_name_weight": construction_name_weight,
            "interpolation_path_weight": interpolation_path_weight,
        }

        if content_weight_experiment:
            content_weight = round(random.uniform(0.1, 10), 1)
            experiment_params["scoring_profile"]["content_weight"] = content_weight

        set_scoring_profile(experiment_params)

    else:
        scoring_params = params.get("scoring_profile", None) if params else None
        file_name_weight = scoring_params.get("file_name_weight", 2) if scoring_params else 2
        construction_name_weight = scoring_params.get("construction_name_weight", 0.5) if scoring_params else 0.5
        interpolation_path_weight = scoring_params.get("interpolation_path_weight", 0.5) if scoring_params else 0.5
        experiment_params["scoring_profile"] = {
            "file_name_weight": file_name_weight,
            "construction_name_weight": construction_name_weight,
            "interpolation_path_weight": interpolation_path_weight,
        }

    if vector_search_experiment:
        path_weight = round(random.uniform(0.1, 10), 1)  # type: ignore
        content_weight = round(random.uniform(0.1, 10), 1)  # type: ignore
        experiment_params["vector_search"] = {
            "path_weight": path_weight,
            "content_weight": content_weight,
        }

    rank = get_rank(questions, answers, experiment_params, vector_search_experiment)
    return experiment_params, rank


def search_parameters_exceed_baseline(
    questions: list,
    answers: list,
    baseline_rank: list,
    experiment_counts: int,
    params: dict | None = None,
    bm25_experiment: bool = False,
    semantic_experiment: bool = False,
    title_field_experiment: bool = False,
    content_field_experiment: bool = True,
    keywords_field_experiment: bool = False,
    scoring_profile_experiment: bool = False,
    file_name_weight_experiment: bool = True,
    construction_name_weight_experiment: bool = True,
    interpolation_path_weight_experiment: bool = True,
    content_weight_experiment: bool = True,
    vector_search_experiment: bool = False,
):
    """
    ベースラインのランキングを超えるパラメータを探索する関数。

    Args:
        questions (list): 質問のリスト。
        answers (list): 回答のリスト。
        baseline_rank (list): 比較する基準となるランキング。
        experiment_counts (int): 実験を行う回数。
        params (dict, optional): 実験に使用するパラメータの辞書。デフォルトは None。
        bm25_experiment (bool, optional): BM25 パラメータを実験に含めるかどうか。デフォルトは False。
        semantic_experiment (bool, optional): セマンティック検索を実験に含めるかどうか。デフォルトは False。
        title_field_experiment (bool, optional): タイトルフィールドに関連する実験を行うかどうか。デフォルトは False。
        content_field_experiment (bool, optional): コンテンツフィールドに関連する実験を行うかどうか。デフォルトは True。
        keywords_field_experiment (bool, optional): キーワードフィールドに関連する実験を行うかどうか。デフォルトは False。
        scoring_profile_experiment (bool, optional): スコアリングプロファイルを実験に含めるかどうか。デフォルトは False。
        file_name_weight_experiment (bool, optional): ファイル名の重み付けに関連する実験を行うかどうか。デフォルトは True。
        construction_name_weight_experiment (bool, optional): 工事名の重み付けに関連する実験を行うかどうか。デフォルトは True。
        interpolation_path_weight_experiment (bool, optional): 補間パスの重み付けに関連する実験を行うかどうか。デフォルトは True。
        content_weight_experiment (bool, optional): コンテンツの重み付けに関連する実験を行うかどうか。デフォルトは True。
        vector_search_experiment (bool, optional): ベクター検索を実験に含めるかどうか。デフォルトは False。

    Returns:
        tuple: ベースラインを超えた場合は、最適なパラメータと新しいランキングを返す。ベースラインを超えない場合は (None, None) を返す。
    """
    experiment_params = params if params else {}
    if not bm25_experiment:
        experiment_params["bm25"] = params.get("bm25", {"k1": 1.2, "b": 0.75}) if params else {"k1": 1.2, "b": 0.75}
        set_bm25_weights(experiment_params)

    if not semantic_experiment:
        experiment_params["semantic_config"] = (
            params.get(
                "semantic_config",
                {
                    "title_field": "file_name",
                    "content_field": ["file_name", "full_path", "content"],
                    "keywords_field": [],
                },
            )
            if params
            else {
                "title_field": "file_name",
                "content_field": ["file_name", "full_path", "content"],
                "keywords_field": [],
            }
        )
        set_semantic_config(experiment_params)

    if not scoring_profile_experiment:
        experiment_params["scoring_profile"] = (
            params.get(
                "scoring_profile",
                {"file_name_weight": 2, "construction_name_weight": 0.5, "interpolation_path_weight": 0.5},
            )
            if params
            else {"file_name_weight": 2, "construction_name_weight": 0.5, "interpolation_path_weight": 0.5}
        )
        set_scoring_profile(experiment_params)

    # tqdm を使って実験進捗を表示
    for experiment_count in tqdm(range(experiment_counts), desc="Running experiments"):
        # 実験パラメータとランキングを最適化する
        experiment_params, rank = optimize_parameters_experiment(
            questions,
            answers,
            params,
            bm25_experiment,
            semantic_experiment,
            title_field_experiment,
            content_field_experiment,
            keywords_field_experiment,
            scoring_profile_experiment,
            file_name_weight_experiment,
            construction_name_weight_experiment,
            interpolation_path_weight_experiment,
            content_weight_experiment,
            vector_search_experiment,
        )

        # 新しいランキングに -1 が含まれている場合、スキップ
        if -1 in rank:
            print(f"Experiment {experiment_count + 1} contains invalid rank (-1), skipping.")
            continue

        # 新しい MRR を計算
        new_mrr = calculate_mrr(rank)
        print(f"Experiment {experiment_count + 1}: New MRR: {new_mrr}")

        # 各実験の結果を出力
        print(f"Experiment {experiment_count + 1}/{experiment_counts}")
        print(f"Experiment Params: {experiment_params}")
        print(f"Rank: {rank}")
        print(f"Baseline Rank: {baseline_rank}")

        # 新しい MRR がベースラインよりも良い場合、結果を返す
        baseline_mrr = calculate_mrr(baseline_rank)
        if new_mrr > baseline_mrr:
            print(f"Found better parameters at experiment {experiment_count + 1}")
            return experiment_params, rank

    # ベースラインを超えるものが見つからなかった場合
    print("Baseline rank is the best across all experiments.")
    return None, None
