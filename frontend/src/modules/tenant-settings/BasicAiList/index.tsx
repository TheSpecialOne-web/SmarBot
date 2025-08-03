import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import { IconButton, Stack, Typography } from "@mui/material";
import { useState } from "react";

import { modelNames } from "@/const/modelFamily";
import { Approach, Bot, ModelFamilyOrText2ImageModelFamily } from "@/orval/models/backend-api";

const getModelFamilyFromBasicAi = (bot: Bot): string | null => {
  if (bot.approach === Approach.chat_gpt_default) {
    return modelNames[bot.model_family];
  }
  if (bot.approach === Approach.text_2_image && bot.text2image_model_family) {
    return modelNames[bot.text2image_model_family];
  }
  return null;
};

type Props = {
  basicAIs: Bot[];
  onDelete: (modelFamily: ModelFamilyOrText2ImageModelFamily) => Promise<void>;
  isLoading: boolean;
};

export const BasicAiList = ({ basicAIs, onDelete, isLoading }: Props) => {
  const [deletingModelFamily, setDeletingModelFamily] =
    useState<ModelFamilyOrText2ImageModelFamily | null>();

  const handleDelete = async (bot: Bot) => {
    await onDelete(
      bot.text2image_model_family && bot.approach === Approach.text_2_image
        ? bot.text2image_model_family
        : bot.model_family,
    );
    setDeletingModelFamily(null);
  };

  return (
    <>
      <Typography variant="h5">基盤モデル一覧</Typography>
      <Stack gap={0.5} sx={{ px: 1.5, py: 1 }}>
        {basicAIs.map(bot => {
          const modelFamily = getModelFamilyFromBasicAi(bot);
          if (!modelFamily) {
            return null;
          }
          return (
            <Stack
              key={bot.model_family}
              direction="row"
              alignItems="center"
              justifyContent="space-between"
            >
              <Typography>{modelFamily}</Typography>
              <IconButton
                onClick={() => {
                  handleDelete(bot);
                }}
                disabled={isLoading && bot.model_family === deletingModelFamily}
              >
                <DeleteOutlineOutlinedIcon
                  color={
                    isLoading && bot.model_family === deletingModelFamily ? "disabled" : "error"
                  }
                />
              </IconButton>
            </Stack>
          );
        })}
      </Stack>
    </>
  );
};
