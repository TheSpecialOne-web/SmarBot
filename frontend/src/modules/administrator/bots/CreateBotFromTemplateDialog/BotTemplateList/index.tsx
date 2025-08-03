import { Grid } from "@mui/material";

import { BotTemplate } from "@/orval/models/administrator-api";

import { BotTemplateCard } from "../../BotTemplateCard";

type Props = {
  templates: BotTemplate[];
  onSelect: (template: BotTemplate) => void;
};

export const BotTemplateList = ({ templates, onSelect }: Props) => {
  return (
    <Grid container spacing={4}>
      {templates.map((template, index) => (
        <Grid item xs={6} md={4} lg={3} key={index}>
          <BotTemplateCard
            botTemplate={template}
            handleSelectBotTemplate={() => onSelect(template)}
          />
        </Grid>
      ))}
    </Grid>
  );
};
