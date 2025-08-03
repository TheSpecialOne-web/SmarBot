import ContactSupportOutlinedIcon from "@mui/icons-material/ContactSupportOutlined";
import { Box, Button, Stack } from "@mui/material";

type Props = {
  questions: string[];
  onQuestionClicked: (question: string) => Promise<void>;
};

export const FollowUpQuestions = ({ questions, onQuestionClicked }: Props) => {
  return (
    <Stack gap={1} alignItems="flex-end">
      <ContactSupportOutlinedIcon color="primary" />
      {questions.map((question, index) => (
        <Box key={index}>
          <Button
            onClick={() => onQuestionClicked(question)}
            sx={{
              py: 0,
              px: 1,
              textAlign: "left",
              backgroundColor: "white",
            }}
            variant="outlined"
          >
            {question}
          </Button>
        </Box>
      ))}
    </Stack>
  );
};
