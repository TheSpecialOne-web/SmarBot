import { AdditionalPlatform } from "@/orval/models/administrator-api";

export const displayAdditionalPlatform = (platform: AdditionalPlatform) => {
  switch (platform) {
    case AdditionalPlatform.gcp:
      return "GCP";
    case AdditionalPlatform.openai:
      return "OpenAI";
    default:
      return "";
  }
};
