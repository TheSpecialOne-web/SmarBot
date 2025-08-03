import {
  ModelFamiliesAndText2ImageModelFamilies,
  ModelFamily,
  Text2ImageModelFamily,
} from "@/orval/models/backend-api";

export const getTextGenerationModelFamiliesFromAllowedModelFamilies = (
  allowedModelFamilies: ModelFamiliesAndText2ImageModelFamilies,
): ModelFamily[] => {
  return allowedModelFamilies.model_families.filter(model => isModelFamily(model)) as ModelFamily[];
};

export const isModelFamily = (
  modelFamily: ModelFamily | Text2ImageModelFamily,
): modelFamily is ModelFamily => {
  return Object.values(ModelFamily).includes(modelFamily as ModelFamily);
};

export const isText2ImageModelFamily = (
  modelFamily: ModelFamily | Text2ImageModelFamily,
): modelFamily is Text2ImageModelFamily => {
  return Object.values(Text2ImageModelFamily).includes(modelFamily as Text2ImageModelFamily);
};
