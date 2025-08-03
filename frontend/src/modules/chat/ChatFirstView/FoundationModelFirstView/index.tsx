import AssignmentRoundedIcon from "@mui/icons-material/AssignmentRounded";
import { Box, Stack, Typography } from "@mui/material";
import { FormEvent, useState } from "react";

import { SearchField } from "@/components/inputs/SearchField";
import { Spacer } from "@/components/spacers/Spacer";
import { filterTest } from "@/libs/searchFilter";
import { useGetPromptTemplates } from "@/orval/backend-api";
import { PromptTemplate } from "@/orval/models/backend-api";

import { PromptTemplateCards } from "../PromptTemplateCards";

const filterPromptTemplate = (promptTemplates: PromptTemplate[], query: string) => {
  return promptTemplates.filter(promptTemplate => {
    return filterTest(query, [promptTemplate.title, promptTemplate.description]);
  });
};

type Props = {
  onInput: (question: string) => void;
  showPromptTemplates?: boolean;
};

export const FoundationModelFirstView = ({ onInput, showPromptTemplates }: Props) => {
  const { data, isValidating: loadingGetPromptTemplates } = useGetPromptTemplates({
    swr: { enabled: showPromptTemplates },
  });

  const [searchQuery, setSearchQuery] = useState<string>("");

  const promptTemplates = filterPromptTemplate(data?.prompt_templates || [], searchQuery);

  const handleSearchChange = (event: FormEvent<HTMLInputElement>) => {
    setSearchQuery(event.currentTarget.value);
  };

  return (
    <>
      <Stack direction="row" sx={{ justifyContent: "flex-start", pl: 1 }}>
        <AssignmentRoundedIcon />
        <Typography variant="h4">プロンプトテンプレート</Typography>
      </Stack>
      <Spacer px={8} horizontal={false} />

      <Box sx={{ pl: 1 }}>
        <SearchField value={searchQuery} onChange={handleSearchChange} />
      </Box>
      <Spacer px={8} horizontal={false} />
      {showPromptTemplates && (
        <PromptTemplateCards<PromptTemplate>
          promptTemplates={promptTemplates}
          onInput={onInput}
          loading={loadingGetPromptTemplates}
        />
      )}
    </>
  );
};
