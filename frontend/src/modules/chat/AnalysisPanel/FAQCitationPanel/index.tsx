import { Divider, Stack, Typography } from "@mui/material";

import { CircularLoading } from "@/components/loadings/CircularLoading";
import { QuestionAnswer } from "@/orval/models/backend-api";
import { formatDate } from "@/utils/formatDate";

type Props = {
  loading: boolean;
  questionAnswerToDisplay: QuestionAnswer | null;
};

export const FAQCitationPanel = ({ loading, questionAnswerToDisplay }: Props) => {
  if (loading || questionAnswerToDisplay === null) {
    return (
      <Stack height="100%" justifyContent="center" alignItems="center">
        <CircularLoading />
      </Stack>
    );
  }

  const citationContents = [
    { title: "質問", content: questionAnswerToDisplay.question },
    { title: "回答", content: questionAnswerToDisplay.answer },
    { title: "最終更新日時", content: formatDate(questionAnswerToDisplay.updated_at) },
  ];

  return (
    <>
      <Stack p={2} pb={1.5}>
        <Typography variant="h4">FAQ参照元</Typography>
      </Stack>

      <Divider />

      <Stack p={2} gap={2}>
        {citationContents.map((content, i) => (
          <Stack key={i} gap={1}>
            <Typography variant="h5">{content.title}</Typography>
            <Typography pl={1}>{content.content}</Typography>
          </Stack>
        ))}
      </Stack>
    </>
  );
};
