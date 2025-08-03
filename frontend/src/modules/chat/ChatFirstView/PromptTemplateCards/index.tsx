import { Box, Skeleton, Stack, styled } from "@mui/material";
import { useState } from "react";

import { Spacer } from "@/components/spacers/Spacer";
import { useScreen } from "@/hooks/useScreen";
import { useWindowSize } from "@/hooks/useWindowSize";
import { BotPromptTemplate, PromptTemplate } from "@/orval/models/backend-api";

import { PromptTemplateCard } from "./PromptTemplateCard";

const ShadeLeft = styled(Box)({
  position: "absolute",
  left: "-20px",
  zIndex: 10,
  minHeight: "100%",
  width: "36px",
  background: "linear-gradient(to right, primaryBackground.main 50%, transparent)",
});

const ShadeRight = styled(Box)({
  position: "absolute",
  right: "-20px",
  zIndex: 10,
  minHeight: "100%",
  width: "36px",
  background: "linear-gradient(to left, primaryBackground.main 50%, transparent)",
});

type Props<T> = {
  onInput: (question: string) => void;
  promptTemplates: T[];
  loading: boolean;
};

// スケルトンの行の数
const SKELETON_ROW_NUM = 6;

const PromptTemplateCardsSkeleton = () => {
  return (
    <>
      <Stack direction="row" spacing={1}>
        {Array.from({ length: SKELETON_ROW_NUM }).map((_, index) => (
          <Skeleton
            key={index}
            animation="pulse"
            variant="rounded"
            sx={{
              minWidth: "240px",
              maxWidth: "240px",
              height: "100px",
              cursor: "pointer",
              borderRadius: 2,
            }}
          />
        ))}
      </Stack>
      <Spacer px={16} />
      <Stack direction="row" spacing={1}>
        {Array.from({ length: SKELETON_ROW_NUM }).map((_, index) => (
          <Skeleton
            key={index + SKELETON_ROW_NUM}
            animation="pulse"
            variant="rounded"
            sx={{
              minWidth: "240px",
              maxWidth: "240px",
              height: "100px",
              cursor: "pointer",
              borderRadius: 2,
            }}
          />
        ))}
      </Stack>
    </>
  );
};

const CARD_WIDTH = 248;
const DESKTOP_PADDING = 320;
const MOBILE_PADDING = 60;

export const PromptTemplateCards = <T extends PromptTemplate | BotPromptTemplate>({
  onInput,
  promptTemplates,
  loading,
}: Props<T>) => {
  const [selectedTemplate, setSelectedTemplate] = useState<T | null>(null);

  const reversedPromptTemplates = [...promptTemplates].reverse();

  const oddTemplates = reversedPromptTemplates.filter((_, index) => index % 2 === 0);
  const evenTemplates = reversedPromptTemplates.filter((_, index) => index % 2 !== 0);

  const { isDesktop } = useScreen();

  const [width] = useWindowSize();
  const displayItemsNum = isDesktop
    ? (width - DESKTOP_PADDING) / CARD_WIDTH
    : (width - MOBILE_PADDING) / CARD_WIDTH;

  const selectTemplate = (promptTemplate: T) => {
    if (promptTemplate.id === selectedTemplate?.id) {
      setSelectedTemplate(null);
      onInput("");
      return;
    }
    setSelectedTemplate(promptTemplate);
    onInput(promptTemplate.prompt);
  };

  if (loading) {
    return <PromptTemplateCardsSkeleton />;
  }

  if (promptTemplates.length === 0) {
    return null;
  }

  return (
    <Box sx={{ position: "relative" }}>
      <ShadeRight />
      <ShadeLeft />
      <Box sx={{ overflow: "auto", pb: 2, px: 1 }}>
        <Stack
          direction="row"
          spacing={1}
          justifyContent={oddTemplates.length < displayItemsNum ? "center" : "flex-start"}
        >
          {oddTemplates.map(template => (
            <PromptTemplateCard
              key={template.id}
              template={template}
              selected={selectedTemplate?.id === template.id}
              selectTemplate={selectTemplate}
            />
          ))}
        </Stack>
        <Spacer px={16} />
        <Stack
          direction="row"
          spacing={1}
          justifyContent={oddTemplates.length < displayItemsNum ? "center" : "flex-start"}
        >
          {evenTemplates.map(template => (
            <PromptTemplateCard
              key={template.id}
              template={template}
              selected={selectedTemplate?.id === template.id}
              selectTemplate={selectTemplate}
            />
          ))}
        </Stack>
      </Box>
    </Box>
  );
};
