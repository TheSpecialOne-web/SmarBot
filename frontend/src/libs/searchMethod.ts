import { SearchMethod } from "@/orval/models/administrator-api";

export const displaySearchMethodForAdministrator = (searchMethod: SearchMethod): string => {
  switch (searchMethod) {
    case SearchMethod.bm25:
      return "BM25";
    case SearchMethod.vector:
      return "ベクトル検索";
    case SearchMethod.hybrid:
      return "ハイブリッド検索";
    case SearchMethod.semantic_hybrid:
      return "セマンティックハイブリッド検索";
    case SearchMethod.ursa:
      return "Ursa Major 資料検索";
    case SearchMethod.ursa_semantic:
      return "Ursa Major セマンティック検索";
    default:
      throw new Error("Invalid search method");
  }
};

export const displaySearchMethodForUser = (searchMethod: SearchMethod): string => {
  switch (searchMethod) {
    case SearchMethod.bm25:
      return "キーワード検索";
    case SearchMethod.vector:
      return "ベクトル検索";
    case SearchMethod.hybrid:
      return "ハイブリッド検索";
    case SearchMethod.semantic_hybrid:
      return "高精度検索";
    case SearchMethod.ursa:
      return "Ursa Major 資料検索";
    case SearchMethod.ursa_semantic:
      return "Ursa Major セマンティック検索";
    default:
      throw new Error("Invalid search method");
  }
};

export const SEARCH_METHODS_FOR_USER = [SearchMethod.semantic_hybrid, SearchMethod.bm25];
