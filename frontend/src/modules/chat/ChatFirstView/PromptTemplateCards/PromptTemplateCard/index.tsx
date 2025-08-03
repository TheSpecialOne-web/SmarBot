import styled from "@emotion/styled";
import { Card, Typography } from "@mui/material";

import { BotPromptTemplate, PromptTemplate } from "@/orval/models/backend-api";
import { theme } from "@/theme";

const StyledCard = styled(Card)(({ color }) => ({
  minWidth: "240px",
  maxWidth: "240px",
  height: "100px",
  cursor: "pointer",
  borderRadius: 5,
  textAlign: "left",
  padding: "12px",
  color: color,
}));

type Props<T> = {
  template: T;
  selected: boolean;
  selectTemplate: (template: T) => void;
};

export const PromptTemplateCard = <T extends PromptTemplate | BotPromptTemplate>({
  template,
  selected,
  selectTemplate,
}: Props<T>) => {
  return (
    <StyledCard
      onClick={() => selectTemplate(template)}
      color={selected ? theme.palette.primary.main : undefined}
    >
      <Typography
        variant="h5"
        width={1}
        overflow="hidden"
        textOverflow="ellipsis"
        whiteSpace="nowrap"
      >
        {template.title}
      </Typography>
      <Typography
        width={1}
        variant="body2"
        overflow="hidden"
        textOverflow="ellipsis"
        pt={0.5}
        sx={{
          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
        }}
      >
        {template.description || template.prompt}
      </Typography>
    </StyledCard>
  );
};
