import {
  ModelFamilies,
  ModelFamily,
  Text2ImageModelFamily,
} from "@/orval/models/administrator-api";

export const getTextGenerationModelFamiliesFromAllowedModelFamilies = (
  allowedModelFamilies: ModelFamilies,
): ModelFamily[] => {
  const textGenerationModels = Object.values(ModelFamily);
  return allowedModelFamilies.model_families.filter(model =>
    textGenerationModels.includes(model as ModelFamily),
  ) as ModelFamily[];
};

export const getImageGenerationModelFamiliesFromAllowedModelFamilies = (
  allowedModelFamilies: ModelFamilies,
): Text2ImageModelFamily[] => {
  const imageGenerationModels = Object.values(Text2ImageModelFamily);
  return allowedModelFamilies.model_families.filter(model =>
    imageGenerationModels.includes(model as Text2ImageModelFamily),
  ) as Text2ImageModelFamily[];
};
